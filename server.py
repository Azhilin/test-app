#!/usr/bin/env python3
"""
Development server for index.html.

Serves the UI and proxies Jira API calls server-side so the browser
never hits Jira directly (avoiding CORS restrictions).

Usage:
    python server.py          # listens on http://localhost:8080
    python server.py 9000     # custom port
"""

import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

MIME = {
    "html": "text/html; charset=utf-8",
    "md":   "text/markdown; charset=utf-8",
    "css":  "text/css",
    "js":   "application/javascript",
    "json": "application/json",
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "svg":  "image/svg+xml",
    "ico":  "image/x-icon",
}


def guess_mime(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return MIME.get(ext, "application/octet-stream")


class Handler(BaseHTTPRequestHandler):
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
        self.wfile.write(data)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return None

    # ── routing ──────────────────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path in ("/", "/index.html"):
            self._serve_file(ROOT / "index.html")
        elif path == "/api/generate":
            self._handle_generate()
        elif path.startswith("/reports/"):
            rel = path.lstrip("/")
            self._serve_file(ROOT / rel)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/test-connection":
            self._handle_test_connection()
        else:
            self.send_response(404)
            self.end_headers()

    # ── handlers ─────────────────────────────────────────────────────────────

    def _handle_test_connection(self) -> None:
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        url   = (body.get("url") or "").strip().rstrip("/")
        email = (body.get("email") or "").strip()
        token = (body.get("token") or "").strip()

        if not url or not email or not token:
            self._send_json(400, {"ok": False, "error": "url, email, and token are required"})
            return

        endpoint = f"{url}/rest/api/3/myself"
        creds    = base64.b64encode(f"{email}:{token}".encode()).decode()

        req = urllib.request.Request(
            endpoint,
            headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                self._send_json(200, {
                    "ok":           True,
                    "displayName":  data.get("displayName", ""),
                    "emailAddress": data.get("emailAddress", ""),
                })
        except urllib.error.HTTPError as exc:
            self._send_json(200, {
                "ok":         False,
                "httpStatus": exc.code,
                "error":      str(exc.reason),
            })
        except urllib.error.URLError as exc:
            self._send_json(200, {
                "ok":    False,
                "error": f"Could not reach Jira: {exc.reason}",
            })
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _handle_generate(self) -> None:
        """Run main.py and stream stdout/stderr as Server-Sent Events."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")  # disable nginx buffering
        self._cors_headers()
        self.end_headers()

        def emit(data: str, event: str = "message") -> None:
            try:
                if event != "message":
                    self.wfile.write(f"event: {event}\n".encode())
                for part in data.splitlines():
                    self.wfile.write(f"data: {part}\n".encode())
                self.wfile.write(b"\n")
                self.wfile.flush()
            except BrokenPipeError:
                pass

        try:
            proc = subprocess.Popen(
                [sys.executable, str(ROOT / "main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(ROOT),
                env={**os.environ},
            )
            for line in proc.stdout:
                emit(line.rstrip())
            proc.wait()

            if proc.returncode == 0:
                emit("__done__", "done")
            else:
                emit(f"__error__:Process exited with code {proc.returncode}", "error")
        except FileNotFoundError:
            emit("__error__:main.py not found — run from the project root", "error")
        except Exception as exc:  # noqa: BLE001
            emit(f"__error__:{exc}", "error")
        finally:
            try:
                self.wfile.write(b"event: close\ndata:\n\n")
                self.wfile.flush()
            except BrokenPipeError:
                pass


if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"  AI Adoption Metrics — dev server")
    print(f"  Listening on {url}")
    print(f"  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
