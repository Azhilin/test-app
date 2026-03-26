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
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8080))

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


_CLIENT_DISCONNECT = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)


class Server(HTTPServer):
    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], _CLIENT_DISCONNECT):
            return
        super().handle_error(request, client_address)


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
        try:
            self.wfile.write(data)
        except _CLIENT_DISCONNECT:
            pass

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
            self._serve_file(ROOT / "ui" / "index.html")
        elif path == "/api/generate":
            self._handle_generate()
        elif path == "/api/config":
            self._handle_get_config()
        elif path.startswith("/generated/reports/"):
            rel = path.lstrip("/")
            self._serve_file(ROOT / rel)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/test-connection":
            self._handle_test_connection()
        elif path == "/api/config":
            self._handle_post_config()
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

    def _handle_get_config(self) -> None:
        """Return current .env values; JIRA_API_TOKEN is masked as '***'."""
        env_path = ROOT / ".env"
        config: dict[str, str] = {}
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    continue
                key, _, val = stripped.partition("=")
                config[key.strip()] = val.strip()

        keys = [
            "JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN",
            "JIRA_BOARD_ID", "JIRA_SPRINT_COUNT", "JIRA_STORY_POINTS_FIELD",
            "JIRA_FILTER_ID", "JIRA_PROJECT", "JIRA_TEAM_ID",
            "JIRA_ISSUE_TYPES", "JIRA_FILTER_STATUS",
            "JIRA_CLOSED_SPRINTS_ONLY", "JIRA_FILTER_PAGE_SIZE",
        ]
        out: dict[str, str] = {}
        for k in keys:
            v = config.get(k, "")
            if k == "JIRA_API_TOKEN" and v:
                out[k] = "***"
            elif v:
                out[k] = v

        configured = bool(out.get("JIRA_URL") and out.get("JIRA_EMAIL") and out.get("JIRA_API_TOKEN"))
        self._send_json(200, {"config": out, "configured": configured})

    def _handle_post_config(self) -> None:
        """Write JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN to .env on disk."""
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        updates: dict[str, str] = {}
        for key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
            val = (body.get(key) or "").strip()
            if val and val != "***":
                updates[key] = val

        try:
            self._write_env_fields(updates)
            self._send_json(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _write_env_fields(self, updates: dict[str, str]) -> None:
        """Update or add key=value pairs in .env, creating from .env.example if absent."""
        env_path     = ROOT / ".env"
        example_path = ROOT / ".env.example"

        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        elif example_path.exists():
            lines = example_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = []

        written = set()
        new_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            # Check if this line (possibly commented) sets one of our keys
            check = stripped.lstrip("# ")
            matched_key = None
            for key in updates:
                if check.startswith(key + "=") or check == key:
                    matched_key = key
                    break
            if matched_key and matched_key not in written:
                new_lines.append(f"{matched_key}={updates[matched_key]}")
                written.add(matched_key)
            else:
                new_lines.append(line)

        # Append any keys that were not found in the existing file
        for key, val in updates.items():
            if key not in written:
                new_lines.append(f"{key}={val}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

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
    server = Server(("", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"  AI Adoption Metrics — dev server")
    print(f"  Listening on {url}")
    print(f"  Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
