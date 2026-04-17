"""Unit-style tests for internal app.server handler branches."""

from __future__ import annotations

import importlib
import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


def _import_app_server_safe():
    """Import app.server without letting its module-level argv parsing explode."""
    orig_argv = sys.argv
    sys.argv = ["server.py"]
    sys.modules.pop("app.server", None)
    try:
        import app.server as srv

        importlib.reload(srv)
    finally:
        sys.argv = orig_argv
    return srv


def _make_handler(monkeypatch, tmp_path: Path, body: dict | None = None, raw: bytes | None = None):
    srv = _import_app_server_safe()
    monkeypatch.setattr(srv, "ROOT", tmp_path)

    payload = raw if raw is not None else json.dumps(body or {}).encode()
    handler = object.__new__(srv.Handler)
    handler.headers = {"Content-Length": str(len(payload))}
    handler.rfile = io.BytesIO(payload)
    handler.wfile = io.BytesIO()
    handler._status = None
    handler._sent_headers = []

    def _send_response(status: int):
        handler._status = status

    def _send_header(name: str, value: str):
        handler._sent_headers.append((name, value))

    handler.send_response = _send_response
    handler.send_header = _send_header
    handler.end_headers = lambda: None
    return srv, handler


def _json_response(handler) -> tuple[int, dict]:
    return handler._status, json.loads(handler.wfile.getvalue().decode())


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("  Team Schema v2  ", "team_schema_v2"),
        ("!!!", "schema"),
    ],
)
def test_slugify_returns_safe_filename(monkeypatch, tmp_path, name, expected):
    srv, _ = _make_handler(monkeypatch, tmp_path)
    assert srv.Handler._slugify(name) == expected


def test_read_env_credentials_reads_values_from_env_file(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)
    (tmp_path / ".env").write_text(
        "JIRA_URL=https://example.atlassian.net/\nJIRA_EMAIL=user@example.com\nJIRA_API_TOKEN=secret-token\n",
        encoding="utf-8",
    )

    assert handler._read_env_credentials() == (
        "https://example.atlassian.net",
        "user@example.com",
        "secret-token",
    )


def test_get_schema_detail_returns_saved_schema_json(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)
    schemas_dir = tmp_path / "generated" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "team_schema.json").write_text(
        json.dumps({"name": "Team Schema", "projects": ["TEAM"]}),
        encoding="utf-8",
    )

    handler._handle_get_schema_detail("team_schema.json")
    status, data = _json_response(handler)

    assert status == 200
    assert data["name"] == "Team Schema"
    assert data["projects"] == ["TEAM"]


def test_get_schema_detail_rejects_path_traversal(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)

    handler._handle_get_schema_detail("../secret.json")
    status, data = _json_response(handler)

    assert status == 400
    assert data["error"] == "Invalid filename"


def test_resolve_report_path_allows_files_under_reports(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)
    target = tmp_path / "generated" / "reports" / "run-1" / "report.html"
    target.parent.mkdir(parents=True)
    target.write_text("<html></html>", encoding="utf-8")

    resolved = handler._resolve_report_path("/generated/reports/run-1/report.html")

    assert resolved == target.resolve()


def test_resolve_report_path_rejects_path_traversal(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)
    (tmp_path / ".env").write_text("secret", encoding="utf-8")

    resolved = handler._resolve_report_path("/generated/reports/../../.env")

    assert resolved is None


def _isolate_schema_file(monkeypatch, tmp_path: Path) -> Path:
    """Redirect schema_mod.SCHEMA_PATH to a seeded temp file and return the path."""
    from app.core import schema as schema_mod

    tmp_file = tmp_path / "jira_schema.json"
    tmp_file.write_text(json.dumps({"schemas": []}) + "\n", encoding="utf-8")
    monkeypatch.setattr(schema_mod, "SCHEMA_PATH", tmp_file)
    return tmp_file


def test_post_schema_requires_schema_key(monkeypatch, tmp_path):
    """POST body without top-level 'schema' returns 400."""
    _isolate_schema_file(monkeypatch, tmp_path)
    (_, handler) = _make_handler(monkeypatch, tmp_path, body={"not_schema": {}})

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 400
    assert data["ok"] is False
    assert "schema" in data["error"].lower()


