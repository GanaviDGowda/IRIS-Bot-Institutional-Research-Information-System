"""
Semantic Search Engine
Provides semantic search capabilities using sentence transformers and vector similarity.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from ..database_unified import get_unified_paper_repository
from .semantic_embedder import semantic_embedder
import json

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Semantic search engine for research papers."""
    
    def __init__(self, paper_repo=None):
        """
        Initialize the semantic search engine.
        
        Args:
            paper_repo: Paper repository instance (optional, will get from unified DB if not provided)
        """
        self.paper_repo = paper_repo or get_unified_paper_repository()
        self.embedder = semantic_embedder
        self.embeddings_cache = {}  # Cache for embeddings
        self.paper_embeddings = {}  # paper_id -> embedding mapping
    
    def generate_all_embeddings(self) -> Dict[int, np.ndarray]:
        """
        Generate embeddings for all papers in the database.
        
        Returns:
            Dictionary mapping paper_id to embedding
        """
        try:
            logger.info("Generating embeddings for all papers...")
            
            # Get all papers
            papers = self.paper_repo.list_all()
            
            if not papers:
                logger.warning("No papers found in database")
                return {}
            
            # Convert papers to dict format
            paper_dicts = []
            paper_ids = []
            
            for paper in papers:
                paper_dict = {
                    'id': paper.get('id'),
                    'title': paper.get('title'),
                    'authors': paper.get('authors'),
                    'abstract': paper.get('abstract'),
                    'journal': paper.get('journal', '') or paper.get('publisher', ''),
                    'publisher': paper.get('publisher'),
                    'metadata': {
                        'department': paper.get('department'),
                        'research_domain': paper.get('research_domain'),
                        'paper_type': paper.get('paper_type', ''),
                        'student': paper.get('student', ''),
                        'review_status': paper.get('review_status', '')
                    }
                }
                paper_dicts.append(paper_dict)
                paper_ids.append(paper.get('id'))
            
            # Generate embeddings in batch
            embeddings = self.embedder.generate_batch_embeddings(paper_dicts)
            
            # Store in cache
            for i, paper_id in enumerate(paper_ids):
                self.paper_embeddings[paper_id] = embeddings[i]
            
            logger.info(f"Generated embeddings for {len(papers)} papers")
            return self.paper_embeddings
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return {}
    
    def search(self, query: str, top_k: int = 10, 
               threshold: float = 0.3, 
               include_metadata: bool = True) -> List[Tuple[Any, float]]:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            include_metadata: Whether to include paper objects or just IDs
            
        Returns:
            List of (paper, similarity_score) tuples
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.generate_embedding(query)
            
            # Get all paper embeddings if not cached
            if not self.paper_embeddings:
                self.generate_all_embeddings()
            
            if not self.paper_embeddings:
                logger.warning("No embeddings available for search")
                return []
            
            # Find similar papers
            paper_ids = list(self.paper_embeddings.keys())
            embeddings = list(self.paper_embeddings.values())
            
            similar_papers = self.embedder.find_similar_papers(
                query_embedding, embeddings, paper_ids, top_k, threshold
            )
            
            if not include_metadata:
                return similar_papers
            
            # Get paper objects for results
            results = []
            for paper_id, similarity in similar_papers:
                try:
                    # Get paper by ID using list_all and filter
                    all_papers = self.paper_repo.list_all()
                    paper = next((p for p in all_papers if p.get('id') == paper_id), None)
                    if paper:
                        results.append((paper, similarity))
                except Exception as e:
                    logger.error(f"Error retrieving paper {paper_id}: {e}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def find_similar_papers(self, paper_id: int, top_k: int = 5, 
                           threshold: float = 0.3) -> List[Tuple[Any, float]]:
        """
        Find papers similar to a given paper.
        
        Args:
            paper_id: ID of the reference paper
            top_k: Number of similar papers to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (paper, similarity_score) tuples
        """
        try:
            # Get the reference paper
            all_papers = self.paper_repo.list_all()
            reference_paper = next((p for p in all_papers if p.get('id') == paper_id), None)
            if not reference_paper:
                logger.warning(f"Paper {paper_id} not found")
                return []
            
            # Generate embedding for reference paper if not cached
            if paper_id not in self.paper_embeddings:
                paper_dict = {
                    'id': reference_paper.get('id'),
                    'title': reference_paper.get('title'),
                    'authors': reference_paper.get('authors'),
                    'abstract': reference_paper.get('abstract'),
                    'journal': getattr(reference_paper, 'journal', '') or getattr(reference_paper, 'publisher', ''),
                    'publisher': reference_paper.get('publisher'),
                    'metadata': {
                        'department': reference_paper.get('department'),
                        'research_domain': reference_paper.get('research_domain'),
                        'paper_type': getattr(reference_paper, 'paper_type', ''),
                        'student': getattr(reference_paper, 'student', ''),
                        'review_status': getattr(reference_paper, 'review_status', '')
                    }
                }
                self.paper_embeddings[paper_id] = self.embedder.generate_paper_embedding(paper_dict)
            
            # Get reference embedding
            reference_embedding = self.paper_embeddings[paper_id]
            
            # Find similar papers (excluding the reference paper itself)
            paper_ids = [pid for pid in self.paper_embeddings.keys() if pid != paper_id]
            embeddings = [self.paper_embeddings[pid] for pid in paper_ids]
            
            similar_papers = self.embedder.find_similar_papers(
                reference_embedding, embeddings, paper_ids, top_k, threshold
            )
            
            # Get paper objects for results
            results = []
            for similar_paper_id, similarity in similar_papers:
                try:
                    # Get paper by ID using list_all and filter
                    all_papers = self.paper_repo.list_all()
                    paper = next((p for p in all_papers if p.get('id') == similar_paper_id), None)
                    if paper:
                        results.append((paper, similarity))
                except Exception as e:
                    logger.error(f"Error retrieving paper {similar_paper_id}: {e}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return []
    
    def hybrid_search(self, query: str, top_k: int = 10, 
                     semantic_weight: float = 0.7, 
                     keyword_weight: float = 0.3) -> List[Tuple[Any, float]]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search results
            keyword_weight: Weight for keyword search results
            
        Returns:
            List of (paper, combined_score) tuples
        """
        try:
            # Perform semantic search
            semantic_results = self.search(query, top_k * 2, 0.1, include_metadata=True)
            
            # Perform keyword search (TF-IDF)
            from ..search_engine import TfidfSearchEngine
            keyword_engine = TfidfSearchEngine(self.paper_repo)
            keyword_results = keyword_engine.search(query)
            
            # Normalize scores
            semantic_scores = {}
            for paper, score in semantic_results:
                semantic_scores[paper.get('id')] = score
            
            keyword_scores = {}
            for paper, score in keyword_results:
                keyword_scores[paper.get('id')] = score
            
            # Normalize keyword scores to 0-1 range
            if keyword_scores:
                max_keyword_score = max(keyword_scores.values())
                if max_keyword_score > 0:
                    keyword_scores = {pid: score / max_keyword_score 
                                    for pid, score in keyword_scores.items()}
            
            # Combine scores
            combined_scores = {}
            all_paper_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
            
            for paper_id in all_paper_ids:
                semantic_score = semantic_scores.get(paper_id, 0)
                keyword_score = keyword_scores.get(paper_id, 0)
                
                combined_score = (semantic_weight * semantic_score + 
                                keyword_weight * keyword_score)
                combined_scores[paper_id] = combined_score
            
            # Sort by combined score
            sorted_papers = sorted(combined_scores.items(), 
                                 key=lambda x: x[1], reverse=True)
            
            # Get top results
            results = []
            for paper_id, score in sorted_papers[:top_k]:
                try:
                    # Get paper by ID using list_all and filter
                    all_papers = self.paper_repo.list_all()
                    paper = next((p for p in all_papers if p.get('id') == paper_id), None)
                    if paper:
                        results.append((paper, score))
                except Exception as e:
                    logger.error(f"Error retrieving paper {paper_id}: {e}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cached embeddings.
        
        Returns:
            Dictionary with embedding statistics
        """
        return {
            'total_embeddings': len(self.paper_embeddings),
            'dimension': self.embedder.get_embedding_dimension(),
            'model_name': self.embedder.model_name,
            'cached_paper_ids': list(self.paper_embeddings.keys())
        }
    
    def clear_cache(self):
        """Clear the embeddings cache."""
        self.paper_embeddings.clear()
        logger.info("Embeddings cache cleared")
    
    def update_paper_embedding(self, paper_id: int):
        """
        Update embedding for a specific paper.
        
        Args:
            paper_id: ID of the paper to update
        """
        try:
            all_papers = self.paper_repo.list_all()
            paper = next((p for p in all_papers if p.get('id') == paper_id), None)
            if not paper:
                logger.warning(f"Paper {paper_id} not found for embedding update")
                return
            
            # Generate new embedding
            paper_dict = {
                'id': paper.get('id'),
                'title': paper.get('title'),
                'authors': paper.get('authors'),
                'abstract': paper.get('abstract'),
                'journal': getattr(paper, 'journal', '') or getattr(paper, 'publisher', ''),
                'publisher': paper.get('publisher'),
                'metadata': {
                    'department': paper.get('department'),
                    'research_domain': paper.get('research_domain'),
                    'paper_type': getattr(paper, 'paper_type', ''),
                    'student': getattr(paper, 'student', ''),
                    'review_status': getattr(paper, 'review_status', '')
                }
            }
            
            new_embedding = self.embedder.generate_paper_embedding(paper_dict)
            self.paper_embeddings[paper_id] = new_embedding
            
            logger.info(f"Updated embedding for paper {paper_id}")
        
        except Exception as e:
            logger.error(f"Error updating embedding for paper {paper_id}: {e}")