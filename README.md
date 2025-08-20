# Research Paper Browser - Desktop App

A Python Tkinter desktop application for browsing and searching research papers stored in an SQLite database. Supports menu-driven navigation (year, author, paper type, research domain, publisher/journal, student, review status), keyword search using TF-IDF + cosine similarity, importing new papers (metadata + PDF), viewing details, and opening PDFs in the default viewer.

## Features
- Browse by year, author, paper type, research domain, publisher/journal, student, review status
- Keyword search using TF-IDF + cosine similarity (scikit-learn)
- Import new research papers (metadata + PDF)
- View paper details and open PDFs
- SQLite database with paper metadata; PDF files stored on disk and linked in DB

## Tech Stack
- Python 3.9+
- Tkinter (GUI)
- SQLite (default DB)
- scikit-learn (TF-IDF + cosine similarity)

## Project Structure
```
app/
  gui/
    __init__.py
    main_window.py
  utils/
    __init__.py
    pdf_opener.py
  __init__.py
  config.py
  database.py
  models.py
  repository.py
  search_engine.py
  seed_data.py
run_app.py
requirements.txt
```
Data directories are created at runtime under `data/`:
- `data/database.db` (SQLite DB file)
- `data/papers/` (PDF storage)

## Setup
1. Create a virtual environment and install dependencies
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: . .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

2. Run the app
```bash
python run_app.py
```

3. (Optional) Seed with sample data
```bash
python -m app.seed_data
```

## Notes
- PDFs are copied into `data/papers/` during import.
- TF-IDF index is rebuilt in memory when the app starts and after imports.
- To switch to PostgreSQL in the future, adapt `app/config.py` and `app/database.py`. 