def test_post_schema_requires_schema_name(monkeypatch, tmp_path):
    """POST with empty schema dict returns 400 about schema_name."""
    _isolate_schema_file(monkeypatch, tmp_path)
    (_, handler) = _make_handler(monkeypatch, tmp_path, body={"schema": {}})

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 400
    assert "schema_name" in data["error"]


def test_post_schema_requires_dict_fields(monkeypatch, tmp_path):
    """POST with fields not being an object returns 400."""
    _isolate_schema_file(monkeypatch, tmp_path)
    (_, handler) = _make_handler(
        monkeypatch,
        tmp_path,
        body={
            "schema": {
                "schema_name": "Test",
                "fields": "oops",
                "status_mapping": {"done_statuses": [], "in_progress_statuses": []},
            },
        },
    )

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 400
    assert "fields" in data["error"]


def test_post_schema_requires_status_mapping_lists(monkeypatch, tmp_path):
    """POST with missing in_progress_statuses returns 400."""
    _isolate_schema_file(monkeypatch, tmp_path)
    (_, handler) = _make_handler(
        monkeypatch,
        tmp_path,
        body={
            "schema": {
                "schema_name": "Test",
                "fields": {},
                "status_mapping": {"done_statuses": []},
            },
        },
    )

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 400
    assert "status_mapping" in data["error"]


def test_post_schema_inserts_new_entry(monkeypatch, tmp_path):
    """POST with a fresh schema_name saves and returns updated:false."""
    schema_file = _isolate_schema_file(monkeypatch, tmp_path)
    (_, handler) = _make_handler(
        monkeypatch,
        tmp_path,
        body={
            "schema": {
                "schema_name": "Inserted",
                "fields": {"labels": {"id": "labels", "type": "array"}},
                "status_mapping": {"done_statuses": ["Done"], "in_progress_statuses": ["In Progress"]},
            },
        },
    )

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is True
    assert data["updated"] is False
    assert data["schema"]["schema_name"] == "Inserted"

    persisted = json.loads(schema_file.read_text(encoding="utf-8"))
    assert any(s["schema_name"] == "Inserted" for s in persisted["schemas"])


def test_post_schema_updates_existing_entry(monkeypatch, tmp_path):
    """Second POST for the same name returns updated:true."""
    schema_file = _isolate_schema_file(monkeypatch, tmp_path)
    seed_body = {
        "schema": {
            "schema_name": "Upsert",
            "fields": {"labels": {"id": "labels", "type": "array"}},
            "status_mapping": {"done_statuses": ["Done"], "in_progress_statuses": ["In Progress"]},
        },
    }
    (_, h1) = _make_handler(monkeypatch, tmp_path, body=seed_body)
    h1._handle_post_schema()

    update_body = json.loads(json.dumps(seed_body))
    update_body["schema"]["description"] = "changed"
    (_, h2) = _make_handler(monkeypatch, tmp_path, body=update_body)
    h2._handle_post_schema()
    status, data = _json_response(h2)

    assert status == 200
    assert data["updated"] is True
    persisted = json.loads(schema_file.read_text(encoding="utf-8"))
    matches = [s for s in persisted["schemas"] if s["schema_name"] == "Upsert"]
    assert len(matches) == 1
    assert matches[0]["description"] == "changed"


def test_delete_schema_removes_existing_file(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)
    schemas_dir = tmp_path / "generated" / "schemas"
    schemas_dir.mkdir(parents=True)
    target = schemas_dir / "team_schema.json"
    target.write_text("{}", encoding="utf-8")

    handler._handle_delete_schema("team_schema.json")
    status, data = _json_response(handler)

    assert status == 200
    assert data == {"ok": True}
    assert not target.exists()


def test_delete_schema_rejects_invalid_filename(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)

    handler._handle_delete_schema("../team_schema.json")
    status, data = _json_response(handler)

    assert status == 400
    assert data["error"] == "Invalid filename"


def test_delete_schema_returns_404_when_missing(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)

    handler._handle_delete_schema("missing.json")
    status, data = _json_response(handler)

    assert status == 404
    assert data["error"] == "Schema not found"


