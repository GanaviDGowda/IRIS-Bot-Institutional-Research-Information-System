"""
PDF Text Extraction Utility
Extracts text from PDF files for full-text search indexing.
"""

import logging
from pathlib import Path
from typing import Optional, List

# Try to import PDF libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Extract text from PDF files using multiple methods for best results."""
    
    def __init__(self):
        self.extraction_methods = []
        
        # Add available extraction methods in order of preference
        if HAS_PDFPLUMBER:
            self.extraction_methods.append(self._extract_with_pdfplumber)
            logger.info("PDFPlumber available for text extraction")
        
        if HAS_PYPDF2:
            self.extraction_methods.append(self._extract_with_pypdf2)
            logger.info("PyPDF2 available for text extraction")
        
        if not self.extraction_methods:
            logger.warning("No PDF text extraction libraries available. Install PyPDF2 or pdfplumber.")
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF file using available methods.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None if extraction fails
        """
        if not self.extraction_methods:
            logger.error("No PDF extraction methods available")
            return None
        
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"PDF file not found: {file_path}")
            return None
        
        if file_path.suffix.lower() != '.pdf':
            logger.error(f"File is not a PDF: {file_path}")
            return None
        
        # Try each extraction method until one succeeds
        for method in self.extraction_methods:
            try:
                text = method(str(file_path))
                if text and text.strip():
                    logger.info(f"Successfully extracted text using {method.__name__}")
                    return self._clean_text(text)
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        logger.error(f"All PDF extraction methods failed for: {file_path}")
        return None
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber (better for complex layouts)."""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"Page {page_num + 1}: {page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
        
        return "\n".join(text_parts)
    
    def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2 (fallback method)."""
        text_parts = []
        
        with open(file_path, 'rb') as file:
            try:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"Page {page_num + 1}: {page_text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
            except Exception as e:
                logger.error(f"PyPDF2 reader failed: {e}")
                return ""
        
        return "\n".join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Remove page numbers and headers
        cleaned_lines = []
        for line in lines:
            # Skip lines that are just page numbers
            if line.lower().startswith('page ') and line.lower().endswith(':'):
                continue
            # Skip very short lines that might be headers/footers
            if len(line) < 3:
                continue
            cleaned_lines.append(line)
        
        # Join with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove multiple spaces
        import re
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def get_extraction_stats(self, file_path: str) -> dict:
        """
        Get statistics about text extraction.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extraction statistics
        """
        text = self.extract_text(file_path)
        if not text:
            return {"success": False, "error": "Text extraction failed"}
        
        # Count words, characters, lines
        words = len(text.split())
        characters = len(text)
        lines = len(text.split('\n'))
        
        return {
            "success": True,
            "words": words,
            "characters": characters,
            "lines": lines,
            "preview": text[:200] + "..." if len(text) > 200 else text
        }


# Global instance
pdf_extractor = PDFTextExtractor()


def extract_pdf_text(file_path: str) -> Optional[str]:
    """
    Convenience function to extract text from PDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text or None if extraction fails
    """
    return pdf_extractor.extract_text(file_path)


def get_pdf_stats(file_path: str) -> dict:
    """
    Get PDF extraction statistics.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dictionary with extraction statistics
    """
    return pdf_extractor.get_extraction_stats(file_path)
