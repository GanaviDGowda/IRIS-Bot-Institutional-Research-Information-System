"""
Export Dialog
Dialog for exporting papers with various format options and filters.
"""

import logging
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QCheckBox, QGroupBox, QFormLayout, QLineEdit,
    QSpinBox, QTextEdit, QMessageBox, QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """Worker thread for export process."""
    
    progress_updated = Signal(int, int)  # current, total
    export_completed = Signal(bool, str)  # success, message
    finished = Signal()
    
    def __init__(self, papers: List[Dict[str, Any]], export_format: str, output_path: str, filters: Dict[str, Any]):
        super().__init__()
        self.papers = papers
        self.export_format = export_format
        self.output_path = output_path
        self.filters = filters
    
    def run(self):
        """Run export process."""
        try:
            if self.export_format == "CSV":
                self._export_csv()
            elif self.export_format == "JSON":
                self._export_json()
            elif self.export_format == "BibTeX":
                self._export_bibtex()
            elif self.export_format == "EndNote":
                self._export_endnote()
            else:
                self.export_completed.emit(False, f"Unsupported format: {self.export_format}")
            
            self.finished.emit()
        except Exception as e:
            logger.error(f"Export error: {e}")
            self.export_completed.emit(False, f"Export failed: {str(e)}")
            self.finished.emit()
    
    def _export_csv(self):
        """Export to CSV format."""
        import pandas as pd
        
        # Prepare data for CSV
        csv_data = []
        for i, paper in enumerate(self.papers):
            self.progress_updated.emit(i + 1, len(self.papers))
            
            metadata = paper.get('metadata', {})
            row = {
                'ID': paper.get('id', ''),
                'Title': paper.get('title', ''),
                'Authors': paper.get('authors', ''),
                'Year': paper.get('year', ''),
                'Abstract': paper.get('abstract', ''),
                'DOI': paper.get('doi', ''),
                'Journal': paper.get('journal', ''),
                'Publisher': paper.get('publisher', ''),
                'ISSN': paper.get('issn', ''),
                'URL': paper.get('url', ''),
                'File Path': paper.get('file_path', ''),
                'Department': metadata.get('department', ''),
                'Research Domain': metadata.get('research_domain', ''),
                'Paper Type': metadata.get('paper_type', ''),
                'Indexing Status': metadata.get('indexing_status', ''),
                'Student Work': metadata.get('student', ''),
                'Review Status': metadata.get('review_status', ''),
                'Keywords': ', '.join(metadata.get('keywords', [])),
                'Confidence': metadata.get('confidence', 0.0),
            }
            csv_data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        df.to_csv(self.output_path, index=False)
        self.export_completed.emit(True, f"Successfully exported {len(csv_data)} papers to CSV")
    
    def _export_json(self):
        """Export to JSON format."""
        import json
        
        # Prepare data for JSON
        json_data = []
        for i, paper in enumerate(self.papers):
            self.progress_updated.emit(i + 1, len(self.papers))
            json_data.append(paper)
        
        # Save to JSON file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        self.export_completed.emit(True, f"Successfully exported {len(json_data)} papers to JSON")
    
    def _export_bibtex(self):
        """Export to BibTeX format."""
        bibtex_entries = []
        for i, paper in enumerate(self.papers):
            self.progress_updated.emit(i + 1, len(self.papers))
            
            # Generate BibTeX entry
            entry = self._generate_bibtex_entry(paper)
            if entry:
                bibtex_entries.append(entry)
        
        # Save to BibTeX file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(bibtex_entries))
        
        self.export_completed.emit(True, f"Successfully exported {len(bibtex_entries)} papers to BibTeX")
    
    def _export_endnote(self):
        """Export to EndNote format."""
        # For now, export as CSV with EndNote-compatible format
        self._export_csv()
        self.export_completed.emit(True, f"Successfully exported {len(self.papers)} papers to EndNote format")
    
    def _generate_bibtex_entry(self, paper: Dict[str, Any]) -> str:
        """Generate BibTeX entry for a paper."""
        try:
            # Extract key information
            title = paper.get('title', 'Untitled')
            authors = paper.get('authors', 'Unknown')
            year = paper.get('year', '')
            journal = paper.get('journal', '')
            publisher = paper.get('publisher', '')
            doi = paper.get('doi', '')
            
            # Generate entry type
            paper_type = paper.get('metadata', {}).get('paper_type', 'article')
            if 'conference' in paper_type.lower():
                entry_type = 'inproceedings'
            elif 'book' in paper_type.lower():
                entry_type = 'inbook'
            elif 'thesis' in paper_type.lower():
                entry_type = 'phdthesis'
            else:
                entry_type = 'article'
            
            # Generate BibTeX key
            first_author = authors.split(',')[0].strip() if authors else 'Unknown'
            bibtex_key = f"{first_author.replace(' ', '').lower()}{year}"
            
            # Build entry
            entry_lines = [f"@{entry_type}{{{bibtex_key},"]
            entry_lines.append(f"  title = {{{title}}},")
            entry_lines.append(f"  author = {{{authors}}},")
            entry_lines.append(f"  year = {{{year}}},")
            
            if journal:
                entry_lines.append(f"  journal = {{{journal}}},")
            if publisher:
                entry_lines.append(f"  publisher = {{{publisher}}},")
            if doi:
                entry_lines.append(f"  doi = {{{doi}}},")
            
            entry_lines.append("}")
            
            return '\n'.join(entry_lines)
            
        except Exception as e:
            logger.error(f"Error generating BibTeX entry: {e}")
            return None


