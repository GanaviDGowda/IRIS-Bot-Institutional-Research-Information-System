from typing import Optional, Union
import sqlite3

try:
	import psycopg2
	import psycopg2.extras
except Exception:  # pragma: no cover
	psycopg2 = None  # type: ignore

from .config import SQLITE_DB_PATH, ensure_directories_exist, DB_BACKEND, POSTGRES_DSN


DbConn = Union[sqlite3.Connection, "psycopg2.extensions.connection"]


def get_connection(dsn: Optional[str] = None) -> DbConn:
	if DB_BACKEND == "sqlite":
		ensure_directories_exist()
		path = dsn if dsn is not None else str(SQLITE_DB_PATH)
		conn = sqlite3.connect(path)
		conn.row_factory = sqlite3.Row
		conn.execute("PRAGMA foreign_keys = ON;")
		return conn
	# Postgres
	if psycopg2 is None:
		raise RuntimeError("psycopg2 is required for PostgreSQL backend")
	conn = psycopg2.connect(dsn or POSTGRES_DSN)
	return conn


def _add_full_text_column(conn: DbConn) -> None:
	"""Add full_text column to existing databases if it doesn't exist."""
	if DB_BACKEND == "sqlite":
		assert isinstance(conn, sqlite3.Connection)
		# Check if full_text column exists
		cursor = conn.execute("PRAGMA table_info(papers)")
		columns = [column[1] for column in cursor.fetchall()]
		
		if "full_text" not in columns:
			with conn:
				conn.execute("ALTER TABLE papers ADD COLUMN full_text TEXT")
				print("Added full_text column to SQLite database")
	else:
		# PostgreSQL
		cursor = conn.cursor()
		try:
			# Check if full_text column exists
			cursor.execute("""
				SELECT column_name 
				FROM information_schema.columns 
				WHERE table_name = 'papers' AND column_name = 'full_text'
			""")
			
			if not cursor.fetchone():
				cursor.execute("ALTER TABLE papers ADD COLUMN full_text TEXT")
				conn.commit()
				print("Added full_text column to PostgreSQL database")
		except Exception as e:
			print(f"Error checking/adding full_text column: {e}")
		finally:
			cursor.close()


def init_db(conn: Optional[DbConn] = None) -> None:
	own_conn = False
	if conn is None:
		conn = get_connection()
		own_conn = True

	if DB_BACKEND == "sqlite":
		assert isinstance(conn, sqlite3.Connection)
		with conn:
			conn.executescript(
				"""
				CREATE TABLE IF NOT EXISTS papers (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					title TEXT NOT NULL,
					authors TEXT NOT NULL,
					year INTEGER NOT NULL,
					abstract TEXT,
					department TEXT,
					paper_type TEXT,
					research_domain TEXT,
					publisher TEXT,
					student TEXT,
					review_status TEXT,
					file_path TEXT NOT NULL,
					full_text TEXT,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				);
				CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
				CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers(authors);
				CREATE INDEX IF NOT EXISTS idx_papers_publisher ON papers(publisher);
				"""
			)
	else:
		# PostgreSQL DDL
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS papers (
				id SERIAL PRIMARY KEY,
				title TEXT NOT NULL,
				authors TEXT NOT NULL,
				year INT NOT NULL,
				abstract TEXT,
				department TEXT,
				paper_type TEXT,
				research_domain TEXT,
				publisher TEXT,
				student TEXT,
				review_status TEXT,
				file_path TEXT NOT NULL,
				full_text TEXT,
				created_at TIMESTAMPTZ DEFAULT NOW()
			);
			CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
			CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers(authors);
			CREATE INDEX IF NOT EXISTS idx_papers_publisher ON papers(publisher);
			"""
		)
		conn.commit()
		cur.close()

	# Add full_text column to existing databases
	_add_full_text_column(conn)

	if own_conn:
		conn.close()  # type: ignore[arg-type] 