"""
Metadata Enrichment System
Validates DOIs, classifies journals, and performs ML-based tagging.
"""

import re
import logging
import requests
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)


@dataclass
class EnrichedMetadata:
    """Container for enriched metadata."""
    doi: str = ""
    validated_doi: bool = False
    journal_name: str = ""
    journal_issn: str = ""
    publisher: str = ""
    indexing_status: str = ""  # "SCI", "Scopus", "Non-Indexed"
    department: str = ""
    research_domain: str = ""
    confidence: float = 0.0


class DOIValidator:
    """DOI validation and metadata retrieval using Crossref API."""
    
    def __init__(self):
        self.crossref_base_url = "https://api.crossref.org/works"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-Paper-Browser/2.0 (https://github.com/your-repo)'
        })
    
    def validate_doi(self, doi: str) -> Optional[Dict]:
        """
        Validate DOI and retrieve metadata from Crossref.
        
        Args:
            doi: DOI string
            
        Returns:
            Dictionary with metadata or None if validation fails
        """
        if not doi or not self._is_valid_doi_format(doi):
            return None
        
        try:
            # Clean DOI
            clean_doi = self._clean_doi(doi)
            
            # Query Crossref API
            url = f"{self.crossref_base_url}/{clean_doi}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_crossref_response(data)
            else:
                logger.warning(f"Crossref API returned status {response.status_code} for DOI: {doi}")
                return None
                
        except Exception as e:
            logger.error(f"Error validating DOI {doi}: {e}")
            return None
    
    def _is_valid_doi_format(self, doi: str) -> bool:
        """Check if DOI has valid format."""
        doi_pattern = re.compile(r'^10\.\d{4,}/[^\s\)]+$')
        return bool(doi_pattern.match(doi.strip()))
    
    def _clean_doi(self, doi: str) -> str:
        """Clean DOI string."""
        # Remove common prefixes
        doi = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', doi.strip())
        # Remove trailing punctuation
        doi = re.sub(r'[.,;]+$', '', doi)
        return doi
    
    def _extract_authors(self, authors_list: List[Dict]) -> str:
        """Extract authors from Crossref author list."""
        if not authors_list:
            return ''
        
        author_names = []
        for author in authors_list[:10]:  # Limit to first 10 authors
            given = author.get('given', '')
            family = author.get('family', '')
            if family:
                if given:
                    author_names.append(f"{given} {family}")
                else:
                    author_names.append(family)
        
        return ', '.join(author_names)
    
    def _parse_crossref_response(self, data: Dict) -> Dict:
        """Parse Crossref API response."""
        try:
            message = data.get('message', {})
            
            return {
                'title': message.get('title', [''])[0] if message.get('title') else '',
                'authors': self._extract_authors(message.get('author', [])),
                'journal': message.get('container-title', [''])[0] if message.get('container-title') else '',
                'publisher': message.get('publisher', ''),
                'year': message.get('published-print', {}).get('date-parts', [[0]])[0][0] if message.get('published-print') else 0,
                'issn': message.get('ISSN', [''])[0] if message.get('ISSN') else '',
                'doi': message.get('DOI', ''),
                'abstract': message.get('abstract', ''),
            }
        except Exception as e:
            logger.error(f"Error parsing Crossref response: {e}")
            return {}


class JournalClassifier:
    """Classify journals as SCI/Scopus indexed or non-indexed."""
    
    def __init__(self):
        self.sci_journals = self._load_sci_journals()
        self.scopus_journals = self._load_scopus_journals()
    
    def _load_sci_journals(self) -> set:
        """Load SCI indexed journals list."""
        # This would typically load from a file or database
        # For now, return a sample set
        return {
            'nature', 'science', 'cell', 'lancet', 'nejm', 'jama',
            'ieee transactions', 'acm computing', 'journal of the acm',
            'physical review', 'chemical reviews', 'nature methods',
            'nature biotechnology', 'nature medicine', 'nature genetics'
        }
    
    def _load_scopus_journals(self) -> set:
        """Load Scopus indexed journals list."""
        # This would typically load from a file or database
        # For now, return a sample set
        return {
            'elsevier', 'springer', 'wiley', 'taylor & francis',
            'sage publications', 'emerald', 'inderscience',
            'ieee', 'acm', 'oxford university press', 'cambridge university press'
        }
    
    def classify_journal(self, journal_name: str) -> str:
        """
        Classify journal indexing status.
        
        Args:
            journal_name: Name of the journal
            
        Returns:
            Classification: "SCI", "Scopus", or "Non-Indexed"
        """
        if not journal_name:
            return "Non-Indexed"
        
        journal_lower = journal_name.lower()
        
        # Check for SCI indexing
        for sci_journal in self.sci_journals:
            if sci_journal in journal_lower:
                return "SCI"
        
        # Check for Scopus indexing
        for scopus_journal in self.scopus_journals:
            if scopus_journal in journal_lower:
                return "Scopus"
        
        return "Non-Indexed"