def test_handle_generate_emits_error_event_for_nonzero_exit(monkeypatch, tmp_path):
    srv, handler = _make_handler(monkeypatch, tmp_path)
    handler.path = "/api/generate"

    class _FakeProc:
        def __init__(self):
            self.stdout = iter(["Starting\n", "Still running\n"])
            self.returncode = 2

        def wait(self):
            return None

    monkeypatch.setattr(srv.subprocess, "Popen", lambda *args, **kwargs: _FakeProc())

    handler._handle_generate()
    output = handler.wfile.getvalue().decode()

    assert handler._status == 200
    assert ("Content-Type", "text/event-stream; charset=utf-8") in handler._sent_headers
    assert "data: Starting" in output
    assert "event: error" in output
    assert "Process exited with code 2" in output
    assert "event: close" in output


def test_handle_generate_emits_error_when_main_file_missing(monkeypatch, tmp_path):
    srv, handler = _make_handler(monkeypatch, tmp_path)
    handler.path = "/api/generate"
    monkeypatch.setattr(srv.subprocess, "Popen", lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()))

    handler._handle_generate()
    output = handler.wfile.getvalue().decode()

    assert handler._status == 200
    assert "event: error" in output
    assert "main.py not found" in output
    assert "event: close" in output


def _make_filter_handler(monkeypatch, tmp_path, body: dict):
    """Helper: handler with a seeded filters file and isolated _load_filters/_save_filters."""
    from app.server import filter_handlers as fh_mod

    filters_path = tmp_path / "config" / "jira_filters.json"
    filters_path.parent.mkdir(parents=True, exist_ok=True)
    filters_path.write_text(json.dumps([fh_mod.FilterHandlerMixin._DEFAULT_FILTER]), encoding="utf-8")

    srv, handler = _make_handler(monkeypatch, tmp_path, body=body)
    monkeypatch.setattr(type(handler), "_filters_config_path", staticmethod(lambda: filters_path))
    return srv, handler, filters_path


def test_post_filter_saves_report_name(monkeypatch, tmp_path):
    """POST /api/filters with report_name stores it; GET returns the same value."""
    _, handler, filters_path = _make_filter_handler(
        monkeypatch,
        tmp_path,
        body={"name": "My Report Filter", "report_name": "Q2 AI Adoption", "params": {"JIRA_PROJECT": "PROJ"}},
    )

    handler._handle_post_filter()
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is True

    persisted = json.loads(filters_path.read_text(encoding="utf-8"))
    entry = next((f for f in persisted if f.get("filter_name") == "My Report Filter"), None)
    assert entry is not None
    assert entry["report_name"] == "Q2 AI Adoption"


def test_post_filter_report_name_defaults_to_filter_name(monkeypatch, tmp_path):
    """When report_name is omitted from POST body, it defaults to the filter name."""
    _, handler, filters_path = _make_filter_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Fallback Filter", "params": {"JIRA_PROJECT": "PROJ"}},
    )

    handler._handle_post_filter()
    _, data = _json_response(handler)
    assert data["ok"] is True

    persisted = json.loads(filters_path.read_text(encoding="utf-8"))
    entry = next((f for f in persisted if f.get("filter_name") == "Fallback Filter"), None)
    assert entry is not None
    assert entry["report_name"] == "Fallback Filter"


