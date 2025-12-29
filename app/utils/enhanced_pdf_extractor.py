"""
Enhanced PDF Metadata Extractor
Extracts structured metadata from research papers using PyMuPDF and regex patterns.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from .crossref_fetcher import fetch_metadata_by_doi
    HAS_CROSSREF = True
except ImportError:
    HAS_CROSSREF = False

try:
    from .issn_validator import issn_validator
    HAS_ISSN_VALIDATOR = True
except ImportError:
    HAS_ISSN_VALIDATOR = False

# Google Scholar validator removed
HAS_SCHOLAR_VALIDATOR = False

try:
    from .journal_patterns import journal_pattern_matcher
    HAS_JOURNAL_PATTERNS = True
except ImportError:
    HAS_JOURNAL_PATTERNS = False

try:
    from .paper_type_detector import paper_type_detector
    HAS_PAPER_TYPE_DETECTOR = True
except ImportError:
    HAS_PAPER_TYPE_DETECTOR = False

try:
    from .indexing_validator import indexing_validator
    HAS_INDEXING_VALIDATOR = True
except ImportError:
    HAS_INDEXING_VALIDATOR = False

try:
    from .domain_assigner import assign_research_domain
    HAS_DOMAIN_ASSIGNER = True
except ImportError:
    HAS_DOMAIN_ASSIGNER = False

try:
    from .research_domain_classifier import research_domain_classifier
    HAS_DOMAIN_CLASSIFIER = True
except ImportError:
    HAS_DOMAIN_CLASSIFIER = False

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Container for extracted PDF metadata."""
    title: str = ""
    authors: str = ""
    abstract: str = ""
    year: int = 0
    published_month: str = ""  # Published month (e.g., "January", "March", "Q1")
    doi: str = ""
    issn: str = ""
    journal: str = ""
    publisher: str = ""
    paper_type: str = ""  # Paper type (Journal Article, Conference Paper, etc.)
    indexing_status: str = ""  # SCI, Scopus, SCI + Scopus, Non-SCI/Non-Scopus
    research_domain: str = ""  # Automatically classified domain
    keywords: List[str] = None
    full_text: str = ""
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class EnhancedPDFExtractor:
    """Enhanced PDF extractor using PyMuPDF for research papers."""
    
    def __init__(self):
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF (fitz) is required for enhanced PDF extraction")
        
        # DOI pattern (fixed - removed extra parenthesis)
        self.doi_pattern = re.compile(
            r'(?:doi:|DOI:)?\s*(?:https?://)?(?:dx\.)?doi\.org/?(10\.\d{4,}/[^\s\)]+)',
            re.IGNORECASE
        )
        
        # ISSN pattern
        self.issn_pattern = re.compile(
            r'\b(\d{4})-(\d{3}[\dXx])\b'
        )
        
        # Year patterns
        self.year_patterns = [
            re.compile(r'\b(19|20)\d{2}\b'),  # 4-digit years
            re.compile(r'\((\d{4})\)'),  # Years in parentheses
            re.compile(r'\b(19|20)\d{2}\s*[,\-–]\s*(19|20)\d{2}\b'),  # Year ranges
        ]
        
        # Month patterns
        self.month_patterns = [
            # Full month names
            re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b', re.IGNORECASE),
            # Abbreviated month names
            re.compile(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\b', re.IGNORECASE),
            # Month numbers
            re.compile(r'\b(0?[1-9]|1[0-2])\b'),
            # Quarters
            re.compile(r'\b(Q[1-4])\b', re.IGNORECASE),
            # Season patterns
            re.compile(r'\b(Spring|Summer|Fall|Autumn|Winter)\b', re.IGNORECASE),
        ]
        
        # Month name mapping
        self.month_mapping = {
            'january': 'January', 'jan': 'January', '1': 'January',
            'february': 'February', 'feb': 'February', '2': 'February',
            'march': 'March', 'mar': 'March', '3': 'March',
            'april': 'April', 'apr': 'April', '4': 'April',
            'may': 'May', '5': 'May',
            'june': 'June', 'jun': 'June', '6': 'June',
            'july': 'July', 'jul': 'July', '7': 'July',
            'august': 'August', 'aug': 'August', '8': 'August',
            'september': 'September', 'sep': 'September', '9': 'September',
            'october': 'October', 'oct': 'October', '10': 'October',
            'november': 'November', 'nov': 'November', '11': 'November',
            'december': 'December', 'dec': 'December', '12': 'December',
            'q1': 'Q1', 'q2': 'Q2', 'q3': 'Q3', 'q4': 'Q4',
            'spring': 'Spring', 'summer': 'Summer', 'fall': 'Fall', 'autumn': 'Autumn', 'winter': 'Winter'
        }
        
        # Common journal patterns
        self.journal_patterns = [
            re.compile(r'Journal\s+of\s+([A-Z][^,\.]+)', re.IGNORECASE),
            re.compile(r'Proceedings\s+of\s+([A-Z][^,\.]+)', re.IGNORECASE),
            re.compile(r'IEEE\s+([A-Z][^,\.]+)', re.IGNORECASE),
            re.compile(r'ACM\s+([A-Z][^,\.]+)', re.IGNORECASE),
            re.compile(r'Nature\s+([A-Z][^,\.]+)', re.IGNORECASE),
            re.compile(r'Science\s+([A-Z][^,\.]+)', re.IGNORECASE),
        ]
        
        # Keywords patterns
        self.keywords_patterns = [
            re.compile(r'Keywords?:\s*([^\n]+)', re.IGNORECASE),
            re.compile(r'Key\s+Words?:\s*([^\n]+)', re.IGNORECASE),
            re.compile(r'Index\s+Terms?:\s*([^\n]+)', re.IGNORECASE),
        ]

    def extract_metadata(self, file_path: str) -> ExtractedMetadata:
        """
        Extract comprehensive metadata from a research paper PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ExtractedMetadata object with extracted information
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            doc = fitz.open(file_path)
            metadata = ExtractedMetadata()
            
            # Extract basic document metadata
            self._extract_document_metadata(doc, metadata)
            
            # Extract full text first (needed for journal pattern matching)
            full_text = ""
            for page_num in range(min(3, len(doc))):  # First 3 pages for pattern matching
                page = doc[page_num]
                full_text += page.get_text() + "\n"
            
            # Try journal-specific patterns first (if available)
            if HAS_JOURNAL_PATTERNS and full_text:
                journal_data = self._extract_with_journal_patterns(full_text, metadata)
                if journal_data:
                    logger.info("Successfully extracted using journal-specific patterns")
            
            # Extract text from first few pages for title, authors, abstract (fallback)
            self._extract_structured_content(doc, metadata)
            
            # If DOI found, fetch accurate metadata from Crossref
            if metadata.doi and HAS_CROSSREF:
                logger.info(f"DOI found: {metadata.doi}. Fetching from Crossref...")
                self._enrich_from_crossref(metadata)
            # If no DOI but have title and authors, try to find DOI via Crossref
            elif metadata.title and metadata.authors and HAS_CROSSREF:
                logger.info("No DOI found. Searching Crossref by title and authors...")
                self._find_and_enrich_from_crossref(metadata)
            # If still no metadata enrichment but have ISSN, validate via ISSN
            elif metadata.issn and HAS_ISSN_VALIDATOR and metadata.confidence < 0.8:
                logger.info(f"No DOI found. Validating journal via ISSN: {metadata.issn}...")
                self._validate_with_issn(metadata)
            
            # Extract full text
            metadata.full_text = self._extract_full_text(doc)
            
            # Detect paper type (using full text from first 3 pages)
            if HAS_PAPER_TYPE_DETECTOR and full_text:
                metadata.paper_type = self._detect_paper_type(full_text, metadata)
            
            # Determine indexing status (SCI, Scopus, etc.)
            if HAS_INDEXING_VALIDATOR:
                metadata.indexing_status = self._determine_indexing_status(metadata)
            
            # Classify research domain
            if (HAS_DOMAIN_ASSIGNER or HAS_DOMAIN_CLASSIFIER) and full_text:
                metadata.research_domain = self._classify_research_domain(full_text, metadata)
            
            # Calculate confidence based on extracted fields
            metadata.confidence = self._calculate_confidence(metadata)
            
            doc.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return ExtractedMetadata()

    def _extract_document_metadata(self, doc: fitz.Document, metadata: ExtractedMetadata) -> None:
        """Extract metadata from PDF document properties."""
        try:
            doc_metadata = doc.metadata
            
            # Extract title
            if doc_metadata.get('title'):
                metadata.title = doc_metadata['title'].strip()
            
            # Extract authors
            if doc_metadata.get('author'):
                metadata.authors = doc_metadata['author'].strip()
            
            # Extract publisher/journal
            if doc_metadata.get('subject'):
                metadata.journal = doc_metadata['subject'].strip()
            elif doc_metadata.get('creator'):
                metadata.publisher = doc_metadata['creator'].strip()
                
        except Exception as e:
            logger.warning(f"Error extracting document metadata: {e}")
    
    def _extract_with_journal_patterns(self, text: str, metadata: ExtractedMetadata) -> bool:
        """
        Try to extract metadata using journal-specific patterns.
        
        Args:
            text: PDF text content
            metadata: ExtractedMetadata object to update
            
        Returns:
            True if successful extraction, False otherwise
        """
        try:
            from .journal_patterns import journal_pattern_matcher
            
            # Identify the journal
            journal_id = journal_pattern_matcher.identify_journal(text)
            
            if not journal_id:
                return False
            
            logger.info(f"Using journal-specific patterns for extraction")
            
            # Extract authors (only if not already extracted or better)
            if not metadata.authors or len(metadata.authors) < 10:
                authors = journal_pattern_matcher.extract_authors(text, journal_id)
                if authors:
                    metadata.authors = authors
            
            # Extract title (only if not already extracted or better)
            if not metadata.title or len(metadata.title) < 15:
                title = journal_pattern_matcher.extract_title(text, journal_id)
                if title:
                    metadata.title = title
            
            # Extract abstract (only if not already extracted or better)
            if not metadata.abstract or len(metadata.abstract) < 50:
                abstract = journal_pattern_matcher.extract_abstract(text, journal_id)
                if abstract:
                    metadata.abstract = abstract
            
            # Extract year (only if not already extracted)
            if not metadata.year:
                year = journal_pattern_matcher.extract_year(text, journal_id)
                if year:
                    metadata.year = year
            
            # Get journal metadata
            journal_meta = journal_pattern_matcher.get_journal_metadata(journal_id)
            
            if not metadata.journal and journal_meta.get('journal_name'):
                metadata.journal = journal_meta['journal_name']
            
            if not metadata.publisher and journal_meta.get('publisher'):
                metadata.publisher = journal_meta['publisher']
            
            if not metadata.issn and journal_meta.get('issn'):
                metadata.issn = journal_meta['issn']
            
            return True
            
        except Exception as e:
            logger.error(f"Error extracting with journal patterns: {e}")
            return False

    def _extract_structured_content(self, doc: fitz.Document, metadata: ExtractedMetadata) -> None:
        """Extract structured content from first few pages."""
        try:
            # Process first 3 pages for title, authors, abstract
            content_pages = min(3, len(doc))
            text_content = ""
            
            for page_num in range(content_pages):
                page = doc[page_num]
                text_content += page.get_text() + "\n"
            
            # Extract title if not found in document metadata
            if not metadata.title:
                metadata.title = self._extract_title(text_content)
            
            # Extract authors if not found in document metadata
            if not metadata.authors:
                metadata.authors = self._extract_authors(text_content)
            
            # Extract abstract
            metadata.abstract = self._extract_abstract(text_content)
            
            # Extract DOI
            metadata.doi = self._extract_doi(text_content)
            
            # Extract ISSN
            metadata.issn = self._extract_issn(text_content)
            
            # Extract year
            metadata.year = self._extract_year(text_content)
            
            # Extract published month
            metadata.published_month = self._extract_month(text_content)
            
            # Extract journal if not found
            if not metadata.journal:
                metadata.journal = self._extract_journal(text_content)
            
            # Extract keywords
            metadata.keywords = self._extract_keywords(text_content)
            
        except Exception as e:
            logger.warning(f"Error extracting structured content: {e}")

    def _extract_title(self, text: str) -> str:
        """Extract paper title from text."""
        lines = text.split('\n')
        
        # Look for title in first few lines (usually the largest text)
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if len(line) > 10 and len(line) < 200:  # Reasonable title length
                # Skip lines that look like headers or page numbers
                if not any(skip in line.lower() for skip in ['page', 'doi:', 'abstract', 'keywords', 'introduction']):
                    return line
        
        return ""

    def _extract_authors(self, text: str) -> str:
        """Extract authors from text - captures ALL authors including multi-line."""
        lines = text.split('\n')
        
        # Try explicit author labels first (IJRASET and many journals use these)
        author_label_patterns = [
            r'Author[s]?\s*[:\-–]\s*([^\n]+)',  # Single line after label
            r'By\s*[:\-–]?\s*([A-Z][^\n]+)',
            r'Written\s+by\s*[:\-–]?\s*([A-Z][^\n]+)',
        ]
        
        first_1500 = text[:1500]
        for pattern in author_label_patterns:
            match = re.search(pattern, first_1500, re.IGNORECASE)
            if match:
                authors = match.group(1).strip()
                
                # Validate: Skip if it contains dates, URLs, or DOIs
                if self._is_invalid_author_string(authors):
                    continue
                
                # Clean and validate
                authors = self._clean_author_string(authors)
                
                if authors and len(authors) > 5 and len(authors) < 500:
                    return authors
        
        # Look for author patterns in lines (WITHOUT multi-line expansion to avoid capturing titles)
        title_line = None
        
        for i, line in enumerate(lines[:25]):  # Look in first 25 lines
            line = line.strip()
            
            # Skip if too short or contains common non-author words
            if len(line) < 5:
                continue
            
            # Skip explicit non-author content
            if any(skip in line.lower() for skip in ['abstract', 'keywords', 'introduction', 'doi:', 'issn', 'volume', 'issue']):
                continue
            
            # Track likely title (usually appears before authors)
            if not title_line and self._looks_like_title(line):
                title_line = i
                continue
            
            # Check if line contains author-like patterns
            if self._looks_like_authors(line) and not self._looks_like_title(line):
                # Only accept if it has clear author patterns (multiple names with commas)
                if ',' in line and re.search(r'[A-Z][a-z]+', line):
                    authors = self._clean_author_string(line)
                    if authors:
                        return authors
        
        return ""
    
    def _looks_like_title(self, line: str) -> bool:
        """Check if a line looks like a paper title."""
        if not line or len(line) < 10:
            return False
        
        # Titles are usually:
        # - Longer than author lines (>50 chars often)
        # - Don't have commas separating names
        # - May be all caps or title case
        # - Don't have typical author patterns
        
        # If it's very long and has no commas, likely a title
        if len(line) > 60 and ',' not in line:
            return True
        
        # If it has title-like keywords
        title_keywords = ['analysis', 'study', 'investigation', 'approach', 'method', 'system', 'using', 'based', 'application', 'development']
        if any(keyword in line.lower() for keyword in title_keywords):
            return True
        
        # If it's all caps and long (common title format)
        if line.isupper() and len(line) > 30:
            return True
        
        return False
    
    def _clean_author_string(self, authors: str) -> str:
        """Clean up author string - remove titles, affiliations, etc."""
        if not authors:
            return ""
        
        # Remove common prefixes/suffixes
        authors = re.sub(r'^(Author[s]?|By|Written\s+by)\s*:\s*', '', authors, flags=re.IGNORECASE)
        
        # Remove institutional affiliations at the end
        authors = re.sub(r'\s+(Department|Institute|University|College|School|Faculty|Center|Centre).*$', '', authors, flags=re.IGNORECASE)
        
        # Remove email addresses
        authors = re.sub(r'\s*[\w.+-]+@[\w-]+\.[\w.-]+\s*', ' ', authors)
        
        # Remove numbers and superscripts at the end (but keep within names)
        authors = re.sub(r'\s+\d+\s*$', '', authors)
        
        # Clean up whitespace
        authors = re.sub(r'\s+', ' ', authors)
        authors = re.sub(r'\s*,\s*', ', ', authors)
        
        authors = authors.strip()
        
        # Final validation
        if self._is_invalid_author_string(authors):
            return ""
        
        # Reject if it looks like a title
        if self._looks_like_title(authors):
            return ""
        
        return authors
    
    def _is_invalid_author_string(self, text: str) -> bool:
        """Check if a string is NOT valid authors (e.g., dates, URLs, DOIs)."""
        if not text or len(text) < 3:
            return True
        
        # Check for URLs and DOIs
        if re.search(r'https?://|www\.|doi\.org|10\.\d{4,}/', text, re.IGNORECASE):
            return True
        
        # Check for date patterns (month + year)
        date_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        ]
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check if mostly non-alphabetic (probably metadata, not names)
        alpha_count = sum(1 for c in text if c.isalpha())
        non_alpha_count = sum(1 for c in text if not c.isalpha() and not c.isspace())
        
        if alpha_count == 0:
            return True
        
        # If more than 60% non-alphabetic, probably not authors
        total_chars = alpha_count + non_alpha_count
        if total_chars > 0 and (non_alpha_count / total_chars) > 0.6:
            return True
        
        # Check for common metadata keywords
        metadata_keywords = ['volume', 'issue', 'issn', 'copyright', '©', 'published', 'received']
        if any(keyword in text.lower() for keyword in metadata_keywords):
            return True
        
        return False
    
    def _expand_author_lines(self, text: str, start_pos: int) -> str:
        """Expand author extraction to capture authors on multiple lines."""
        # Get text starting from the match position
        text_from_match = text[start_pos:]
        lines = text_from_match.split('\n')[:5]  # Look at next 5 lines
        
        authors_lines = []
        first_line = True
        
        for line in lines:
            line = line.strip()
            if not line:
                break
            
            # Skip the label line itself (e.g., "Authors:")
            if first_line and re.match(r'^(Author[s]?|By|Written\s+by)\s*:', line, re.IGNORECASE):
                first_line = False
                continue
            
            first_line = False
            
            # Stop if we hit non-author content
            if any(stop in line.lower() for stop in ['abstract', 'keywords', 'introduction', 'university', 'department', 'email', '@', 'institute', 'college']):
                break
            
            # Stop if it's a title-like line (all capitals or very long)
            if line.isupper() and len(line) > 20:
                break
            
            # Stop if it looks like metadata
            if self._is_invalid_author_string(line):
                break
            
            # Check if line looks like authors (has proper names)
            if re.search(r'[A-Z][a-z]+', line) and not line.lower().startswith(('volume', 'issue', 'page', 'doi', 'issn')):
                # Only add if it has name-like patterns
                if re.search(r'[A-Z][a-z]+[,\s]+[A-Z]', line):  # Has at least 2 name patterns
                    authors_lines.append(line)
                elif len(authors_lines) == 0:  # First line can be more lenient
                    authors_lines.append(line)
            else:
                break
        
        result = ' '.join(authors_lines)
        
        # Don't return if it looks invalid
        if self._is_invalid_author_string(result):
            return ""
        
        return result
    
    def _capture_multi_line_authors(self, lines: list, start_idx: int) -> str:
        """Capture authors that may span multiple consecutive lines."""
        if start_idx >= len(lines):
            return ""
        
        first_line = lines[start_idx].strip()
        
        # If first line is invalid, stop immediately
        if self._is_invalid_author_string(first_line):
            return ""
        
        authors_parts = [first_line]
        
        # Look at next few lines to see if they're continuation of authors
        for i in range(start_idx + 1, min(start_idx + 3, len(lines))):  # Reduced from 4 to 3
            line = lines[i].strip()
            
            # Empty line means end of author block
            if not line:
                break
            
            # Stop if we hit clearly non-author content
            if any(stop in line.lower() for stop in ['abstract', 'keywords', 'introduction', 'email', '@', 'department', 'university', 'institute', 'college', 'school']):
                break
            
            # Stop if it's metadata
            if self._is_invalid_author_string(line):
                break
            
            # Stop if line is all uppercase (likely a section header)
            if line.isupper() and len(line) > 10:
                break
            
            # If line has author-like patterns, include it
            if self._looks_like_authors(line):
                # But only if it actually has name patterns
                if re.search(r'[A-Z][a-z]+[,\s]+[A-Z]', line):
                    authors_parts.append(line)
                else:
                    break
            # If line looks like continuation (starts with lowercase or comma)
            elif re.match(r'^[a-z,]', line) or line.startswith(','):
                authors_parts.append(line)
            else:
                break
        
        # Join all parts
        authors = ' '.join(authors_parts)
        
        # Clean up
        authors = re.sub(r'\s+', ' ', authors)
        authors = re.sub(r'\s*,\s*', ', ', authors)  # Normalize commas
        
        # Final validation
        if self._is_invalid_author_string(authors):
            return ""
        
        # Remove common suffixes that might have been captured
        authors = re.sub(r'\s+(Department|Institute|University|College|School).*$', '', authors, flags=re.IGNORECASE)
        
        return authors.strip()

    def _looks_like_authors(self, line: str) -> bool:
        """Check if a line looks like it contains authors."""
        # Skip lines that are clearly not authors
        skip_words = ['copyright', 'volume', 'issue', 'journal', 'published', 'received', 'accepted', 'doi:', 'issn', 'http', 'www', '.com', '.org', '.edu']
        if any(word in line.lower() for word in skip_words):
            return False
        
        # Skip lines with dates (month + year patterns)
        date_patterns = [
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Dates like 12/31/2020
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # Dates like 2020-12-31
        ]
        for pattern in date_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return False
        
        # Skip lines that contain URLs or DOIs
        if re.search(r'https?://|doi\.org|10\.\d{4,}/|www\.', line, re.IGNORECASE):
            return False
        
        # Skip lines that are mostly numbers or special characters
        non_alpha_chars = sum(1 for c in line if not c.isalpha() and not c.isspace())
        alpha_chars = sum(1 for c in line if c.isalpha())
        if alpha_chars > 0 and non_alpha_chars / (alpha_chars + non_alpha_chars) > 0.5:
            return False
        
        # Common author indicators
        author_indicators = ['university', 'college', 'institute', 'department', 'lab', 'center', 'school', 'faculty']
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Check for email addresses
        if re.search(email_pattern, line):
            return True
        
        # Check for institutional affiliations
        if any(indicator in line.lower() for indicator in author_indicators):
            return True
        
        # Check for superscript numbers (common in author affiliations): Name¹, Name²
        if re.search(r'[A-Z][a-z]+\s*[¹²³⁴⁵¹²³⁴⁵⁶⁷⁸⁹⁰\d]', line):
            return True
        
        # Check for common author name patterns
        name_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+',  # First Last
            r'\b[A-Z][a-z]+,\s*[A-Z]',  # Last, First
            r'\b[A-Z]\.\s*[A-Z]\.\s*[A-Z][a-z]+',  # A. B. Last
            r'\b[A-Z][a-z]+\s+[A-Z]\.',  # First L.
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # First Middle Last
        ]
        
        # Count how many name-like patterns we find
        name_matches = 0
        for pattern in name_patterns:
            if re.search(pattern, line):
                name_matches += 1
        
        # If we have 2+ name patterns, it's likely an author line
        if name_matches >= 2:
            return True
        
        # Check for comma-separated names (common in multi-author papers)
        if ',' in line:
            parts = line.split(',')
            # Check if multiple parts look like names
            name_like_parts = sum(1 for part in parts if re.search(r'[A-Z][a-z]+\s+[A-Z]', part.strip()))
            if name_like_parts >= 2:
                return True
        
        return False

    def _extract_abstract(self, text: str) -> str:
        """Extract abstract from text."""
        # Look for abstract section in first 3000 characters
        first_part = text[:3000]
        
        # Try multiple abstract patterns
        abstract_patterns = [
            r'Abstract[:\s\-–]*\n(.*?)(?=\n\s*(?:Keywords?|Key\s+Words?|Introduction|1\.|I\.|Background|Methods|References?|©|\d+\.\s+Introduction))',
            r'ABSTRACT[:\s\-–]*\n(.*?)(?=\n\s*(?:KEYWORDS?|KEY\s+WORDS?|INTRODUCTION|1\.|I\.|BACKGROUND|METHODS|REFERENCES?|©|\d+\.\s+INTRODUCTION))',
            r'(?:Abstract|ABSTRACT)[:\s\-–]+(.*?)(?=\n\n|Keywords?|Introduction)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, first_part, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)
                abstract = re.sub(r'\n+', ' ', abstract)
                
                # Remove page numbers and other artifacts
                abstract = re.sub(r'Page\s+\d+', '', abstract)
                abstract = re.sub(r'\d+\s*$', '', abstract)
                
                # Check if it's a reasonable abstract length (50-5000 chars)
                if 50 <= len(abstract) <= 5000:
                    return abstract.strip()
        
        return ""

    def _extract_doi(self, text: str) -> str:
        """Extract DOI from text."""
        match = self.doi_pattern.search(text)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_issn(self, text: str) -> str:
        """Extract ISSN from text."""
        # Look in first 2000 characters
        search_text = text[:2000]
        
        # Try ISSN pattern with label first
        issn_label_pattern = re.compile(
            r'ISSN[:\s]+(\d{4})-(\d{3}[\dXx])',
            re.IGNORECASE
        )
        
        match = issn_label_pattern.search(search_text)
        if match:
            if isinstance(match.groups(), tuple) and len(match.groups()) >= 2:
                return f"{match.group(1)}-{match.group(2)}"
        
        # Try generic ISSN pattern
        match = self.issn_pattern.search(search_text)
        if match:
            if isinstance(match.groups(), tuple) and len(match.groups()) >= 2:
                return f"{match.group(1)}-{match.group(2)}"
        
        return ""

    def _extract_year(self, text: str) -> int:
        """Extract publication year from text."""
        years = []
        
        # Look for 4-digit years in first 500 characters (where metadata usually is)
        first_part = text[:500]
        year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        matches = year_pattern.findall(first_part)
        
        for match in matches:
            if isinstance(match, str):
                year = int(match)
            else:
                year = int(''.join(match))
            
            # Only accept reasonable years (1950-2030)
            if 1950 <= year <= 2030:
                years.append(year)
        
        if years:
            # Return the most recent year (likely publication year)
            return max(years)
        
        # Try full text if not found in first part
        all_matches = year_pattern.findall(text[:2000])
        for match in all_matches:
            if isinstance(match, str):
                year = int(match)
            else:
                year = int(''.join(match))
            
            if 1950 <= year <= 2030:
                years.append(year)
        
        return max(years) if years else 0

    def _extract_month(self, text: str) -> str:
        """Extract publication month from text."""
        # Look for month patterns in first 1000 characters (where metadata usually is)
        first_part = text[:1000]
        
        for pattern in self.month_patterns:
            matches = pattern.findall(first_part)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Get first group if tuple
                
                match_lower = match.lower().strip()
                if match_lower in self.month_mapping:
                    return self.month_mapping[match_lower]
        
        # Try to find month near year
        year_month_pattern = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*[,\.]?\s*(19|20)\d{2}\b', re.IGNORECASE)
        matches = year_month_pattern.findall(text[:2000])
        
        for match in matches:
            month_part = match[0].lower().strip()
            if month_part in self.month_mapping:
                return self.month_mapping[month_part]
        
        # Try to find month in date patterns (MM/DD/YYYY, DD/MM/YYYY, etc.)
        date_patterns = [
            re.compile(r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/(19|20)\d{2}\b'),  # MM/DD/YYYY
            re.compile(r'\b(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/(19|20)\d{2}\b'),  # DD/MM/YYYY
            re.compile(r'\b(19|20)\d{2}-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])\b'),  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = pattern.findall(text[:2000])
            for match in matches:
                if len(match) >= 2:
                    month_num = match[1] if match[0].startswith('19') or match[0].startswith('20') else match[0]
                    if month_num in self.month_mapping:
                        return self.month_mapping[month_num]
        
        return ""  # Default if no month found

    def _extract_journal(self, text: str) -> str:
        """Extract journal name from text."""
        # Look in first 1000 characters where journal name usually appears
        first_part = text[:1000]
        
        # Try pattern matching first
        for pattern in self.journal_patterns:
            match = pattern.search(first_part)
            if match:
                journal_name = match.group(0).strip()
                # Clean up the journal name
                journal_name = re.sub(r'^(Journal|Proceedings|Conference)\s+', '', journal_name, flags=re.IGNORECASE)
                return journal_name
        
        # Look for common journal indicators
        journal_indicators = [
            r'(?:Published\s+in|In)\s+([A-Z][^,\n]{10,80})',
            r'(?:Conference|Workshop|Symposium)\s+(?:on|of)\s+([A-Z][^,\n]{10,60})',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s+Journal)',
        ]
        
        for pattern_str in journal_indicators:
            pattern = re.compile(pattern_str)
            match = pattern.search(first_part)
            if match:
                return match.group(1).strip()
        
        return ""

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        keywords = []
        
        for pattern in self.keywords_patterns:
            match = pattern.search(text)
            if match:
                keyword_text = match.group(1).strip()
                # Split by common separators
                keyword_list = re.split(r'[,;]', keyword_text)
                keywords.extend([kw.strip() for kw in keyword_list if kw.strip()])
                break
        
        return keywords

    def _extract_full_text(self, doc: fitz.Document) -> str:
        """Extract full text from entire document."""
        full_text = ""
        
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text:
                    full_text += f"Page {page_num + 1}:\n{page_text}\n\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                continue
        
        return full_text.strip()

    def _find_and_enrich_from_crossref(self, metadata: ExtractedMetadata) -> None:
        """Find DOI via Crossref search and enrich metadata."""
        try:
            from .crossref_fetcher import crossref_fetcher
            
            # Search for DOI using title and authors
            logger.info(f"Searching for DOI with title: {metadata.title[:50]}...")
            found_doi = crossref_fetcher.find_doi_by_metadata(metadata.title, metadata.authors)
            
            if found_doi:
                logger.info(f"Found DOI via search: {found_doi}")
                metadata.doi = found_doi
                
                # Now fetch full metadata using the found DOI
                self._enrich_from_crossref(metadata)
            else:
                logger.warning("Could not find matching DOI via Crossref search")
                
        except Exception as e:
            logger.error(f"Error finding DOI from Crossref: {e}")
    
    def _enrich_from_crossref(self, metadata: ExtractedMetadata) -> None:
        """Enrich metadata using Crossref API."""
        try:
            crossref_data = fetch_metadata_by_doi(metadata.doi)
            
            if crossref_data.success:
                logger.info("Successfully fetched metadata from Crossref")
                
                # Update with Crossref data (only if better than extracted)
                if crossref_data.title and len(crossref_data.title) > len(metadata.title):
                    metadata.title = crossref_data.title
                    logger.info(f"Updated title from Crossref: {metadata.title[:50]}...")
                
                if crossref_data.authors and len(crossref_data.authors) > len(metadata.authors):
                    metadata.authors = crossref_data.authors
                    logger.info(f"Updated authors from Crossref")
                
                if crossref_data.journal:
                    metadata.journal = crossref_data.journal
                    logger.info(f"Updated journal from Crossref: {metadata.journal}")
                
                if crossref_data.publisher:
                    metadata.publisher = crossref_data.publisher
                
                if crossref_data.year > 0:
                    metadata.year = crossref_data.year
                    logger.info(f"Updated year from Crossref: {metadata.year}")
                
                if crossref_data.abstract and len(crossref_data.abstract) > len(metadata.abstract):
                    metadata.abstract = crossref_data.abstract
                    logger.info("Updated abstract from Crossref")
                
                # Boost confidence since we have Crossref validation
                metadata.confidence = 0.95
            else:
                logger.warning(f"Crossref fetch failed: {crossref_data.error}")
                
        except Exception as e:
            logger.error(f"Error enriching from Crossref: {e}")
    
    def _validate_with_issn(self, metadata: ExtractedMetadata) -> None:
        """Validate and enrich metadata using ISSN."""
        try:
            from .issn_validator import issn_validator
            
            logger.info(f"Validating journal with ISSN: {metadata.issn}")
            issn_data = issn_validator.validate_by_issn(metadata.issn)
            
            if issn_data.success:
                logger.info(f"Successfully validated journal: {issn_data.title}")
                
                # Update with ISSN data (only if not already present)
                if issn_data.title and not metadata.journal:
                    metadata.journal = issn_data.title
                    logger.info(f"Updated journal from ISSN: {metadata.journal}")
                
                if issn_data.publisher and not metadata.publisher:
                    metadata.publisher = issn_data.publisher
                    logger.info(f"Updated publisher from ISSN: {metadata.publisher}")
                
                # Boost confidence since we validated via ISSN
                metadata.confidence = max(metadata.confidence, 0.75)
                logger.info(f"Boosted confidence to {metadata.confidence} via ISSN validation")
            else:
                logger.warning(f"ISSN validation failed: {issn_data.error}")
                
        except Exception as e:
            logger.error(f"Error validating with ISSN: {e}")
    
    def _detect_paper_type(self, text: str, metadata: ExtractedMetadata) -> str:
        """Detect paper type from PDF content."""
        try:
            from .paper_type_detector import paper_type_detector
            
            paper_type = paper_type_detector.detect_paper_type(
                text=text,
                title=metadata.title,
                doi=metadata.doi
            )
            
            logger.info(f"Detected paper type: {paper_type}")
            return paper_type
            
        except Exception as e:
            logger.error(f"Error detecting paper type: {e}")
            return "Unknown"
    
    def _determine_indexing_status(self, metadata: ExtractedMetadata) -> str:
        """Determine indexing status (SCI, Scopus, etc.)."""
        try:
            from .indexing_validator import indexing_validator
            
            # Prepare metadata dictionary
            metadata_dict = {
                'journal': metadata.journal,
                'publisher': metadata.publisher,
                'issn': metadata.issn,
                'doi': metadata.doi,
                'paper_type': metadata.paper_type,
                'title': metadata.title,
                'authors': metadata.authors
            }
            
            # Get indexing status
            status = indexing_validator.validate_indexing_status(metadata_dict)
            
            logger.info(f"Indexing status determined: {status.indexing_label} ({status.confidence:.1%})")
            return status.indexing_label
            
        except Exception as e:
            logger.error(f"Error determining indexing status: {e}")
            return "Non-SCI/Non-Scopus"
    
    def _classify_research_domain(self, text: str, metadata: ExtractedMetadata) -> str:
        """Classify research domain based on content."""
        try:
            # Try new domain assigner first
            if HAS_DOMAIN_ASSIGNER:
                domain = assign_research_domain(
                    title=metadata.title or "",
                    abstract=metadata.abstract or "",
                    keywords=metadata.keywords or []
                )
                logger.info(f"Research domain assigned: {domain}")
                return domain
            
            # Fallback to existing classifier
            from .research_domain_classifier import research_domain_classifier
            
            # Classify domain
            classification = research_domain_classifier.classify_domain(
                text=text,
                title=metadata.title,
                abstract=metadata.abstract,
                keywords=metadata.keywords
            )
            
            logger.info(f"Research domain classified: {classification.primary_domain} ({classification.confidence:.1%})")
            return classification.primary_domain
            
        except Exception as e:
            logger.error(f"Error classifying research domain: {e}")
            return ""
    
    def _calculate_confidence(self, metadata: ExtractedMetadata) -> float:
        """Calculate confidence score for extracted metadata."""
        score = 0.0
        total_fields = 10  # title, authors, abstract, year, doi, issn, journal, paper_type, indexing_status, research_domain
        
        if metadata.title:
            score += 1.0
        if metadata.authors:
            score += 1.0
        if metadata.abstract:
            score += 1.0
        if metadata.year > 0:
            score += 1.0
        if metadata.doi:
            score += 1.0
        if metadata.issn:
            score += 1.0
        if metadata.journal:
            score += 1.0
        if metadata.paper_type and metadata.paper_type != "Unknown":
            score += 1.0
        if metadata.indexing_status and metadata.indexing_status != "Non-SCI/Non-Scopus":
            score += 1.0
        if metadata.research_domain:
            score += 1.0
        
        return score / total_fields

    def get_extraction_stats(self, file_path: str) -> Dict:
        """Get detailed extraction statistics."""
        metadata = self.extract_metadata(file_path)
        
        return {
            "success": metadata.confidence > 0,
            "confidence": metadata.confidence,
            "title_found": bool(metadata.title),
            "authors_found": bool(metadata.authors),
            "abstract_found": bool(metadata.abstract),
            "year_found": metadata.year > 0,
            "doi_found": bool(metadata.doi),
            "issn_found": bool(metadata.issn),
            "journal_found": bool(metadata.journal),
            "paper_type": metadata.paper_type,
            "paper_type_detected": bool(metadata.paper_type and metadata.paper_type != "Unknown"),
            "indexing_status": metadata.indexing_status,
            "indexing_detected": bool(metadata.indexing_status and metadata.indexing_status != "Non-SCI/Non-Scopus"),
            "research_domain": metadata.research_domain,
            "domain_classified": bool(metadata.research_domain),
            "keywords_count": len(metadata.keywords),
            "full_text_length": len(metadata.full_text),
            "word_count": len(metadata.full_text.split()) if metadata.full_text else 0,
        }


# Global instance
enhanced_pdf_extractor = EnhancedPDFExtractor() if HAS_PYMUPDF else None


def extract_paper_metadata(file_path: str) -> ExtractedMetadata:
    """
    Convenience function to extract metadata from a research paper PDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        ExtractedMetadata object
    """
    if not HAS_PYMUPDF:
        logger.error("PyMuPDF is required for enhanced PDF extraction")
        return ExtractedMetadata()
    
    return enhanced_pdf_extractor.extract_metadata(file_path)


def get_extraction_stats(file_path: str) -> Dict:
    """
    Get extraction statistics for a PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dictionary with extraction statistics
    """
    if not HAS_PYMUPDF:
        return {"success": False, "error": "PyMuPDF not available"}
    
    return enhanced_pdf_extractor.get_extraction_stats(file_path)