class MLTagger:
    """Machine learning-based tagging for department and research domain."""
    
    def __init__(self):
        self.department_classifier = None
        self.domain_classifier = None
        self.is_trained = False
    
    def train_classifiers(self, training_data: List[Tuple[str, str, str]]) -> None:
        """
        Train ML classifiers on existing data.
        
        Args:
            training_data: List of (abstract, department, domain) tuples
        """
        if not HAS_SKLEARN or not training_data:
            logger.warning("Cannot train classifiers: sklearn not available or no training data")
            return
        
        try:
            abstracts, departments, domains = zip(*training_data)
            
            # Train department classifier
            self.department_classifier = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            self.department_classifier.fit(abstracts, departments)
            
            # Train domain classifier
            self.domain_classifier = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
            self.domain_classifier.fit(abstracts, domains)
            
            self.is_trained = True
            logger.info("ML classifiers trained successfully")
            
        except Exception as e:
            logger.error(f"Error training classifiers: {e}")
    
    def predict_tags(self, abstract: str) -> Tuple[str, str]:
        """
        Predict department and research domain from abstract.
        
        Args:
            abstract: Paper abstract text
            
        Returns:
            Tuple of (department, research_domain)
        """
        if not self.is_trained or not abstract:
            return "Unknown", "Unknown"
        
        try:
            department = self.department_classifier.predict([abstract])[0]
            domain = self.domain_classifier.predict([abstract])[0]
            return department, domain
        except Exception as e:
            logger.error(f"Error predicting tags: {e}")
            return "Unknown", "Unknown"


class MetadataEnricher:
    """Main class for metadata enrichment."""
    
    def __init__(self):
        self.doi_validator = DOIValidator()
        self.journal_classifier = JournalClassifier()
        self.ml_tagger = MLTagger()
    
    def enrich_metadata(self, title: str, authors: str, abstract: str, 
                       doi: str, journal: str, year: int) -> EnrichedMetadata:
        """
        Enrich metadata with DOI validation, journal classification, and ML tagging.
        
        Args:
            title: Paper title
            authors: Paper authors
            abstract: Paper abstract
            doi: DOI string
            journal: Journal name
            year: Publication year
            
        Returns:
            EnrichedMetadata object
        """
        enriched = EnrichedMetadata()
        
        # DOI validation
        if doi:
            crossref_data = self.doi_validator.validate_doi(doi)
            if crossref_data:
                enriched.doi = crossref_data.get('doi', doi)
                enriched.validated_doi = True
                enriched.journal_name = crossref_data.get('journal', journal)
                enriched.journal_issn = crossref_data.get('issn', '')
                enriched.publisher = crossref_data.get('publisher', '')
            else:
                enriched.doi = doi
                enriched.validated_doi = False
        else:
            enriched.journal_name = journal
        
        # Journal classification
        journal_to_classify = enriched.journal_name or journal
        enriched.indexing_status = self.journal_classifier.classify_journal(journal_to_classify)
        
        # ML-based tagging
        if abstract and self.ml_tagger.is_trained:
            department, domain = self.ml_tagger.predict_tags(abstract)
            enriched.department = department
            enriched.research_domain = domain
        
        # Calculate confidence
        enriched.confidence = self._calculate_enrichment_confidence(enriched)
        
        return enriched
    
    def _calculate_enrichment_confidence(self, enriched: EnrichedMetadata) -> float:
        """Calculate confidence score for enriched metadata."""
        score = 0.0
        total_fields = 4  # validated_doi, journal_name, indexing_status, department
        
        if enriched.validated_doi:
            score += 1.0
        if enriched.journal_name:
            score += 1.0
        if enriched.indexing_status != "Non-Indexed":
            score += 1.0
        if enriched.department and enriched.department != "Unknown":
            score += 1.0
        
        return score / total_fields


# Global instance
metadata_enricher = MetadataEnricher()


def enrich_paper_metadata(title: str, authors: str, abstract: str, 
                         doi: str, journal: str, year: int) -> EnrichedMetadata:
    """
    Convenience function to enrich paper metadata.
    
    Args:
        title: Paper title
        authors: Paper authors
        abstract: Paper abstract
        doi: DOI string
        journal: Journal name
        year: Publication year
        
    Returns:
        EnrichedMetadata object
    """
    return metadata_enricher.enrich_metadata(title, authors, abstract, doi, journal, year)
