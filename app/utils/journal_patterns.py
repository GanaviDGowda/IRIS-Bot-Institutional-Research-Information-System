"""
Journal-Specific Pattern Recognition
Specialized extractors for different journal layouts.
"""

import re
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JournalPattern:
    """Pattern definition for a specific journal."""
    name: str
    identifier_patterns: List[str]  # Patterns to identify the journal
    author_patterns: List[str]  # Patterns to extract authors
    title_patterns: List[str]  # Patterns to extract title
    abstract_patterns: List[str]  # Patterns to extract abstract
    year_patterns: List[str]  # Patterns to extract year
    special_rules: Dict = None  # Special extraction rules
    
    def __post_init__(self):
        if self.special_rules is None:
            self.special_rules = {}


class JournalPatternMatcher:
    """Matches and extracts metadata using journal-specific patterns."""
    
    def __init__(self):
        """Initialize with known journal patterns."""
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, JournalPattern]:
        """Load all known journal patterns."""
        patterns = {}
        
        # International Journal of Digital Crime and Forensics (IJDCF)
        patterns['ijdcf'] = JournalPattern(
            name="International Journal of Digital Crime and Forensics",
            identifier_patterns=[
                r'International\s+Journal\s+of\s+Digital\s+Crime\s+and\s+Forensics',
                r'IJDCF',
                r'DOI:\s*10\.4018/IJDCF',
            ],
            author_patterns=[
                # IJDCF typically has authors right after title with affiliations
                r'(?:Author[s]?|By)\s*[:\-–]?\s*([^\n]+(?:\n[A-Z][^\n]+){0,2})',
                # Names followed by affiliation in parentheses
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*)\s*\([^)]+\)',
                # Names with comma separation
                r'([A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+)+)',
            ],
            title_patterns=[
                # Title is usually all caps or title case before authors
                r'^([A-Z][A-Z\s:]+[A-Z])\s*\n',
                r'\n([A-Z][^\n]{20,150})\n(?:[A-Z][a-z]+\s+[A-Z])',
            ],
            abstract_patterns=[
                r'ABSTRACT\s*\n+(.*?)(?=\n\s*(?:KEYWORDS?|INTRODUCTION|1\.|BACKGROUND))',
                r'Abstract\s*[:.\-–]?\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction|Background))',
            ],
            year_patterns=[
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(\d{4})',
                r'Volume\s+\d+[,\s]+Issue\s+\d+[,\s]+(\d{4})',
            ],
            special_rules={
                'has_doi_prefix': '10.4018/IJDCF',
                'issn': '1941-6210',  # Print ISSN
                'eissn': '1941-6229',  # Electronic ISSN
                'publisher': 'IGI Global',
            }
        )
        
        # International Journal for Research in Applied Science & Engineering Technology (IJRASET)
        patterns['ijraset'] = JournalPattern(
            name="International Journal for Research in Applied Science & Engineering Technology",
            identifier_patterns=[
                r'International\s+Journal\s+for\s+Research\s+in\s+Applied\s+Science',
                r'IJRASET',
                r'DOI:\s*10\.22214/ijraset',
            ],
            author_patterns=[
                r'Author[s]?\s*[:\-–]\s*([^\n]+)',
                r'By\s*[:\-–]?\s*([A-Z][^\n]+)',
                # Names with comma separation
                r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s*,\s*[A-Z][a-z]+[^\n]+)',
            ],
            title_patterns=[
                r'^([A-Z][^\n]{15,100})\n',
                r'Title\s*[:\-–]\s*([^\n]+)',
            ],
            abstract_patterns=[
                r'Abstract\s*[:\-–]?\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction|I\.))',
            ],
            year_patterns=[
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
                r'Volume\s+\d+[,\s]+Issue\s+[IVX\d]+[,\s]+(\d{4})',
            ],
            special_rules={
                'has_doi_prefix': '10.22214/ijraset',
                'publisher': 'IJRASET',
            }
        )
        
        # IEEE Journals
        patterns['ieee'] = JournalPattern(
            name="IEEE Journals",
            identifier_patterns=[
                r'IEEE\s+(?:Transactions|Journal)',
                r'©\s*\d{4}\s+IEEE',
                r'DOI:\s*10\.1109/',
            ],
            author_patterns=[
                # IEEE format: Author names with affiliations in italics
                r'([A-Z][A-Z\s,\.]+(?:,\s*(?:Member|Fellow|Senior Member),\s*IEEE)?)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
            ],
            title_patterns=[
                r'^([A-Z][^\n]{20,120})\n',
            ],
            abstract_patterns=[
                r'Abstract[:\-–]?\s*\n+(.*?)(?=\n\s*(?:Index\s+Terms|Keywords?|I\.\s+INTRODUCTION))',
            ],
            year_patterns=[
                r'(?:VOL\.|Volume)\s+\d+,\s+NO\.\s+\d+,\s+\w+\s+(\d{4})',
            ],
            special_rules={
                'has_doi_prefix': '10.1109/',
                'publisher': 'IEEE',
            }
        )
        
        # International Journal Publications (General Pattern)
        patterns['intl_journal'] = JournalPattern(
            name="International Journal (General)",
            identifier_patterns=[
                r'International\s+Journal\s+(?:of|for|on)',
                r'(?:European|American|Asian|African)\s+Journal\s+(?:of|for)',
                r'ISSN[:\s]+\d{4}-\d{3}[\dXx]',
            ],
            author_patterns=[
                # Standard academic format: First Last, First Last
                r'Author[s]?\s*[:\-–]?\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+)*)',
                # Authors with superscript numbers
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\d|\*)+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:\d|\*)+)*)',
                # Multiple lines with "and" separator
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:.*?\n.*?)*?(?:and\s+[A-Z][a-z]+\s+[A-Z][a-z]+))',
            ],
            title_patterns=[
                # Title usually first prominent text, may be all caps or title case
                r'^(?:.*?\n){0,3}([A-Z][A-Za-z\s:,\-–]{20,200})\n',
                # After journal name before authors
                r'(?:ISSN|Volume).*?\n+([A-Z][^\n]{20,150})\n',
            ],
            abstract_patterns=[
                r'ABSTRACT\s*\n+(.*?)(?=\n\s*(?:Keywords?|KEYWORDS?|INTRODUCTION|Introduction|1\.))',
                r'Abstract\s*[:.\-–]?\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction|Background|1\.))',
                # Some journals use "Summary" instead
                r'Summary\s*[:.\-–]?\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction))',
            ],
            year_patterns=[
                r'©\s*(\d{4})',
                r'Volume\s+\d+.*?(\d{4})',
                r'Published[:\s]+.*?(\d{4})',
                r'\b(20\d{2})\b',  # Any 4-digit year starting with 20
            ],
            special_rules={
                'extract_issn': True,
                'validate_crossref': True,
                'check_doaj': True,
            }
        )
        
        # International Conference (General Pattern)
        patterns['intl_conference'] = JournalPattern(
            name="International Conference (General)",
            identifier_patterns=[
                r'(?:International|Annual|Regional|World)\s+Conference\s+(?:on|of)',
                r'Proceedings\s+of\s+(?:the\s+)?(?:International|Annual)',
                r'(?:IEEE|ACM|AAAI)\s+.*?Conference',
            ],
            author_patterns=[
                # Conference papers often have authors with affiliations
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+){0,10})',
                # With superscript numbers for affiliations
                r'([A-Z][a-z]+\s+[A-Z][a-z]+\d+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+\d+)*)',
                # Comma-separated with middle initials
                r'([A-Z]\.\s*[A-Z][a-z]+(?:\s*,\s*[A-Z]\.\s*[A-Z][a-z]+)+)',
            ],
            title_patterns=[
                # Conference title often bold/large at top
                r'^(?:.*?Conference.*?\n+)?([A-Z][A-Za-z\s:,\-–]{15,200}?)\n(?:[A-Z][a-z]+\s+[A-Z])',
                # After Proceedings line
                r'Proceedings.*?\n+([A-Z][^\n]{20,150})\n',
            ],
            abstract_patterns=[
                r'ABSTRACT\s*\n+(.*?)(?=\n\s*(?:Keywords?|Categories|General Terms|1\.|INTRODUCTION))',
                r'Abstract\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction|1\.))',
            ],
            year_patterns=[
                r'(\d{4})\s+(?:IEEE|ACM|Conference)',
                r'(?:Conference|Symposium).*?(\d{4})',
                r'\b(20\d{2})\b',
            ],
            special_rules={
                'paper_type': 'Conference Paper',
                'extract_conference_name': True,
                'validate_crossref': True,
            }
        )
        
        # Book Chapter (Enhanced Pattern)
        patterns['book_chapter'] = JournalPattern(
            name="Book Chapter",
            identifier_patterns=[
                r'Chapter\s+\d+',
                r'ISBN[:\s]+[\d\-]+',
                r'\(Ed[s]?\.\)',
                r'In[:\s]+.*?\(Ed[s]?\.\)',
            ],
            author_patterns=[
                # Chapter authors before the "In: Book Title (Eds.)"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*)\s*\n+In[:\s]',
                # Authors listed at top
                r'^(?:Chapter\s+\d+\s*\n+)?([A-Z][a-z]+\s+[A-Z][a-z]+(?:.*?\n.*?)*?)(?:\n\n|Abstract)',
                # With affiliations
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*,\s*[^\n]+University)',
            ],
            title_patterns=[
                # Chapter title usually after "Chapter X" or before authors
                r'Chapter\s+\d+\s*\n+([A-Z][^\n]{15,150})',
                # Before "In: Book Title"
                r'([A-Z][A-Za-z\s:,\-–]{20,150})\s*\n+In[:\s]',
                # At the top of the page
                r'^([A-Z][A-Z\s]{15,100})\n',
            ],
            abstract_patterns=[
                r'Abstract\s*[:.\-–]?\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction|1\.))',
                r'Summary\s*[:.\-–]?\s*\n+(.*?)(?=\n\s*(?:Keywords?|Introduction))',
            ],
            year_patterns=[
                r'©\s*(\d{4})',
                r'(?:Springer|Elsevier|Wiley|Cambridge|Oxford).*?(\d{4})',
                r'\b(20\d{2})\b',
            ],
            special_rules={
                'paper_type': 'Book Chapter',
                'extract_isbn': True,
                'extract_book_title': True,
                'extract_editors': True,
                'publisher_keywords': ['Springer', 'Elsevier', 'Wiley', 'Cambridge', 'Oxford', 'Taylor & Francis'],
            }
        )
        
        # Springer Journal/Book Pattern
        patterns['springer'] = JournalPattern(
            name="Springer Publications",
            identifier_patterns=[
                r'Springer',
                r'DOI:\s*10\.1007',
                r'©.*?Springer',
            ],
            author_patterns=[
                # Springer format: Name¹, Name²
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:[¹²³⁴⁵\d\*]+)?(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+(?:[¹²³⁴⁵\d\*]+)?)*)',
                # With middle initials
                r'([A-Z]\.\s*[A-Z]\.\s*[A-Z][a-z]+(?:\s*,\s*[A-Z]\.\s*[A-Z]\.\s*[A-Z][a-z]+)*)',
            ],
            title_patterns=[
                # Springer titles are usually clear at the top
                r'^([A-Z][A-Za-z\s:,\-–]{20,200}?)\n(?:[A-Z][a-z]+\s+[A-Z])',
            ],
            abstract_patterns=[
                r'Abstract\s+([^\n]+(?:\n(?!Keywords)[^\n]+)*)',
                r'Summary\s+([^\n]+(?:\n(?!Keywords)[^\n]+)*)',
            ],
            year_patterns=[
                r'©\s*(\d{4})\s+Springer',
                r'Published[:\s]+.*?(\d{4})',
            ],
            special_rules={
                'publisher': 'Springer',
                'doi_prefix': '10.1007',
            }
        )
        
        # Elsevier Journal Pattern
        patterns['elsevier'] = JournalPattern(
            name="Elsevier Publications",
            identifier_patterns=[
                r'Elsevier',
                r'DOI:\s*10\.1016',
                r'©.*?Elsevier',
            ],
            author_patterns=[
                # Elsevier format with superscripts
                r'([A-Z][a-z]+\s+[A-Z][a-z]+[a-z]*(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+[a-z]*){0,10})',
            ],
            title_patterns=[
                r'^([A-Z][^\n]{20,200})\n',
            ],
            abstract_patterns=[
                r'[Aa]bstract\s*\n+(.*?)(?=\n\s*(?:©|Keywords?|Introduction|1\.))',
            ],
            year_patterns=[
                r'©\s*(\d{4})\s+Elsevier',
                r'\b(20\d{2})\b',
            ],
            special_rules={
                'publisher': 'Elsevier',
                'doi_prefix': '10.1016',
            }
        )
        
        # Nature Portfolio Pattern
        patterns['nature'] = JournalPattern(
            name="Nature Portfolio",
            identifier_patterns=[
                r'Nature\s+(?:Publishing|Portfolio)?',
                r'DOI:\s*10\.1038',
                r'Scientific\s+Reports',
            ],
            author_patterns=[
                # Nature format: First Last, First Last & First Last
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*(?:\s+&\s+[A-Z][a-z]+\s+[A-Z][a-z]+)?)',
            ],
            title_patterns=[
                r'^([A-Z][^\n]{20,200})\n',
            ],
            abstract_patterns=[
                r'Abstract\s*\n+(.*?)(?=\n\s*(?:Introduction|Results|Methods))',
            ],
            year_patterns=[
                r'\b(20\d{2})\b',
            ],
            special_rules={
                'publisher': 'Nature Portfolio',
                'doi_prefix': '10.1038',
            }
        )
        
        return patterns
    
    def identify_journal(self, text: str) -> Optional[str]:
        """
        Identify which journal a paper is from.
        
        Args:
            text: PDF text content
            
        Returns:
            Journal identifier (key) or None
        """
        # Check first 2000 characters for journal identifiers
        search_text = text[:2000].replace('\n', ' ')
        
        for journal_id, pattern in self.patterns.items():
            for identifier in pattern.identifier_patterns:
                if re.search(identifier, search_text, re.IGNORECASE):
                    logger.info(f"Identified journal: {pattern.name}")
                    return journal_id
        
        return None
    
    def extract_authors(self, text: str, journal_id: str) -> Optional[str]:
        """
        Extract authors using journal-specific patterns.
        
        Args:
            text: PDF text content
            journal_id: Identified journal
            
        Returns:
            Extracted authors or None
        """
        if journal_id not in self.patterns:
            return None
        
        pattern = self.patterns[journal_id]
        search_text = text[:2000]
        
        for author_pattern in pattern.author_patterns:
            match = re.search(author_pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                authors = match.group(1).strip()
                
                # Clean up
                authors = re.sub(r'\s+', ' ', authors)
                authors = re.sub(r'\([^)]+\)', '', authors)  # Remove affiliations in parentheses
                authors = re.sub(r'\d+', '', authors)  # Remove affiliation numbers
                authors = authors.strip()
                
                if len(authors) > 5 and len(authors) < 300:
                    logger.info(f"Extracted authors using {pattern.name} pattern: {authors[:50]}...")
                    return authors
        
        return None
    
    def extract_title(self, text: str, journal_id: str) -> Optional[str]:
        """Extract title using journal-specific patterns."""
        if journal_id not in self.patterns:
            return None
        
        pattern = self.patterns[journal_id]
        search_text = text[:1500]
        
        for title_pattern in pattern.title_patterns:
            match = re.search(title_pattern, search_text, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                
                # Clean up
                title = re.sub(r'\s+', ' ', title)
                
                if len(title) > 10 and len(title) < 200:
                    logger.info(f"Extracted title using {pattern.name} pattern")
                    return title
        
        return None
    
    def extract_abstract(self, text: str, journal_id: str) -> Optional[str]:
        """Extract abstract using journal-specific patterns."""
        if journal_id not in self.patterns:
            return None
        
        pattern = self.patterns[journal_id]
        search_text = text[:5000]
        
        for abstract_pattern in pattern.abstract_patterns:
            match = re.search(abstract_pattern, search_text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                
                # Clean up
                abstract = re.sub(r'\s+', ' ', abstract)
                
                if len(abstract) > 50 and len(abstract) < 5000:
                    logger.info(f"Extracted abstract using {pattern.name} pattern")
                    return abstract
        
        return None
    
    def extract_year(self, text: str, journal_id: str) -> Optional[int]:
        """Extract year using journal-specific patterns."""
        if journal_id not in self.patterns:
            return None
        
        pattern = self.patterns[journal_id]
        search_text = text[:2000]
        
        for year_pattern in pattern.year_patterns:
            match = re.search(year_pattern, search_text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 1950 <= year <= 2030:
                    logger.info(f"Extracted year using {pattern.name} pattern: {year}")
                    return year
        
        return None
    
    def get_journal_metadata(self, journal_id: str) -> Dict:
        """Get known metadata for a journal."""
        if journal_id not in self.patterns:
            return {}
        
        pattern = self.patterns[journal_id]
        return {
            'journal_name': pattern.name,
            'publisher': pattern.special_rules.get('publisher', ''),
            'issn': pattern.special_rules.get('issn', ''),
            'eissn': pattern.special_rules.get('eissn', ''),
            'doi_prefix': pattern.special_rules.get('has_doi_prefix', ''),
        }
    
    def add_custom_pattern(self, journal_id: str, pattern: JournalPattern):
        """
        Add a custom journal pattern.
        
        Args:
            journal_id: Unique identifier for the journal
            pattern: JournalPattern object
        """
        self.patterns[journal_id] = pattern
        logger.info(f"Added custom pattern for {pattern.name}")


# Global instance
journal_pattern_matcher = JournalPatternMatcher()


def extract_with_journal_patterns(text: str) -> Dict:
    """
    Try to extract metadata using journal-specific patterns.
    
    Args:
        text: PDF text content
        
    Returns:
        Dictionary with extracted metadata
    """
    # Identify journal
    journal_id = journal_pattern_matcher.identify_journal(text)
    
    if not journal_id:
        return {}
    
    # Extract using journal-specific patterns
    result = {
        'journal_identified': True,
        'journal_id': journal_id,
    }
    
    # Extract metadata
    authors = journal_pattern_matcher.extract_authors(text, journal_id)
    if authors:
        result['authors'] = authors
    
    title = journal_pattern_matcher.extract_title(text, journal_id)
    if title:
        result['title'] = title
    
    abstract = journal_pattern_matcher.extract_abstract(text, journal_id)
    if abstract:
        result['abstract'] = abstract
    
    year = journal_pattern_matcher.extract_year(text, journal_id)
    if year:
        result['year'] = year
    
    # Add journal metadata
    journal_meta = journal_pattern_matcher.get_journal_metadata(journal_id)
    result.update(journal_meta)
    
    return result

