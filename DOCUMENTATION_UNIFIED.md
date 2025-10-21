# Research Paper Browser – Unified Documentation (v3 Unified)

## Abstract
This document presents the design and implementation of a desktop system for automated ingestion, validation, enrichment, classification, and semantic retrieval of academic papers. Leveraging layout-aware PDF processing, multi-source metadata validation (Crossref, DOAJ/ISSN, Scholar fallback), and machine learning for domain and type classification, the system delivers a unified workflow from import to advanced search. We detail the architecture, algorithms, and data model, along with operational guidance and reproducibility instructions, enabling researchers to evaluate and extend the platform or to reproduce results for empirical studies.

## 1. Overview
A comprehensive, AI-assisted desktop application to import, validate, enrich, classify, search, manage, and export research papers. It unifies prior documentation into a single source of truth describing functional features, nonfunctional requirements, data model, processing pipelines, and technical details.

- Target users: Researchers, librarians, faculty, students
- Application type: Desktop (Qt/PySide6)
- Storage: SQLite by default; unified repository layer designed to be backend-agnostic
- Core strengths: Accurate PDF extraction, robust validation/enrichment, ML-assisted classification, fast hybrid/semantic search, and a clean GUI workflow

## 2. Key Functional Features
- Import PDFs: single, multi-select, and drag-and-drop
- Automated metadata extraction: title, authors, abstract, year, DOI, ISSN, journal, publisher
- Validation/enrichment: Crossref, ISSN/DOAJ, indexing status, quartiles, fallback via Google Scholar
- AI/ML classification: department, research domain, paper type
- Duplicate detection and merging assistance
- Advanced search: keyword (TF-IDF), semantic (embeddings), hybrid fusion, filtering
- Paper management: open PDF, edit fields, verify, delete, export CSV
- Operational tools: generate embeddings, clear caches, stats

## 3. Nonfunctional Requirements (NFRs)
- Performance: responsive UI; import ~2–5s per typical PDF; semantic query <1s for 10k+ papers with cache
- Scalability: designed for thousands to tens of thousands of papers on commodity hardware
- Reliability: resilient validations with fallbacks, transactional DB writes, integrity checks on migration
- Security & Privacy: local-only processing by default, minimal external calls (Crossref/Scholar), no telemetry
- Usability & Accessibility: consistent keyboard shortcuts, progress feedback, readable typography
- Maintainability: modular utilities, well-defined repository boundaries, centralized configuration
- Portability: Windows primary; Linux/macOS compatible with appropriate environment

## 4. Problem Statement
Managing large personal or institutional collections of academic PDFs is time-consuming and error-prone. PDFs lack consistent structure; manual metadata entry and verification are costly; searching by meaning across heterogeneous collections is difficult. This system addresses: (1) reliable extraction of structured metadata from PDFs, (2) authoritative metadata validation and enrichment, (3) automated classification to support organization, and (4) high-quality semantic/hybrid retrieval over local collections.

## 5. Contributions
- End-to-end unified desktop workflow for import→validate→enrich→classify→search
- Layout-aware extraction pipeline tuned for academic PDFs
- Multi-source validation strategy with principled fallback (Crossref → DOAJ/ISSN → Scholar)
- Integrated ML pipeline for department, domain, and paper type classification
- Hybrid semantic-keyword retrieval with caching and batch embedding generation
- Unified repository and schema guidance enabling backend portability

## 6. Methodology
### 6.1 Extraction
- PyMuPDF-based layout parsing (blocks, fonts, sizes)
- Title detection via size/position heuristics and pattern checks
- Author parsing via delimiters and capitalization; affiliation cues optional
- DOI/ISSN detection using robust regex and normalization
- Abstract detection via heading patterns and proximity

### 6.2 Validation & Enrichment
- Crossref API by DOI/title; reconciliation of fields (title, authors, journal, year)
- ISSN/DOAJ lookup for journal validity/indexing; indexing status normalization
- Scholar fallback: conservative scraping with throttled access; field triangulation

### 6.3 Classification
- Text preprocessing: lowercasing, tokenization, stopword removal
- Vectorization: TF-IDF unigram/bigram features for domain/department
- Models: linear/naive Bayes baselines (tunable)
- Paper type: rule-based classifier with keyword/section cues and confidence scoring

### 6.4 Search
- Semantic embeddings: `all-MiniLM-L6-v2` (384-dim) by default
- Cosine similarity for ranking; optional top-k candidate narrowing
- TF-IDF keyword search for lexical relevance
- Hybrid fusion: weighted sum of normalized semantic and TF-IDF scores; weights configurable

