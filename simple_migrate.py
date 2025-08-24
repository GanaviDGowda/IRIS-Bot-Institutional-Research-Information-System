#!/usr/bin/env python3
"""
Simple Database Migration
Directly adds full_text column to PostgreSQL database.
"""

import psycopg2
import os


def migrate_postgres():
    """Add full_text column to PostgreSQL database."""
    print("=" * 60)
    print("Simple PostgreSQL Migration")
    print("=" * 60)
    
    # Get connection details from environment or use defaults
    dsn = os.environ.get("APP_POSTGRES_DSN")
    if not dsn:
        print("No APP_POSTGRES_DSN environment variable found.")
        print("Using default connection...")
        dsn = "dbname=research user=postgres password=Ganu@2004 host=localhost port=5432"
    
    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        
        cursor = conn.cursor()
        
        # Check if full_text column exists
        print("Checking if full_text column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'papers' AND column_name = 'full_text'
        """)
        
        if cursor.fetchone():
            print("✓ full_text column already exists")
        else:
            print("Adding full_text column...")
            cursor.execute("ALTER TABLE papers ADD COLUMN full_text TEXT")
            print("✓ full_text column added successfully")
        
        # Check table structure
        cursor.execute("SELECT * FROM papers LIMIT 1")
        columns = [desc[0] for desc in cursor.description]
        print(f"Table columns: {columns}")
        
        # Count papers
        cursor.execute("SELECT COUNT(*) FROM papers")
        count = cursor.fetchone()[0]
        print(f"✓ Found {count} papers in database")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Migration Complete!")
        print("=" * 60)
        print("You can now run: python run_app.py")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify connection details")
        print("3. Check if database 'research' exists")


if __name__ == "__main__":
    migrate_postgres()
