"""End-to-end tests: exercise via subprocess, no mocking."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import urllib.request

import pytest

pytestmark = pytest.mark.e2e

PYTHON = sys.executable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
    """Start server.py subprocess on a random port, GET / → 200, then kill."""
    port = 18765  # unlikely to be in use
    proc = subprocess.Popen(
        [PYTHON, os.path.join(PROJECT_ROOT, "server.py"), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJECT_ROOT,
    )
    try:
        # Give server time to start
        time.sleep(2)
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5)
        assert resp.status == 200
    finally:
        proc.terminate()
        proc.wait(timeout=5)
