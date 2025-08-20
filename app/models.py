from dataclasses import dataclass
from typing import Optional


@dataclass
class Paper:
	id: Optional[int]
	title: str
	authors: str
	year: int
	abstract: str
	department: str
	paper_type: str
	research_domain: str
	publisher: str
	student: str
	review_status: str
	file_path: str

	def to_corpus_text(self) -> str:
		parts = [
			self.title or "",
			self.abstract or "",
			self.authors or "",
			self.department or "",
			self.research_domain or "",
			self.publisher or "",
			self.student or "",
			self.paper_type or "",
			self.review_status or "",
		]
		return "\n".join(p for p in parts if p) 