def test_generate_exports_filter_schema_name_to_subprocess(monkeypatch, tmp_path):
    """JFM-P-011: /api/generate?filter=<slug> exports filter.params.schema_name as JIRA_SCHEMA_NAME.

    The filter's schema_name must win over defaults.env values and be visible to main.py.
    """
    srv, handler = _make_handler(monkeypatch, tmp_path)
    handler.path = "/api/generate?filter=team_alpha"

    # Seed the project root with a filters file and a defaults.env carrying a different schema.
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "defaults.env").write_text("JIRA_SCHEMA_NAME=FromDefaults\n", encoding="utf-8")
    (tmp_path / "config" / "jira_filters.json").write_text(
        json.dumps(
            [
                {
                    "filter_name": "Team Alpha",
                    "slug": "team_alpha",
                    "is_default": False,
                    "jql": "",
                    "params": {
                        "JIRA_PROJECT": "ALPHA",
                        "schema_name": "Team_Alpha_Schema",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    captured: dict = {}

    class _FakeProc:
        def __init__(self):
            self.stdout = iter([])
            self.returncode = 0

        def wait(self):
            return None

    def _fake_popen(*args, **kwargs):
        captured["env"] = kwargs.get("env") or {}
        return _FakeProc()

    monkeypatch.setattr(srv.subprocess, "Popen", _fake_popen)

    handler._handle_generate()

    env = captured.get("env") or {}
    assert env.get("JIRA_SCHEMA_NAME") == "Team_Alpha_Schema", (
        f"Expected filter's schema_name to win; got {env.get('JIRA_SCHEMA_NAME')!r}"
    )
    assert env.get("JIRA_PROJECT") == "ALPHA"


def test_generate_exports_report_name_to_subprocess(monkeypatch, tmp_path):
    """report_name query param is forwarded as REPORT_NAME env var to main.py."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    handler.path = "/api/generate?filter=team_alpha&report_name=My+Custom+Report"

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "defaults.env").write_text("", encoding="utf-8")
    (tmp_path / "config" / "jira_filters.json").write_text(
        json.dumps(
            [
                {
                    "filter_name": "Team Alpha",
                    "slug": "team_alpha",
                    "is_default": False,
                    "jql": "",
                    "report_name": "Team Alpha",
                    "params": {"JIRA_PROJECT": "ALPHA", "schema_name": "S"},
                }
            ]
        ),
        encoding="utf-8",
    )

    captured: dict = {}

    class _FakeProc:
        def __init__(self):
            self.stdout = iter([])
            self.returncode = 0

        def wait(self):
            return None

    def _fake_popen(*args, **kwargs):
        captured["env"] = kwargs.get("env") or {}
        return _FakeProc()

    monkeypatch.setattr(srv.subprocess, "Popen", _fake_popen)

    handler._handle_generate()

    env = captured.get("env") or {}
    assert env.get("REPORT_NAME") == "My Custom Report"


def test_generate_uses_stored_report_name_when_no_param(monkeypatch, tmp_path):
    """When no report_name query param is given, the filter's stored report_name is used."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    handler.path = "/api/generate?filter=team_alpha"

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "defaults.env").write_text("", encoding="utf-8")
    (tmp_path / "config" / "jira_filters.json").write_text(
        json.dumps(
            [
                {
                    "filter_name": "Team Alpha",
                    "slug": "team_alpha",
                    "is_default": False,
                    "jql": "",
                    "report_name": "Stored Report Name",
                    "params": {"JIRA_PROJECT": "ALPHA", "schema_name": "S"},
                }
            ]
        ),
        encoding="utf-8",
    )

    captured: dict = {}

    class _FakeProc:
        def __init__(self):
            self.stdout = iter([])
            self.returncode = 0

        def wait(self):
            return None

    def _fake_popen(*args, **kwargs):
        captured["env"] = kwargs.get("env") or {}
        return _FakeProc()

    monkeypatch.setattr(srv.subprocess, "Popen", _fake_popen)

    handler._handle_generate()

    env = captured.get("env") or {}
    assert env.get("REPORT_NAME") == "Stored Report Name"


def test_handle_test_connection_returns_user_details_on_success(monkeypatch, tmp_path):
    srv, handler = _make_handler(
        monkeypatch,
        tmp_path,
        body={
            "url": "https://example.atlassian.net",
            "email": "user@example.com",
            "token": "secret-token",
        },
    )
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {"displayName": "Test User", "emailAddress": "user@example.com"}
    ).encode()
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False
    monkeypatch.setattr(srv.urllib.request, "urlopen", lambda *args, **kwargs: mock_response)

    handler._handle_test_connection()
    status, data = _json_response(handler)

    assert status == 200
    assert data == {
        "ok": True,
        "displayName": "Test User",
        "emailAddress": "user@example.com",
    }


def test_handle_test_connection_uses_custom_ssl_context(monkeypatch, tmp_path):
    srv, handler = _make_handler(
        monkeypatch,
        tmp_path,
        body={
            "url": "https://example.atlassian.net",
            "email": "user@example.com",
            "token": "secret-token",
        },
    )
    create_calls: list[tuple] = []
    load_verify_calls: list[str] = []
    urlopen_calls: list[object] = []
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {"displayName": "Test User", "emailAddress": "user@example.com"}
    ).encode()
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    mock_ctx = MagicMock()
    mock_ctx.load_verify_locations = lambda cafile=None: load_verify_calls.append(cafile)

    monkeypatch.setattr(srv.config, "JIRA_SSL_CERT", "/tmp/jira_ca_bundle.pem")
    monkeypatch.setattr(
        srv.ssl, "create_default_context", lambda *args, **kwargs: create_calls.append(kwargs) or mock_ctx
    )
    monkeypatch.setattr(
        srv.urllib.request,
        "urlopen",
        lambda *args, **kwargs: urlopen_calls.append(kwargs["context"]) or mock_response,
    )

    handler._handle_test_connection()

    # create_default_context must be called WITHOUT cafile so system CAs are included
    assert len(create_calls) == 1
    assert "cafile" not in create_calls[0], (
        "_jira_ssl_context() must not pass cafile= to create_default_context(); "
        "system CA store would be bypassed and connections break after cert renewal"
    )
    # The custom cert must be added via load_verify_locations
    assert load_verify_calls == ["/tmp/jira_ca_bundle.pem"]
    assert len(urlopen_calls) == 1


def test_run_defaults_host_to_loopback(monkeypatch):
    monkeypatch.delenv("HOST", raising=False)
    srv = _import_app_server_safe()

    assert srv.HOST == "127.0.0.1"


# ── NFR-R-003: _CLIENT_DISCONNECT covers all disconnect types ───────────


def test_client_disconnect_tuple_includes_all_error_types():
    """_CLIENT_DISCONNECT must catch BrokenPipeError, ConnectionAbortedError, and ConnectionResetError."""
    srv = _import_app_server_safe()
    assert BrokenPipeError in srv._CLIENT_DISCONNECT
    assert ConnectionAbortedError in srv._CLIENT_DISCONNECT
    assert ConnectionResetError in srv._CLIENT_DISCONNECT


@pytest.mark.parametrize("exc_type", [BrokenPipeError, ConnectionAbortedError, ConnectionResetError])
def test_serve_file_catches_client_disconnect(monkeypatch, tmp_path, exc_type):
    """_serve_file must suppress all _CLIENT_DISCONNECT exceptions during write."""
    srv, handler = _make_handler(monkeypatch, tmp_path)
    target = tmp_path / "test.txt"
    target.write_text("hello", encoding="utf-8")

    def _exploding_write(data):
        raise exc_type("client gone")

    handler.wfile.write = _exploding_write
    # Should not raise
    handler._serve_file(target)


# ── _handle_cert_status ──────────────────────────────────────────────────


def test_handle_cert_status_returns_validity_fields_for_valid_cert(monkeypatch, tmp_path):
    """_handle_cert_status returns exists=True plus all validity fields when cert parses OK."""
    srv, handler = _make_handler(monkeypatch, tmp_path)

    certs_dir = tmp_path / "certs"
    certs_dir.mkdir()

    fake_validate_result = {
        "valid": True,
        "expires_at": "2026-12-31",
        "days_remaining": 180,
        "subject": "CN=*.example.com",
    }
    (certs_dir / "jira_ca_bundle.pem").write_bytes(b"placeholder")
    monkeypatch.setattr("app.utils.cert_utils.validate_cert", lambda path: fake_validate_result)

    handler._handle_cert_status()
    status, data = _json_response(handler)

    assert status == 200
    assert data["exists"] is True
    assert data["path"] == "certs/jira_ca_bundle.pem"
    assert data["valid"] is True
    assert data["expires_at"] == "2026-12-31"
    assert data["days_remaining"] == 180
    assert data["subject"] == "CN=*.example.com"
    assert "error" not in data


def test_handle_cert_status_returns_error_key_when_cert_unreadable(monkeypatch, tmp_path):
    """_handle_cert_status returns exists=True plus error key when validate_cert fails."""
    srv, handler = _make_handler(monkeypatch, tmp_path)

    certs_dir = tmp_path / "certs"
    certs_dir.mkdir()
    (certs_dir / "jira_ca_bundle.pem").write_bytes(b"not a valid PEM")

    corrupt_result = {
        "valid": False,
        "expires_at": None,
        "days_remaining": None,
        "subject": None,
        "error": "Unable to load PEM file",
    }
    monkeypatch.setattr("app.utils.cert_utils.validate_cert", lambda path: corrupt_result)

    handler._handle_cert_status()
    status, data = _json_response(handler)

    assert status == 200
    assert data["exists"] is True
    assert data["path"] == "certs/jira_ca_bundle.pem"
    assert data["valid"] is False
    assert data["error"] == "Unable to load PEM file"