class ExportDialog(QDialog):
    """Dialog for exporting papers with various options."""
    
    def __init__(self, papers: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.papers = papers
        self.worker = None
        
        self.setWindowTitle("Export Papers")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.populate_options()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Export format selection
        format_group = QGroupBox("Export Format")
        format_layout = QFormLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "JSON", "BibTeX", "EndNote"])
        self.format_combo.setToolTip("Select the export format")
        format_layout.addRow("Format:", self.format_combo)
        
        # Output file selection
        file_group = QGroupBox("Output File")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select output file...")
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addWidget(format_group)
        layout.addWidget(file_group)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_metadata_check = QCheckBox("Include metadata")
        self.include_metadata_check.setChecked(True)
        options_layout.addWidget(self.include_metadata_check)
        
        self.include_fulltext_check = QCheckBox("Include full text")
        self.include_fulltext_check.setChecked(False)
        options_layout.addWidget(self.include_fulltext_check)
        
        self.include_confidence_check = QCheckBox("Include confidence scores")
        self.include_confidence_check.setChecked(True)
        options_layout.addWidget(self.include_confidence_check)
        
        layout.addWidget(options_group)
        
        # Filters
        filters_group = QGroupBox("Filters (Optional)")
        filters_layout = QFormLayout(filters_group)
        
        self.department_filter = QComboBox()
        self.department_filter.setEditable(True)
        self.department_filter.setPlaceholderText("All departments...")
        filters_layout.addRow("Department:", self.department_filter)
        
        self.domain_filter = QComboBox()
        self.domain_filter.setEditable(True)
        self.domain_filter.setPlaceholderText("All domains...")
        filters_layout.addRow("Research Domain:", self.domain_filter)
        
        self.year_from_spin = QSpinBox()
        self.year_from_spin.setRange(1900, 2030)
        self.year_from_spin.setValue(2000)
        filters_layout.addRow("Year From:", self.year_from_spin)
        
        self.year_to_spin = QSpinBox()
        self.year_to_spin.setRange(1900, 2030)
        self.year_to_spin.setValue(2024)
        filters_layout.addRow("Year To:", self.year_to_spin)
        
        layout.addWidget(filters_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel(f"Ready to export {len(self.papers)} papers")
        self.status_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def populate_options(self):
        """Populate dropdown options."""
        try:
            # Load departments
            from ..utils.department_manager import get_all_departments
            departments = get_all_departments()
            self.department_filter.addItems(["All"] + departments)
        except Exception as e:
            logger.error(f"Error loading departments: {e}")
            self.department_filter.addItems([
                "All", "Computer Science & Engineering", "Civil Engineering", 
                "Mechanical Engineering", "Electrical & Electronics Engineering"
            ])
        
        # Load research domains
        research_domains = [
            "All", "Machine Learning", "Artificial Intelligence", "Data Science", "Quantum Computing",
            "Computer Vision", "Natural Language Processing", "Robotics", "Cybersecurity",
            "Software Engineering", "Database Systems", "Computer Networks", "Operating Systems",
            "Algorithms", "Data Structures", "Computer Graphics", "Human-Computer Interaction",
            "Information Systems", "Web Technologies", "Mobile Computing", "Cloud Computing",
            "Big Data", "Internet of Things", "Blockchain", "Digital Forensics"
        ]
        self.domain_filter.addItems(research_domains)
    
    def browse_output_file(self):
        """Browse for output file."""
        format_extensions = {
            "CSV": "CSV Files (*.csv)",
            "JSON": "JSON Files (*.json)",
            "BibTeX": "BibTeX Files (*.bib)",
            "EndNote": "EndNote Files (*.txt)"
        }
        
        file_filter = format_extensions.get(self.format_combo.currentText(), "All Files (*.*)")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Export File", "", file_filter
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def start_export(self):
        """Start the export process."""
        if not self.file_path_edit.text().strip():
            QMessageBox.warning(self, "No File Selected", "Please select an output file.")
            return
        
        # Get filters
        filters = {}
        if self.department_filter.currentText() and self.department_filter.currentText() != "All":
            filters['department'] = self.department_filter.currentText()
        if self.domain_filter.currentText() and self.domain_filter.currentText() != "All":
            filters['research_domain'] = self.domain_filter.currentText()
        if self.year_from_spin.value() > 1900:
            filters['year_from'] = self.year_from_spin.value()
        if self.year_to_spin.value() < 2030:
            filters['year_to'] = self.year_to_spin.value()
        
        # Filter papers
        filtered_papers = self._apply_filters(self.papers, filters)
        
        if not filtered_papers:
            QMessageBox.warning(self, "No Papers", "No papers match the selected filters.")
            return
        
        # Start export worker
        self.worker = ExportWorker(
            filtered_papers,
            self.format_combo.currentText(),
            self.file_path_edit.text(),
            filters
        )
        
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.export_completed.connect(self.export_completed)
        self.worker.finished.connect(self.export_finished)
        
        self.worker.start()
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(filtered_papers))
        self.export_button.setEnabled(False)
        self.status_label.setText(f"Exporting {len(filtered_papers)} papers...")
    
    def _apply_filters(self, papers: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to papers."""
        filtered = papers.copy()
        
        for key, value in filters.items():
            if key == 'department':
                filtered = [p for p in filtered if value.lower() in p.get('metadata', {}).get('department', '').lower()]
            elif key == 'research_domain':
                filtered = [p for p in filtered if value.lower() in p.get('metadata', {}).get('research_domain', '').lower()]
            elif key == 'year_from':
                filtered = [p for p in filtered if p.get('year', 0) >= value]
            elif key == 'year_to':
                filtered = [p for p in filtered if p.get('year', 0) <= value]
        
        return filtered
    
    def update_progress(self, current: int, total: int):
        """Update progress bar."""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Exporting... {current}/{total} papers")
    
    def export_completed(self, success: bool, message: str):
        """Handle export completion."""
        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", message)
    
    def export_finished(self):
        """Handle export worker finished."""
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.status_label.setText(f"Ready to export {len(self.papers)} papers")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()


