"""Playwright E2E tests for the Schema Setup tab UI.

Covers JSR-UI-001..009: tab visibility, dropdown load, JSON editor round-trip,
delete button behaviour for the default schema, and client-side JSON validation.
"""

from __future__ import annotations

import copy
import json
import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import _goto

pytestmark = pytest.mark.e2e


DEFAULT_SCHEMA = {
    "schema_name": "Default_Jira_Cloud",
    "description": "Standard Jira Cloud field mapping",
    "fields": {
        "story_points": {"id": "customfield_10016", "type": "number"},
        "status": {"id": "status", "type": "string"},
        "labels": {"id": "labels", "type": "array"},
    },
    "status_mapping": {
        "done_statuses": ["Done", "Closed"],
        "in_progress_statuses": ["In Progress"],
    },
}


def _install_stateful_schema_api(page: Page) -> dict:
    """Install a stateful /api/schemas mock that backs GET/POST/DELETE in-memory."""
    state: dict = {
        "schemas": {"Default_Jira_Cloud": copy.deepcopy(DEFAULT_SCHEMA)},
    }

    def _handle(route):
        request = route.request
        method = request.method
        url = request.url

        if method == "GET":
            if "name=" in url:
                name = url.split("name=", 1)[1].split("&")[0]
                import urllib.parse as up

                name = up.unquote(name)
                schema = state["schemas"].get(name)
                if schema is None:
                    route.fulfill(
                        status=404,
                        content_type="application/json",
                        body=json.dumps({"ok": False, "error": f"Schema '{name}' not found"}),
                    )
                else:
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        body=json.dumps({"ok": True, "schema": schema}),
                    )
                return
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "schemas": list(state["schemas"].keys())}),
            )
            return

        if method == "POST":
            body = request.post_data_json or {}
            schema = body.get("schema") or {}
            name = (schema.get("schema_name") or "").strip()
            updated = name in state["schemas"]
            state["schemas"][name] = schema
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "updated": updated, "schema": schema}),
            )
            return

        if method == "DELETE":
            name = url.split("name=", 1)[1].split("&")[0] if "name=" in url else ""
            import urllib.parse as up

            name = up.unquote(name)
            if name == "Default_Jira_Cloud":
                route.fulfill(
                    status=400,
                    content_type="application/json",
                    body=json.dumps({"ok": False, "error": "Cannot delete the default schema"}),
                )
                return
            state["schemas"].pop(name, None)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True}),
            )
            return

        route.continue_()

    page.route("**/api/schemas**", _handle)
    return state


# ---------------------------------------------------------------------------
# JSR-UI-001 — tab placement
# ---------------------------------------------------------------------------


def test_schema_tab_visible_between_connection_and_filter(page: Page, live_server_url: str):
    """Schema Setup tab sits between Jira Connection and Filter Builder."""
    _install_stateful_schema_api(page)
    _goto(page, live_server_url)

    tabs = page.locator('[role="tab"]').all_text_contents()
    # Order matters — Schema Setup must appear between Connection and Filter Builder
    connection_idx = tabs.index("Jira Connection")
    schema_idx = tabs.index("Schema Setup")
    filter_idx = tabs.index("Filter Builder")
    assert connection_idx < schema_idx < filter_idx

    page.get_by_role("tab", name="Schema Setup").click()
    expect(page.locator("#panel-schema")).to_be_visible()
    expect(page.locator("#tab-schema")).to_have_attribute("aria-selected", "true")


# ---------------------------------------------------------------------------
# JSR-UI-002 / JSR-UI-003 — dropdown populated & selection loads JSON
# ---------------------------------------------------------------------------


def test_schema_load_into_editor_on_select(page: Page, live_server_url: str):
    """Selecting Default_Jira_Cloud loads its JSON into the editor."""
    _install_stateful_schema_api(page)
    _goto(page, live_server_url)

    page.get_by_role("tab", name="Schema Setup").click()
    expect(page.locator("#schema-select option[value='Default_Jira_Cloud']")).to_have_count(1)

    page.select_option("#schema-select", "Default_Jira_Cloud")
    editor = page.locator("#schema-json-editor")
    expect(editor).to_have_value(re.compile(r'"schema_name":\s*"Default_Jira_Cloud"'))


# ---------------------------------------------------------------------------
# JSR-UI-004 / JSR-UI-005 — New Schema template + save round-trip
# ---------------------------------------------------------------------------


