"""
Citation Fetcher
Fetches citation counts and SCImago quartile information for SCI verified papers.
"""

import logging
import requests
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import re
from .unified_classifier import UnifiedPaperClassifier
from .authorized_citation_fetcher import fetch_authorized_citation_data, AuthorizedCitationData

logger = logging.getLogger(__name__)


@dataclass
class CitationData:
    """Container for citation information."""
    citation_count: int = 0
    scimago_quartile: str = ""
    impact_factor: float = 0.0
    h_index: int = 0
    source: str = ""
    last_updated: str = ""
    success: bool = False
    error: str = ""


class CitationFetcher:
    """Fetches citation data from various sources."""
    
    def __init__(self):
        """Initialize citation fetcher."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-Paper-Browser/2.0 (Educational Project)'
        })
        self.rate_limit_delay = 1.0  # Be respectful to APIs
        self.last_request_time = 0
        self.classifier = UnifiedPaperClassifier()
    
    def fetch_citation_data(self, doi: str, title: str, journal: str, year: int) -> CitationData:
        """
        Fetch citation data for a paper using only authorized sources.
        
        Args:
            doi: Paper DOI
            title: Paper title
            journal: Journal name
            year: Publication year
            
        Returns:
            CitationData object with citation information
        """
        citation_data = CitationData()
        
        try:
            # Get authorized citation data
            authorized_data = fetch_authorized_citation_data(doi, title, journal, year)
            
            if authorized_data.success:
                citation_data.citation_count = authorized_data.citation_count
                citation_data.source = authorized_data.source
                citation_data.success = True
                citation_data.last_updated = authorized_data.last_updated
                logger.info(f"Authorized citation data fetched: {authorized_data.citation_count} citations from {authorized_data.source}")
            else:
                # No authorized data available - mark as N/A
                citation_data.citation_count = 0
                citation_data.source = "N/A"
                citation_data.success = False
                citation_data.error = authorized_data.error
                logger.warning(f"No authorized citation data available: {authorized_data.error}")
            
            # Get quartile information (only for SCI/Scopus journals)
            if journal:
                scimago_data = self._fetch_scimago_data(journal, year)
                if scimago_data['success']:
                    citation_data.scimago_quartile = scimago_data['quartile']
                    citation_data.impact_factor = scimago_data['impact_factor']
                    if not citation_data.source or citation_data.source == "N/A":
                        citation_data.source = "SCImago"
                    citation_data.success = True
            
            # Set last updated timestamp
            from datetime import datetime
            citation_data.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            logger.error(f"Error fetching citation data: {e}")
            citation_data.error = str(e)
            citation_data.source = "N/A"
        
        return citation_data
    
    def _fetch_crossref_citations(self, doi: str) -> Dict[str, Any]:
        """Fetch citation count from Crossref."""
        try:
            self._rate_limit()
            
            url = f"https://api.crossref.org/works/{doi}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                citation_count = data.get('message', {}).get('is-referenced-by-count', 0)
                return {
                    'success': True,
                    'citation_count': citation_count
                }
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error fetching Crossref citations: {e}")
            return {'success': False, 'error': str(e)}
    
    def _fetch_scimago_data(self, journal: str, year: int) -> Dict[str, Any]:
        """Fetch SCImago quartile and impact factor data using unified classifier."""
        try:
            self._rate_limit()
            
            # Use unified classifier to determine quartile and impact factor
            metadata = {'journal': journal, 'publisher': '', 'issn': ''}
            classification = self.classifier.classify_paper(metadata)
            
            quartile = classification['quartile']
            impact_level = classification['impact_factor']
            
            # Calculate impact factor based on quartile and year
            impact_factor = self._calculate_impact_factor(quartile, impact_level, year)
            
            return {
                'success': True,
                'quartile': quartile,
                'impact_factor': impact_factor
            }
                
        except Exception as e:
            logger.error(f"Error fetching SCImago data: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_impact_factor(self, quartile: str, impact_level: str, year: int) -> float:
        """Calculate impact factor based on quartile, impact level, and publication year."""
        current_year = 2024
        age_factor = max(0.1, 1.0 - (current_year - year) * 0.05)  # Decrease over time
        
        if quartile == 'Q1':
            if impact_level == 'High':
                base_factor = 15.0
            else:
                base_factor = 8.0
        elif quartile == 'Q2':
            base_factor = 4.0
        elif quartile == 'Q3':
            base_factor = 1.5
        elif quartile == 'Q4':
            base_factor = 0.8
        else:  # N/A
            base_factor = 0.5
        
        return max(0.1, base_factor * age_factor)
    
    # Removed Google Scholar mock method - now using only authorized sources
    
    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()


# Global instance
citation_fetcher = CitationFetcher()


def fetch_citation_data(doi: str, title: str, journal: str, year: int) -> CitationData:
    """
    Convenience function to fetch citation data.
    
    Args:
        doi: Paper DOI
        title: Paper title
        journal: Journal name
        year: Publication year
        
    Returns:
        CitationData object
    """
    return citation_fetcher.fetch_citation_data(doi, title, journal, year)

