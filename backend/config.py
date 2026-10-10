"""
NextHire - Configuration Module
Manages application configuration, database settings, and file paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "nexthire_dev_secret_key_2026_mca")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # MySQL Configuration
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "nexthire_db")

    # File Uploads
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}

    # Frontend Directories
    FRONTEND_DIR = BASE_DIR / "frontend"

    @classmethod
    def init_app(cls):
        """Ensure critical folders exist."""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
