from typing import List, Tuple, Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from .repository import PaperRepository
from .models import Paper
from .config import SEARCH_TOP_K, MIN_SIMILARITY_THRESHOLD, MAX_FEATURES, ENABLE_CACHING, BATCH_INDEXING


class TfidfSearchEngine:
	def __init__(self, repository: PaperRepository) -> None:
		self.repository = repository
		self.vectorizer: Optional[TfidfVectorizer] = None
		self.doc_term_matrix = None
		self.paper_id_by_row_index: list[int] = []
		# Minimum similarity threshold to filter irrelevant results
		self.min_similarity_threshold = MIN_SIMILARITY_THRESHOLD
		
		# Performance optimizations
		self.search_cache: Dict[str, List[Tuple[Paper, float]]] = {}
		self.last_index_update = 0
		self.paper_count = 0

	def rebuild_index(self) -> None:
		"""Rebuild the search index with performance optimizations."""
		print("Building search index...")
		
		paper_ids, texts = self.repository.get_corpus()
		self.paper_count = len(paper_ids)
		
		if not texts:
			self.vectorizer = None
			self.doc_term_matrix = None
			self.paper_id_by_row_index = []
			return
		
		# Configure TF-IDF for large collections
		self.vectorizer = TfidfVectorizer(
			stop_words="english",
			max_features=MAX_FEATURES,  # Limit features for memory efficiency
			ngram_range=(1, 2),  # Include bigrams for better context
			min_df=1,  # Include words that appear in at least 1 paper (was 2)
			max_df=0.95  # Exclude words that appear in more than 95% of papers
		)
		
		print(f"Processing {len(texts)} papers...")
		self.doc_term_matrix = self.vectorizer.fit_transform(texts)
		self.paper_id_by_row_index = paper_ids
		
		# Clear cache when index is rebuilt
		self.search_cache.clear()
		self.last_index_update = self.paper_count
		
		print(f"✓ Index built with {self.doc_term_matrix.shape[1]} features")

	def _should_rebuild_index(self) -> bool:
		"""Check if index needs rebuilding based on paper count changes."""
		current_count = len(self.repository.list_all())
		return current_count != self.paper_count

	def search(self, query: str, top_k: int = SEARCH_TOP_K) -> List[Tuple[Paper, float]]:
		"""Search with caching and performance optimizations."""
		if not query.strip():
			return []
		
		# Check if index needs rebuilding
		if self._should_rebuild_index():
			print("Paper count changed, rebuilding index...")
			self.rebuild_index()
		
		# Check cache first
		cache_key = f"{query.lower().strip()}_{top_k}"
		if ENABLE_CACHING and cache_key in self.search_cache:
			return self.search_cache[cache_key]
		
		if self.vectorizer is None or self.doc_term_matrix is None or not self.paper_id_by_row_index:
			self.rebuild_index()
			if self.vectorizer is None or self.doc_term_matrix is None:
				return []
		
		query_vec = self.vectorizer.transform([query])
		scores = linear_kernel(query_vec, self.doc_term_matrix).ravel()
		
		if scores.size == 0:
			return []
		
		# Filter results by minimum similarity threshold
		relevant_indices = []
		for idx, score in enumerate(scores):
			if score >= self.min_similarity_threshold:
				relevant_indices.append((idx, score))
		
		# Sort by score (highest first) and limit to top_k
		relevant_indices.sort(key=lambda x: x[1], reverse=True)
		relevant_indices = relevant_indices[:top_k]
		
		# Build results list
		results: list[Tuple[Paper, float]] = []
		for idx, score in relevant_indices:
			paper_id = self.paper_id_by_row_index[idx]
			paper = self.repository.find_by_id(paper_id)
			if paper is not None:
				results.append((paper, float(score)))
		
		# Cache results
		if ENABLE_CACHING:
			self.search_cache[cache_key] = results
		
		return results

	def batch_import_papers(self, papers: List[Paper]) -> None:
		"""Efficiently handle batch imports without rebuilding index each time."""
		if not BATCH_INDEXING:
			# Rebuild after each import (original behavior)
			self.rebuild_index()
			return
		
		# Batch processing for better performance
		current_count = len(self.repository.list_all())
		if current_count % 10 == 0:  # Rebuild every 10 papers
			print(f"Batch threshold reached ({current_count} papers), rebuilding index...")
			self.rebuild_index()
		else:
			print(f"Paper imported. Index will be rebuilt after {10 - (current_count % 10)} more papers.")

	def set_min_similarity_threshold(self, threshold: float) -> None:
		"""Set minimum similarity threshold (0.0 to 1.0)"""
		if 0.0 <= threshold <= 1.0:
			self.min_similarity_threshold = threshold
		else:
			raise ValueError("Threshold must be between 0.0 and 1.0")

	def get_performance_stats(self) -> dict:
		"""Get performance statistics for monitoring."""
		return {
			"total_papers": self.paper_count,
			"index_features": self.vectorizer.get_feature_names_out().shape[0] if self.vectorizer else 0,
			"cache_size": len(self.search_cache),
			"memory_usage_mb": self._estimate_memory_usage(),
			"last_update": self.last_index_update
		}

	def _estimate_memory_usage(self) -> float:
		"""Estimate memory usage in MB."""
		if self.doc_term_matrix is None:
			return 0.0
		
		# Rough estimate: 8 bytes per float × matrix size
		matrix_size = self.doc_term_matrix.shape[0] * self.doc_term_matrix.shape[1]
		estimated_bytes = matrix_size * 8
		return estimated_bytes / (1024 * 1024)  # Convert to MB

	def get_search_stats(self, query: str) -> dict:
		"""Get search statistics for debugging."""
		if not query.strip():
			return {"total_papers": 0, "relevant_papers": 0, "threshold": self.min_similarity_threshold}
		
		if self.vectorizer is None or self.doc_term_matrix is None:
			return {"error": "Index not built"}
		
		query_vec = self.vectorizer.transform([query])
		scores = linear_kernel(query_vec, self.doc_term_matrix).ravel()
		
		total_papers = len(scores)
		relevant_papers = sum(1 for score in scores if score >= self.min_similarity_threshold)
		
		return {
			"total_papers": total_papers,
			"relevant_papers": relevant_papers,
			"threshold": self.min_similarity_threshold,
			"max_score": float(scores.max()) if scores.size > 0 else 0.0,
			"min_score": float(scores.min()) if scores.size > 0 else 0.0,
			"avg_score": float(scores.mean()) if scores.size > 0 else 0.0,
			"cache_hit": query.lower().strip() in [k.split('_')[0] for k in self.search_cache.keys()]
		}

	def clear_cache(self) -> None:
		"""Clear search cache to free memory."""
		self.search_cache.clear()
		print("Search cache cleared")

	def optimize_for_large_collection(self) -> None:
		"""Apply optimizations for large paper collections."""
		# Reduce feature count for memory efficiency
		global MAX_FEATURES
		MAX_FEATURES = min(MAX_FEATURES, 5000)
		
		# Enable batch processing
		global BATCH_INDEXING
		BATCH_INDEXING = True
		
		print("Applied optimizations for large collections:")
		print(f"  - Max features: {MAX_FEATURES}")
		print(f"  - Batch indexing: {BATCH_INDEXING}")
		print(f"  - Caching: {ENABLE_CACHING}") 