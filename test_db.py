#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script
Tests connection, creates database if needed, and verifies basic operations.
"""

import sys
import os

def test_psycopg2():
    """Test if psycopg2 is available"""
    try:
        import psycopg2
        print("✓ psycopg2 is installed")
        return True
    except ImportError:
        print("✗ psycopg2 is not installed. Run: pip install psycopg2-binary")
        return False

def test_connection(dsn):
    """Test basic connection to PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        print("✓ Connected to PostgreSQL successfully!")
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✓ PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def create_database(dsn, db_name="research"):
    """Create database if it doesn't exist"""
    try:
        import psycopg2
        
        # Connect to default postgres database first
        # Extract connection params from DSN
        if "dbname=" in dsn:
            # Remove dbname from DSN for initial connection
            base_dsn = dsn.replace(f"dbname={db_name}", "dbname=postgres")
        else:
            base_dsn = dsn + " dbname=postgres"
        
        conn = psycopg2.connect(base_dsn)
        conn.autocommit = True  # Required for CREATE DATABASE
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"✓ Database '{db_name}' already exists")
        else:
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"✓ Database '{db_name}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        return False

def test_app_database(dsn):
    """Test connection to the app's database and create tables"""
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        print("✓ Connected to app database successfully!")
        
        cursor = conn.cursor()
        
        # Test if papers table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'papers'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✓ Papers table already exists")
        else:
            # Create papers table
            cursor.execute("""
                CREATE TABLE papers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    year INT NOT NULL,
                    abstract TEXT,
                    department TEXT,
                    paper_type TEXT,
                    research_domain TEXT,
                    publisher TEXT,
                    student TEXT,
                    review_status TEXT,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_papers_year ON papers(year);")
            cursor.execute("CREATE INDEX idx_papers_authors ON papers(authors);")
            cursor.execute("CREATE INDEX idx_papers_publisher ON papers(publisher);")
            
            print("✓ Papers table and indexes created successfully")
        
        # Test insert and select
        cursor.execute("SELECT COUNT(*) FROM papers")
        count = cursor.fetchone()[0]
        print(f"✓ Papers table has {count} records")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Failed to test app database: {e}")
        return False

def main():
    print("=" * 50)
    print("PostgreSQL Connection Test")
    print("=" * 50)
    
    # Check if psycopg2 is installed
    if not test_psycopg2():
        sys.exit(1)
    
    # Get DSN from environment or use default
    dsn = os.environ.get("APP_POSTGRES_DSN")
    if not dsn:
        print("\nNo APP_POSTGRES_DSN environment variable found.")
        print("Using default connection parameters...")
        dsn = "dbname=research user=postgres password=postgres host=localhost port=5432"
        print(f"DSN: {dsn}")
        print("\nTo use custom DSN, set environment variable:")
        print("$env:APP_POSTGRES_DSN = 'your_connection_string'")
    
    print(f"\nTesting connection with DSN: {dsn}")
    
    # Test basic connection
    if not test_connection(dsn):
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if the password is correct")
        print("3. Verify host and port settings")
        print("4. Ensure the user has proper permissions")
        sys.exit(1)
    
    # Create database if needed
    print("\nCreating/checking database...")
    if not create_database(dsn):
        sys.exit(1)
    
    # Test app database
    print("\nTesting app database...")
    if not test_app_database(dsn):
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! PostgreSQL is ready for the app.")
    print("=" * 50)
    print("\nYou can now run the app with:")
    print("python run_app.py")

if __name__ == "__main__":
    main()
