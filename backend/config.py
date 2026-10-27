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

    # XAMPP MySQL Database Configuration (localhost:3306, user: root, password: "", db: rice)
    _default_mysql_uri = "mysql+pymysql://root:@localhost:3306/rice?charset=utf8mb4"
    _db_uri = os.getenv("DATABASE_URI", _default_mysql_uri)
    try:
        import pymysql
        conn = pymysql.connect(host="localhost", user="root", password="", port=3306, connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS rice CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()
        SQLALCHEMY_DATABASE_URI = _db_uri
        print("[AgriVersion] Connected to XAMPP MySQL on localhost:3306 (database: rice)")
    except Exception as _e:
        print(f"[AgriVersion] XAMPP MySQL unavailable ({_e}). Falling back to local SQLite database.")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'agriversion.db')}"

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