### 6.5 Duplicate Detection
- Normalized title and author overlap
- Optional embedding similarity on abstracts or titles
- Threshold-based flagging with user confirmation

## 7. Evaluation Protocol
- Datasets: curated local corpus of N papers (include domain diversity; provide stats)
- Tasks:
  - Extraction accuracy: compare extracted fields vs. ground-truth labels
  - Validation coverage: % of papers validated via Crossref/DOAJ/ISSN; fallback efficacy
  - Classification performance: per-class precision/recall/F1 for department/domain/type
  - Search quality: nDCG@k and Recall@k for query set with relevance judgments
  - Latency: import time per PDF; query time for semantic/keyword/hybrid
- Method:
  - Split labeled subset for classification (e.g., 80/20)
  - Use fixed random seeds for reproducibility
  - Report macro/micro metrics and confidence intervals where appropriate

## 8. Results Template
Provide a section in the paper with tables such as:

- Extraction Accuracy
  - Title/Authors/Year/DOI/ISSN accuracy (%)
- Validation Coverage
  - Crossref hit rate; DOAJ/ISSN success; fallback success
- Classification
  - Macro-F1, Micro-F1 per task (department/domain/type)
- Search
  - nDCG@10, Recall@10 for semantic vs. keyword vs. hybrid
- Latency
  - Import seconds/PDF; Query ms/query (mean ± std)

## 9. Ethical Considerations
- Respect API terms of use and robots.txt
- Minimize external data transmission (no full-text upload)
- Transparently disclose ML model limitations and biases
- Provide user controls for disabling external calls

## 10. Reproducibility Checklist
- Environment: Python version, package versions frozen in `requirements.txt`
- Determinism: set seeds for ML pipelines; document randomization points
- Data availability: specify corpus sources; include sampling rules
- Configuration snapshots: record key config values used in experiments
- Scripts: provide minimal scripts to run import, embedding generation, and evaluation

## 11. Architecture Summary
- GUI: PySide6; dialogs for verification/edit/export
- Integration: orchestrates pipelines
- Utilities: extractors, validators, classifiers, search
- Data: unified repository (SQLite default)
See `ARCHITECTURE_AND_DIAGRAMS.md` for diagrams.

## 12. Installation & Setup
### 12.1 Prerequisites
- Python 3.8+
- Windows 10+

### 12.2 Install
```bash
pip install -r requirements.txt
```

### 12.3 Configuration
Environment variables (optional):
- `APP_DB_BACKEND`, `APP_SQLITE_PATH`, `APP_EMBED_MODEL`, proxy vars

## 13. Running
```bash
python run_unified_app.py
```

## 14. Data Dictionary (Unified)
Papers:
- id, title, authors, year, doi, journal, publisher, file_path, full_text, is_duplicate, duplicate_of_id, similarity_score, created_at, updated_at

Paper Metadata:
- id, paper_id, department, research_domain, paper_type, student, review_status, indexing_status, issn, published_month, created_at, updated_at

Citation Data:
- id, paper_id, citation_count, scimago_quartile, impact_factor, h_index, citation_source, citation_updated_at, created_at, updated_at

## 15. Algorithms & Heuristics
- Title/author/abstract heuristics; DOI/ISSN regex; year context windows
- Hybrid score fusion: s_hybrid = w_sem * s_sem_norm + w_kw * s_kw_norm
- Classification: TF-IDF + linear/naive Bayes; thresholds for abstention optional

## 16. External API Usage & Caching
- Crossref, DOAJ/ISSN, Scholar fallback with backoff
- In-memory embedding cache; TF-IDF index cache in process

## 17. Error Handling & Performance Tuning
- Retries/backoff for HTTP errors
- Batch embedding; pre-generation; candidate narrowing; filtering

## 18. Testing & Ops
- Unit/integration/UI tests; seeds for reproducibility
- Backups: copy `data/database.db`
- Logs: rotation and levels; stats view

## 19. Configuration Reference
See `app/config.py` for defaults and recommended overrides.

## 20. Example Usage
```python
from app.integration_manager import get_integration_manager
mgr = get_integration_manager()
res = mgr.process_pdf_file("data/papers/example.pdf")
```

## 21. Limitations & Future Work
- Limited multi-user support with SQLite; consider server DB backends
- Embedding model choices affect quality; explore domain-specific models
- OCR for scanned PDFs can be integrated for broader coverage

## 22. Conclusion
We deliver an integrated, performant, and extensible desktop system that automates the lifecycle of personal academic libraries and supports rigorous, reproducible evaluation of extraction, validation, classification, and search.

---
This document is ready to support writing a technical paper, providing methodology, evaluation guidance, and reproducibility details in addition to system documentation.
