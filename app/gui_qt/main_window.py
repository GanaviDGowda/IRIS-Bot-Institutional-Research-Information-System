from typing import Optional, List
from PySide6.QtWidgets import (
	QApplication,
	QMainWindow,
	QWidget,
	QVBoxLayout,
	QHBoxLayout,
	QLineEdit,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QMenu,
	QFileDialog,
	QMessageBox,
	QProgressDialog,
)
from PySide6.QtCore import Qt
from pathlib import Path
import shutil

from ..config import APP_NAME
from ..database import get_connection, init_db
from ..repository import PaperRepository
from ..models import Paper
from ..search_engine import TfidfSearchEngine
from ..utils.pdf_opener import open_pdf
from ..utils.pdf_extractor import extract_pdf_text, get_pdf_stats


class MainWindow(QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle(APP_NAME)
		self.resize(1100, 720)

		self.conn = get_connection()
		init_db(self.conn)
		self.repo = PaperRepository(self.conn)
		self.search_engine = TfidfSearchEngine(self.repo)
		self.search_engine.rebuild_index()

		self._build_menu()
		self._build_body()

	def _build_menu(self) -> None:
		menubar = self.menuBar()
		browse = menubar.addMenu("Browse")
		for label, field in [
			("By Year", "year"),
			("By Author", "authors"),
			("By Paper Type", "paper_type"),
			("By Research Domain", "research_domain"),
			("By Publisher/Journal", "publisher"),
			("By Student", "student"),
			("By Review Status", "review_status"),
			("By Department", "department"),
		]:
			browse.addAction(label, lambda f=field: self._choose_filter_and_list(f))

		file_menu = menubar.addMenu("File")
		file_menu.addAction("Import Paper", self._import_paper)
		file_menu.addSeparator()
		file_menu.addAction("Exit", self.close)
		
		# Performance monitoring for large collections
		tools_menu = menubar.addMenu("Tools")
		tools_menu.addAction("Performance Stats", self._show_performance_stats)
		tools_menu.addAction("Clear Search Cache", self.search_engine.clear_cache)
		tools_menu.addAction("Optimize for Large Collection", self.search_engine.optimize_for_large_collection)

	def _build_body(self) -> None:
		central = QWidget()
		layout = QVBoxLayout(central)

		search_row = QHBoxLayout()
		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText("Search keywords...")
		self.search_input.returnPressed.connect(self._perform_search)
		btn = QPushButton("Search")
		btn.clicked.connect(self._perform_search)
		search_row.addWidget(self.search_input)
		search_row.addWidget(btn)
		layout.addLayout(search_row)

		self.table = QTableWidget(0, 5)
		self.table.setHorizontalHeaderLabels(["ID", "Title", "Authors", "Year", "Publisher"])
		self.table.cellDoubleClicked.connect(self._open_selected)
		layout.addWidget(self.table)

		buttons = QHBoxLayout()
		open_btn = QPushButton("Open PDF")
		open_btn.clicked.connect(self._open_selected)
		details_btn = QPushButton("View Details")
		details_btn.clicked.connect(self._view_selected_details)
		buttons.addWidget(open_btn)
		buttons.addWidget(details_btn)
		layout.addLayout(buttons)

		self.setCentralWidget(central)

	def _populate_results(self, papers: List[Paper]) -> None:
		self.table.setRowCount(0)
		for p in papers:
			row = self.table.rowCount()
			self.table.insertRow(row)
			self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
			self.table.setItem(row, 1, QTableWidgetItem(p.title))
			self.table.setItem(row, 2, QTableWidgetItem(p.authors))
			self.table.setItem(row, 3, QTableWidgetItem(str(p.year)))
			self.table.setItem(row, 4, QTableWidgetItem(p.publisher))
			for col in range(5):
				item = self.table.item(row, col)
				if item:
					item.setFlags(item.flags() ^ Qt.ItemIsEditable)

	def _perform_search(self) -> None:
		query = self.search_input.text().strip()
		self._populate_results([])
		if not query:
			return
		results = self.search_engine.search(query)
		papers = [p for p, _ in results]
		self._populate_results(papers)

	def _get_selected_paper(self) -> Optional[Paper]:
		row = self.table.currentRow()
		if row < 0:
			return None
		paper_id_item = self.table.item(row, 0)
		if paper_id_item is None:
			return None
		paper_id = int(paper_id_item.text())
		return self.repo.find_by_id(paper_id)

	def _open_selected(self) -> None:
		paper = self._get_selected_paper()
		if not paper:
			QMessageBox.information(self, "Open PDF", "Select a paper first.")
			return
		try:
			open_pdf(paper.file_path)
		except Exception as e:
			QMessageBox.critical(self, "Open PDF", str(e))

	def _view_selected_details(self) -> None:
		paper = self._get_selected_paper()
		if not paper:
			QMessageBox.information(self, "Details", "Select a paper first.")
			return
		
		# Show paper details including full text preview
		details_text = (
			f"Title: {paper.title}\n"
			f"Authors: {paper.authors}\n"
			f"Year: {paper.year}\n"
			f"Publisher/Journal: {paper.publisher}\n"
			f"Department: {paper.department}\n"
			f"Paper Type: {paper.paper_type}\n"
			f"Research Domain: {paper.research_domain}\n"
			f"Student: {paper.student}\n"
			f"Review Status: {paper.review_status}\n"
			f"PDF: {paper.file_path}\n\n"
			f"Abstract:\n{paper.abstract}\n\n"
		)
		
		# Add full text preview if available
		if paper.full_text:
			text_preview = paper.full_text[:500] + "..." if len(paper.full_text) > 500 else paper.full_text
			details_text += f"Full Text Preview:\n{text_preview}"
		else:
			details_text += "Full Text: Not extracted yet"
		
		QMessageBox.information(self, "Paper Details", details_text)

	def _choose_filter_and_list(self, field_name: str) -> None:
		values = self.repo.get_distinct_values(field_name)
		if not values:
			QMessageBox.information(self, "Browse", f"No values for {field_name}.")
			return
		menu = QMenu(self)
		for v in values:
			menu.addAction(str(v), lambda val=v: self._apply_filter(field_name, str(val)))
		# Show under the menu bar position
		pos = self.menuBar().mapToGlobal(self.menuBar().pos())
		menu.exec(pos)

	def _apply_filter(self, field_name: str, value: str) -> None:
		papers = self.repo.list_by_field(field_name, value)
		self._populate_results(papers)

	def _import_paper(self) -> None:
		# Get PDF first
		pdf_path, _ = QFileDialog.getOpenFileName(self, "Select PDF", str(Path.cwd()), "PDF Files (*.pdf)")
		if not pdf_path:
			return
		
		# Show progress dialog for text extraction
		progress = QProgressDialog("Extracting text from PDF...", "Cancel", 0, 100, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.setValue(25)
		progress.show()
		
		# Extract full text from PDF
		full_text = ""
		try:
			full_text = extract_pdf_text(pdf_path)
			if full_text:
				progress.setValue(75)
				QMessageBox.information(self, "Text Extraction", 
					f"Successfully extracted {len(full_text.split())} words from PDF")
			else:
				QMessageBox.warning(self, "Text Extraction", 
					"Could not extract text from PDF. Paper will be imported without full-text search.")
		except Exception as e:
			QMessageBox.warning(self, "Text Extraction", 
				f"Text extraction failed: {e}. Paper will be imported without full-text search.")
		
		progress.setValue(100)
		progress.close()
		
		# Get metadata from user
		from PySide6.QtWidgets import QInputDialog
		
		def ask(label: str, default: str = "") -> str:
			text, ok = QInputDialog.getText(self, "Import Paper", label, text=default)
			return str(text) if ok else ""

		title = ask("Title")
		authors = ask("Authors")
		year_str = ask("Year", "2024")
		abstract = ask("Abstract")
		department = ask("Department")
		paper_type = ask("Paper Type")
		research_domain = ask("Research Domain")
		publisher = ask("Publisher/Journal")
		student = ask("Student")
		review_status = ask("Review Status")

		if not title or not authors:
			QMessageBox.warning(self, "Import", "Title and Authors are required.")
			return
		try:
			year = int(year_str or "0")
		except ValueError:
			QMessageBox.warning(self, "Import", "Year must be an integer.")
			return

		# Copy PDF into data/papers
		from ..config import PAPERS_DIR
		PAPERS_DIR.mkdir(parents=True, exist_ok=True)
		src = Path(pdf_path)
		dest = PAPERS_DIR / src.name
		counter = 1
		while dest.exists():
			dest = PAPERS_DIR / f"{src.stem}_{counter}{src.suffix}"
			counter += 1
		shutil.copy2(src, dest)

		paper = Paper(
			id=None,
			title=title,
			authors=authors,
			year=year,
			abstract=abstract,
			department=department,
			paper_type=paper_type,
			research_domain=research_domain,
			publisher=publisher,
			student=student,
			review_status=review_status,
			file_path=str(dest),
			full_text=full_text,  # Include extracted full text
		)
		
		# Add paper to database
		new_paper = self.repo.add_paper(paper)
		
		# Use batch processing for better performance
		self.search_engine.batch_import_papers([new_paper])
		
		QMessageBox.information(self, "Import", 
			f"Paper imported successfully!\n"
			f"Title: {title}\n"
			f"Full text extracted: {'Yes' if full_text else 'No'}\n"
			f"Total papers: {len(self.repo.list_all())}")

	def _show_performance_stats(self) -> None:
		"""Show performance statistics for monitoring large collections."""
		stats = self.search_engine.get_performance_stats()
		
		stats_text = (
			f"Performance Statistics:\n\n"
			f"Total Papers: {stats['total_papers']}\n"
			f"Index Features: {stats['index_features']}\n"
			f"Cache Size: {stats['cache_size']}\n"
			f"Memory Usage: {stats['memory_usage_mb']:.2f} MB\n"
			f"Last Index Update: {stats['last_update']}\n\n"
			f"Search Cache: {'Enabled' if ENABLE_CACHING else 'Disabled'}\n"
			f"Batch Indexing: {'Enabled' if BATCH_INDEXING else 'Disabled'}\n"
			f"Max Features: {MAX_FEATURES}"
		)
		
		QMessageBox.information(self, "Performance Stats", stats_text)


def launch_app() -> None:
	app = QApplication([])
	w = MainWindow()
	w.show()
	app.exec() 