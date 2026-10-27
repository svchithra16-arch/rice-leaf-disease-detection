"""
Gunicorn Configuration for AgriVersion
Automatically loaded by Gunicorn when starting the web service.
Binds to 0.0.0.0 on the port specified by the PORT environment variable (Render, Heroku, Docker).
"""

import os

# Render and most cloud providers inject the port to listen on via the PORT env var.
# Default to 10000 on Render, or 5000 locally.
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker configuration: free tier containers usually have 1 vCPU / 512MB RAM
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = 2
timeout = 120
keepalive = 5

# Direct all logs to standard output/error so Render live logs capture them
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True

print(f"[AgriVersion Gunicorn] Starting server bound to {bind} with {workers} worker(s)...")
