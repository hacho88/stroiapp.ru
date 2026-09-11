"""
Passenger WSGI entry point for ai.stroiapp.ru (Timeweb shared hosting).

Passenger loads this file and calls `application`. FastAPI is ASGI,
so we wrap it with asgiref's WsgiToAsgi adapter.

Expected directory layout on the server:
  ~/ai.stroiapp.ru/backend/   <- this file lives here
  backend/data/app.db         <- SQLite (created automatically)

 passenger_wsgi.py must be in the site's app root.
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load .env manually (python-dotenv may be absent)
_env_path = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

from app.main import app as fastapi_app  # noqa: E402

try:
    from asgiref.wsgi import WsgiToAsgi
    application = WsgiToAsgi(fastapi_app)
except ImportError:
    # Fallback: bare WSGI bridge (GET/POST JSON only, no websockets)
    def application(environ, start_response):
        from urllib.parse import parse_qs
        import json as _json

        path = environ.get("PATH_INFO", "")
        # Strip /api prefix if Passenger mounts at root
        if path.startswith("/api"):
            environ["PATH_INFO"] = path[4:] or "/"
        from app.main import app  # noqa
        raise RuntimeError("Install asgiref: pip install -r requirements.txt")
