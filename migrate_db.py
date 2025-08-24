#!/usr/bin/env python3
"""
Database Migration Script
Adds full_text column to existing databases for full-text search functionality.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

# Change to app directory for imports
os.chdir(str(app_dir))

try:
    from database import get_connection, init_db
    from repository import PaperRepository
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import method...")
    
    # Alternative import method
    import importlib.util
    spec = importlib.util.spec_from_file_location("database", app_dir / "database.py")
    database = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database)
    
    spec = importlib.util.spec_from_file_location("repository", app_dir / "repository.py")
    repository = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(repository)
    
    get_connection = database.get_connection
    init_db = database.init_db
    PaperRepository = repository.PaperRepository


def migrate_database():
    """Migrate existing database to include full_text column."""
    print("=" * 60)
    print("Database Migration: Adding Full-Text Search Support")
    print("=" * 60)
    
    try:
        # Get connection and initialize database
        print("Connecting to database...")
        conn = get_connection()
        
        print("Initializing database schema...")
        init_db(conn)
        
        # Check if migration was successful
        repo = PaperRepository(conn)
        papers = repo.list_all()
        
        print(f"✓ Migration completed successfully!")
        print(f"✓ Database now supports full-text search")
        print(f"✓ Found {len(papers)} existing papers")
        
        # Show sample paper structure
        if papers:
            sample = papers[0]
            print(f"\nSample paper structure:")
            print(f"  Title: {sample.title}")
            print(f"  Has full_text field: {'Yes' if hasattr(sample, 'full_text') else 'No'}")
            if hasattr(sample, 'full_text'):
                print(f"  Full text length: {len(sample.full_text)} characters")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("Migration Complete! You can now:")
        print("1. Run the app: python run_app.py")
        print("2. Import new papers with full-text extraction")
        print("3. Search across complete paper content")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check database connection")
        print("2. Ensure PostgreSQL is running")
        print("3. Verify password in app/config.py")
        sys.exit(1)


if __name__ == "__main__":
    migrate_database()
