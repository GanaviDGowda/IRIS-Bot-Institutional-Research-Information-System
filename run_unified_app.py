#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Research Paper Browser v3.0 - Unified Database
Main application launcher with unified database structure.
"""

import sys
import logging
from pathlib import Path

# Set UTF-8 encoding for stdout/stderr
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from app.gui_qt.enhanced_main_window import launch_enhanced_app
from app.database_unified import get_unified_database_manager, get_unified_paper_repository
from app.config import APP_NAME, DB_BACKEND

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_paper_browser_unified.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import fitz  # PyMuPDF
    except ImportError:
        missing_deps.append("PyMuPDF (fitz)")
    
    try:
        import sklearn
    except ImportError:
        missing_deps.append("scikit-learn")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import psycopg2
    except ImportError:
        missing_deps.append("psycopg2-binary")
    
    try:
        import sqlalchemy
    except ImportError:
        missing_deps.append("SQLAlchemy")
    
    if missing_deps:
        error_msg = f"Missing required dependencies:\n{chr(10).join(f'- {dep}' for dep in missing_deps)}\n\n"
        error_msg += "Please install them using:\npip install -r requirements.txt"
        
        print(error_msg)
        return False
    
    return True


def check_database_connection():
    """Check database connection."""
    try:
        db_manager = get_unified_database_manager()
        repo = get_unified_paper_repository()
        
        # Test database connection
        papers = repo.list_all()
        
        logger.info(f"Database connected successfully. Backend: {DB_BACKEND}")
        logger.info(f"Total papers in unified database: {len(papers)}")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def main():
    """Main application entry point."""
    print(f"Starting {APP_NAME}...")
    print(f"Database Backend: {DB_BACKEND}")
    print("Using Unified Database Structure")
    print("-" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database connection
    if not check_database_connection():
        print("Warning: Database connection issues detected.")
        print("The application may not function properly.")
        
        # Ask user if they want to continue
        try:
            app = QApplication([])
            reply = QMessageBox.question(
                None, "Database Connection Warning",
                "Database connection failed. Do you want to continue anyway?\n"
                "Some features may not work properly.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                sys.exit(1)
        except Exception:
            # If GUI can't be created, just continue
            pass
    
    try:
        # Launch the enhanced application
        print("Launching enhanced GUI with unified database...")
        
        # Set Qt application properties for proper Unicode handling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        launch_enhanced_app()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
