"""
AgriVersion - WSGI Application Entry Point
Supports Render, Heroku, Docker, Gunicorn, and Waitress deployment.
Enables running `gunicorn app:app` directly from root directory.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles if invoked directly
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in Python module path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app import create_app
from backend.config import Config

# WSGI application callable for Gunicorn / Render / Waitress
app = create_app(Config)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", Config.PORT))
    print("=" * 70)
    print("🌾 AgriVersion - AI-Powered Multilingual Rice Leaf Disease Detection")
    print(f"🚀 Server running on http://0.0.0.0:{port}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
