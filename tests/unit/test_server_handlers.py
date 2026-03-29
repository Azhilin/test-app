"""Unit-style tests for internal app.server handler branches."""

from __future__ import annotations

import importlib
import io
import json
import sys
import urllib.error
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
    schemas_dir = tmp_path / "docs" / "product" / "schemas"
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


def test_post_schema_requires_saved_jira_credentials(monkeypatch, tmp_path):
    (_, handler) = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Team Schema", "projects": "TEAM"},
    )

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 400
    assert "Jira credentials not found in .env" in data["error"]


def test_post_schema_fetches_and_saves_schema(monkeypatch, tmp_path):
    (_, handler) = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Team Schema", "projects": "TEAM, CORE", "filter_id": "42"},
    )
    (tmp_path / ".env").write_text(
        "JIRA_URL=https://example.atlassian.net\nJIRA_EMAIL=user@example.com\nJIRA_API_TOKEN=secret-token\n",
        encoding="utf-8",
    )

    def _fake_jira_get(endpoint: str, url: str, email: str, token: str):
        assert url == "https://example.atlassian.net"
        assert email == "user@example.com"
        assert token == "secret-token"
        if endpoint == "/rest/api/2/field":
            return [
                {"id": "summary", "name": "Summary", "custom": False, "schema": {"type": "string"}},
                {
                    "id": "customfield_10016",
                    "name": "Story Points",
                    "custom": True,
                    "schema": {"type": "number", "custom": "com.atlassian.jira.plugin", "system": ""},
                },
            ]
        if endpoint.startswith("/rest/api/2/search?"):
            return {
                "issues": [
                    {
                        "key": "TEAM-123",
                        "fields": {
                            "summary": "Latest issue",
                            "customfield_10016": 5,
                            "description": None,
                        },
                    }
                ]
            }
        if endpoint == "/rest/api/2/filter/42":
            return {"jql": "project in (TEAM, CORE)"}
        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    monkeypatch.setattr(handler, "_jira_api_get", _fake_jira_get)

    handler._handle_post_schema()
    status, data = _json_response(handler)

    saved_path = tmp_path / "docs" / "product" / "schemas" / "team_schema.json"
    saved_data = json.loads(saved_path.read_text(encoding="utf-8"))

    assert status == 200
    assert data["ok"] is True
    assert data["updated"] is False
    assert data["filename"] == "team_schema.json"
    assert data["field_count"] == 2
    assert data["custom_count"] == 1
    assert saved_data["projects"] == ["TEAM", "CORE"]
    assert saved_data["filter_id"] == "42"
    assert saved_data["filter_jql"] == "project in (TEAM, CORE)"
    assert saved_data["sample_issue_key"] == "TEAM-123"
    assert saved_data["populated_fields"] == ["summary", "customfield_10016"]


def test_post_schema_returns_jira_error_when_fields_request_fails(monkeypatch, tmp_path):
    (_, handler) = _make_handler(
        monkeypatch,
        tmp_path,
        body={"name": "Team Schema", "projects": "TEAM"},
    )
    (tmp_path / ".env").write_text(
        "JIRA_URL=https://example.atlassian.net\nJIRA_EMAIL=user@example.com\nJIRA_API_TOKEN=secret-token\n",
        encoding="utf-8",
    )

    http_error = urllib.error.HTTPError(
        url="https://example.atlassian.net/rest/api/2/field",
        code=500,
        msg="Server Error",
        hdrs=None,
        fp=None,
    )
    monkeypatch.setattr(handler, "_jira_api_get", lambda *args: (_ for _ in ()).throw(http_error))

    handler._handle_post_schema()
    status, data = _json_response(handler)

    assert status == 200
    assert data["ok"] is False
    assert "HTTP 500 Server Error" in data["error"]


def test_delete_schema_removes_existing_file(monkeypatch, tmp_path):
    (_, handler) = _make_handler(monkeypatch, tmp_path)
    schemas_dir = tmp_path / "docs" / "product" / "schemas"
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
