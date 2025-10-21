# Unified Architecture and Diagrams

## 1. High-Level System Architecture
```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Enhanced Main Window]
        VD[Smart Verification Dialog]
        ED[Paper Edit Dialog]
        XD[Export Dialog]
    end

    subgraph "Application Layer"
        IM[Integration Manager]
        CFG[Config]
        LOG[Logging]
    end

    subgraph "Processing Layer"
        PEX[Enhanced PDF Extractor]
        ENR[Metadata Enricher]
        VAL[Validators]
        CLS[Classifiers]
        DED[Duplicate Detector]
    end

    subgraph "Search Layer"
        SEMSE[Semantic Search Engine]
        HYBSE[Hybrid Search Engine]
        TFIDF[TF-IDF Engine]
        EMBD[Semantic Embedder]
        CACHE[Embedding Cache]
    end

    subgraph "Data Layer"
        REPO[Unified Repository]
        DB[(SQLite DB)]
    end

    subgraph "External Services"
        CR[Crossref API]
        GS[Google Scholar]
        ISSN[ISSN/DOAJ]
        HF[Hugging Face Hub]
    end

    UI --> IM
    VD --> IM
    ED --> IM
    XD --> IM

    IM --> PEX
    IM --> ENR
    IM --> CLS
    IM --> DED

    IM --> SEMSE
    IM --> HYBSE
    HYBSE --> SEMSE
    HYBSE --> TFIDF
    SEMSE --> EMBD

    IM --> REPO
    REPO --> DB

    ENR --> VAL
    ENR --> CR
    VAL --> ISSN
    VAL --> GS

    EMBD --> HF

    SEMSE --> CACHE
    LOG --- IM
```

## 2. End-to-End Import Flow (Sequence)
```mermaid
sequenceDiagram
    participant U as User
    participant UI as Main Window
    participant IM as Integration Manager
    participant PEX as PDF Extractor
    participant ENR as Metadata Enricher
    participant VAL as Validators
    participant CLS as Classifiers
    participant RP as Repository
    participant DB as Database

    U->>UI: Import PDFs
    UI->>IM: process_pdf_file(path)
    IM->>PEX: extract_paper_metadata(path)
    PEX-->>IM: extracted metadata + full text
    IM->>ENR: enrich_paper_metadata(extracted)
    ENR->>VAL: DOI/ISSN/Index checks
    VAL-->>ENR: validated/enriched fields
    ENR-->>IM: enriched metadata
    IM->>CLS: predict department/domain/type
    CLS-->>IM: classifications + confidences
    IM->>RP: save paper + metadata
    RP->>DB: insert/update rows
    DB-->>RP: ok
    RP-->>IM: saved entity ids
    IM-->>UI: show review/verification
```

## 3. Search Flow (Sequence)
```mermaid
sequenceDiagram
    participant U as User
    participant UI as Main Window
    participant IM as Integration Manager
    participant SEM as Semantic Search
    participant HYB as Hybrid Search
    participant TF as TF-IDF Engine
    participant EMB as Semantic Embedder
    participant RP as Repository
    participant DB as Database

    U->>UI: Enter query (Semantic/Keyword/Hybrid)
    UI->>IM: search(query, type, filters)
    alt Semantic
        IM->>SEM: search_semantic(query, filters)
        SEM->>EMB: embed(query)
        EMB-->>SEM: Query embedding
        SEM->>RP: fetch candidates
        RP->>DB: SELECT ...
        DB-->>RP: rows
        SEM-->>IM: ranked results
    else Hybrid
        IM->>HYB: search_hybrid(query, filters)
        HYB->>SEM: semantic_scores
        HYB->>TF: tfidf_scores
        RP->>DB: SELECT ...
        DB-->>RP: rows
        HYB-->>IM: fused ranking
    else Keyword
        IM->>TF: search_tfidf(query, filters)
        RP->>DB: SELECT ...
        DB-->>RP: rows
        TF-->>IM: ranked results
    end
    IM-->>UI: display results
```

