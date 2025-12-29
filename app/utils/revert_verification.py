"""
Utility script to help revert incorrectly verified papers.

This script helps identify papers that were partially verified and might have
had their metadata incorrectly overwritten. It provides functions to:
1. List recently partially verified papers
2. Clear verification status to allow re-verification with improved logic
"""

import logging
import sys
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database_unified import get_unified_paper_repository

logger = logging.getLogger(__name__)


def list_partially_verified_papers(days: int = 7):
    """List papers that were partially verified in the last N days."""
    repo = get_unified_paper_repository()
    papers = repo.get_recently_verified_papers(status='partial', days=days)
    
    if not papers:
        print(f"No partially verified papers found in the last {days} days.")
        return
    
    print(f"\nFound {len(papers)} partially verified papers in the last {days} days:\n")
    print("-" * 100)
    print(f"{'ID':<6} {'Title':<40} {'Confidence':<12} {'Method':<15} {'Date':<20}")
    print("-" * 100)
    
    for paper in papers:
        paper_id = paper.get('id', 'N/A')
        title = (paper.get('title', 'N/A') or 'N/A')[:38]
        confidence = paper.get('verification_confidence', 0.0)
        method = (paper.get('verification_method', 'N/A') or 'N/A')[:13]
        date = str(paper.get('verification_date', 'N/A'))[:18]
        
        print(f"{paper_id:<6} {title:<40} {confidence:<12.2f} {method:<15} {date:<20}")
    
    print("-" * 100)
    return papers


def restore_metadata_from_pdf(paper_id: int):
    """Restore metadata by re-extracting from the original PDF file."""
    repo = get_unified_paper_repository()
    
    # Get paper info first
    paper = repo.get_paper_by_id(paper_id)
    if not paper:
        print(f"Paper {paper_id} not found.")
        return False
    
    print(f"\nPaper {paper_id}: {paper.get('title', 'Unknown')}")
    print(f"PDF file: {paper.get('file_path', 'N/A')}")
    print(f"Current verification status: {paper.get('verification_status', 'N/A')}")
    
    # Check if PDF file exists
    from pathlib import Path
    file_path = paper.get('file_path')
    if not file_path or not Path(file_path).exists():
        print(f"✗ PDF file not found: {file_path}")
        print("  Cannot restore metadata without the original PDF file.")
        return False
    
    print(f"\nRe-extracting metadata from PDF...")
    success = repo.restore_metadata_from_pdf(paper_id)
    
    if success:
        print(f"✓ Successfully restored metadata from PDF for paper {paper_id}")
        print("  Metadata has been restored to original extracted values.")
        print("  Verification status has been cleared.")
    else:
        print(f"✗ Failed to restore metadata for paper {paper_id}")
        print("  Check the logs for more details.")
    
    return success


def clear_verification_for_paper(paper_id: int):
    """Clear verification status for a specific paper."""
    repo = get_unified_paper_repository()
    
    # Get paper info first
    paper = repo.get_paper_by_id(paper_id)
    if not paper:
        print(f"Paper {paper_id} not found.")
        return False
    
    print(f"\nPaper {paper_id}: {paper.get('title', 'Unknown')}")
    print(f"Current verification status: {paper.get('verification_status', 'N/A')}")
    print(f"Verification method: {paper.get('verification_method', 'N/A')}")
    print(f"Confidence: {paper.get('verification_confidence', 0.0)}")
    
    success = repo.clear_verification_status(paper_id)
    if success:
        print(f"✓ Successfully cleared verification status for paper {paper_id}")
        print("  The paper can now be re-verified with the improved verification logic.")
    else:
        print(f"✗ Failed to clear verification status for paper {paper_id}")
    
    return success


def clear_verification_for_multiple_papers(paper_ids: List[int]):
    """Clear verification status for multiple papers."""
    repo = get_unified_paper_repository()
    success_count = 0
    
    for paper_id in paper_ids:
        if repo.clear_verification_status(paper_id):
            success_count += 1
            print(f"✓ Cleared verification for paper {paper_id}")
        else:
            print(f"✗ Failed to clear verification for paper {paper_id}")
    
    print(f"\nCleared verification for {success_count}/{len(paper_ids)} papers.")
    return success_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Revert verification status for papers")
    parser.add_argument("--list", action="store_true", help="List recently partially verified papers")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--clear", type=int, help="Clear verification for a specific paper ID")
    parser.add_argument("--clear-multiple", nargs="+", type=int, help="Clear verification for multiple paper IDs")
    parser.add_argument("--restore", type=int, help="Restore metadata from PDF for a specific paper ID (re-extracts from PDF)")
    
    args = parser.parse_args()
    
    if args.list:
        list_partially_verified_papers(days=args.days)
    elif args.restore:
        restore_metadata_from_pdf(args.restore)
    elif args.clear:
        clear_verification_for_paper(args.clear)
    elif args.clear_multiple:
        clear_verification_for_multiple_papers(args.clear_multiple)
    else:
        parser.print_help()

