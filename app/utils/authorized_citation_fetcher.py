"""
Authorized Citation Fetcher

This module fetches citation data only from authorized academic APIs:
- Crossref (DOI-based citations)
- OpenAlex (Comprehensive academic database)
- Semantic Scholar (AI-powered research tool)

No mock or simulated data - only real, authorized citation counts.
"""

import logging
import requests
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class AuthorizedCitationData:
    """Container for authorized citation information."""
    citation_count: int = 0
    source: str = "N/A"
    last_updated: str = ""
    success: bool = False
    error: str = ""
    confidence: str = "N/A"  # High, Medium, Low based on source

class AuthorizedCitationFetcher:
    """Fetches citation data from authorized academic APIs only."""
    
    def __init__(self):
        """Initialize authorized citation fetcher."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-Paper-Browser/2.0 (Educational Project)',
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 1.0  # Be respectful to APIs
        self.last_request_time = 0
        
        # API endpoints
        self.crossref_base = "https://api.crossref.org/works"
        self.openalex_base = "https://api.openalex.org/works"
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1/paper"
    
    def fetch_citation_data(self, doi: str, title: str, journal: str, year: int) -> AuthorizedCitationData:
        """
        Fetch citation data from authorized sources only.
        
        Args:
            doi: Paper DOI
            title: Paper title
            journal: Journal name
            year: Publication year
            
        Returns:
            AuthorizedCitationData object with real citation information
        """
        citation_data = AuthorizedCitationData()
        
        try:
            # Try authorized sources in order of reliability
            if doi:
                # 1. Try Crossref (most reliable for DOI-based papers)
                crossref_data = self._fetch_crossref_citations(doi)
                if crossref_data['success']:
                    citation_data.citation_count = crossref_data['citation_count']
                    citation_data.source = "Crossref"
                    citation_data.confidence = "High"
                    citation_data.success = True
                    logger.info(f"Crossref citation data fetched: {citation_data.citation_count} citations")
            
            # 2. Try OpenAlex (comprehensive academic database)
            if not citation_data.success and (doi or title):
                openalex_data = self._fetch_openalex_citations(doi, title, journal, year)
                if openalex_data['success']:
                    citation_data.citation_count = openalex_data['citation_count']
                    citation_data.source = "OpenAlex"
                    citation_data.confidence = "High"
                    citation_data.success = True
                    logger.info(f"OpenAlex citation data fetched: {citation_data.citation_count} citations")
            
            # 3. Try Semantic Scholar (AI-powered research tool)
            if not citation_data.success and (doi or title):
                semantic_data = self._fetch_semantic_scholar_citations(doi, title, journal, year)
                if semantic_data['success']:
                    citation_data.citation_count = semantic_data['citation_count']
                    citation_data.source = "Semantic Scholar"
                    citation_data.confidence = "Medium"
                    citation_data.success = True
                    logger.info(f"Semantic Scholar citation data fetched: {citation_data.citation_count} citations")
            
            # If no authorized source worked, mark as N/A
            if not citation_data.success:
                citation_data.citation_count = 0
                citation_data.source = "N/A"
                citation_data.confidence = "N/A"
                citation_data.error = "No authorized citation data available"
                logger.warning(f"No authorized citation data found for: {title[:50]}...")
            
            # Set last updated timestamp
            from datetime import datetime
            citation_data.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            logger.error(f"Error fetching authorized citation data: {e}")
            citation_data.error = str(e)
            citation_data.source = "N/A"
        
        return citation_data
    
    def _fetch_crossref_citations(self, doi: str) -> Dict[str, Any]:
        """Fetch citation count from Crossref API."""
        try:
            self._rate_limit()
            
            # Clean DOI
            clean_doi = doi.strip()
            if not clean_doi.startswith('http'):
                clean_doi = f"https://doi.org/{clean_doi}"
            
            url = f"{self.crossref_base}/{clean_doi}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                citation_count = data.get('message', {}).get('is-referenced-by-count', 0)
                return {
                    'success': True,
                    'citation_count': int(citation_count)
                }
            else:
                logger.warning(f"Crossref API error: HTTP {response.status_code}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching Crossref citations: {e}")
            return {'success': False, 'error': str(e)}
    
    def _fetch_openalex_citations(self, doi: str, title: str, journal: str, year: int) -> Dict[str, Any]:
        """Fetch citation count from OpenAlex API."""
        try:
            self._rate_limit()
            
            # Build search query
            if doi:
                query = f"doi:{doi}"
            elif title:
                # Clean title for search
                clean_title = title.replace('"', '').replace("'", "").strip()
                query = f'title:"{clean_title}"'
            else:
                return {'success': False, 'error': 'No DOI or title provided'}
            
            url = f"{self.openalex_base}"
            params = {
                'filter': query,
                'mailto': 'research-paper-browser@example.com'  # Required for OpenAlex
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Get the most relevant result
                    paper = results[0]
                    citation_count = paper.get('cited_by_count', 0)
                    return {
                        'success': True,
                        'citation_count': int(citation_count)
                    }
                else:
                    return {'success': False, 'error': 'No results found'}
            else:
                logger.warning(f"OpenAlex API error: HTTP {response.status_code}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching OpenAlex citations: {e}")
            return {'success': False, 'error': str(e)}
    
    def _fetch_semantic_scholar_citations(self, doi: str, title: str, journal: str, year: int) -> Dict[str, Any]:
        """Fetch citation count from Semantic Scholar API."""
        try:
            self._rate_limit()
            
            # Build search query
            if doi:
                query = f"doi:{doi}"
            elif title:
                clean_title = title.replace('"', '').replace("'", "").strip()
                query = f'title:"{clean_title}"'
            else:
                return {'success': False, 'error': 'No DOI or title provided'}
            
            url = f"{self.semantic_scholar_base}/search"
            params = {
                'query': query,
                'limit': 1,
                'fields': 'paperId,title,citationCount'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                papers = data.get('data', [])
                
                if papers:
                    paper = papers[0]
                    citation_count = paper.get('citationCount', 0)
                    return {
                        'success': True,
                        'citation_count': int(citation_count)
                    }
                else:
                    return {'success': False, 'error': 'No results found'}
            else:
                logger.warning(f"Semantic Scholar API error: HTTP {response.status_code}")
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching Semantic Scholar citations: {e}")
            return {'success': False, 'error': str(e)}
    
    def _rate_limit(self):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = current_time
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all authorized APIs."""
        return {
            'crossref': 'https://api.crossref.org/works',
            'openalex': 'https://api.openalex.org/works',
            'semantic_scholar': 'https://api.semanticscholar.org/graph/v1/paper',
            'rate_limit_delay': self.rate_limit_delay,
            'user_agent': self.session.headers.get('User-Agent')
        }


# Global instance
authorized_citation_fetcher = AuthorizedCitationFetcher()


def fetch_authorized_citation_data(doi: str, title: str, journal: str, year: int) -> AuthorizedCitationData:
    """
    Convenience function to fetch authorized citation data.
    
    Args:
        doi: Paper DOI
        title: Paper title
        journal: Journal name
        year: Publication year
        
    Returns:
        AuthorizedCitationData object
    """
    return authorized_citation_fetcher.fetch_citation_data(doi, title, journal, year)


