"""End-to-end tests: exercise via subprocess, no mocking."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

PYTHON = sys.executable
# __file__ is tests/e2e/test_e2e.py → parents[2] is the project root
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])


def test_cli_clean_via_subprocess(tmp_path):
    """python main.py --clean → exit 0."""
    result = subprocess.run(
        [PYTHON, os.path.join(PROJECT_ROOT, "main.py"), "--clean"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=30,
    )
    assert result.returncode == 0


def test_cli_no_credentials_via_subprocess():
    """python main.py with empty env → exit 1, stderr contains error."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("JIRA_")}
    # Ensure required vars are empty
    env["JIRA_URL"] = ""
    env["JIRA_EMAIL"] = ""
    env["JIRA_API_TOKEN"] = ""

    result = subprocess.run(
        [PYTHON, os.path.join(PROJECT_ROOT, "main.py")],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=30,
    )
    assert result.returncode == 1
    assert "Config error" in result.stderr or "JIRA_URL" in result.stderr


def test_server_health_check():
    """Start server.py subprocess on an OS-assigned port, poll until ready, GET / → 200."""
    # Let the OS assign a free ephemeral port before starting the subprocess.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        [PYTHON, os.path.join(PROJECT_ROOT, "server.py"), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT,
    )
    try:
        # Poll until server is ready (up to 15 s) instead of sleeping a fixed amount.
        deadline = time.monotonic() + 15
        resp = None
        while time.monotonic() < deadline:
            try:
                resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.25)
        assert resp is not None and resp.status == 200, "Server did not become ready"
    finally:
        proc.terminate()
        proc.wait(timeout=5)
