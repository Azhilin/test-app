"""Shared base handler, helpers, routing dispatch, Server class."""

from __future__ import annotations

import base64
import json
import logging
import os
import ssl
import sys
import sys as _sys
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import unquote as urlunquote

from dotenv import dotenv_values

from app.core import config

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
HOST = os.environ.get("HOST", "127.0.0.1").strip() or "127.0.0.1"
try:
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8080))
except (ValueError, TypeError):
    PORT = int(os.environ.get("PORT", 8080))

MIME = {
    "html": "text/html; charset=utf-8",
    "md": "text/markdown; charset=utf-8",
    "css": "text/css",
    "js": "application/javascript",
    "json": "application/json",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "svg": "image/svg+xml",
    "ico": "image/x-icon",
}


def guess_mime(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return MIME.get(ext, "application/octet-stream")


_CLIENT_DISCONNECT = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)


def _root() -> Path:
    """Return project ROOT from app.server, supporting test-time patching via srv.ROOT."""
    _m = _sys.modules.get("app.server")
    return _m.ROOT if _m is not None else ROOT


def _dotenv_values(path: Path) -> dict:
    """Load .env values, supporting test-time patching via srv.dotenv_values."""
    _m = _sys.modules.get("app.server")
    fn = getattr(_m, "dotenv_values", None) if _m is not None else None
    if fn is None:
        fn = dotenv_values
    return fn(path)


class Server(HTTPServer):
    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], _CLIENT_DISCONNECT):
            return
        super().handle_error(request, client_address)


class HandlerBase(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress per-request noise
        pass

    # ── helpers ──────────────────────────────────────────────────────────────

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_response(404)
            self.end_headers()
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", guess_mime(path.name))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except _CLIENT_DISCONNECT:
            # Client disconnected before or during write; no further action needed.
            pass

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")

    @staticmethod
    def _reports_dir() -> Path:
        return (_root() / "generated" / "reports").resolve()

    @staticmethod
    def _sanitise_exc(exc: BaseException, *secrets: str) -> str:
        """Replace known secret values in an exception string before logging."""
        msg = str(exc)
        for s in secrets:
            if s:
                msg = msg.replace(s, "***")
        return msg

    @staticmethod
    def _jira_ssl_context() -> ssl.SSLContext | None:
        if config.JIRA_SSL_CERT is True:
            return None
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(cafile=config.JIRA_SSL_CERT)
        return ctx

    def _resolve_report_path(self, requested_path: str) -> Path | None:
        rel = urlunquote(requested_path[len("/generated/reports/") :]).lstrip("/")
        if not rel:
            return None
        target = (self._reports_dir() / rel).resolve()
        try:
            target.relative_to(self._reports_dir())
        except ValueError:
            return None
        return target

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return None

    def _read_env_credentials(self) -> tuple[str, str, str]:
        values = dotenv_values(_root() / ".env")
        return (
            str(values.get("JIRA_URL", "")).rstrip("/"),
            str(values.get("JIRA_EMAIL", "")),
            str(values.get("JIRA_API_TOKEN", "")),
        )

    def _jira_api_get(self, endpoint: str, url: str, email: str, token: str):
        creds = base64.b64encode(f"{email}:{token}".encode()).decode()
        req = urllib.request.Request(
            f"{url}{endpoint}",
            headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30, context=self._jira_ssl_context()) as resp:
            return json.loads(resp.read())

    # ── routing ──────────────────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _query_params(self) -> dict[str, list[str]]:
        """Parse query string from self.path into a dict."""
        qs = self.path.split("?", 1)[1] if "?" in self.path else ""
        return parse_qs(qs)

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path in ("/", "/index.html"):
            self._serve_file(_root() / "ui" / "index.html")
        elif path == "/api/generate":
            self._handle_generate()
        elif path == "/api/cert-status":
            self._handle_cert_status()
        elif path == "/api/config":
            self._handle_get_config()
        elif path == "/api/schemas":
            self._handle_get_schemas()
        elif path == "/api/reports":
            self._handle_get_reports()
        elif path == "/api/filters":
            self._handle_get_filters()
        elif path.startswith("/api/schema-detail/"):
            filename = path[len("/api/schema-detail/") :]
            self._handle_get_schema_detail(filename)
        elif path.startswith("/generated/reports/"):
            target = self._resolve_report_path(path)
            if target is None:
                self._send_json(404, {"ok": False, "error": "Not found"})
                return
            self._serve_file(target)
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/test-connection":
            self._handle_test_connection()
        elif path == "/api/fetch-cert":
            self._handle_fetch_cert()
        elif path == "/api/config":
            self._handle_post_config()
        elif path == "/api/schemas":
            self._handle_post_schema()
        elif path == "/api/filters":
            self._handle_post_filter()
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})

    def do_DELETE(self) -> None:
        path = self.path.split("?")[0]

        if path.startswith("/api/schemas/"):
            filename = path[len("/api/schemas/") :]
            self._handle_delete_schema(filename)
        elif path == "/api/schemas":
            self._handle_delete_schema()
        elif path.startswith("/api/filters/"):
            slug = urlunquote(path[len("/api/filters/") :])
            self._handle_delete_filter(slug)
        else:
            self._send_json(404, {"ok": False, "error": "Not found"})
