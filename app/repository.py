from typing import Iterable, List, Optional, Tuple
import sqlite3

try:
	import psycopg2
	import psycopg2.extras
except Exception:  # pragma: no cover
	psycopg2 = None  # type: ignore

from .models import Paper
from .config import DB_BACKEND


def _row_to_paper(row) -> Paper:
	# row can be sqlite3.Row or dict from psycopg2.extras
	get = row.__getitem__ if isinstance(row, sqlite3.Row) else (lambda k: row[k])
	
	# Handle missing full_text column gracefully
	try:
		full_text = get("full_text") or ""
	except (KeyError, IndexError):
		full_text = ""  # Default to empty string if column doesn't exist
	
	return Paper(
		id=get("id"),
		title=get("title"),
		authors=get("authors"),
		year=get("year"),
		abstract=get("abstract") or "",
		department=get("department") or "",
		paper_type=get("paper_type") or "",
		research_domain=get("research_domain") or "",
		publisher=get("publisher") or "",
		student=get("student") or "",
		review_status=get("review_status") or "",
		file_path=get("file_path"),
		full_text=full_text,
	)


class PaperRepository:
	def __init__(self, conn) -> None:
		self.conn = conn

	def _placeholders(self, n: int) -> str:
		return ", ".join(["%s" if DB_BACKEND == "postgres" else "?"] * n)

	def add_paper(self, paper: Paper) -> Paper:
		params = (
			paper.title,
			paper.authors,
			paper.year,
			paper.abstract,
			paper.department,
			paper.paper_type,
			paper.research_domain,
			paper.publisher,
			paper.student,
			paper.review_status,
			paper.file_path,
			paper.full_text,
		)
		if DB_BACKEND == "sqlite":
			with self.conn:
				cur = self.conn.execute(
					f"""
					INSERT INTO papers
					(title, authors, year, abstract, department, paper_type, research_domain, publisher, student, review_status, file_path, full_text)
					VALUES ({self._placeholders(12)})
					""",
					params,
				)
				new_id = cur.lastrowid
		else:
			cur = self.conn.cursor()
			cur.execute(
				f"""
				INSERT INTO papers (title, authors, year, abstract, department, paper_type, research_domain, publisher, student, review_status, file_path, full_text)
				VALUES ({self._placeholders(12)}) RETURNING id
				""",
				params,
			)
			new_id = cur.fetchone()[0]
			self.conn.commit()
			cur.close()
		return Paper(id=new_id, **{k: v for k, v in paper.__dict__.items() if k != "id"})

	def update_full_text(self, paper_id: int, full_text: str) -> bool:
		"""Update the full text content of a paper"""
		try:
			if DB_BACKEND == "sqlite":
				with self.conn:
					cur = self.conn.execute(
						"UPDATE papers SET full_text = ? WHERE id = ?",
						(full_text, paper_id)
					)
					return cur.rowcount > 0
			else:
				cur = self.conn.cursor()
				cur.execute(
					"UPDATE papers SET full_text = %s WHERE id = %s",
					(full_text, paper_id)
				)
				self.conn.commit()
				cur.close()
				return cur.rowcount > 0
		except Exception as e:
			print(f"Error updating full text: {e}")
			return False

	def list_all(self) -> List[Paper]:
		if DB_BACKEND == "sqlite":
			cur = self.conn.execute("SELECT * FROM papers ORDER BY created_at DESC")
			rows = cur.fetchall()
		else:
			cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[arg-type]
			cur.execute("SELECT * FROM papers ORDER BY created_at DESC")
			rows = cur.fetchall()
			cur.close()
		return [_row_to_paper(r) for r in rows]

	def find_by_id(self, paper_id: int) -> Optional[Paper]:
		if DB_BACKEND == "sqlite":
			cur = self.conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
			row = cur.fetchone()
		else:
			cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[arg-type]
			cur.execute("SELECT * FROM papers WHERE id = %s", (paper_id,))
			row = cur.fetchone()
			cur.close()
		return _row_to_paper(row) if row else None

	def list_by_field(self, field_name: str, field_value: str) -> List[Paper]:
		if field_name not in {
			"year",
			"authors",
			"paper_type",
			"research_domain",
			"publisher",
			"student",
			"review_status",
			"department",
		}:
			raise ValueError("Unsupported filter field")
		op = "%s" if DB_BACKEND == "postgres" else "?"
		query = f"SELECT * FROM papers WHERE {field_name} = {op} ORDER BY year DESC, title ASC"
		if DB_BACKEND == "sqlite":
			cur = self.conn.execute(query, (field_value,))
			rows = cur.fetchall()
		else:
			cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[arg-type]
			cur.execute(query, (field_value,))
			rows = cur.fetchall()
			cur.close()
		return [_row_to_paper(r) for r in rows]

	def get_distinct_values(self, field_name: str) -> List[str]:
		if field_name not in {
			"year",
			"authors",
			"paper_type",
			"research_domain",
			"publisher",
			"student",
			"review_status",
			"department",
		}:
			raise ValueError("Unsupported field")
		
		# Handle integer fields differently
		if field_name == "year":
			if DB_BACKEND == "sqlite":
				cur = self.conn.execute(
					f"SELECT DISTINCT {field_name} AS v FROM papers WHERE {field_name} IS NOT NULL ORDER BY v ASC"
				)
				rows = cur.fetchall()
			else:
				cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[arg-type]
				cur.execute(
					f"SELECT DISTINCT {field_name} AS v FROM papers WHERE {field_name} IS NOT NULL ORDER BY v ASC"
				)
				rows = cur.fetchall()
				cur.close()
		else:
			# For text fields, check both NULL and empty string
			if DB_BACKEND == "sqlite":
				cur = self.conn.execute(
					f"SELECT DISTINCT {field_name} AS v FROM papers WHERE {field_name} IS NOT NULL AND {field_name} <> '' ORDER BY v ASC"
				)
				rows = cur.fetchall()
			else:
				cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[arg-type]
				cur.execute(
					f"SELECT DISTINCT {field_name} AS v FROM papers WHERE {field_name} IS NOT NULL AND {field_name} <> '' ORDER BY v ASC"
				)
				rows = cur.fetchall()
				cur.close()
		
		return [r["v"] if isinstance(r, sqlite3.Row) else r["v"] for r in rows]

	def get_corpus(self) -> Tuple[list[int], list[str]]:
		if DB_BACKEND == "sqlite":
			cur = self.conn.execute("SELECT * FROM papers")
			rows = cur.fetchall()
		else:
			cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore[arg-type]
			cur.execute("SELECT * FROM papers")
			rows = cur.fetchall()
			cur.close()
		paper_ids: list[int] = []
		texts: list[str] = []
		for r in rows:
			p = _row_to_paper(r)
			paper_ids.append(p.id or 0)
			texts.append(p.to_corpus_text())
		return paper_ids, texts 