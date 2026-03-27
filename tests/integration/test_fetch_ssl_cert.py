"""Tests for tools/fetch_ssl_cert.py — importable function + subprocess smoke."""

from __future__ import annotations

import os
import ssl
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the refactored function
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))
from fetch_ssl_cert import fetch_and_save_cert  # noqa: E402

pytestmark = pytest.mark.integration

FAKE_PEM = "-----BEGIN CERTIFICATE-----\nMIIBfake\n-----END CERTIFICATE-----\n"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_fetch_cert_happy_path(tmp_path):
    with patch("fetch_ssl_cert.ssl.get_server_certificate", return_value=FAKE_PEM):
        result = fetch_and_save_cert("https://example.atlassian.net", root=tmp_path)
    cert = tmp_path / "certs" / "jira_ca_bundle.pem"
    assert cert.exists()
    assert cert.read_text(encoding="ascii") == FAKE_PEM
    assert result == str(cert)


def test_fetch_cert_creates_certs_dir(tmp_path):
    assert not (tmp_path / "certs").exists()
    with patch("fetch_ssl_cert.ssl.get_server_certificate", return_value=FAKE_PEM):
        fetch_and_save_cert("https://example.atlassian.net", root=tmp_path)
    assert (tmp_path / "certs").is_dir()


def test_fetch_cert_overwrites_existing(tmp_path):
    certs_dir = tmp_path / "certs"
    certs_dir.mkdir()
    (certs_dir / "jira_ca_bundle.pem").write_text("OLD CERT", encoding="ascii")
    with patch("fetch_ssl_cert.ssl.get_server_certificate", return_value=FAKE_PEM):
        fetch_and_save_cert("https://example.atlassian.net", root=tmp_path)
    assert (certs_dir / "jira_ca_bundle.pem").read_text(encoding="ascii") == FAKE_PEM


def test_fetch_cert_parses_custom_port(tmp_path):
    with patch("fetch_ssl_cert.ssl.get_server_certificate", return_value=FAKE_PEM) as mock_get:
        fetch_and_save_cert("https://jira.corp.local:8443", root=tmp_path)
    mock_get.assert_called_once_with(("jira.corp.local", 8443))


# ---------------------------------------------------------------------------
# Error paths — SystemExit expected
# ---------------------------------------------------------------------------


def test_fetch_cert_exits_when_url_empty(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        fetch_and_save_cert("", root=tmp_path)
    assert exc_info.value.code == 1


def test_fetch_cert_exits_when_hostname_unparseable(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        fetch_and_save_cert("not-a-url", root=tmp_path)
    assert exc_info.value.code == 1


def test_fetch_cert_exits_on_ssl_error(tmp_path):
    with patch(
        "fetch_ssl_cert.ssl.get_server_certificate",
        side_effect=ssl.SSLError("handshake failure"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            fetch_and_save_cert("https://bad.host.example", root=tmp_path)
    assert exc_info.value.code == 1


def test_fetch_cert_exits_on_os_error(tmp_path):
    with patch(
        "fetch_ssl_cert.ssl.get_server_certificate",
        side_effect=OSError("connection refused"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            fetch_and_save_cert("https://unreachable.example", root=tmp_path)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Subprocess smoke test — runs the script as a CLI tool
# ---------------------------------------------------------------------------


def test_fetch_cert_subprocess_smoke(tmp_path):
    """Run tools/fetch_ssl_cert.py as a subprocess with no JIRA_URL -> should exit 1."""
    script = Path(__file__).resolve().parent.parent.parent / "tools" / "fetch_ssl_cert.py"
    env = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "JIRA_URL": "",  # explicit empty — load_dotenv won't override existing keys
    }
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert result.returncode == 1
    assert "JIRA_URL" in result.stderr
