"""
Direct Crossref API Metadata Fetcher
Fetches complete, accurate metadata directly from Crossref using DOI.
"""

import logging
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class CrossrefMetadata:
    """Container for Crossref metadata."""
    doi: str = ""
    title: str = ""
    authors: str = ""
    journal: str = ""
    publisher: str = ""
    issn: str = ""
    isbn: str = ""
    year: int = 0
    publication_date: str = ""
    abstract: str = ""
    url: str = ""
    type: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    success: bool = False
    error: str = ""


class CrossrefAPIFetcher:
    """Fetch metadata directly from Crossref API."""
    
    def __init__(self, email: str = "research-browser@example.com"):
        """
        Initialize Crossref API fetcher.
        
        Args:
            email: Your email for polite API usage (gets better rate limits)
        """
        self.base_url = "https://api.crossref.org/works"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'ResearchPaperBrowser/2.0 (mailto:{email})'
        })
        self.rate_limit_delay = 1.0  # Respect rate limits
        self.last_request_time = 0
    
    def fetch_by_doi(self, doi: str) -> CrossrefMetadata:
        """
        Fetch complete metadata from Crossref using DOI.
        
        Args:
            doi: DOI string (e.g., "10.1000/182" or "https://doi.org/10.1000/182")
            
        Returns:
            CrossrefMetadata object with all available fields
        """
        # Clean DOI
        doi = self._clean_doi(doi)
        
        if not doi:
            return CrossrefMetadata(error="Invalid DOI format")
        
        try:
            # Rate limiting
            self._respect_rate_limit()
            
            # Make API request
            url = f"{self.base_url}/{doi}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data, doi)
            elif response.status_code == 404:
                logger.warning(f"DOI not found in Crossref: {doi}")
                return CrossrefMetadata(doi=doi, error="DOI not found in Crossref database")
            else:
                logger.error(f"Crossref API error {response.status_code} for DOI: {doi}")
                return CrossrefMetadata(doi=doi, error=f"API error: {response.status_code}")
                
        except requests.Timeout:
            logger.error(f"Timeout fetching DOI: {doi}")
            return CrossrefMetadata(doi=doi, error="Request timeout")
        except Exception as e:
            logger.error(f"Error fetching DOI {doi}: {e}")
            return CrossrefMetadata(doi=doi, error=str(e))
    
    def _clean_doi(self, doi: str) -> str:
        """Clean and validate DOI."""
        import re
        
        if not doi:
            return ""
        
        # Remove common prefixes
        doi = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', doi.strip())
        
        # Remove trailing punctuation
        doi = re.sub(r'[.,;]+$', '', doi)
        
        # Validate DOI format
        if not re.match(r'^10\.\d{4,}/[^\s]+$', doi):
            logger.warning(f"Invalid DOI format: {doi}")
            return ""
        
        return doi
    
    def _respect_rate_limit(self):
        """Respect Crossref API rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _parse_response(self, data: Dict, doi: str) -> CrossrefMetadata:
        """Parse Crossref API response into CrossrefMetadata."""
        try:
            message = data.get('message', {})
            
            metadata = CrossrefMetadata()
            metadata.doi = doi
            metadata.success = True
            
            # Title
            if message.get('title'):
                metadata.title = message['title'][0] if isinstance(message['title'], list) else message['title']
            
            # Authors
            metadata.authors = self._extract_authors(message.get('author', []))
            
            # Journal/Container title
            if message.get('container-title'):
                metadata.journal = message['container-title'][0] if isinstance(message['container-title'], list) else message['container-title']
            
            # Publisher
            metadata.publisher = message.get('publisher', '')
            
            # ISSN
            if message.get('ISSN'):
                issn_list = message['ISSN']
                metadata.issn = issn_list[0] if isinstance(issn_list, list) else issn_list
            
            # ISBN
            if message.get('ISBN'):
                isbn_list = message['ISBN']
                metadata.isbn = isbn_list[0] if isinstance(isbn_list, list) else isbn_list
            
            # Publication date and year
            metadata.year, metadata.publication_date = self._extract_date(message)
            
            # Abstract (if available)
            metadata.abstract = message.get('abstract', '')
            
            # URL
            metadata.url = message.get('URL', '')
            
            # Type (journal-article, conference-paper, etc.)
            metadata.type = message.get('type', '')
            
            # Volume, Issue, Pages
            metadata.volume = message.get('volume', '')
            metadata.issue = message.get('issue', '')
            metadata.pages = message.get('page', '')
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing Crossref response: {e}")
            return CrossrefMetadata(doi=doi, error=f"Parse error: {e}")
    
    def _extract_authors(self, authors_list: list) -> str:
        """Extract and format authors from Crossref author list."""
        if not authors_list:
            return ""
        
        author_names = []
        for author in authors_list[:20]:  # Limit to first 20 authors
            given = author.get('given', '')
            family = author.get('family', '')
            
            if family:
                if given:
                    # Format: Given Family
                    author_names.append(f"{given} {family}")
                else:
                    author_names.append(family)
        
        return ', '.join(author_names)
    
    def _extract_date(self, message: Dict) -> tuple:
        """Extract year and full publication date."""
        year = 0
        full_date = ""
        
        # Try different date fields in order of preference
        date_fields = ['published-print', 'published-online', 'created', 'issued']
        
        for field in date_fields:
            if field in message:
                date_parts = message[field].get('date-parts', [[]])
                if date_parts and date_parts[0]:
                    parts = date_parts[0]
                    
                    # Extract year
                    if len(parts) >= 1:
                        year = int(parts[0])
                    
                    # Build full date string
                    if len(parts) >= 3:
                        full_date = f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
                    elif len(parts) >= 2:
                        full_date = f"{parts[0]}-{parts[1]:02d}"
                    elif len(parts) >= 1:
                        full_date = str(parts[0])
                    
                    if year > 0:
                        break
        
        return year, full_date
    
    def search_by_title_and_author(self, title: str, author: str = "", limit: int = 5) -> list:
        """
        Search Crossref by title and author (useful when DOI is not available).
        
        Args:
            title: Paper title
            author: Author name (optional, improves accuracy)
            limit: Maximum number of results
            
        Returns:
            List of CrossrefMetadata objects sorted by relevance
        """
        try:
            self._respect_rate_limit()
            
            url = f"{self.base_url}"
            params = {
                'query.title': title,
                'rows': limit
            }
            
            # Add author to query if provided
            if author:
                # Extract first author's last name for better matching
                first_author = author.split(',')[0].strip()
                params['query.author'] = first_author
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('message', {}).get('items', []):
                    doi = item.get('DOI', '')
                    if doi:
                        metadata = self._parse_response({'message': item}, doi)
                        # Calculate match score
                        metadata.match_score = self._calculate_match_score(
                            title, author, metadata
                        )
                        results.append(metadata)
                
                # Sort by match score
                results.sort(key=lambda x: getattr(x, 'match_score', 0), reverse=True)
                return results
            else:
                logger.error(f"Search error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching by title and author: {e}")
            return []
    
    def search_by_title(self, title: str, limit: int = 5) -> list:
        """
        Search Crossref by title only.
        
        Args:
            title: Paper title
            limit: Maximum number of results
            
        Returns:
            List of CrossrefMetadata objects
        """
        return self.search_by_title_and_author(title, "", limit)
    
    def find_doi_by_metadata(self, title: str, authors: str = "") -> Optional[str]:
        """
        Find DOI using title and authors.
        Returns the best matching DOI or None.
        
        Args:
            title: Paper title
            authors: Author names
            
        Returns:
            DOI string or None
        """
        try:
            results = self.search_by_title_and_author(title, authors, limit=3)
            
            if results and len(results) > 0:
                # Return the best match (highest score)
                best_match = results[0]
                match_score = getattr(best_match, 'match_score', 0)
                
                # Only return if match score is reasonable (>0.6)
                if match_score > 0.6:
                    return best_match.doi
                else:
                    logger.warning(f"Match score too low: {match_score:.2f}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding DOI: {e}")
            return None
    
    def _calculate_match_score(self, query_title: str, query_author: str, 
                               result: CrossrefMetadata) -> float:
        """
        Calculate how well a result matches the query.
        
        Returns score between 0 and 1.
        """
        score = 0.0
        
        # Title similarity (70% weight)
        if query_title and result.title:
            title_similarity = self._string_similarity(
                query_title.lower(), 
                result.title.lower()
            )
            score += title_similarity * 0.7
        
        # Author similarity (30% weight)
        if query_author and result.authors:
            # Extract first author from query
            first_author = query_author.split(',')[0].strip().lower()
            result_authors_lower = result.authors.lower()
            
            if first_author in result_authors_lower:
                score += 0.3
            else:
                # Partial match
                author_words = first_author.split()
                matches = sum(1 for word in author_words if word in result_authors_lower)
                score += (matches / len(author_words)) * 0.3 if author_words else 0
        
        return min(score, 1.0)
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using simple word overlap.
        Returns value between 0 and 1.
        """
        if not s1 or not s2:
            return 0.0
        
        # Tokenize
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        # Remove common words
        stop_words = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'with'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


# Global instance
crossref_fetcher = CrossrefAPIFetcher()


def fetch_metadata_by_doi(doi: str) -> CrossrefMetadata:
    """
    Convenience function to fetch metadata by DOI.
    
    Args:
        doi: DOI string
        
    Returns:
        CrossrefMetadata object
    """
    return crossref_fetcher.fetch_by_doi(doi)


def search_metadata_by_title(title: str, limit: int = 5) -> list:
    """
    Convenience function to search by title.
    
    Args:
        title: Paper title
        limit: Maximum results
        
    Returns:
        List of CrossrefMetadata objects
    """
    return crossref_fetcher.search_by_title(title, limit)
