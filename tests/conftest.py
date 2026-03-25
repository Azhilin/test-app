"""Shared fixtures and factories for the test suite."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helper factories (plain functions, not fixtures, so tests can call them freely)
# ---------------------------------------------------------------------------

def make_sprint(id: int, name: str = "", start: str | None = None, end: str | None = None) -> dict:
    return {
        "id": id,
        "name": name or f"Sprint {id}",
        "startDate": start,
        "endDate": end,
    }


def make_issue(
    key: str,
    status: str = "Done",
    points: float | None = 5.0,
    story_points_field: str = "customfield_10016",
) -> dict:
    fields: dict = {
        "status": {"name": status},
    }
    if points is not None:
        fields[story_points_field] = points
    return {"key": key, "fields": fields}


def make_issue_with_changelog(
    key: str,
    in_progress_ts: str | None = None,
    done_ts: str | None = None,
) -> dict:
    """Build an issue dict with a synthetic changelog."""
    histories = []
    if in_progress_ts:
        histories.append({
            "created": in_progress_ts,
            "items": [{"field": "status", "fromString": "To Do", "toString": "In Progress"}],
        })
    if done_ts:
        histories.append({
            "created": done_ts,
            "items": [{"field": "status", "fromString": "In Progress", "toString": "Done"}],
        })
    return {
        "key": key,
        "fields": {"status": {"name": "Done"}},
        "changelog": {"histories": histories},
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_issue_with_labels(
    key: str,
    status: str = "Done",
    points: float | None = 5.0,
    labels: list[str] | None = None,
    story_points_field: str = "customfield_10016",
) -> dict:
    """Build an issue dict with labels for AI metric tests."""
    fields: dict = {
        "status": {"name": status},
        "labels": labels or [],
    }
    if points is not None:
        fields[story_points_field] = points
    return {"key": key, "fields": fields}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_jira():
    """Return a MagicMock with spec=Jira and common stubs."""
    from unittest.mock import MagicMock
    from atlassian import Jira

    jira = MagicMock(spec=Jira)
    jira.get_all_agile_boards.return_value = {"values": [{"id": 1, "name": "Board 1"}]}
    jira.get_all_sprints_from_board.return_value = {"values": []}
    jira.get_all_issues_for_sprint_in_board.return_value = {"issues": [], "total": 0}
    jira.get_filter.return_value = {"jql": "project = TEST"}
    jira.get_issue.return_value = {"key": "TEST-1", "fields": {}, "changelog": {"histories": []}}
    return jira


@pytest.fixture
def server_url():
    """Start a Server on a random port in a daemon thread, yield the base URL, then shut down."""
    import importlib
    import sys

    # server.py parses sys.argv[1] at module level — override before import
    orig_argv = sys.argv
    sys.argv = ["server.py"]
    sys.modules.pop("server", None)
    try:
        import server as srv_mod
        importlib.reload(srv_mod)
    finally:
        sys.argv = orig_argv

    server = srv_mod.Server(("127.0.0.1", 0), srv_mod.Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture
def minimal_metrics_dict() -> dict:
    return {
        "generated_at": "2026-03-25T12:00:00+00:00",
        "velocity": [
            {
                "sprint_id": 1,
                "sprint_name": "Sprint Alpha",
                "start_date": "2026-03-01T00:00:00.000Z",
                "end_date": "2026-03-15T00:00:00.000Z",
                "velocity": 20.0,
                "issue_count": 4,
            }
        ],
        "cycle_time": {
            "mean_days": 3.5,
            "median_days": 3.0,
            "min_days": 1.0,
            "max_days": 6.0,
            "sample_size": 4,
            "values": [1.0, 3.0, 4.0, 6.0],
        },
        "custom_trends": [],
        "ai_assisted_label": "AI_assistance",
        "ai_exclude_labels": [],
        "ai_assistance_trend": [
            {
                "sprint_id": 1,
                "sprint_name": "Sprint Alpha",
                "start_date": "2026-03-01T00:00:00.000Z",
                "end_date": "2026-03-15T00:00:00.000Z",
                "total_sp": 20.0,
                "ai_sp": 10.0,
                "ai_pct": 50.0,
            }
        ],
        "ai_usage_details": {
            "ai_assisted_issue_count": 2,
            "tool_breakdown": [
                {"label": "AI_Tool_Copilot", "count": 2, "pct": 100.0},
            ],
            "action_breakdown": [
                {"label": "AI_Case_CodeGen", "count": 1, "pct": 50.0},
                {"label": "AI_Case_Review", "count": 1, "pct": 50.0},
            ],
        },
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
    }


@pytest.fixture
def empty_metrics_dict() -> dict:
    return {
        "generated_at": "2026-03-25T12:00:00+00:00",
        "velocity": [],
        "cycle_time": {
            "mean_days": None,
            "median_days": None,
            "min_days": None,
            "max_days": None,
            "sample_size": 0,
            "values": [],
        },
        "custom_trends": [],
        "ai_assisted_label": "AI_assistance",
        "ai_exclude_labels": [],
        "ai_assistance_trend": [],
        "ai_usage_details": {
            "ai_assisted_issue_count": 0,
            "tool_breakdown": [],
            "action_breakdown": [],
        },
        "filter_name": None,
        "filter_id": None,
        "filter_jql": None,
        "project_key": None,
    }


@pytest.fixture(scope="session")
def live_server_url():
    """Start server.py in-process on a random port using ThreadingHTTPServer.

    Using a threaded server avoids the single-threaded HTTPServer blocking
    issue where concurrent browser requests (JS fetch to /api/*) stall
    the page load.
    """
    import importlib
    from http.server import HTTPServer
    from socketserver import ThreadingMixIn

    orig_argv = sys.argv
    sys.argv = ["server.py"]
    sys.modules.pop("server", None)
    try:
        import server as srv_mod
        importlib.reload(srv_mod)
    finally:
        sys.argv = orig_argv

    class ThreadedServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

        def handle_error(self, request, client_address):
            exc = sys.exc_info()[1]
            if isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
                return
            super().handle_error(request, client_address)

    server = ThreadedServer(("127.0.0.1", 0), srv_mod.Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Wait for server to be ready
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    else:
        server.shutdown()
        raise RuntimeError(f"Server did not start on port {port}")

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
