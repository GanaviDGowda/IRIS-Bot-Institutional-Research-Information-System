#!/usr/bin/env python3
"""
Bulk Import Utility for Research Papers
Efficiently imports multiple PDFs with data cleaning and validation.
"""

import sys
import os
from pathlib import Path
import shutil
from typing import List, Dict, Optional
import csv
import json

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.database import get_connection, init_db
from app.repository import PaperRepository
from app.models import Paper
from app.search_engine import TfidfSearchEngine
from app.utils.pdf_extractor import extract_pdf_text, get_pdf_stats


class BulkImporter:
    """Handles bulk import of research papers with data processing."""
    
    def __init__(self):
        self.conn = get_connection()
        init_db(self.conn)
        self.repo = PaperRepository(self.conn)
        self.search_engine = TfidfSearchEngine(self.repo)
        
        # Import statistics
        self.stats = {
            "total_files": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "skipped_files": 0,
            "errors": []
        }
    
    def import_from_directory(self, source_dir: str, metadata_file: Optional[str] = None) -> Dict:
        """
        Import all PDFs from a directory.
        
        Args:
            source_dir: Directory containing PDF files
            metadata_file: Optional CSV/JSON file with paper metadata
            
        Returns:
            Dictionary with import statistics
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise ValueError(f"Source directory not found: {source_dir}")
        
        # Load metadata if provided
        metadata = self._load_metadata(metadata_file) if metadata_file else {}
        
        # Find all PDF files
        pdf_files = list(source_path.glob("**/*.pdf"))
        self.stats["total_files"] = len(pdf_files)
        
        print(f"Found {len(pdf_files)} PDF files")
        print("Starting bulk import...")
        
        # Process files in batches
        batch_size = 10
        for i in range(0, len(pdf_files), batch_size):
            batch = pdf_files[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(pdf_files) + batch_size - 1)//batch_size}")
            
            for pdf_file in batch:
                try:
                    self._import_single_paper(pdf_file, metadata)
                    self.stats["successful_imports"] += 1
                except Exception as e:
                    self.stats["failed_imports"] += 1
                    self.stats["errors"].append(f"{pdf_file.name}: {str(e)}")
                    print(f"Failed to import {pdf_file.name}: {e}")
        
        # Rebuild search index after all imports
        print("Rebuilding search index...")
        self.search_engine.rebuild_index()
        
        return self.stats
    
    def import_from_csv(self, csv_file: str, pdf_dir: str) -> Dict:
        """
        Import papers using metadata from CSV file.
        
        CSV format: title,authors,year,abstract,department,paper_type,research_domain,publisher,student,review_status,filename
        """
        csv_path = Path(csv_file)
        pdf_path = Path(pdf_dir)
        
        if not csv_path.exists():
            raise ValueError(f"CSV file not found: {csv_file}")
        if not pdf_path.exists():
            raise ValueError(f"PDF directory not found: {pdf_dir}")
        
        # Load CSV data
        papers_data = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            papers_data = list(reader)
        
        self.stats["total_files"] = len(papers_data)
        print(f"Found {len(papers_data)} papers in CSV")
        
        # Process each paper
        for i, paper_data in enumerate(papers_data):
            try:
                print(f"Importing paper {i+1}/{len(papers_data)}: {paper_data.get('title', 'Unknown')}")
                self._import_from_csv_row(paper_data, pdf_path)
                self.stats["successful_imports"] += 1
            except Exception as e:
                self.stats["failed_imports"] += 1
                self.stats["errors"].append(f"Row {i+1}: {str(e)}")
                print(f"Failed to import row {i+1}: {e}")
        
        # Rebuild search index
        print("Rebuilding search index...")
        self.search_engine.rebuild_index()
        
        return self.stats
    
    def _import_single_paper(self, pdf_file: Path, metadata: Dict) -> None:
        """Import a single PDF file with optional metadata."""
        # Extract text from PDF
        full_text = extract_pdf_text(str(pdf_file))
        if not full_text:
            print(f"Warning: Could not extract text from {pdf_file.name}")
            full_text = ""
        
        # Get metadata (from file or generate defaults)
        paper_metadata = self._get_paper_metadata(pdf_file, metadata)
        
        # Copy PDF to papers directory
        dest_file = self._copy_pdf_file(pdf_file)
        
        # Create paper object
        paper = Paper(
            id=None,
            title=paper_metadata["title"],
            authors=paper_metadata["authors"],
            year=paper_metadata["year"],
            abstract=paper_metadata["abstract"],
            department=paper_metadata["department"],
            paper_type=paper_metadata["paper_type"],
            research_domain=paper_metadata["research_domain"],
            publisher=paper_metadata["publisher"],
            student=paper_metadata["student"],
            review_status=paper_metadata["review_status"],
            file_path=str(dest_file),
            full_text=full_text
        )
        
        # Add to database
        self.repo.add_paper(paper)
    
    def _import_from_csv_row(self, paper_data: Dict, pdf_dir: Path) -> None:
        """Import paper using data from CSV row."""
        filename = paper_data.get('filename', '').strip()
        if not filename:
            raise ValueError("No filename specified in CSV")
        
        pdf_file = pdf_dir / filename
        if not pdf_file.exists():
            raise ValueError(f"PDF file not found: {pdf_file}")
        
        # Extract text
        full_text = extract_pdf_text(str(pdf_file))
        if not full_text:
            full_text = ""
        
        # Copy PDF
        dest_file = self._copy_pdf_file(pdf_file)
        
        # Create paper with CSV data
        paper = Paper(
            id=None,
            title=paper_data.get('title', '').strip(),
            authors=paper_data.get('authors', '').strip(),
            year=int(paper_data.get('year', 2024)),
            abstract=paper_data.get('abstract', '').strip(),
            department=paper_data.get('department', '').strip(),
            paper_type=paper_data.get('paper_type', '').strip(),
            research_domain=paper_data.get('research_domain', '').strip(),
            publisher=paper_data.get('publisher', '').strip(),
            student=paper_data.get('student', '').strip(),
            review_status=paper_data.get('review_status', '').strip(),
            file_path=str(dest_file),
            full_text=full_text
        )
        
        # Validate required fields
        if not paper.title or not paper.authors:
            raise ValueError("Title and authors are required")
        
        # Add to database
        self.repo.add_paper(paper)
    
    def _get_paper_metadata(self, pdf_file: Path, metadata: Dict) -> Dict:
        """Get metadata for a paper, using filename-based lookup or defaults."""
        filename = pdf_file.stem
        
        # Try to find metadata by filename
        if filename in metadata:
            return metadata[filename]
        
        # Generate default metadata from filename
        return self._generate_metadata_from_filename(filename)
    
    def _generate_metadata_from_filename(self, filename: str) -> Dict:
        """Generate basic metadata from filename."""
        # Common filename patterns: "Author_Title_Year.pdf" or "Title_Author_Year.pdf"
        parts = filename.replace('_', ' ').replace('-', ' ').split()
        
        # Try to extract year (4-digit number)
        year = 2024
        for part in parts:
            if part.isdigit() and len(part) == 4 and 1900 <= int(part) <= 2030:
                year = int(part)
                parts.remove(part)
                break
        
        # Use remaining parts for title
        title = ' '.join(parts) if parts else filename
        
        return {
            "title": title,
            "authors": "Unknown Author",
            "year": year,
            "abstract": "",
            "department": "",
            "paper_type": "",
            "research_domain": "",
            "publisher": "",
            "student": "",
            "review_status": ""
        }
    
    def _copy_pdf_file(self, source_file: Path) -> Path:
        """Copy PDF file to papers directory with unique naming."""
        from app.config import PAPERS_DIR
        PAPERS_DIR.mkdir(parents=True, exist_ok=True)
        
        dest_file = PAPERS_DIR / source_file.name
        counter = 1
        
        # Ensure unique filename
        while dest_file.exists():
            dest_file = PAPERS_DIR / f"{source_file.stem}_{counter}{source_file.suffix}"
            counter += 1
        
        shutil.copy2(source_file, dest_file)
        return dest_file
    
    def _load_metadata(self, metadata_file: str) -> Dict:
        """Load metadata from CSV or JSON file."""
        file_path = Path(metadata_file)
        
        if file_path.suffix.lower() == '.csv':
            return self._load_csv_metadata(file_path)
        elif file_path.suffix.lower() == '.json':
            return self._load_json_metadata(file_path)
        else:
            raise ValueError("Metadata file must be CSV or JSON")
    
    def _load_csv_metadata(self, csv_file: Path) -> Dict:
        """Load metadata from CSV file."""
        metadata = {}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row.get('filename', '').strip()
                if filename:
                    # Remove .pdf extension if present
                    filename = Path(filename).stem
                    metadata[filename] = row
        
        return metadata
    
    def _load_json_metadata(self, json_file: Path) -> Dict:
        """Load metadata from JSON file."""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to filename-based lookup
        metadata = {}
        for item in data:
            filename = item.get('filename', '').strip()
            if filename:
                filename = Path(filename).stem
                metadata[filename] = item
        
        return metadata
    
    def create_metadata_template(self, output_file: str, format_type: str = 'csv') -> None:
        """Create a metadata template file for bulk import."""
        if format_type.lower() == 'csv':
            self._create_csv_template(output_file)
        elif format_type.lower() == 'json':
            self._create_json_template(output_file)
        else:
            raise ValueError("Format must be 'csv' or 'json'")
    
    def _create_csv_template(self, output_file: str) -> None:
        """Create CSV template for metadata."""
        headers = [
            'filename', 'title', 'authors', 'year', 'abstract', 
            'department', 'paper_type', 'research_domain', 
            'publisher', 'student', 'review_status'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerow([
                'example.pdf', 'Example Paper Title', 'John Doe; Jane Smith',
                '2024', 'This is an example abstract...', 'Computer Science',
                'Journal', 'Machine Learning', 'Example Journal', 'Student Name', 'Under Review'
            ])
        
        print(f"CSV template created: {output_file}")
    
    def _create_json_template(self, output_file: str) -> None:
        """Create JSON template for metadata."""
        template = [
            {
                "filename": "example.pdf",
                "title": "Example Paper Title",
                "authors": "John Doe; Jane Smith",
                "year": 2024,
                "abstract": "This is an example abstract...",
                "department": "Computer Science",
                "paper_type": "Journal",
                "research_domain": "Machine Learning",
                "publisher": "Example Journal",
                "student": "Student Name",
                "review_status": "Under Review"
            }
        ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"JSON template created: {output_file}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Main function for bulk import."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk import research papers")
    parser.add_argument("--source", required=True, help="Source directory or CSV file")
    parser.add_argument("--pdf-dir", help="PDF directory (when using CSV)")
    parser.add_argument("--create-template", help="Create metadata template file")
    parser.add_argument("--format", choices=['csv', 'json'], default='csv', help="Template format")
    
    args = parser.parse_args()
    
    if args.create_template:
        importer = BulkImporter()
        importer.create_metadata_template(args.create_template, args.format)
        return
    
    try:
        importer = BulkImporter()
        
        if args.source.endswith('.csv'):
            if not args.pdf_dir:
                print("Error: --pdf-dir is required when using CSV file")
                return
            stats = importer.import_from_csv(args.source, args.pdf_dir)
        else:
            stats = importer.import_from_directory(args.source)
        
        # Print results
        print("\n" + "="*60)
        print("BULK IMPORT COMPLETED")
        print("="*60)
        print(f"Total files: {stats['total_files']}")
        print(f"Successful: {stats['successful_imports']}")
        print(f"Failed: {stats['failed_imports']}")
        print(f"Skipped: {stats['skipped_files']}")
        
        if stats['errors']:
            print(f"\nErrors ({len(stats['errors'])}):")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")
        
        importer.close()
        
    except Exception as e:
        print(f"Bulk import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


