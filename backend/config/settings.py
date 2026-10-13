import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT = BACKEND_DIR.parent
FRONTEND_DIR = ROOT / "frontend"

# Lets the backend import the ml/, dl/ and database/ folders that sit beside it.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class Config:
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "1") == "1"
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB uploads

    # "sqlite" (default, zero setup) or "mysql"
    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
    SQLITE_PATH = os.getenv("SQLITE_PATH", str(BACKEND_DIR / "smartpack.db"))
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "smartpack")
