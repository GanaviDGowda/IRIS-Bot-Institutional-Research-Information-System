"""
Semantic Embedding Service
Generates and manages semantic embeddings for research papers using Sentence Transformers.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import json
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class SemanticEmbedder:
    """Service for generating and managing semantic embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic embedder.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array containing the embedding
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim)
        
        try:
            # Clean and prepare text
            clean_text = self._preprocess_text(text)
            
            # Generate embedding
            embedding = self.model.encode([clean_text], convert_to_numpy=True)[0]
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dim)
    
    def generate_paper_embedding(self, paper: Dict[str, Any]) -> np.ndarray:
        """
        Generate embedding for a research paper.
        
        Args:
            paper: Paper dictionary with title, abstract, authors, etc.
            
        Returns:
            Numpy array containing the paper embedding
        """
        # Combine relevant text fields
        text_parts = []
        
        # Add title (most important)
        if paper.get('title'):
            text_parts.append(paper['title'])
        
        # Add abstract (very important)
        if paper.get('abstract'):
            text_parts.append(paper['abstract'])
        
        # Add authors (for author-based similarity)
        if paper.get('authors'):
            text_parts.append(paper['authors'])
        
        # Add research domain (for domain-based similarity)
        metadata = paper.get('metadata', {})
        if metadata.get('research_domain'):
            text_parts.append(metadata['research_domain'])
        
        # Add department (for department-based similarity)
        if metadata.get('department'):
            text_parts.append(metadata['department'])
        
        # Add journal/publisher (for publication-based similarity)
        if paper.get('journal'):
            text_parts.append(paper['journal'])
        elif paper.get('publisher'):
            text_parts.append(paper['publisher'])
        
        # Combine all text
        combined_text = " ".join(text_parts)
        
        return self.generate_embedding(combined_text)
    
    def generate_batch_embeddings(self, papers: List[Dict[str, Any]]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple papers efficiently.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of numpy arrays containing embeddings
        """
        if not papers:
            return []
        
        try:
            # Prepare texts for batch processing
            texts = []
            for paper in papers:
                text_parts = []
                
                if paper.get('title'):
                    text_parts.append(paper['title'])
                if paper.get('abstract'):
                    text_parts.append(paper['abstract'])
                if paper.get('authors'):
                    text_parts.append(paper['authors'])
                
                metadata = paper.get('metadata', {})
                if metadata.get('research_domain'):
                    text_parts.append(metadata['research_domain'])
                if metadata.get('department'):
                    text_parts.append(metadata['department'])
                
                if paper.get('journal'):
                    text_parts.append(paper['journal'])
                elif paper.get('publisher'):
                    text_parts.append(paper['publisher'])
                
                combined_text = " ".join(text_parts)
                texts.append(self._preprocess_text(combined_text))
            
            # Generate embeddings in batch
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            return [emb for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [np.zeros(self.embedding_dim) for _ in papers]
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text before embedding.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (sentence transformers have limits)
        max_length = 512  # Conservative limit
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def find_similar_papers(self, query_embedding: np.ndarray, 
                           paper_embeddings: List[np.ndarray], 
                           paper_ids: List[int], 
                           top_k: int = 10, 
                           threshold: float = 0.3) -> List[Tuple[int, float]]:
        """
        Find papers similar to the query embedding.
        
        Args:
            query_embedding: Query embedding
            paper_embeddings: List of paper embeddings
            paper_ids: List of corresponding paper IDs
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (paper_id, similarity_score) tuples
        """
        similarities = []
        
        for i, paper_embedding in enumerate(paper_embeddings):
            similarity = self.cosine_similarity(query_embedding, paper_embedding)
            
            if similarity >= threshold:
                similarities.append((paper_ids[i], similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.embedding_dim
    
    def save_embeddings(self, embeddings: List[np.ndarray], 
                       paper_ids: List[int], 
                       file_path: str):
        """
        Save embeddings to file.
        
        Args:
            embeddings: List of embeddings
            paper_ids: List of corresponding paper IDs
            file_path: Path to save file
        """
        try:
            data = {
                'paper_ids': paper_ids,
                'embeddings': [emb.tolist() for emb in embeddings],
                'model_name': self.model_name,
                'dimension': self.embedding_dim
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Saved {len(embeddings)} embeddings to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
    
    def load_embeddings(self, file_path: str) -> Tuple[List[np.ndarray], List[int]]:
        """
        Load embeddings from file.
        
        Args:
            file_path: Path to load file from
            
        Returns:
            Tuple of (embeddings, paper_ids)
        """
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            embeddings = [np.array(emb) for emb in data['embeddings']]
            paper_ids = data['paper_ids']
            
            logger.info(f"Loaded {len(embeddings)} embeddings from {file_path}")
            
            return embeddings, paper_ids
        
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return [], []


# Global instance
semantic_embedder = SemanticEmbedder()