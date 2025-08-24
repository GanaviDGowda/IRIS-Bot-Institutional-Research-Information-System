from pathlib import Path
import os


APP_NAME = "Research Paper Browser"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PAPERS_DIR = DATA_DIR / "papers"
SQLITE_DB_PATH = DATA_DIR / "database.db"

# Select database backend: "sqlite" or "postgres"
DB_BACKEND = os.environ.get("APP_DB_BACKEND", "postgres").lower()

# PostgreSQL connection settings
# TODO: Replace YOUR_ACTUAL_PASSWORD with your real PostgreSQL password
POSTGRES_DSN = os.environ.get(
    "APP_POSTGRES_DSN",
    "dbname=research user=postgres password=Ganu@2004 host=localhost port=5432",
)

# UI
DEFAULT_WINDOW_SIZE = "1100x720"

# Search
SEARCH_TOP_K = 50
MIN_SIMILARITY_THRESHOLD = 0.01  # Minimum similarity score to show results

# Performance settings for large collections
MAX_FEATURES = 10000  # Limit TF-IDF features for memory efficiency
CHUNK_SIZE = 100  # Process papers in chunks for large collections
ENABLE_CACHING = True  # Cache search results for better performance
BATCH_INDEXING = True  # Rebuild index in batches instead of after each import


def ensure_directories_exist() -> None:
	DATA_DIR.mkdir(parents=True, exist_ok=True)
	PAPERS_DIR.mkdir(parents=True, exist_ok=True) 