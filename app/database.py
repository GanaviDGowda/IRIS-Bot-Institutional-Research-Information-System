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
				created_at TIMESTAMPTZ DEFAULT NOW()
			);
			CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
			CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers(authors);
			CREATE INDEX IF NOT EXISTS idx_papers_publisher ON papers(publisher);
			"""
		)
		conn.commit()
		cur.close()

	if own_conn:
		conn.close()  # type: ignore[arg-type] 