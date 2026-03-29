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
import logging
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote

from dotenv import dotenv_values, load_dotenv

logger = logging.getLogger(__name__)

from app.core import config

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
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

_CONFIG_KEYS = [
    "JIRA_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_BOARD_ID",
    "JIRA_SPRINT_COUNT",
    "JIRA_SCHEMA_NAME",
    "JIRA_FILTER_ID",
    "JIRA_PROJECT",
    "JIRA_TEAM_ID",
    "JIRA_ISSUE_TYPES",
    "JIRA_FILTER_STATUS",
    "JIRA_CLOSED_SPRINTS_ONLY",
    "JIRA_FILTER_PAGE_SIZE",
    "AI_ASSISTED_LABEL",
    "AI_EXCLUDE_LABELS",
    "AI_TOOL_LABELS",
    "AI_ACTION_LABELS",
]


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

    @staticmethod
    def _reports_dir() -> Path:
        return (ROOT / "generated" / "reports").resolve()

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
            self._serve_file(ROOT / "ui" / "index.html")
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
                self.send_response(404)
                self.end_headers()
                return
            self._serve_file(target)
        else:
            self.send_response(404)
            self.end_headers()

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
            self.send_response(404)
            self.end_headers()

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
            self.send_response(404)
            self.end_headers()

    # ── handlers ─────────────────────────────────────────────────────────────

    def _handle_test_connection(self) -> None:
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        url = (body.get("url") or "").strip().rstrip("/")
        email = (body.get("email") or "").strip()
        token = (body.get("token") or "").strip()

        if not url or not email or not token:
            self._send_json(400, {"ok": False, "error": "url, email, and token are required"})
            return

        if token == "***":
            _, _, env_token = self._read_env_credentials()
            if not env_token:
                self._send_json(400, {"ok": False, "error": "No saved token on server"})
                return
            token = env_token

        endpoint = f"{url}/rest/api/3/myself"
        creds = base64.b64encode(f"{email}:{token}".encode()).decode()

        req = urllib.request.Request(
            endpoint,
            headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=12, context=self._jira_ssl_context()) as resp:
                data = json.loads(resp.read())
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "displayName": data.get("displayName", ""),
                        "emailAddress": data.get("emailAddress", ""),
                    },
                )
        except urllib.error.HTTPError as exc:
            self._send_json(
                200,
                {
                    "ok": False,
                    "httpStatus": exc.code,
                    "error": str(exc.reason),
                },
            )
        except urllib.error.URLError as exc:
            self._send_json(
                200,
                {
                    "ok": False,
                    "error": f"Could not reach Jira: {exc.reason}",
                },
            )
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

        out: dict[str, str] = {}
        for k in _CONFIG_KEYS:
            v = config.get(k, "")
            if k == "JIRA_API_TOKEN" and v:
                out[k] = "***"
            elif v:
                out[k] = v

        configured = bool(out.get("JIRA_URL") and out.get("JIRA_EMAIL") and out.get("JIRA_API_TOKEN"))
        self._send_json(200, {"config": out, "configured": configured})

    def _handle_post_config(self) -> None:
        """Write whitelisted config keys to .env on disk."""
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        updates: dict[str, str] = {}
        for key in _CONFIG_KEYS:
            val = (body.get(key) or "").strip()
            if key == "JIRA_API_TOKEN" and val == "***":
                continue
            if val:
                updates[key] = val

        try:
            self._write_env_fields(updates)
            self._send_json(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _write_env_fields(self, updates: dict[str, str]) -> None:
        """Update or add key=value pairs in .env, creating from .env.example if absent."""
        env_path = ROOT / ".env"
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

    def _handle_cert_status(self) -> None:
        """Return whether certs/jira_ca_bundle.pem exists, plus validity metadata."""
        from app.utils.cert_utils import validate_cert

        cert_path = ROOT / "certs" / "jira_ca_bundle.pem"
        if not cert_path.is_file():
            self._send_json(200, {"exists": False, "path": "certs/jira_ca_bundle.pem"})
            return
        info = validate_cert(cert_path)
        self._send_json(
            200,
            {
                "exists": True,
                "path": "certs/jira_ca_bundle.pem",
                "valid": info["valid"],
                "expires_at": info["expires_at"],
                "days_remaining": info["days_remaining"],
                "subject": info["subject"],
                **({"error": info["error"]} if "error" in info else {}),
            },
        )

    def _handle_fetch_cert(self) -> None:
        """Fetch the TLS certificate from the Jira host and save it locally."""
        body = self._read_json_body() or {}
        url = (body.get("url") or os.getenv("JIRA_URL", "")).strip().rstrip("/")

        if not url:
            self._send_json(400, {"ok": False, "error": "url is required"})
            return

        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443

        if not host:
            self._send_json(400, {"ok": False, "error": f"Cannot parse hostname from URL: {url!r}"})
            return

        try:
            pem = ssl.get_server_certificate((host, port))
        except ssl.SSLError as exc:
            self._send_json(200, {"ok": False, "error": f"SSL error from {host}:{port}: {exc}"})
            return
        except OSError as exc:
            self._send_json(200, {"ok": False, "error": f"Could not connect to {host}:{port}: {exc}"})
            return

        certs_dir = ROOT / "certs"
        certs_dir.mkdir(exist_ok=True)
        cert_file = certs_dir / "jira_ca_bundle.pem"
        cert_file.write_bytes(pem.encode("ascii"))

        self._send_json(200, {"ok": True, "path": "certs/jira_ca_bundle.pem", "host": host})

    @staticmethod
    def _schemas_dir() -> Path:
        return ROOT / "docs" / "product" / "schemas"

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower().strip())
        slug = slug.strip("_")[:80]
        return slug or "schema"

    def _read_env_credentials(self) -> tuple[str, str, str]:
        values = dotenv_values(ROOT / ".env")
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

    def _handle_get_schema_detail(self, filename: str) -> None:
        filename = urlunquote(filename)
        if not filename.endswith(".json") or "/" in filename or "\\" in filename:
            self._send_json(400, {"ok": False, "error": "Invalid filename"})
            return
        target = self._schemas_dir() / filename
        if not target.is_file():
            self._send_json(404, {"ok": False, "error": "Schema not found"})
            return
        try:
            self._send_json(200, json.loads(target.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})

    def _handle_get_reports(self) -> None:
        """Return generated report folders, newest-first."""
        reports_dir = self._reports_dir()
        entries: list[dict[str, str]] = []
        if reports_dir.is_dir():
            for folder in sorted(reports_dir.iterdir(), reverse=True):
                if not folder.is_dir():
                    continue
                entries.append({"ts": folder.name, "html": "report.html", "md": "report.md"})
        self._send_json(200, {"reports": entries})

    def _handle_get_schemas(self) -> None:
        """List schema names, or return a single schema when ?name= is provided."""
        from app.core import schema as schema_mod

        params = self._query_params()
        name_list = params.get("name")

        if name_list:
            name = name_list[0]
            schema = schema_mod.get_schema(name)
            if schema is None:
                self._send_json(404, {"ok": False, "error": f"Schema '{name}' not found"})
            else:
                self._send_json(200, {"ok": True, "schema": schema})
        else:
            schemas = schema_mod.load_schemas()
            names = [s.get("schema_name", "") for s in schemas]
            self._send_json(200, {"ok": True, "schemas": names})

    def _handle_post_schema(self) -> None:
        """Auto-fetch Jira fields and create a new schema entry."""
        from app.core import schema as schema_mod

        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        legacy_name = (body.get("name") or "").strip()
        if legacy_name or body.get("projects") is not None or body.get("filter_id") is not None:
            projects = [p.strip() for p in str(body.get("projects") or "").split(",") if p.strip()]
            filter_id = (body.get("filter_id") or "").strip() or None

            if not legacy_name:
                self._send_json(400, {"ok": False, "error": "Schema name is required"})
                return
            if not projects:
                self._send_json(400, {"ok": False, "error": "At least one Project Key is required"})
                return

            url, email, token = self._read_env_credentials()
            if not url or not email or not token:
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": (
                            "Jira credentials not found in .env. Save credentials in the Jira Connection tab first."
                        ),
                    },
                )
                return

            try:
                fields_raw = self._jira_api_get("/rest/api/2/field", url, email, token)
            except urllib.error.HTTPError as exc:
                self._send_json(
                    200,
                    {"ok": False, "error": f"Jira API error fetching fields: HTTP {exc.code} {exc.reason}"},
                )
                return
            except (urllib.error.URLError, OSError) as exc:
                self._send_json(200, {"ok": False, "error": f"Could not reach Jira: {exc}"})
                return

            fields: list[dict] = []
            for field in fields_raw if isinstance(fields_raw, list) else []:
                entry = {
                    "id": field.get("id", ""),
                    "name": field.get("name", ""),
                    "custom": field.get("custom", False),
                }
                if field.get("schema"):
                    entry["schema"] = {
                        "type": field["schema"].get("type", ""),
                        "custom": field["schema"].get("custom", ""),
                        "system": field["schema"].get("system", ""),
                    }
                fields.append(entry)

            sample_issue_key = None
            populated_fields: list[str] = []
            proj_clause = projects[0] if len(projects) == 1 else f"({', '.join(projects)})"
            jql = f"project {'= ' + proj_clause if len(projects) == 1 else 'IN ' + proj_clause} ORDER BY created DESC"
            try:
                search_result = self._jira_api_get(
                    f"/rest/api/2/search?jql={urlquote(jql)}&maxResults=1&fields=*all",
                    url,
                    email,
                    token,
                )
                issues = search_result.get("issues") or []
                if issues:
                    issue = issues[0]
                    sample_issue_key = issue.get("key")
                    issue_fields = issue.get("fields") or {}
                    populated_fields = [k for k, v in issue_fields.items() if v is not None]
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                # Best-effort sampling of a recent issue; failure is non-fatal but logged for debugging.
                logger.warning("Failed to fetch sample Jira issue for schema inference: %s", self._sanitise_exc(exc, url, email, token))

            filter_jql = None
            if filter_id:
                try:
                    filter_data = self._jira_api_get(f"/rest/api/2/filter/{filter_id}", url, email, token)
                    filter_jql = filter_data.get("jql")
                except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                    # Failure to load filter details is non-fatal; continue without filter JQL.
                    logger.warning("Could not fetch Jira filter %s: %s", filter_id, self._sanitise_exc(exc, url, email, token))

            created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
            filename = f"{self._slugify(legacy_name)}.json"
            schemas_dir = self._schemas_dir()
            schemas_dir.mkdir(parents=True, exist_ok=True)
            out_path = schemas_dir / filename
            updated = out_path.exists()
            out_path.write_text(
                json.dumps(
                    {
                        "name": legacy_name,
                        "created_at": created_at,
                        "projects": projects,
                        "filter_id": filter_id,
                        "filter_jql": filter_jql,
                        "fields": fields,
                        "sample_issue_key": sample_issue_key,
                        "populated_fields": populated_fields,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            self._send_json(
                200,
                {
                    "ok": True,
                    "updated": updated,
                    "name": legacy_name,
                    "filename": filename,
                    "created_at": created_at,
                    "field_count": len(fields),
                    "custom_count": sum(1 for field in fields if field.get("custom")),
                },
            )
            return

        schema_name = (body.get("schema_name") or "").strip()
        url = (body.get("jira_url") or "").strip().rstrip("/")
        email = (body.get("jira_email") or "").strip()
        token = (body.get("jira_token") or "").strip()

        if not schema_name:
            self._send_json(400, {"ok": False, "error": "schema_name is required"})
            return
        if not url or not email or not token:
            self._send_json(400, {"ok": False, "error": "jira_url, jira_email, and jira_token are required"})
            return

        try:
            jira_fields = self._jira_api_get("/rest/api/2/field", url, email, token)
        except urllib.error.HTTPError as exc:
            self._send_json(200, {"ok": False, "error": f"Jira returned HTTP {exc.code}: {exc.reason}"})
            return
        except urllib.error.URLError as exc:
            self._send_json(200, {"ok": False, "error": f"Could not reach Jira: {exc.reason}"})
            return
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        if not isinstance(jira_fields, list):
            self._send_json(200, {"ok": False, "error": "Unexpected response from Jira /rest/api/2/field"})
            return

        new_schema = schema_mod.build_schema_from_fields(
            jira_fields,
            schema_name=schema_name,
            jira_url=url,
        )
        schema_mod.save_schema(new_schema)
        self._send_json(200, {"ok": True, "schema": new_schema})

    def _handle_delete_schema(self, filename: str | None = None) -> None:
        """Delete a schema entry by filename or by ?name=."""
        from app.core import schema as schema_mod

        if filename is not None:
            filename = urlunquote(filename)
            if not filename.endswith(".json") or "/" in filename or "\\" in filename:
                self._send_json(400, {"ok": False, "error": "Invalid filename"})
                return
            target = self._schemas_dir() / filename
            if target.is_file():
                target.unlink()
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"ok": False, "error": "Schema not found"})
            return

        params = self._query_params()
        name_list = params.get("name")
        if not name_list:
            self._send_json(400, {"ok": False, "error": "Query parameter 'name' is required"})
            return

        name = name_list[0]
        if name == schema_mod.DEFAULT_SCHEMA_NAME:
            self._send_json(400, {"ok": False, "error": "Cannot delete the default schema"})
            return

        deleted = schema_mod.delete_schema(name)
        if deleted:
            self._send_json(200, {"ok": True})
        else:
            self._send_json(404, {"ok": False, "error": f"Schema '{name}' not found"})

    # ── Filter management ────────────────────────────────────────────────────

    @staticmethod
    def _filters_config_path() -> Path:
        return ROOT / "config" / "jira_filters.json"

    _DEFAULT_FILTER: dict = {
        "filter_name": "Default_Jira_Filter",
        "slug": "default_jira_filter",
        "description": "Default JQL filter template. Set JIRA_PROJECT before saving.",
        "is_default": True,
        "created_at": None,
        "jql": "",
        "params": {
            "JIRA_PROJECT": "",
            "JIRA_TEAM_ID": "",
            "JIRA_ISSUE_TYPES": "",
            "JIRA_FILTER_STATUS": "Done",
            "JIRA_CLOSED_SPRINTS_ONLY": "true",
            "schema_name": "Default_Jira_Cloud",
        },
    }

    def _load_filters(self) -> list[dict]:
        """Read config/jira_filters.json, creating it with the default entry if missing."""
        path = self._filters_config_path()
        if not path.is_file():
            filters = [self._DEFAULT_FILTER.copy()]
            path.write_text(json.dumps(filters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return filters
        try:
            filters = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(filters, list):
                filters = []
        except (OSError, json.JSONDecodeError):
            filters = []
        # Ensure the default entry is always present
        if not any(f.get("is_default") for f in filters):
            filters.insert(0, self._DEFAULT_FILTER.copy())
        return filters

    def _save_filters(self, filters: list[dict]) -> None:
        path = self._filters_config_path()
        path.write_text(json.dumps(filters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @staticmethod
    def _build_jql_from_params(params: dict, team_jql_field: str = "Team[Team]") -> str:
        """Build a JQL query from filter params. Mirrors buildJqlLocally() in ui/index.html."""

        def jql_quote(v: str) -> str:
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                return v
            if any(c in v for c in " (),=<>"):
                return f'"{v}"'
            return v

        raw_project = (params.get("JIRA_PROJECT") or "").strip()
        projects = [p.strip() for p in raw_project.split(",") if p.strip()]
        if not projects:
            return ""

        clauses: list[str] = []
        if len(projects) == 1:
            clauses.append(f"project = {projects[0]}")
        else:
            clauses.append(f"project IN ({', '.join(projects)})")

        raw_team = (params.get("JIRA_TEAM_ID") or "").strip()
        team_ids = [t.strip() for t in raw_team.split(",") if t.strip()]
        if team_ids:
            quoted = [jql_quote(t) for t in team_ids]
            tf = f'"{team_jql_field}"'
            if len(quoted) == 1:
                clauses.append(f"{tf} = {quoted[0]}")
            else:
                clauses.append(f"{tf} IN ({', '.join(quoted)})")

        raw_status = (params.get("JIRA_FILTER_STATUS") or "Done").strip()
        statuses = [s.strip() for s in raw_status.split(",") if s.strip()] or ["Done"]
        quoted_st = [jql_quote(s) for s in statuses]
        if len(quoted_st) == 1:
            clauses.append(f"status = {quoted_st[0]}")
        else:
            clauses.append(f"status IN ({', '.join(quoted_st)})")

        raw_types = (params.get("JIRA_ISSUE_TYPES") or "").strip()
        types = [t.strip() for t in raw_types.split(",") if t.strip()]
        if types:
            clauses.append(f"type IN ({', '.join(jql_quote(t) for t in types)})")

        closed_only = (params.get("JIRA_CLOSED_SPRINTS_ONLY") or "true").strip().lower()
        if closed_only in ("1", "true", "yes", "on"):
            clauses.append("sprint in closedSprints()")

        return " AND ".join(clauses)

    def _handle_get_filters(self) -> None:
        """Return all saved filters from config/jira_filters.json."""
        filters = self._load_filters()
        # Normalise for the UI: default first, then user filters newest-first
        defaults = [f for f in filters if f.get("is_default")]
        user = [f for f in filters if not f.get("is_default")]
        user.sort(key=lambda f: f.get("created_at") or "", reverse=True)
        self._send_json(200, {"ok": True, "filters": defaults + user})

    def _handle_post_filter(self) -> None:
        """Create or update a named filter in config/jira_filters.json."""
        body = self._read_json_body()
        if body is None:
            self._send_json(400, {"ok": False, "error": "Invalid JSON body"})
            return

        name = (body.get("name") or "").strip()
        params = body.get("params") or {}

        if not name:
            self._send_json(400, {"ok": False, "error": "Filter name is required"})
            return
        if not (params.get("JIRA_PROJECT") or "").strip():
            self._send_json(200, {"ok": False, "error": "JIRA_PROJECT is required to build a JQL filter"})
            return

        # Resolve team JQL field name from schema
        team_jql_field = "Team[Team]"
        schema_name = (params.get("schema_name") or "").strip()
        if schema_name:
            try:
                from app.core import schema as schema_mod
                schema = schema_mod.get_schema(schema_name)
                if schema:
                    team_field = (schema.get("fields") or {}).get("team") or {}
                    team_jql_field = team_field.get("jql_name") or team_field.get("id") or team_jql_field
            except Exception:  # noqa: BLE001
                pass

        jql = self._build_jql_from_params(params, team_jql_field)

        slug = self._slugify(name) or "filter"
        created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")

        filters = self._load_filters()
        idx = next((i for i, f in enumerate(filters) if f.get("filter_name", "").lower() == name.lower()), None)
        updated = idx is not None and not filters[idx].get("is_default")

        entry: dict = {
            "filter_name": name,
            "slug": slug,
            "description": "",
            "is_default": False,
            "created_at": created_at,
            "jql": jql,
            "params": params,
        }

        if updated:
            entry["created_at"] = filters[idx].get("created_at") or created_at
            filters[idx] = entry
        else:
            filters.append(entry)

        self._save_filters(filters)
        self._send_json(200, {"ok": True, "updated": updated, "jql": jql, "slug": slug, "created_at": entry["created_at"]})

    def _handle_delete_filter(self, slug: str) -> None:
        """Remove a filter entry by slug. The default filter cannot be deleted."""
        if not slug:
            self._send_json(400, {"ok": False, "error": "Filter slug is required"})
            return

        filters = self._load_filters()
        target = next((f for f in filters if f.get("slug") == slug), None)

        if target is None:
            self._send_json(200, {"ok": False, "error": "Filter not found"})
            return
        if target.get("is_default"):
            self._send_json(200, {"ok": False, "error": "Cannot delete the default filter"})
            return

        self._save_filters([f for f in filters if f.get("slug") != slug])
        self._send_json(200, {"ok": True})

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
                # Client disconnected from the SSE stream; safe to ignore.
                pass

        try:
            fresh_env = {**os.environ, **dotenv_values(ROOT / ".env")}

            # JFM-FUT-001: apply selected filter's params to the subprocess env
            qs = parse_qs(urlparse(self.path).query)
            filter_slug = urlunquote((qs.get("filter") or [""])[0]).strip()
            if filter_slug:
                _FILTER_PARAM_KEYS = [
                    "JIRA_PROJECT",
                    "JIRA_TEAM_ID",
                    "JIRA_ISSUE_TYPES",
                    "JIRA_FILTER_STATUS",
                    "JIRA_CLOSED_SPRINTS_ONLY",
                    "JIRA_FILTER_PAGE_SIZE",
                ]
                for _entry in self._load_filters():
                    if _entry.get("slug") == filter_slug:
                        _params = _entry.get("params") or {}
                        for _key in _FILTER_PARAM_KEYS:
                            _val = (_params.get(_key) or "").strip()
                            if _val:
                                fresh_env[_key] = _val
                        break

            proc = subprocess.Popen(
                [sys.executable, str(ROOT / "main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(ROOT),
                env=fresh_env,
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
                # Client disconnected before the final SSE "close" event could be sent; safe to ignore.
                pass


def run(port: int = PORT, host: str = HOST) -> None:
    """Start the HTTP server on the given port."""
    server = Server((host, port), Handler)
    url = f"http://localhost:{port}" if host in {"127.0.0.1", "localhost"} else f"http://{host}:{port}"
    logger.info("AI Adoption Metrics — dev server")
    logger.info("Listening on %s", url)
    logger.info("Press Ctrl+C to stop.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")


if __name__ == "__main__":
    run()
