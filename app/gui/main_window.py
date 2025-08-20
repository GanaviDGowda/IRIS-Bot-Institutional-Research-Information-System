import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import shutil
from typing import Optional

from ..config import APP_NAME, DEFAULT_WINDOW_SIZE, PAPERS_DIR
from ..database import get_connection, init_db
from ..repository import PaperRepository
from ..models import Paper
from ..search_engine import TfidfSearchEngine
from ..utils.pdf_opener import open_pdf


class MainWindow:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title(APP_NAME)
		self.root.geometry(DEFAULT_WINDOW_SIZE)

		# Data and services
		self.conn = get_connection()
		init_db(self.conn)
		self.repo = PaperRepository(self.conn)
		self.search_engine = TfidfSearchEngine(self.repo)
		self.search_engine.rebuild_index()

		# UI elements
		self._build_menu()
		self._build_toolbar()
		self._build_results()

		self._refresh_filters()

	def _build_menu(self) -> None:
		menubar = tk.Menu(self.root)

		browse_menu = tk.Menu(menubar, tearoff=0)
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
			browse_menu.add_command(label=label, command=lambda f=field: self._open_filter_window(f))

		file_menu = tk.Menu(menubar, tearoff=0)
		file_menu.add_command(label="Import Paper", command=self._import_new_paper)
		file_menu.add_separator()
		file_menu.add_command(label="Exit", command=self.root.quit)

		menubar.add_cascade(label="Browse", menu=browse_menu)
		menubar.add_cascade(label="File", menu=file_menu)
		self.root.config(menu=menubar)

	def _build_toolbar(self) -> None:
		frame = ttk.Frame(self.root, padding=(8, 8))
		frame.pack(fill=tk.X)

		self.search_var = tk.StringVar()
		entry = ttk.Entry(frame, textvariable=self.search_var)
		entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
		entry.bind("<Return>", lambda e: self._perform_search())

		btn = ttk.Button(frame, text="Search", command=self._perform_search)
		btn.pack(side=tk.LEFT, padx=(8, 0))

	def _build_results(self) -> None:
		columns = ("id", "title", "authors", "year", "publisher")
		tree = ttk.Treeview(self.root, columns=columns, show="headings")
		for c in columns:
			tree.heading(c, text=c.capitalize())
			tree.column(c, anchor=tk.W, width=150)
			tree.column("id", width=60)
			tree.column("year", width=80)
		tree.pack(fill=tk.BOTH, expand=True)
		self.tree = tree

		# Context + double click
		tree.bind("<Double-1>", self._open_selected)

		# Bottom action bar
		bottom = ttk.Frame(self.root, padding=(8, 8))
		bottom.pack(fill=tk.X)
		open_btn = ttk.Button(bottom, text="Open PDF", command=self._open_selected)
		open_btn.pack(side=tk.LEFT)
		details_btn = ttk.Button(bottom, text="View Details", command=self._view_selected_details)
		details_btn.pack(side=tk.LEFT, padx=(8, 0))

	def _refresh_filters(self) -> None:
		# Potentially load filter caches; currently fetched on-demand
		pass

	def _perform_search(self) -> None:
		query = self.search_var.get().strip()
		self._populate_results([])
		if not query:
			return
		results = self.search_engine.search(query)
		items = []
		for paper, score in results:
			items.append((paper, score))
		self._populate_results([p for p, _ in items])

	def _populate_results(self, papers: list[Paper]) -> None:
		for i in self.tree.get_children():
			self.tree.delete(i)
		for p in papers:
			self.tree.insert("", tk.END, values=(p.id, p.title, p.authors, p.year, p.publisher))

	def _get_selected_paper(self) -> Optional[Paper]:
		selected = self.tree.selection()
		if not selected:
			return None
		item = self.tree.item(selected[0])
		paper_id = item["values"][0]
		return self.repo.find_by_id(int(paper_id))

	def _open_selected(self, event=None) -> None:  # type: ignore[override]
		paper = self._get_selected_paper()
		if not paper:
			messagebox.showinfo("Open PDF", "Select a paper first.")
			return
		try:
			open_pdf(paper.file_path)
		except Exception as e:
			messagebox.showerror("Open PDF", str(e))

	def _view_selected_details(self) -> None:
		paper = self._get_selected_paper()
		if not paper:
			messagebox.showinfo("Details", "Select a paper first.")
			return
		self._show_paper_details(paper)

	def _show_paper_details(self, paper: Paper) -> None:
		d = tk.Toplevel(self.root)
		d.title("Paper Details")
		d.geometry("700x500")
		text = tk.Text(d, wrap=tk.WORD)
		text.pack(fill=tk.BOTH, expand=True)
		text.insert(
			"1.0",
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
			f"Abstract:\n{paper.abstract}",
		)
		text.config(state=tk.DISABLED)

	def _open_filter_window(self, field_name: str) -> None:
		values = self.repo.get_distinct_values(field_name)
		w = tk.Toplevel(self.root)
		w.title(f"Browse {field_name}")
		w.geometry("400x500")
		lb = tk.Listbox(w)
		lb.pack(fill=tk.BOTH, expand=True)
		for v in values:
			lb.insert(tk.END, v)

		def on_select():
			selection = lb.curselection()
			if not selection:
				return
			value = lb.get(selection[0])
			papers = self.repo.list_by_field(field_name, value)
			self._populate_results(papers)
			w.destroy()

		btn = ttk.Button(w, text="Filter", command=on_select)
		btn.pack(pady=8)

	def _import_new_paper(self) -> None:
		# Simple modal form
		f = tk.Toplevel(self.root)
		f.title("Import Paper")
		f.geometry("600x600")

		fields = [
			("Title", "title"),
			("Authors", "authors"),
			("Year", "year"),
			("Abstract", "abstract"),
			("Department", "department"),
			("Paper Type", "paper_type"),
			("Research Domain", "research_domain"),
			("Publisher/Journal", "publisher"),
			("Student", "student"),
			("Review Status", "review_status"),
		]

		entries: dict[str, tk.Widget] = {}
		frm = ttk.Frame(f, padding=8)
		frm.pack(fill=tk.BOTH, expand=True)

		for idx, (label, key) in enumerate(fields):
			ttk.Label(frm, text=label).grid(row=idx, column=0, sticky=tk.W, pady=4)
			if key == "abstract":
				text = tk.Text(frm, height=6, wrap=tk.WORD)
				text.grid(row=idx, column=1, sticky=tk.EW, pady=4)
				entries[key] = text
			else:
				var = tk.StringVar()
				ent = ttk.Entry(frm, textvariable=var)
				ent.grid(row=idx, column=1, sticky=tk.EW, pady=4)
				entries[key] = ent

		frm.columnconfigure(1, weight=1)

		pdf_path_var = tk.StringVar()
		pdf_row = len(fields)
		ttk.Label(frm, text="PDF File").grid(row=pdf_row, column=0, sticky=tk.W, pady=4)
		pdf_entry = ttk.Entry(frm, textvariable=pdf_path_var)
		pdf_entry.grid(row=pdf_row, column=1, sticky=tk.EW, pady=4)
		def pick_pdf():
			p = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
			if p:
				pdf_path_var.set(p)
		pick_btn = ttk.Button(frm, text="Browse...", command=pick_pdf)
		pick_btn.grid(row=pdf_row, column=2, padx=4)

		def submit():
			try:
				title = self._get_entry_value(entries["title"]) or ""
				authors = self._get_entry_value(entries["authors"]) or ""
				year_str = self._get_entry_value(entries["year"]) or "0"
				abstract = self._get_text_value(entries.get("abstract")) or ""
				department = self._get_entry_value(entries["department"]) or ""
				paper_type = self._get_entry_value(entries["paper_type"]) or ""
				research_domain = self._get_entry_value(entries["research_domain"]) or ""
				publisher = self._get_entry_value(entries["publisher"]) or ""
				student = self._get_entry_value(entries["student"]) or ""
				review_status = self._get_entry_value(entries["review_status"]) or ""
				pdf_src = pdf_path_var.get()

				if not title or not authors or not pdf_src:
					raise ValueError("Title, Authors, and PDF are required.")
				year = int(year_str)

				# Copy PDF into papers dir
				pdf_src_path = Path(pdf_src)
				if pdf_src_path.suffix.lower() != ".pdf":
					raise ValueError("Selected file must be a PDF.")
				PAPERS_DIR.mkdir(parents=True, exist_ok=True)
				dest = PAPERS_DIR / pdf_src_path.name
				counter = 1
				while dest.exists():
					dest = PAPERS_DIR / f"{pdf_src_path.stem}_{counter}{pdf_src_path.suffix}"
					counter += 1
				shutil.copy2(pdf_src_path, dest)

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
				)
				self.repo.add_paper(paper)
				self.search_engine.rebuild_index()
				messagebox.showinfo("Import", "Paper imported successfully.")
				f.destroy()
			except Exception as e:
				messagebox.showerror("Import", str(e))

		submit_btn = ttk.Button(frm, text="Import", command=submit)
		submit_btn.grid(row=pdf_row + 1, column=0, columnspan=3, pady=12)

	def _get_entry_value(self, widget: tk.Widget) -> str:
		if isinstance(widget, ttk.Entry):
			return widget.get().strip()
		return ""

	def _get_text_value(self, widget: Optional[tk.Widget]) -> str:
		if widget is None:
			return ""
		if isinstance(widget, tk.Text):
			return widget.get("1.0", tk.END).strip()
		return ""


def launch_app() -> None:
	root = tk.Tk()
	MainWindow(root)
	root.mainloop() 