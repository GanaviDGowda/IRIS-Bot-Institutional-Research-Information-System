from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from .repository import PaperRepository
from .models import Paper
from .config import SEARCH_TOP_K


class TfidfSearchEngine:
	def __init__(self, repository: PaperRepository) -> None:
		self.repository = repository
		self.vectorizer: Optional[TfidfVectorizer] = None
		self.doc_term_matrix = None
		self.paper_id_by_row_index: list[int] = []

	def rebuild_index(self) -> None:
		paper_ids, texts = self.repository.get_corpus()
		self.vectorizer = TfidfVectorizer(stop_words="english")
		if texts:
			self.doc_term_matrix = self.vectorizer.fit_transform(texts)
			self.paper_id_by_row_index = paper_ids
		else:
			self.doc_term_matrix = None
			self.paper_id_by_row_index = []

	def search(self, query: str, top_k: int = SEARCH_TOP_K) -> List[Tuple[Paper, float]]:
		if not query.strip():
			return []
		if self.vectorizer is None or self.doc_term_matrix is None or not self.paper_id_by_row_index:
			self.rebuild_index()
			if self.vectorizer is None or self.doc_term_matrix is None:
				return []
		query_vec = self.vectorizer.transform([query])
		scores = linear_kernel(query_vec, self.doc_term_matrix).ravel()
		if scores.size == 0:
			return []
		indices = scores.argsort()[::-1][:top_k]
		results: list[Tuple[Paper, float]] = []
		for idx in indices:
			paper_id = self.paper_id_by_row_index[idx]
			paper = self.repository.find_by_id(paper_id)
			if paper is not None:
				results.append((paper, float(scores[idx])))
		return results 