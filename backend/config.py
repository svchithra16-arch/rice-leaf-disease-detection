"""
AgriVersion - Backend Configuration
Loads settings from environment variables with sensible production defaults.
"""

import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "agriversion_super_secret_key_2026_dev")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))

    # Database with auto-fallback to SQLite if MySQL service is offline
    _db_uri = os.getenv("DATABASE_URI", "")
    if _db_uri and "mysql" in _db_uri:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            err = s.connect_ex(("127.0.0.1", 3306))
            s.close()
            if err == 0:
                SQLALCHEMY_DATABASE_URI = _db_uri
            else:
                print("[AgriVersion] MySQL server offline. Using local SQLite database (agriversion.db).")
                SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'agriversion.db')}"
        except Exception:
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'agriversion.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = _db_uri or f"sqlite:///{os.path.join(BASE_DIR, 'agriversion.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI Model & Multimodal API Keys (Optional)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    DEFAULT_AI_MODEL = os.getenv("DEFAULT_AI_MODEL", "auto")

    # Storage paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads"))
    REPORTS_FOLDER = os.path.join(BASE_DIR, os.getenv("REPORTS_FOLDER", "static_reports"))
    TRANSLATIONS_FOLDER = os.path.join(BASE_DIR, "translations")

    # Security & Upload constraints
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

    # ML Thresholds
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.60))
    BLUR_THRESHOLD = float(os.getenv("BLUR_THRESHOLD", 45.0))


# Ensure directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