def test_schema_save_round_trip(page: Page, live_server_url: str):
    """'New Schema' → edit → Save persists and the new name appears in the dropdown."""
    _install_stateful_schema_api(page)
    _goto(page, live_server_url)

    page.get_by_role("tab", name="Schema Setup").click()
    page.locator("#btn-schema-new").click()

    editor = page.locator("#schema-json-editor")
    new_schema = {
        "schema_name": "E2E_Manual",
        "description": "via e2e",
        "fields": {"labels": {"id": "labels", "type": "array"}},
        "status_mapping": {"done_statuses": ["Done"], "in_progress_statuses": ["In Progress"]},
    }
    editor.fill(json.dumps(new_schema, indent=2))
    page.locator("#btn-schema-save").click()

    expect(page.locator("#schema-status")).to_contain_text("E2E_Manual")
    expect(page.locator("#schema-select option[value='E2E_Manual']")).to_have_count(1)
    expect(page.locator("#schema-select")).to_have_value("E2E_Manual")


# ---------------------------------------------------------------------------
# JSR-UI-008 — Delete disabled for Default_Jira_Cloud
# ---------------------------------------------------------------------------


def test_schema_delete_button_disabled_for_default(page: Page, live_server_url: str):
    """Delete button is disabled when Default_Jira_Cloud is selected."""
    _install_stateful_schema_api(page)
    _goto(page, live_server_url)

    page.get_by_role("tab", name="Schema Setup").click()
    # After initial load, Default_Jira_Cloud is selected
    expect(page.locator("#schema-select")).to_have_value("Default_Jira_Cloud")
    expect(page.locator("#btn-schema-delete")).to_be_disabled()


# ---------------------------------------------------------------------------
# JSR-UI-006 — Invalid JSON blocks save
# ---------------------------------------------------------------------------


def test_schema_invalid_json_shows_error(page: Page, live_server_url: str):
    """Invalid JSON surfaces a parse error in the log output and blocks the POST."""
    state = _install_stateful_schema_api(page)
    _goto(page, live_server_url)

    page.get_by_role("tab", name="Schema Setup").click()
    editor = page.locator("#schema-json-editor")
    editor.fill("{not valid json")
    page.locator("#btn-schema-save").click()

    log = page.locator("#schema-log-output")
    expect(log).to_contain_text("Invalid JSON")
    # State should be unchanged — only the default schema
    assert set(state["schemas"].keys()) == {"Default_Jira_Cloud"}


# ---------------------------------------------------------------------------
# JSR-UI-010 — Schema Setup is editor-only; does not set the filter's active schema
# ---------------------------------------------------------------------------


def test_schema_setup_does_not_set_active_schema_for_filter(page: Page, live_server_url: str):
    """Changing the Schema Setup dropdown must not affect the Filter Builder's Active Schema."""
    state = _install_stateful_schema_api(page)
    # Seed a second schema so the Schema Setup dropdown has a non-default option.
    other_schema = copy.deepcopy(DEFAULT_SCHEMA)
    other_schema["schema_name"] = "Alt_Schema"
    state["schemas"]["Alt_Schema"] = other_schema

    page.route(
        "**/api/filters",
        lambda route: (
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "ok": True,
                        "filters": [
                            {
                                "filter_name": "Default_Jira_Filter",
                                "slug": "default_jira_filter",
                                "is_default": True,
                                "jql": "",
                                "created_at": None,
                                "params": {"schema_name": "Default_Jira_Cloud"},
                            }
                        ],
                    }
                ),
            )
            if route.request.method == "GET"
            else route.continue_()
        ),
    )
    _goto(page, live_server_url)

    # Open Schema Setup tab and switch to the non-default schema.
    page.get_by_role("tab", name="Schema Setup").click()
    page.locator("#schema-select").select_option("Alt_Schema")
    expect(page.locator("#schema-select")).to_have_value("Alt_Schema")

    # Switch to Filter Builder and confirm the Active Schema is still Default_Jira_Cloud
    # (taken from the selected filter's params.schema_name, not from Schema Setup).
    page.get_by_role("tab", name="Filter Builder").click()
    expect(page.locator("#panel-filter")).to_be_visible()
    expect(page.locator("#filter-schema-select")).to_have_value("Default_Jira_Cloud")
