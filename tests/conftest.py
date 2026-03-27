"""Shared factories and cross-layer fixtures for the test suite.

Layer-specific fixtures live in each layer's own conftest.py:
  tests/unit/conftest.py       — mock_jira
  tests/component/conftest.py  — minimal_metrics_dict, empty_metrics_dict
  tests/e2e/conftest.py        — live_server_url
"""

from __future__ import annotations

import sys
import threading
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
        histories.append(
            {
                "created": in_progress_ts,
                "items": [{"field": "status", "fromString": "To Do", "toString": "In Progress"}],
            }
        )
    if done_ts:
        histories.append(
            {
                "created": done_ts,
                "items": [{"field": "status", "fromString": "In Progress", "toString": "Done"}],
            }
        )
    return {
        "key": key,
        "fields": {"status": {"name": "Done"}},
        "changelog": {"histories": histories},
    }


# ---------------------------------------------------------------------------
# Helper factories (continued)
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
# Cross-layer fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def server_url():
    """Start a Server on a random port in a daemon thread, yield the base URL, then shut down."""
    import importlib

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
