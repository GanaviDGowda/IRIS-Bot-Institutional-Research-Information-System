"""
Hybrid Search Engine combining Semantic and Keyword Search
Provides the best of both worlds for research paper search.
"""

import logging
from typing import List, Dict, Any, Tuple
from .semantic_search_engine import SemanticSearchEngine
from ..database_unified import get_unified_paper_repository

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """Hybrid search engine combining semantic and keyword search."""
    
    def __init__(self, paper_repo=None):
        """
        Initialize the hybrid search engine.
        
        Args:
            paper_repo: Paper repository instance (optional, will get from unified DB if not provided)
        """
        self.paper_repo = paper_repo or get_unified_paper_repository()
        self.semantic_engine = SemanticSearchEngine(self.paper_repo)
    
    def search(self, query: str, 
               search_type: str = "hybrid",
               top_k: int = 10,
               semantic_weight: float = 0.7,
               keyword_weight: float = 0.3,
               semantic_threshold: float = 0.3) -> List[Tuple[Any, float]]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            search_type: Type of search ("semantic", "keyword", "hybrid")
            top_k: Number of results to return
            semantic_weight: Weight for semantic search results (0.0-1.0)
            keyword_weight: Weight for keyword search results (0.0-1.0)
            semantic_threshold: Minimum similarity threshold for semantic search
            
        Returns:
            List of (paper, combined_score) tuples
        """
        try:
            if not query or not query.strip():
                return []
            
            results = []
            
            if search_type == "semantic":
                # Pure semantic search
                results = self.semantic_engine.search(query, top_k, semantic_threshold)
                
            elif search_type == "keyword":
                # Simple keyword search using database query
                results = self._keyword_search(query, top_k)
                
            else:  # hybrid
                # Get results from both engines
                semantic_results = self.semantic_engine.search(query, top_k * 2, semantic_threshold)
                keyword_results = self._keyword_search(query, top_k * 2)
                
                # Normalize scores
                semantic_results = self._normalize_scores(semantic_results)
                keyword_results = self._normalize_scores(keyword_results)
                
                # Combine results
                results = self._combine_results(
                    semantic_results, keyword_results,
                    semantic_weight, keyword_weight, top_k
                )
            
            logger.info(f"Hybrid search found {len(results)} results for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def _keyword_search(self, query: str, top_k: int) -> List[Tuple[Any, float]]:
        """
        Perform simple keyword search using database queries.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (paper, score) tuples
        """
        try:
            # Get all papers
            papers = self.paper_repo.list_all()
            
            if not papers:
                return []
            
            # Simple keyword matching
            query_lower = query.lower()
            results = []
            
            for paper in papers:
                score = 0.0
                
                # Check title
                title = paper.get('title', '')
                if query_lower in title.lower():
                    score += 2.0  # Higher weight for title matches
                
                # Check abstract
                abstract = paper.get('abstract', '')
                if query_lower in abstract.lower():
                    score += 1.0  # Lower weight for abstract matches
                
                # Check authors
                authors = paper.get('authors', '')
                if query_lower in authors.lower():
                    score += 0.5  # Lower weight for author matches
                
                # Check journal
                journal = paper.get('journal', '')
                if query_lower in journal.lower():
                    score += 0.5  # Lower weight for journal matches
                
                if score > 0:
                    results.append((paper, score))
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _normalize_scores(self, results: List[Tuple[Any, float]]) -> List[Tuple[Any, float]]:
        """
        Normalize scores to 0-1 range.
        
        Args:
            results: List of (paper, score) tuples
            
        Returns:
            List of (paper, normalized_score) tuples
        """
        if not results:
            return []
        
        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same, return as is
            return results
        
        # Normalize to 0-1 range
        normalized_results = []
        for paper, score in results:
            normalized_score = (score - min_score) / (max_score - min_score)
            normalized_results.append((paper, normalized_score))
        
        return normalized_results
    
    def _combine_results(self, semantic_results: List[Tuple[Any, float]], 
                        keyword_results: List[Tuple[Any, float]],
                        semantic_weight: float, keyword_weight: float,
                        top_k: int) -> List[Tuple[Any, float]]:
        """
        Combine semantic and keyword search results.
        
        Args:
            semantic_results: Semantic search results
            keyword_results: Keyword search results
            semantic_weight: Weight for semantic results
            keyword_weight: Weight for keyword results
            top_k: Number of results to return
            
        Returns:
            Combined results sorted by combined score
        """
        # Create a dictionary to store combined scores
        combined_scores = {}
        
        # Add semantic results
        for paper, score in semantic_results:
            paper_id = paper.get('id')
            combined_scores[paper_id] = {
                'paper': paper,
                'semantic_score': score,
                'keyword_score': 0.0,
                'combined_score': score * semantic_weight
            }
        
        # Add keyword results
        for paper, score in keyword_results:
            paper_id = paper.get('id')
            if paper_id in combined_scores:
                # Paper exists in both results
                combined_scores[paper_id]['keyword_score'] = score
                combined_scores[paper_id]['combined_score'] = (
                    combined_scores[paper_id]['semantic_score'] * semantic_weight +
                    score * keyword_weight
                )
            else:
                # Paper only in keyword results
                combined_scores[paper_id] = {
                    'paper': paper,
                    'semantic_score': 0.0,
                    'keyword_score': score,
                    'combined_score': score * keyword_weight
                }
        
        # Sort by combined score and return top_k results
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return [(item['paper'], item['combined_score']) for item in sorted_results[:top_k]]
    
    def find_similar_papers(self, paper_id: int, top_k: int = 5, 
                          threshold: float = 0.3) -> List[Tuple[Any, float]]:
        """
        Find papers similar to a specific paper using semantic search.
        
        Args:
            paper_id: ID of the reference paper
            top_k: Number of similar papers to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (paper, similarity_score) tuples
        """
        return self.semantic_engine.find_similar_papers(paper_id, top_k, threshold)
    
    def get_search_suggestions(self, query: str, top_k: int = 5) -> List[str]:
        """
        Get search suggestions based on existing papers.
        
        Args:
            query: Partial query
            top_k: Number of suggestions
            
        Returns:
            List of suggested search terms
        """
        try:
            if not query or len(query) < 2:
                return []
            
            # Get all papers
            papers = self.paper_repo.list_all()
            
            # Extract potential suggestions from titles and abstracts
            suggestions = set()
            query_lower = query.lower()
            
            for paper in papers:
                # Check title
                title = paper.get('title', '')
                if query_lower in title.lower():
                    words = title.lower().split()
                    for word in words:
                        if word.startswith(query_lower) and len(word) > len(query_lower):
                            suggestions.add(word)
                
                # Check abstract
                abstract = paper.get('abstract', '')
                if query_lower in abstract.lower():
                    words = abstract.lower().split()
                    for word in words:
                        if word.startswith(query_lower) and len(word) > len(query_lower):
                            suggestions.add(word)
            
            # Sort by length (shorter first) and return top_k
            sorted_suggestions = sorted(suggestions, key=len)[:top_k]
            return sorted_suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            'semantic_stats': self.semantic_engine.get_embedding_stats(),
            'total_papers': len(self.paper_repo.list_all())
        }






