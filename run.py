"""
AgriVersion - Application Launcher
Run this script to start the AgriVersion web server.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
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

app = create_app(Config)

if __name__ == "__main__":
    print("=" * 70)
    print("🌾 AgriVersion - AI-Powered Multilingual Rice Leaf Disease Detection")
    print(f"🚀 Server running on http://127.0.0.1:{Config.PORT}")
    print("👤 Admin Login:   admin@agriversion.com   / Admin@123")
    print("👨‍🌾 Farmer Login:  farmer@agriversion.com  / Farmer@123")
    print("=" * 70)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
