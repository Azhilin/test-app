"""Component tests for /api/filters HTTP routes.

Tests run against a real server on a random port (server_url fixture).
Filter-mutating tests use the restore_filters fixture to leave
config/jira_filters.json unchanged after each test.

Covers JFM-D-003/004, JFM-P-001, JFM-P-003/004, JFM-P-008/009/010.
"""

from __future__ import annotations

import json
import threading
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.component

# ---------------------------------------------------------------------------
# Fixture: backup and restore config/jira_filters.json
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FILTERS_PATH = _PROJECT_ROOT / "config" / "jira_filters.json"


@pytest.fixture
def restore_filters():
    """Backup config/jira_filters.json before the test and restore it afterwards."""
    backup: bytes | None = _FILTERS_PATH.read_bytes() if _FILTERS_PATH.exists() else None
    yield _FILTERS_PATH
    if backup is not None:
        _FILTERS_PATH.write_bytes(backup)
    elif _FILTERS_PATH.exists():
        _FILTERS_PATH.unlink()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _get_filters(base_url: str) -> dict:
    resp = urllib.request.urlopen(f"{base_url}/api/filters")
    return json.loads(resp.read().decode())


def _post_filter(base_url: str, name: str, project: str = "PROJ") -> dict:
    body = json.dumps({"name": name, "params": {"JIRA_PROJECT": project}}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/filters",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def _post_filter_with_report_name(base_url: str, name: str, project: str, report_name: str) -> dict:
    body = json.dumps({"name": name, "report_name": report_name, "params": {"JIRA_PROJECT": project}}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/filters",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def _post_filter_with_params(base_url: str, name: str, params: dict) -> dict:
    body = json.dumps({"name": name, "params": params}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/filters",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def _delete_filter(base_url: str, slug: str) -> dict:
    req = urllib.request.Request(
        f"{base_url}/api/filters/{urllib.parse.quote(slug, safe='')}",
        method="DELETE",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# JFM-P-001 — GET returns default entry first
# ---------------------------------------------------------------------------


def test_get_filters_default_is_first(server_url):
    """GET /api/filters returns the default filter as the first entry."""
    data = _get_filters(server_url)

    assert data["ok"] is True
    filters = data["filters"]
    assert len(filters) >= 1
    assert filters[0]["is_default"] is True
    assert filters[0]["filter_name"] == "Default_Jira_Filter"


# ---------------------------------------------------------------------------
# JFM-D-003 — Default always present even after user filters are deleted
# ---------------------------------------------------------------------------


def test_get_filters_always_includes_default_after_user_delete(server_url, restore_filters):
    """GET /api/filters always includes the default filter, even after all user filters are removed."""
    # Create and then delete a user filter
    post_data = _post_filter(server_url, "Temp Filter")
    slug = post_data["slug"]
    _delete_filter(server_url, slug)

    data = _get_filters(server_url)
    assert data["ok"] is True
    defaults = [f for f in data["filters"] if f.get("is_default")]
    assert len(defaults) == 1


# ---------------------------------------------------------------------------
# JFM-D-004 — Default filter cannot be deleted via HTTP
# ---------------------------------------------------------------------------


def test_delete_default_filter_returns_error(server_url):
    """DELETE /api/filters/default_jira_filter returns ok=False."""
    data = _delete_filter(server_url, "default_jira_filter")

    assert data["ok"] is False
    assert "Cannot delete the default filter" in data["error"]


# ---------------------------------------------------------------------------
# JFM-P-003 — POST creates a new filter and GET returns it
# ---------------------------------------------------------------------------


def test_post_filter_creates_new_and_get_returns_it(server_url, restore_filters):
    """A new filter POSTed to /api/filters appears in the subsequent GET response."""
    post_data = _post_filter(server_url, "My New Filter", project="NEWPROJ")

    assert post_data["ok"] is True
    assert post_data["updated"] is False

    filters = _get_filters(server_url)["filters"]
    names = [f["filter_name"] for f in filters]
    assert "My New Filter" in names


# ---------------------------------------------------------------------------
# JFM-P-004 — POST upserts existing filter by name
# ---------------------------------------------------------------------------


def test_post_filter_upserts_on_duplicate_name(server_url, restore_filters):
    """Posting the same name twice updates the existing entry; only one user filter exists."""
    _post_filter(server_url, "Upsert Filter", project="FIRST")
    second = _post_filter(server_url, "Upsert Filter", project="SECOND")

    assert second["ok"] is True
    assert second["updated"] is True

    filters = _get_filters(server_url)["filters"]
    user_filters = [f for f in filters if not f.get("is_default")]
    assert len([f for f in user_filters if f["filter_name"] == "Upsert Filter"]) == 1


# ---------------------------------------------------------------------------
# JFM-P-008 — DELETE removes the matching entry
# ---------------------------------------------------------------------------


def test_delete_filter_removes_entry(server_url, restore_filters):
    """DELETE /api/filters/<slug> removes the entry; subsequent GET does not include it."""
    post_data = _post_filter(server_url, "Delete Me", project="DEL")
    slug = post_data["slug"]

    delete_data = _delete_filter(server_url, slug)
    assert delete_data["ok"] is True

    filters = _get_filters(server_url)["filters"]
    slugs = [f.get("slug") for f in filters]
    assert slug not in slugs


# ---------------------------------------------------------------------------
# JFM-P-009 — DELETE with unknown slug returns "Filter not found"
# ---------------------------------------------------------------------------


def test_delete_unknown_slug_returns_not_found(server_url):
    """DELETE /api/filters/no-such-slug returns ok=False with a descriptive error."""
    data = _delete_filter(server_url, "absolutely_no_such_slug_xyz")

    assert data["ok"] is False
    assert "Filter not found" in data["error"]


# ---------------------------------------------------------------------------
# JFM-P-010 — Filter data persists across server restarts
# ---------------------------------------------------------------------------


def test_filter_persists_across_server_restart(server_url, restore_filters):
    """A filter written via POST is returned by a fresh server instance reading the same file."""
    import importlib
    import sys

    post_data = _post_filter(server_url, "Persist Test", project="PERSIST")
    assert post_data["ok"] is True
    slug = post_data["slug"]

    # Verify the entry is on disk (independent of in-memory state)
    assert _FILTERS_PATH.exists()
    on_disk = json.loads(_FILTERS_PATH.read_text(encoding="utf-8"))
    assert any(f.get("slug") == slug for f in on_disk)

    # Start a fresh server instance pointing to the same real project root
    orig_argv = sys.argv
    sys.argv = ["server.py"]
    sys.modules.pop("server", None)
    try:
        import server as srv_mod

        importlib.reload(srv_mod)
    finally:
        sys.argv = orig_argv

    server2 = srv_mod.Server(("127.0.0.1", 0), srv_mod.Handler)
    port2 = server2.server_address[1]
    t = threading.Thread(target=server2.serve_forever, daemon=True)
    t.start()
    try:
        url2 = f"http://127.0.0.1:{port2}"
        result = _get_filters(url2)
        slugs = [f.get("slug") for f in result.get("filters", [])]
        assert slug in slugs
    finally:
        server2.shutdown()


# ---------------------------------------------------------------------------
# JFM-P-007 — POST preserves params.schema_name across round-trip
# ---------------------------------------------------------------------------


def test_post_filter_round_trip_preserves_schema_name(server_url, restore_filters):
    """POST /api/filters with params.schema_name stores it; GET returns the same value."""
    params = {
        "JIRA_PROJECT": "SCHEMA_RT",
        "schema_name": "Default_Jira_Cloud",
    }
    post_data = _post_filter_with_params(server_url, "Schema Round Trip", params)
    assert post_data["ok"] is True

    filters = _get_filters(server_url)["filters"]
    entry = next(
        (f for f in filters if f.get("filter_name") == "Schema Round Trip"),
        None,
    )
    assert entry is not None, "Posted filter was not returned by GET"
    assert entry.get("params", {}).get("schema_name") == "Default_Jira_Cloud"


# ---------------------------------------------------------------------------
# report_name round-trip
# ---------------------------------------------------------------------------


def test_post_filter_round_trip_preserves_report_name(server_url, restore_filters):
    """POST /api/filters with report_name stores it; GET returns the same value."""
    post_data = _post_filter_with_report_name(server_url, "Report Name RT", "RPROJ", "Custom Report Title")
    assert post_data["ok"] is True

    filters = _get_filters(server_url)["filters"]
    entry = next((f for f in filters if f.get("filter_name") == "Report Name RT"), None)
    assert entry is not None, "Posted filter was not returned by GET"
    assert entry.get("report_name") == "Custom Report Title"


def test_post_filter_report_name_defaults_to_filter_name(server_url, restore_filters):
    """When report_name is omitted, it defaults to the filter name."""
    post_data = _post_filter(server_url, "Default Report Name", project="DPROJ")
    assert post_data["ok"] is True

    filters = _get_filters(server_url)["filters"]
    entry = next((f for f in filters if f.get("filter_name") == "Default Report Name"), None)
    assert entry is not None
    assert entry.get("report_name") == "Default Report Name"
