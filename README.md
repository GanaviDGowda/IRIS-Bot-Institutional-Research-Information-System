# 📚 Research Paper Management & Intelligent Search System

A **Python-based, NLP- and ML-powered research paper management system** that automates **PDF metadata extraction, verification, classification, duplicate detection, and intelligent search** using **semantic embeddings and hybrid information retrieval techniques**.

This project is designed as an **academic-grade research management platform**, suitable for **VTU final-year project submission**.

---

## 📌 Key Features

### ✅ Automated PDF Processing

* Extracts metadata directly from academic PDF files
* Supports title, authors, abstract, DOI, journal, year, and keywords
* Uses **confidence-based validation** to filter low-quality extraction

### ✅ Metadata Enrichment & Verification

* DOI normalization and validation
* Journal–publisher consistency checking
* Indexing verification (SCI, Scopus, ESCI, DOAJ, Conference, Preprint)
* Confidence aggregation to prevent incorrect overwrites

### ✅ Research Domain Classification

* Rule-based **NLP keyword prioritization**
* Regex-driven text matching
* Supports **multi-domain classification with confidence scores**
* Fully explainable (no black-box predictions)

### ✅ Semantic Search & Hybrid Retrieval

* Transformer-based **semantic embeddings**
* Keyword-based **TF-IDF vectorization**
* Hybrid search combining **semantic relevance + keyword matching**
* Cosine similarity in high-dimensional vector space

### ✅ Duplicate Detection

* Semantic similarity using sentence embeddings
* Metadata overlap analysis (title, DOI, authors)
* Threshold-based duplicate marking
* Prevents false positives seen in hash-based systems

### ✅ Performance Benchmarking

* Execution-time benchmarking for:

  * Database operations
  * Search engines
  * Verification pipeline
* Generates:

  * CSV results
  * VTU-ready performance report (Markdown)

### ✅ Scalable Modular Architecture

* Repository pattern for database abstraction
* Centralized **Integration Manager**
* Backend-independent (PostgreSQL / SQLite)

---

## 🧠 Machine Learning & NLP Techniques Used

### 🔹 Sentence Transformers

* Model: **all-MiniLM-L6-v2**
* Embedding size: **384 dimensions**
* Used for:

  * Semantic search
  * Similar paper recommendation
  * Duplicate detection

### 🔹 NLP Techniques

* Text preprocessing and normalization
* Regex-based keyword extraction
* Rule-based classification with priority weighting

### 🔹 Information Retrieval Models

* **Cosine Similarity** (dense vector comparison)
* **TF-IDF** (sparse keyword relevance)
* Hybrid ranking for improved retrieval accuracy

---

## 🏗️ System Architecture

```
PDF Input
   ↓
Metadata Extraction
   ↓
Metadata Enrichment & Verification
   ↓
Research Domain Classification
   ↓
Semantic Embedding Generation
   ↓
Duplicate Detection
   ↓
Database Storage
   ↓
Semantic / Hybrid Search
```

All components are coordinated through a **central Integration Manager**.

---

## 🧩 Project Structure

```
project-root/
│
├── app/
│   ├── database_unified.py
│   ├── integration_manager.py
│   ├── config.py
│   │
│   ├── utils/
│   │   ├── enhanced_pdf_extractor.py
│   │   ├── metadata_enricher.py
│   │   ├── duplicate_detector.py
│   │   ├── semantic_embedder.py
│   │   ├── semantic_search_engine.py
│   │   ├── hybrid_search_engine.py
│   │   ├── post_import_verifier.py
│   │
│   └── classifiers/
│       ├── unified_classifier.py
│       ├── research_domain_classifier.py
│
├── performance_timer.py
├── project_performance_analysis.py
├── generate_performance_report.py
├── performance_results.csv
├── vtu_performance_report.md
├── requirements.txt
└── README.md
```

---

## 💾 Data Storage

* **Metadata**: Stored in relational database (PostgreSQL / SQLite)
* **PDF Files**: Stored in filesystem, referenced by path in database
* **Embeddings**:

  * Generated dynamically
  * Cached in memory for faster retrieval
  * Can be persisted if required

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone <repository-url>
cd project-root
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Database

Edit:

```text
app/config.py
```

Set database backend and connection details.

### 4️⃣ Run Application

```bash
python app/main.py
```

---

## 🚀 Running Performance Analysis

### Step 1: Execute Benchmark Script

```bash
python project_performance_analysis.py
```

### Step 2: Generated Outputs

* `performance_results.csv`
* `vtu_performance_report.md`

### Metrics Measured

* Average execution time
* Minimum & maximum latency
* Standard deviation

---

## 📊 Performance Evaluation Summary

| Component             | Avg Time (ms) |
| --------------------- | ------------- |
| Database Insert       | ~2.5 ms       |
| Database Search       | ~3.3 ms       |
| Semantic Search       | ~108 ms       |
| Hybrid Search         | ~125 ms       |
| Verification Pipeline | ~2011 ms      |

---

## 🎯 Project Objectives (Simplified)

* Automate research paper metadata extraction and validation
* Apply NLP and ML for intelligent classification and duplicate detection
* Enable semantic and hybrid search over academic content
* Provide a scalable, database-driven research paper management system

---

## 🧪 Accuracy & Validation Strategy

* No misleading accuracy percentages used
* Confidence-based validation for extraction and verification
* Manual relevance testing for semantic search
* Threshold-controlled duplicate detection
* Explainable rule-based classification

---

## 📌 Advantages Over Existing Systems

| Existing Platforms             | This Project                    |
| ------------------------------ | ------------------------------- |
| Keyword-only search            | Semantic + Hybrid search        |
| No duplicate control           | Intelligent duplicate detection |
| No offline support             | Fully local deployment          |
| Black-box ranking              | Explainable algorithms          |
| No institutional customization | Department/domain-aware         |

---

## 📈 Future Enhancements

* Labeled dataset-based evaluation (Precision@K, Recall@K)
* FAISS-based vector indexing
* Incremental embedding updates
* Web-based multi-user deployment
* Citation trend analytics

---

## 🎓 Academic Compliance

✔ VTU-approved architecture
✔ No illegal scraping
✔ Explainable ML models
✔ Ethical data usage
✔ Reproducible experiments

---

## 🏁 Conclusion

This project demonstrates the **practical application of NLP, machine learning, and information retrieval techniques** to solve real-world challenges in academic research management, offering a scalable, accurate, and intelligent alternative to traditional research paper platforms.

---