## 4. Unified Database Architecture (ER Diagram)
```mermaid
erDiagram
    PAPERS ||--o{ PAPER_METADATA : has
    PAPERS ||--o{ CITATION_DATA : has

    PAPERS {
        int id PK
        string title
        string authors
        int year
        string doi
        string journal
        string publisher
        string file_path
        text full_text
        boolean is_duplicate
        int duplicate_of_id
        float similarity_score
        datetime created_at
        datetime updated_at
    }

    PAPER_METADATA {
        int id PK
        int paper_id FK
        string department
        string research_domain
        string paper_type
        string student
        string review_status
        string indexing_status
        string issn
        string published_month
        datetime created_at
        datetime updated_at
    }

    CITATION_DATA {
        int id PK
        int paper_id FK
        int citation_count
        string scimago_quartile
        float impact_factor
        int h_index
        string citation_source
        datetime citation_updated_at
        datetime created_at
        datetime updated_at
    }
```

## 5. Detailed Entity Relationship Diagram (ERD)
```mermaid
erDiagram
    PAPERS {
        int id PK "Primary Key"
        string title "Paper Title"
        string authors "Author Names"
        int year "Publication Year"
        string abstract "Paper Abstract"
        string doi "Digital Object Identifier"
        string journal "Journal Name"
        string publisher "Publisher"
        string file_path "PDF File Path"
        text full_text "Extracted Full Text"
        boolean is_duplicate "Duplicate Flag"
        int duplicate_of_id FK "Reference to Original"
        float similarity_score "Duplicate Similarity"
        datetime created_at "Creation Timestamp"
        datetime updated_at "Last Update"
    }

    PAPER_METADATA {
        int id PK "Primary Key"
        int paper_id FK "Foreign Key to PAPERS"
        string department "Academic Department"
        string research_domain "Research Domain"
        string paper_type "Type of Paper"
        string student "Student Author Flag"
        string review_status "Review Status"
        string indexing_status "Indexing Status"
        string issn "ISSN Number"
        string published_month "Publication Month"
        datetime created_at "Creation Timestamp"
        datetime updated_at "Last Update"
    }

    CITATION_DATA {
        int id PK "Primary Key"
        int paper_id FK "Foreign Key to PAPERS"
        int citation_count "Number of Citations"
        string scimago_quartile "Scimago Quartile"
        float impact_factor "Journal Impact Factor"
        int h_index "H-Index"
        string citation_source "Citation Data Source"
        datetime citation_updated_at "Last Citation Update"
        datetime created_at "Creation Timestamp"
        datetime updated_at "Last Update"
    }

    SEARCH_INDEX {
        int id PK "Primary Key"
        int paper_id FK "Foreign Key to PAPERS"
        text search_vector "Full-text Search Vector"
        blob embedding_vector "Semantic Embedding"
        text tfidf_vector "TF-IDF Vector"
        datetime created_at "Creation Timestamp"
        datetime updated_at "Last Update"
    }

    USER_ACTIONS {
        int id PK "Primary Key"
        int paper_id FK "Foreign Key to PAPERS"
        string action_type "Action Type"
        string user_id "User Identifier"
        text action_data "Action Metadata"
        datetime created_at "Action Timestamp"
    }

    PAPERS ||--o{ PAPER_METADATA : "has metadata"
    PAPERS ||--o{ CITATION_DATA : "has citations"
    PAPERS ||--o{ SEARCH_INDEX : "has search data"
    PAPERS ||--o{ USER_ACTIONS : "has actions"
    PAPERS ||--o{ PAPERS : "duplicate_of"
```

## 6. Database Schema Details

### 6.1 Table Definitions
- **PAPERS**: Core paper information with bibliographic data
- **PAPER_METADATA**: Research-specific metadata and classifications
- **CITATION_DATA**: Citation metrics and impact factors
- **SEARCH_INDEX**: Search vectors and embeddings for retrieval
- **USER_ACTIONS**: User interaction tracking and analytics

### 6.2 Key Relationships
- One-to-Many: Papers → Metadata, Citations, Search Index, User Actions
- Self-Reference: Papers → Papers (duplicate relationships)
- Foreign Keys ensure referential integrity

### 6.3 Indexes and Performance
- Primary keys on all tables
- Foreign key indexes for join performance
- Full-text search indexes on search_vector
- Composite indexes on frequently queried fields

