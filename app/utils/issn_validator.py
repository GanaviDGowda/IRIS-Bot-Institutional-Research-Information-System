"""
ISSN Validator and Metadata Fetcher
Validates journals and fetches metadata using ISSN when DOI is not available.
Supports: ISSN Portal API and DOAJ API (for open-access journals).
"""

import logging
import requests
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class ISSNMetadata:
    """Container for ISSN-based metadata."""
    issn: str = ""
    title: str = ""
    publisher: str = ""
    country: str = ""
    language: str = ""
    subjects: List[str] = None
    url: str = ""
    is_open_access: bool = False
    license: str = ""
    apc_charges: str = ""  # Article Processing Charges
    success: bool = False
    error: str = ""
    source: str = ""  # "issn_portal" or "doaj"
    
    def __post_init__(self):
        if self.subjects is None:
            self.subjects = []


class ISSNValidator:
    """Validate journals and fetch metadata using ISSN."""
    
    def __init__(self):
        """Initialize ISSN validator."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ResearchPaperBrowser/2.0 (Educational Project)'
        })
        
        # API endpoints
        self.issn_portal_url = "https://portal.issn.org/api/search"
        self.doaj_api_url = "https://doaj.org/api/v2/search/journals"
        
        # Rate limiting
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
        
        # ISSN pattern for extraction
        self.issn_pattern = re.compile(
            r'\b(\d{4})-(\d{3}[\dXx])\b'
        )
    
    def extract_issn_from_text(self, text: str) -> List[str]:
        """
        Extract ISSN numbers from text.
        
        Args:
            text: Text content to search
            
        Returns:
            List of ISSN numbers found
        """
        issns = []
        
        # Look for ISSN pattern in first 2000 characters
        search_text = text[:2000]
        
        # Find all ISSN patterns
        matches = self.issn_pattern.findall(search_text)
        
        for match in matches:
            if isinstance(match, tuple):
                issn = f"{match[0]}-{match[1]}"
            else:
                issn = match
            
            # Validate ISSN format
            if self._validate_issn_format(issn):
                issns.append(issn)
        
        # Also look for explicit ISSN labels
        issn_label_pattern = re.compile(
            r'ISSN[:\s]+(\d{4})-(\d{3}[\dXx])',
            re.IGNORECASE
        )
        
        label_matches = issn_label_pattern.findall(search_text)
        for match in label_matches:
            if isinstance(match, tuple):
                issn = f"{match[0]}-{match[1]}"
            else:
                issn = match
            
            if self._validate_issn_format(issn) and issn not in issns:
                issns.append(issn)
        
        return issns
    
    def _validate_issn_format(self, issn: str) -> bool:
        """
        Validate ISSN format and checksum.
        
        Args:
            issn: ISSN string (e.g., "1234-5678")
            
        Returns:
            True if valid ISSN format
        """
        # Remove hyphen for validation
        issn_digits = issn.replace('-', '').replace('-', '')
        
        if len(issn_digits) != 8:
            return False
        
        # Calculate checksum
        try:
            total = 0
            for i in range(7):
                digit = int(issn_digits[i])
                total += digit * (8 - i)
            
            checksum = issn_digits[7]
            if checksum.upper() == 'X':
                checksum_value = 10
            else:
                checksum_value = int(checksum)
            
            # Check if valid
            remainder = total % 11
            expected = (11 - remainder) % 11
            if expected == 10:
                expected = 'X'
            else:
                expected = str(expected)
            
            return str(checksum_value) == str(expected) or checksum.upper() == expected
            
        except ValueError:
            return False
    
    def validate_by_issn(self, issn: str) -> ISSNMetadata:
        """
        Validate journal using ISSN and fetch metadata.
        Tries DOAJ first (faster), then falls back to ISSN Portal.
        
        Args:
            issn: ISSN number (e.g., "1234-5678")
            
        Returns:
            ISSNMetadata object with journal information
        """
        # Clean ISSN
        issn = self._clean_issn(issn)
        
        if not issn or not self._validate_issn_format(issn):
            return ISSNMetadata(
                issn=issn,
                error="Invalid ISSN format",
                success=False
            )
        
        # Try DOAJ first (open access journals, faster response)
        logger.info(f"Trying DOAJ API for ISSN: {issn}")
        doaj_result = self._fetch_from_doaj(issn)
        
        if doaj_result.success:
            logger.info(f"Found journal in DOAJ: {doaj_result.title}")
            return doaj_result
        
        # Fallback to ISSN Portal
        logger.info(f"Trying ISSN Portal for ISSN: {issn}")
        portal_result = self._fetch_from_issn_portal(issn)
        
        if portal_result.success:
            logger.info(f"Found journal in ISSN Portal: {portal_result.title}")
            return portal_result
        
        # Both failed
        return ISSNMetadata(
            issn=issn,
            error="ISSN not found in DOAJ or ISSN Portal",
            success=False
        )
    
    def _clean_issn(self, issn: str) -> str:
        """Clean and format ISSN."""
        if not issn:
            return ""
        
        # Remove all non-digit and non-X characters
        issn = re.sub(r'[^\dXx]', '', issn)
        
        # Ensure 8 characters
        if len(issn) != 8:
            return ""
        
        # Format with hyphen
        return f"{issn[:4]}-{issn[4:]}"
    
    def _respect_rate_limit(self):
        """Respect API rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _fetch_from_doaj(self, issn: str) -> ISSNMetadata:
        """
        Fetch metadata from DOAJ (Directory of Open Access Journals).
        Best for open-access journals.
        
        Args:
            issn: ISSN number
            
        Returns:
            ISSNMetadata object
        """
        try:
            self._respect_rate_limit()
            
            # DOAJ API v2 endpoint
            url = f"{self.doaj_api_url}/issn:{issn}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('total', 0) > 0 and data.get('results'):
                    journal = data['results'][0]['bibjson']
                    
                    metadata = ISSNMetadata()
                    metadata.issn = issn
                    metadata.success = True
                    metadata.source = "doaj"
                    metadata.is_open_access = True  # All DOAJ journals are OA
                    
                    # Extract fields
                    metadata.title = journal.get('title', '')
                    metadata.publisher = journal.get('publisher', {}).get('name', '') if isinstance(journal.get('publisher'), dict) else journal.get('publisher', '')
                    metadata.url = journal.get('ref', {}).get('journal', '') if isinstance(journal.get('ref'), dict) else ''
                    
                    # Subjects/keywords
                    subjects = journal.get('subjects', [])
                    metadata.subjects = [s.get('term', '') for s in subjects if isinstance(s, dict)]
                    
                    # License information
                    licenses = journal.get('license', [])
                    if licenses:
                        metadata.license = licenses[0].get('type', '')
                    
                    # APC information
                    apc = journal.get('apc', {})
                    if isinstance(apc, dict):
                        has_apc = apc.get('has_apc', False)
                        if has_apc:
                            amount = apc.get('max', [{}])[0] if apc.get('max') else {}
                            if isinstance(amount, dict):
                                metadata.apc_charges = f"{amount.get('price', 'Unknown')} {amount.get('currency', '')}"
                        else:
                            metadata.apc_charges = "No APC"
                    
                    # Language
                    languages = journal.get('language', [])
                    if languages:
                        metadata.language = ', '.join(languages[:3])  # First 3 languages
                    
                    # Country
                    country = journal.get('publisher', {}).get('country', '')
                    if isinstance(country, str):
                        metadata.country = country
                    
                    logger.info(f"Successfully fetched from DOAJ: {metadata.title}")
                    return metadata
                else:
                    return ISSNMetadata(
                        issn=issn,
                        error="ISSN not found in DOAJ",
                        success=False
                    )
            else:
                logger.warning(f"DOAJ API error {response.status_code} for ISSN: {issn}")
                return ISSNMetadata(
                    issn=issn,
                    error=f"DOAJ API error: {response.status_code}",
                    success=False
                )
                
        except requests.Timeout:
            logger.error(f"Timeout fetching from DOAJ for ISSN: {issn}")
            return ISSNMetadata(issn=issn, error="DOAJ timeout", success=False)
        except Exception as e:
            logger.error(f"Error fetching from DOAJ: {e}")
            return ISSNMetadata(issn=issn, error=f"DOAJ error: {e}", success=False)
    
    def _fetch_from_issn_portal(self, issn: str) -> ISSNMetadata:
        """
        Fetch metadata from ISSN Portal.
        Covers all registered journals (not just OA).
        
        Args:
            issn: ISSN number
            
        Returns:
            ISSNMetadata object
        """
        try:
            self._respect_rate_limit()
            
            # ISSN Portal search API
            params = {
                'search': issn,
                'searchType': 'issn'
            }
            
            response = self.session.get(
                self.issn_portal_url,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if results found
                records = data.get('records', [])
                if records and len(records) > 0:
                    record = records[0]
                    
                    metadata = ISSNMetadata()
                    metadata.issn = issn
                    metadata.success = True
                    metadata.source = "issn_portal"
                    
                    # Extract fields (ISSN Portal structure)
                    metadata.title = record.get('title', '')
                    
                    # Publisher information
                    publishers = record.get('publisher', [])
                    if publishers:
                        metadata.publisher = publishers[0].get('name', '') if isinstance(publishers[0], dict) else str(publishers[0])
                    
                    # Country
                    countries = record.get('country', [])
                    if countries:
                        metadata.country = countries[0] if isinstance(countries, list) else countries
                    
                    # Language
                    languages = record.get('language', [])
                    if languages:
                        metadata.language = ', '.join(languages[:3])
                    
                    # URL
                    urls = record.get('url', [])
                    if urls:
                        metadata.url = urls[0] if isinstance(urls, list) else urls
                    
                    # Format (subject/type)
                    formats = record.get('format', [])
                    if formats:
                        metadata.subjects = formats if isinstance(formats, list) else [formats]
                    
                    logger.info(f"Successfully fetched from ISSN Portal: {metadata.title}")
                    return metadata
                else:
                    return ISSNMetadata(
                        issn=issn,
                        error="ISSN not found in ISSN Portal",
                        success=False
                    )
            else:
                logger.warning(f"ISSN Portal error {response.status_code} for ISSN: {issn}")
                return ISSNMetadata(
                    issn=issn,
                    error=f"ISSN Portal error: {response.status_code}",
                    success=False
                )
                
        except requests.Timeout:
            logger.error(f"Timeout fetching from ISSN Portal for ISSN: {issn}")
            return ISSNMetadata(issn=issn, error="ISSN Portal timeout", success=False)
        except Exception as e:
            logger.error(f"Error fetching from ISSN Portal: {e}")
            return ISSNMetadata(issn=issn, error=f"ISSN Portal error: {e}", success=False)
    
    def search_journals_by_title(self, title: str, limit: int = 5) -> List[ISSNMetadata]:
        """
        Search for journals by title in DOAJ.
        Useful when you have journal name but no ISSN.
        
        Args:
            title: Journal title to search
            limit: Maximum number of results
            
        Returns:
            List of ISSNMetadata objects
        """
        try:
            self._respect_rate_limit()
            
            # DOAJ search by title
            url = f"{self.doaj_api_url}/title:{title}"
            params = {'pageSize': limit}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('results', [])[:limit]:
                    journal = item.get('bibjson', {})
                    
                    # Extract ISSN
                    issns = journal.get('issn', [])
                    issn = issns[0] if issns else ""
                    
                    if issn:
                        metadata = ISSNMetadata()
                        metadata.issn = issn
                        metadata.success = True
                        metadata.source = "doaj"
                        metadata.is_open_access = True
                        metadata.title = journal.get('title', '')
                        metadata.publisher = journal.get('publisher', {}).get('name', '') if isinstance(journal.get('publisher'), dict) else journal.get('publisher', '')
                        
                        results.append(metadata)
                
                return results
            else:
                logger.warning(f"DOAJ search error {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching journals by title: {e}")
            return []


# Global instance
issn_validator = ISSNValidator()


def validate_journal_by_issn(issn: str) -> ISSNMetadata:
    """
    Convenience function to validate journal by ISSN.
    
    Args:
        issn: ISSN number
        
    Returns:
        ISSNMetadata object
    """
    return issn_validator.validate_by_issn(issn)


def extract_issn_from_text(text: str) -> List[str]:
    """
    Convenience function to extract ISSN from text.
    
    Args:
        text: Text content
        
    Returns:
        List of ISSN numbers found
    """
    return issn_validator.extract_issn_from_text(text)


