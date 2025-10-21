"""
Paper Edit Dialog
Dialog for editing individual paper metadata in the verification system.
"""

import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QFormLayout,
    QGroupBox, QMessageBox, QTabWidget, QWidget, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class PaperEditDialog(QDialog):
    """Dialog for editing paper metadata."""
    
    def __init__(self, paper_data: Dict[str, Any], verified_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.paper_data = paper_data
        self.verified_data = verified_data
        self.edited_data = {}
        
        self.setWindowTitle(f"Edit Paper: {paper_data.get('title', 'Unknown')[:50]}...")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.populate_fields()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Basic Information Tab
        self.basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "Basic Information")
        
        # Publication Details Tab
        self.publication_tab = self.create_publication_tab()
        self.tab_widget.addTab(self.publication_tab, "Publication Details")
        
        # Metadata Tab
        self.metadata_tab = self.create_metadata_tab()
        self.tab_widget.addTab(self.metadata_tab, "Metadata")
        
        # Verified Data Tab
        self.verified_tab = self.create_verified_tab()
        self.tab_widget.addTab(self.verified_tab, "Verified Data")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Original")
        self.reset_button.clicked.connect(self.reset_to_original)
        
        self.reset_verified_button = QPushButton("Use Verified Data")
        self.reset_verified_button.clicked.connect(self.use_verified_data)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setDefault(True)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.reset_verified_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def create_basic_tab(self) -> QWidget:
        """Create the basic information tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Paper title")
        layout.addRow("Title:", self.title_edit)
        
        # Authors
        self.authors_edit = QLineEdit()
        self.authors_edit.setPlaceholderText("Author names (comma-separated)")
        layout.addRow("Authors:", self.authors_edit)
        
        # Year
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2030)
        self.year_spin.setValue(2024)
        layout.addRow("Year:", self.year_spin)
        
        # Published Month
        self.published_month_edit = QLineEdit()
        self.published_month_edit.setPlaceholderText("Published month (e.g., January, March, Q1)")
        layout.addRow("Published Month:", self.published_month_edit)
        
        # Abstract
        self.abstract_edit = QTextEdit()
        self.abstract_edit.setMaximumHeight(150)
        self.abstract_edit.setPlaceholderText("Paper abstract")
        layout.addRow("Abstract:", self.abstract_edit)
        
        # File Path (read-only)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("File Path:", self.file_path_edit)
        
        return widget
    
    def create_publication_tab(self) -> QWidget:
        """Create the publication details tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # DOI
        self.doi_edit = QLineEdit()
        self.doi_edit.setPlaceholderText("Digital Object Identifier")
        layout.addRow("DOI:", self.doi_edit)
        
        # Journal
        self.journal_edit = QLineEdit()
        self.journal_edit.setPlaceholderText("Journal name")
        layout.addRow("Journal:", self.journal_edit)
        
        # Publisher
        self.publisher_edit = QLineEdit()
        self.publisher_edit.setPlaceholderText("Publisher name")
        layout.addRow("Publisher:", self.publisher_edit)
        
        # ISSN
        self.issn_edit = QLineEdit()
        self.issn_edit.setPlaceholderText("ISSN number")
        layout.addRow("ISSN:", self.issn_edit)
        
        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paper URL")
        layout.addRow("URL:", self.url_edit)
        
        # Type
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("Publication type (e.g., journal-article)")
        layout.addRow("Type:", self.type_edit)
        
        return widget
    
    def create_metadata_tab(self) -> QWidget:
        """Create the metadata tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Department
        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        self.department_combo.setPlaceholderText("Select or enter department...")
        self._load_department_options()
        layout.addRow("Department:", self.department_combo)
        
        # Research Domain
        self.research_domain_combo = QComboBox()
        self.research_domain_combo.setEditable(True)
        self.research_domain_combo.setPlaceholderText("Select or enter research domain...")
        self._load_research_domain_options()
        layout.addRow("Research Domain:", self.research_domain_combo)
        
        # Paper Type
        self.paper_type_combo = QComboBox()
        self.paper_type_combo.setEditable(True)
        self.paper_type_combo.setPlaceholderText("Select or enter paper type...")
        self._load_paper_type_options()
        layout.addRow("Paper Type:", self.paper_type_combo)
        
        # Student
        self.student_combo = QComboBox()
        self.student_combo.addItems(["Yes", "No", "Unknown"])
        layout.addRow("Student Work:", self.student_combo)
        
        # Review Status
        self.review_status_combo = QComboBox()
        self.review_status_combo.setEditable(True)
        self.review_status_combo.addItems([
            "Imported", "Under Review", "Accepted", "Rejected", "Published", "Draft"
        ])
        layout.addRow("Review Status:", self.review_status_combo)
        
        return widget
    
    def create_verified_tab(self) -> QWidget:
        """Create the verified data tab (read-only)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Show verified data in a text area
        self.verified_text = QTextEdit()
        self.verified_text.setReadOnly(True)
        self.verified_text.setStyleSheet("background-color: #f8f9fa; font-family: monospace;")
        layout.addWidget(self.verified_text)
        
        return widget
    
    def populate_fields(self):
        """Populate fields with current data."""
        # Basic information
        self.title_edit.setText(self.paper_data.get('title', ''))
        self.authors_edit.setText(self.paper_data.get('authors', ''))
        self.year_spin.setValue(self.paper_data.get('year', 2024))
        self.published_month_edit.setText(self.paper_data.get('published_month', ''))
        self.abstract_edit.setPlainText(self.paper_data.get('abstract', ''))
        self.file_path_edit.setText(self.paper_data.get('file_path', ''))
        
        # Publication details
        self.doi_edit.setText(self.paper_data.get('doi', ''))
        self.journal_edit.setText(self.paper_data.get('journal', ''))
        self.publisher_edit.setText(self.paper_data.get('publisher', ''))
        self.issn_edit.setText(self.paper_data.get('issn', ''))
        self.url_edit.setText(self.paper_data.get('url', ''))
        self.type_edit.setText(self.paper_data.get('type', ''))
        
        # Metadata
        metadata = self.paper_data.get('metadata', {})
        self.department_combo.setCurrentText(metadata.get('department', ''))
        self.research_domain_combo.setCurrentText(metadata.get('research_domain', ''))
        self.paper_type_combo.setCurrentText(metadata.get('paper_type', 'Research Paper'))
        self.student_combo.setCurrentText(metadata.get('student', 'No'))
        self.review_status_combo.setCurrentText(metadata.get('review_status', 'Imported'))
        
        # Verified data
        self.update_verified_display()
    
    def update_verified_display(self):
        """Update the verified data display."""
        if not self.verified_data:
            self.verified_text.setPlainText("No verified data available")
            return
        
        lines = ["Verified Data Available:", "=" * 40, ""]
        
        for key, value in self.verified_data.items():
            if value:
                lines.append(f"{key}: {value}")
        
        if len(lines) == 3:  # Only header lines
            lines.append("No verified data to display")
        
        self.verified_text.setPlainText("\n".join(lines))
    
    def reset_to_original(self):
        """Reset all fields to original paper data."""
        reply = QMessageBox.question(
            self, "Reset to Original",
            "Are you sure you want to reset all fields to the original paper data?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.populate_fields()
    
    def use_verified_data(self):
        """Use verified data to populate fields."""
        if not self.verified_data:
            QMessageBox.information(self, "No Verified Data", "No verified data available to use.")
            return
        
        reply = QMessageBox.question(
            self, "Use Verified Data",
            "Are you sure you want to replace current values with verified data?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Update basic information
            if 'title' in self.verified_data:
                self.title_edit.setText(self.verified_data['title'])
            if 'authors' in self.verified_data:
                self.authors_edit.setText(self.verified_data['authors'])
            if 'year' in self.verified_data:
                self.year_spin.setValue(self.verified_data['year'])
            if 'abstract' in self.verified_data:
                self.abstract_edit.setPlainText(self.verified_data['abstract'])
            
            # Update publication details
            if 'doi' in self.verified_data:
                self.doi_edit.setText(self.verified_data['doi'])
            if 'journal' in self.verified_data:
                self.journal_edit.setText(self.verified_data['journal'])
            if 'publisher' in self.verified_data:
                self.publisher_edit.setText(self.verified_data['publisher'])
            if 'issn' in self.verified_data:
                self.issn_edit.setText(self.verified_data['issn'])
            if 'url' in self.verified_data:
                self.url_edit.setText(self.verified_data['url'])
            if 'type' in self.verified_data:
                self.type_edit.setText(self.verified_data['type'])
    
    def get_edited_data(self) -> Dict[str, Any]:
        """Get the edited data."""
        return {
            'title': self.title_edit.text().strip(),
            'authors': self.authors_edit.text().strip(),
            'year': self.year_spin.value(),
            'published_month': self.published_month_edit.text().strip(),
            'abstract': self.abstract_edit.toPlainText().strip(),
            'doi': self.doi_edit.text().strip(),
            'journal': self.journal_edit.text().strip(),
            'publisher': self.publisher_edit.text().strip(),
            'issn': self.issn_edit.text().strip(),
            'url': self.url_edit.text().strip(),
            'type': self.type_edit.text().strip(),
            'metadata': {
                'department': self.department_combo.currentText().strip(),
                'research_domain': self.research_domain_combo.currentText().strip(),
                'paper_type': self.paper_type_combo.currentText().strip(),
                'student': self.student_combo.currentText().strip(),
                'review_status': self.review_status_combo.currentText().strip(),
            }
        }
    
    def accept(self):
        """Handle save button click."""
        # Validate required fields
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            return
        
        if not self.authors_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Authors are required.")
            return
        
        # Get edited data
        self.edited_data = self.get_edited_data()
        
        # Confirm save
        reply = QMessageBox.question(
            self, "Save Changes",
            "Are you sure you want to save these changes?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            super().accept()
    
    def _load_department_options(self):
        """Load department options from department manager."""
        try:
            from ..utils.department_manager import get_all_departments
            departments = get_all_departments()
            self.department_combo.addItems(departments)
            logger.info(f"Loaded {len(departments)} departments for paper edit dialog")
        except Exception as e:
            logger.error(f"Error loading departments for paper edit dialog: {e}")
            # Fallback to basic departments
            self.department_combo.addItems([
                "Computer Science & Engineering",
                "Civil Engineering", 
                "Mechanical Engineering",
                "Electrical & Electronics Engineering",
                "Chemical Engineering",
                "Aerospace Engineering",
                "Biomedical Engineering",
                "Environmental Engineering"
            ])
    
    def _load_research_domain_options(self):
        """Load research domain options."""
        research_domains = [
            "Machine Learning", "Artificial Intelligence", "Data Science", "Quantum Computing",
            "Computer Vision", "Natural Language Processing", "Robotics", "Cybersecurity",
            "Software Engineering", "Database Systems", "Computer Networks", "Operating Systems",
            "Algorithms", "Data Structures", "Computer Graphics", "Human-Computer Interaction",
            "Information Systems", "Web Technologies", "Mobile Computing", "Cloud Computing",
            "Big Data", "Internet of Things", "Blockchain", "Digital Forensics",
            "Materials Science", "Renewable Energy", "Biomedical Engineering", "Environmental Engineering",
            "Structural Engineering", "Transportation Engineering", "Geotechnical Engineering",
            "Water Resources Engineering", "Thermodynamics", "Fluid Mechanics", "Heat Transfer",
            "Control Systems", "Power Systems", "Signal Processing", "Communication Systems",
            "Microelectronics", "VLSI Design", "Embedded Systems", "Wireless Communication"
        ]
        self.research_domain_combo.addItems(research_domains)
    
    def _load_paper_type_options(self):
        """Load paper type options."""
        paper_types = [
            "Journal Article", "Conference Paper", "Book Chapter", "Thesis/Dissertation",
            "Technical Report", "Preprint", "Review Article", "Case Study", "Short Paper",
            "Poster", "Workshop Paper", "White Paper", "Research Paper", "Other"
        ]
        self.paper_type_combo.addItems(paper_types)


