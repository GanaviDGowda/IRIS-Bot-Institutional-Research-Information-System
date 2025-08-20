from pathlib import Path
import os


APP_NAME = "Research Paper Browser"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PAPERS_DIR = DATA_DIR / "papers"
SQLITE_DB_PATH = DATA_DIR / "database.db"

# Select database backend: "sqlite" or "postgres"
DB_BACKEND = os.environ.get("APP_DB_BACKEND", "postgres").lower()

# PostgreSQL connection settings (env vars preferred)
POSTGRES_DSN = os.environ.get(
	"APP_POSTGRES_DSN",
	"dbname=research user=postgres password=postgres host=localhost port=5432",
)

# UI
DEFAULT_WINDOW_SIZE = "1100x720"

# Search
SEARCH_TOP_K = 50


def ensure_directories_exist() -> None:
	DATA_DIR.mkdir(parents=True, exist_ok=True)
	PAPERS_DIR.mkdir(parents=True, exist_ok=True) 