## 7. Component Diagram (Modules)
```mermaid
graph LR
    subgraph GUI
        M[enhanced_main_window.py]
        V[smart_verification_dialog.py]
        E[paper_edit_dialog.py]
        X[export_dialog.py]
    end
    subgraph Utils
        P[enhanced_pdf_extractor.py]
        N[metadata_enricher.py]
        C[crossref_fetcher.py]
        I[issn_validator.py]
        J[journal_patterns.py]
        S[semantic_embedder.py]
        SE[semantic_search_engine.py]
        H[hybrid_search_engine.py]
        R[research_domain_classifier.py]
        U[unified_classifier.py]
        T[paper_type_detector.py]
        D[department_manager.py]
        A[domain_assigner.py]
    end
    subgraph Core
        G[integration_manager.py]
        B[database_unified.py]
        F[config.py]
    end

    M --> G
    V --> G
    E --> G
    X --> G

    G --> P
    G --> N
    N --> C
    N --> I
    P --> J

    G --> S
    G --> SE
    G --> H

    G --> R
    G --> U
    G --> T
    G --> D
    G --> A

    G --> B
    B --> F
```

## 8. Deployment Diagram
```mermaid
graph TD
    User((User)) -->|Qt Desktop| App[Research Paper Browser]
    App --> DB[(SQLite File data/database.db)]
    App --> HF[Hugging Face Hub]
    App --> CR[Crossref API]
    App --> DOAJ[DOAJ/ISSN]
    App -.-> Proxy[HTTP/HTTPS Proxy (optional)]
```

## 9. State Machine (Paper Lifecycle)
```mermaid
stateDiagram-v2
    [*] --> Imported
    Imported --> Extracted: PDF parsed
    Extracted --> Enriched: DOI/ISSN/Indexing fetched
    Enriched --> Classified: ML classification
    Classified --> Verified: User verification
    Verified --> Stored: Persisted with embeddings
    Stored --> Indexed: Embeddings generated
    Indexed --> [*]

    Enriched --> NeedsReview: validation conflicts
    NeedsReview --> Verified: user resolves
```

## 11. Performance & Scalability Notes
- Batch embedding generation recommended after imports
- Keep working set within memory by clearing cache when not needed
- Apply filters to reduce candidate sets before ranking
- Repository abstraction eases migration to larger backends if required

## 12. Security & Privacy
- Local-only processing by default; network use limited to metadata APIs and model downloads
- No telemetry; in-memory caches cleared on exit

## 13. Responsibilities & Ownership
- UI flows and interactions: GUI layer
- Coordination and business logic: Integration Manager
- Persistence and schema evolution: Database Unified
- ML/Search: Utilities under `app/utils/`

## 10. Additional System Architecture Diagram (Ingestion and Indexing Pipeline)
```mermaid
flowchart TD
    %% Inputs
    U([User]) -->|Select PDFs| IMP[Import Manager]
    FS[(File System)] --> IMP

    %% Extraction
    IMP --> PEX[Enhanced PDF Extractor]
    PEX --> TXT[Full Text]
    PEX --> META[Raw Metadata]

    %% Validation & Enrichment
    META --> ENR[Metadata Enricher]
    ENR --> CR[(Crossref)]
    ENR --> ISS[(DOAJ/ISSN)]
    ENR --> GSV[(Google Scholar)]
    CR --> ENR
    ISS --> ENR
    GSV --> ENR

    %% Classification & Dedup
    ENR --> CLS[Classifiers]
    TXT --> CLS
    ENR --> DED[Duplicate Detector]
    TXT --> DED

    %% Repository
    CLS --> REP[Unified Repository]
    DED --> REP
    TXT --> REP

    %% Embedding Generation
    REP -->|Batch| EMBG[Embedding Generator]
    EMBG --> EC[(Embedding Cache)]

    %% Indexing
    REP --> IDX[TF-IDF Index Builder]
    IDX --> IC[(Index Cache)]

    %% Search readiness
    EC --> READY[(Semantic Ready)]
    IC --> READY

    %% Styling
    classDef ext fill:#e0f7fa,stroke:#006064
    class CR,ISS,GSV ext
    classDef data fill:#f1f8e9,stroke:#33691e
    class TXT,META,EC,IC data
```
