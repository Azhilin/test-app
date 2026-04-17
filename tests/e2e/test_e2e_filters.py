"""Playwright E2E tests for Jira filter UI behaviour.

Covers JFM-UI-001 through JFM-UI-006.

Run:
    pytest tests/e2e/test_e2e_filters.py -v            # headless
    pytest tests/e2e/test_e2e_filters.py -v --headed   # visual debug
"""

from __future__ import annotations

import json
import re

import allure
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

_DEFAULT_FILTER = {
    "filter_name": "Default_Jira_Filter",
    "slug": "default_jira_filter",
    "is_default": True,
    "jql": "",
    "created_at": None,
    "params": {"JIRA_PROJECT": ""},
}

_USER_FILTER = {
    "filter_name": "My Sprint Filter",
    "slug": "my_sprint_filter",
    "is_default": False,
    "jql": "project = ABC AND status = Done AND sprint in closedSprints()",
    "created_at": "2026-03-01T10:00:00",
    "params": {"JIRA_PROJECT": "ABC"},
}

_USER_FILTER_RICH = {
    "filter_name": "Team Alpha",
    "slug": "team_alpha",
    "is_default": False,
    "jql": "project = ALPHA AND status = Done",
    "created_at": "2026-03-15T10:00:00",
    "params": {
        "JIRA_PROJECT": "ALPHA",
        "JIRA_TEAM_ID": "uuid-alpha",
        "JIRA_ISSUE_TYPES": "Bug, Story",
        "JIRA_CLOSED_SPRINTS_ONLY": "true",
        "PROJECT_TYPE": "SCRUM",
        "ESTIMATION_TYPE": "StoryPoints",
        "JIRA_BOARD_ID": "42",
        "JIRA_SPRINT_COUNT": "8",
        "JIRA_FILTER_PAGE_SIZE": "100",
        "schema_name": "Custom_Schema",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _goto(page: Page, url: str, filters: list | None = None) -> None:
    """Navigate to the app with standard API mocks (config, reports) and optional filter data."""
    page.route(
        "**/api/config",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "configured": True, "config": {}}),
        ),
    )
    page.route(
        "**/api/reports",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"reports": []}),
        ),
    )
    if filters is not None:
        _route_filters_get(page, filters)

    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=5000)
            return
        except Exception:
            if attempt == 2:
                raise


def _route_filters_get(page: Page, filters: list) -> None:
    """Mock GET /api/filters to return the given filter list."""
    page.route(
        "**/api/filters",
        lambda route: (
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "filters": filters}),
            )
            if route.request.method == "GET"
            else route.continue_()
        ),
    )


def _route_schemas_get(page: Page, schemas: list[str]) -> None:
    """Mock GET /api/schemas (list + per-name detail) to return the given schema names.

    Detail lookups (?name=<n>) return a minimal schema body so the editor can populate.
    """

    def _handler(route):
        request = route.request
        if request.method != "GET":
            route.continue_()
            return
        url = request.url
        if "name=" in url:
            import urllib.parse as up

            name = up.unquote(url.split("name=", 1)[1].split("&")[0])
            if name in schemas:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "ok": True,
                            "schema": {
                                "schema_name": name,
                                "fields": {"team": {"id": "customfield_10001", "jql_name": "Team[Team]"}},
                                "status_mapping": {"done_statuses": ["Done"], "in_progress_statuses": ["In Progress"]},
                            },
                        }
                    ),
                )
            else:
                route.fulfill(
                    status=404,
                    content_type="application/json",
                    body=json.dumps({"ok": False, "error": f"Schema '{name}' not found"}),
                )
            return
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "schemas": schemas}),
        )

    page.route("**/api/schemas**", _handler)


def _open_filter_tab(page: Page) -> None:
    page.get_by_role("tab", name="Filter Builder").click()
    expect(page.locator("#panel-filter")).to_be_visible()


# ---------------------------------------------------------------------------
# JFM-UI-001 — Filter Name pre-populated on empty load
# ---------------------------------------------------------------------------


def test_filter_name_prepopulated_on_empty_load(page: Page, live_server_url: str):
    """On page load with an empty filter-name field, the input is set to Default_Jira_Filter_<YYYY-MM-DD>."""
    with allure.step("Navigate to the app and clear localStorage on the correct origin"):
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER])
        page.evaluate("localStorage.clear()")
        # Reload to trigger fresh init with empty localStorage; routes remain active
        page.reload(wait_until="domcontentloaded")

    with allure.step("Open the Filter tab"):
        _open_filter_tab(page)

    with allure.step("Assert filter-name is pre-populated with Default_Jira_Filter_YYYY-MM-DD"):
        filter_name_input = page.locator("#filter-name")
        expect(filter_name_input).not_to_have_value("")
        value = filter_name_input.input_value()
        assert re.match(r"^Default_Jira_Filter_\d{4}-\d{2}-\d{2}$", value), (
            f"Expected Default_Jira_Filter_YYYY-MM-DD, got: {value!r}"
        )


# ---------------------------------------------------------------------------
# JFM-UI-002 — Pre-population does not fire again after user edits
# ---------------------------------------------------------------------------


def test_filter_name_not_overwritten_after_user_edit(page: Page, live_server_url: str):
    """After the user types into filter-name, switching tabs and returning does not reset the value."""
    with allure.step("Navigate and open Filter tab"):
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER])
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="domcontentloaded")
        _open_filter_tab(page)

    with allure.step("User overwrites the pre-populated value"):
        page.locator("#filter-name").fill("My Custom Filter Name")

    with allure.step("Switch to Generate tab and back to Filter tab"):
        page.get_by_role("tab", name="Generate Report").click()
        page.get_by_role("tab", name="Filter Builder").click()
        expect(page.locator("#panel-filter")).to_be_visible()

    with allure.step("Filter-name still shows the user's value"):
        expect(page.locator("#filter-name")).to_have_value("My Custom Filter Name")


# ---------------------------------------------------------------------------
# JFM-UI-003 — Saved filters displayed on load
# ---------------------------------------------------------------------------


def test_filter_list_displayed_on_load(page: Page, live_server_url: str):
    """Both the default filter and a user filter appear in the filter list after page load."""
    with allure.step("Navigate with two filters in the mock response"):
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER])
        _open_filter_tab(page)

    with allure.step("Both filters appear in the filter list"):
        filter_list = page.locator("#filters-list")
        expect(filter_list).to_be_visible()
        expect(filter_list.locator("li")).to_have_count(2)

    with allure.step("Filter names are visible in the list"):
        expect(filter_list).to_contain_text("Default_Jira_Filter")
        expect(filter_list).to_contain_text("My Sprint Filter")


# ---------------------------------------------------------------------------
# JFM-UI-004 — Default filter has no Remove button
# ---------------------------------------------------------------------------


def test_default_filter_has_no_remove_button(page: Page, live_server_url: str):
    """The Default_Jira_Filter list item does not contain a Remove button."""
    with allure.step("Navigate with default + user filter"):
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER])
        _open_filter_tab(page)

    with allure.step("Locate the default filter list item"):
        # The first <li> should be the default filter
        filter_list = page.locator("#filters-list")
        expect(filter_list.locator("li")).to_have_count(2)
        first_item = filter_list.locator("li").first

    with allure.step("Assert no Remove (btn-danger) button in the default entry"):
        expect(first_item).to_contain_text("Default_Jira_Filter")
        expect(first_item.locator("button.btn-danger")).to_have_count(0)


# ---------------------------------------------------------------------------
# JFM-UI-005 — Non-default user filters have a Remove button
# ---------------------------------------------------------------------------


def test_user_filter_has_remove_button(page: Page, live_server_url: str):
    """A non-default user filter list item contains a Remove button."""
    with allure.step("Navigate with default + user filter"):
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER])
        _open_filter_tab(page)

    with allure.step("Locate the user filter list item (second item)"):
        filter_list = page.locator("#filters-list")
        expect(filter_list.locator("li")).to_have_count(2)
        second_item = filter_list.locator("li").nth(1)

    with allure.step("Assert Remove button is present in the user filter entry"):
        expect(second_item).to_contain_text("My Sprint Filter")
        remove_btn = second_item.locator("button.btn-danger")
        expect(remove_btn).to_have_count(1)
        expect(remove_btn).to_have_text("Remove")


# ---------------------------------------------------------------------------
# JFM-UI-006 — Clicking Remove updates the list immediately
# ---------------------------------------------------------------------------


def test_remove_filter_updates_list(page: Page, live_server_url: str):
    """Clicking Remove on a user filter calls DELETE and re-renders the list without that entry."""
    # Use a stateful GET mock: first call returns both filters, subsequent calls return only default
    get_call_count: dict[str, int] = {"n": 0}

    def _handle_filters_route(route):
        if route.request.method == "GET":
            if get_call_count["n"] == 0:
                data = {"ok": True, "filters": [_DEFAULT_FILTER, _USER_FILTER]}
            else:
                data = {"ok": True, "filters": [_DEFAULT_FILTER]}
            get_call_count["n"] += 1
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(data),
            )
        elif route.request.method == "DELETE":
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True}),
            )
        else:
            route.continue_()

    with allure.step("Navigate with default + user filter, intercept DELETE"):
        page.route("**/api/filters", _handle_filters_route)
        page.route(
            "**/api/filters/**",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True}),
            ),
        )
        _goto(page, live_server_url)
        _open_filter_tab(page)

    with allure.step("Verify both filters are initially visible"):
        filter_list = page.locator("#filters-list")
        expect(filter_list.locator("li")).to_have_count(2)

    with allure.step("Click Remove on the user filter"):
        second_item = filter_list.locator("li").nth(1)
        remove_btn = second_item.locator("button.btn-danger")
        remove_btn.click()

    with allure.step("List updates to show only the default filter"):
        expect(filter_list.locator("li")).to_have_count(1, timeout=5000)
        expect(filter_list).to_contain_text("Default_Jira_Filter")
        expect(filter_list).not_to_contain_text("My Sprint Filter")


# ---------------------------------------------------------------------------
# JFM-UI-007 — Active Schema dropdown populated from /api/schemas
# ---------------------------------------------------------------------------


def test_filter_schema_dropdown_populated_on_load(page: Page, live_server_url: str):
    """#filter-schema-select is populated from /api/schemas and defaults to Default_Jira_Cloud."""
    with allure.step("Navigate with mocked schemas and filters"):
        _route_schemas_get(page, ["Default_Jira_Cloud", "Custom_Schema"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER])
        _open_filter_tab(page)

    with allure.step("Both schema options appear and Default_Jira_Cloud is selected"):
        select = page.locator("#filter-schema-select")
        expect(select.locator("option[value='Default_Jira_Cloud']")).to_have_count(1)
        expect(select.locator("option[value='Custom_Schema']")).to_have_count(1)
        expect(select).to_have_value("Default_Jira_Cloud")


# ---------------------------------------------------------------------------
# JFM-UI-008 — Filter Name dropdown lists existing filters
# ---------------------------------------------------------------------------


def test_filter_name_dropdown_lists_existing_filters(page: Page, live_server_url: str):
    """#filter-name-select shows '— New filter —' plus every saved filter (default tagged)."""
    with allure.step("Navigate with default + user filter"):
        _route_schemas_get(page, ["Default_Jira_Cloud"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER])
        _open_filter_tab(page)

    with allure.step("Dropdown contains three options in the expected order"):
        name_select = page.locator("#filter-name-select")
        expect(name_select.locator("option")).to_have_count(3)
        expect(name_select.locator("option").nth(0)).to_have_attribute("value", "__new__")
        expect(name_select.locator("option").nth(0)).to_contain_text("New filter")
        expect(name_select.locator("option[value='Default_Jira_Filter']")).to_contain_text("(default)")
        expect(name_select.locator("option[value='My Sprint Filter']")).to_have_count(1)


# ---------------------------------------------------------------------------
# JFM-UI-009 — Selecting an existing filter loads it into the form
# ---------------------------------------------------------------------------


def test_selecting_existing_filter_loads_form(page: Page, live_server_url: str):
    """Selecting a filter from #filter-name-select populates the form with its params."""
    with allure.step("Navigate with rich user filter and its schema available"):
        _route_schemas_get(page, ["Default_Jira_Cloud", "Custom_Schema"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER_RICH])
        _open_filter_tab(page)

    with allure.step("Select the rich user filter"):
        page.locator("#filter-name-select").select_option("Team Alpha")

    with allure.step("Form fields reflect the filter's params"):
        expect(page.locator("#jira-project")).to_have_value("ALPHA")
        expect(page.locator("#jira-team-id")).to_have_value("uuid-alpha")
        expect(page.locator("#jira-issue-types")).to_have_value("Bug, Story")
        expect(page.locator("#jira-closed-sprints-only")).to_have_value("true")
        expect(page.locator("#jira-board-id")).to_have_value("42")
        expect(page.locator("#sprint-count")).to_have_value("8")
        expect(page.locator("#filter-schema-select")).to_have_value("Custom_Schema")

    with allure.step("Filter name input is hidden and mirrors the filter name"):
        name_input = page.locator("#filter-name")
        expect(name_input).to_be_hidden()
        expect(name_input).to_have_value("Team Alpha")


# ---------------------------------------------------------------------------
# JFM-UI-010 — "— New filter —" resets the form
# ---------------------------------------------------------------------------


def test_new_filter_option_resets_form(page: Page, live_server_url: str):
    """Switching back to '— New filter —' unhides the name input and clears every param field."""
    with allure.step("Navigate with rich filter, load it, then switch back to New filter"):
        _route_schemas_get(page, ["Default_Jira_Cloud", "Custom_Schema"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER_RICH])
        _open_filter_tab(page)
        page.locator("#filter-name-select").select_option("Team Alpha")
        expect(page.locator("#jira-project")).to_have_value("ALPHA")
        page.locator("#filter-name-select").select_option("__new__")

    with allure.step("Form fields are cleared and the name input is visible + pre-populated"):
        expect(page.locator("#jira-project")).to_have_value("")
        expect(page.locator("#jira-team-id")).to_have_value("")
        expect(page.locator("#jira-issue-types")).to_have_value("")
        expect(page.locator("#jira-board-id")).to_have_value("")
        expect(page.locator("#sprint-count")).to_have_value("")
        expect(page.locator("#filter-schema-select")).to_have_value("Default_Jira_Cloud")

        name_input = page.locator("#filter-name")
        expect(name_input).to_be_visible()
        assert re.match(
            r"^Default_Jira_Filter_\d{4}-\d{2}-\d{2}$",
            name_input.input_value(),
        ), f"Expected Default_Jira_Filter_YYYY-MM-DD, got: {name_input.input_value()!r}"


# ---------------------------------------------------------------------------
# JFM-UI-011 — Save uses schema_name from #filter-schema-select
# ---------------------------------------------------------------------------


def test_save_sends_schema_from_filter_dropdown(page: Page, live_server_url: str):
    """POST /api/filters body.params.schema_name equals the dropdown value — not localStorage."""
    captured: dict = {}

    def _handle_filters(route):
        req = route.request
        if req.method == "GET":
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "filters": [_DEFAULT_FILTER]}),
            )
            return
        if req.method == "POST":
            captured["body"] = req.post_data_json or {}
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "ok": True,
                        "updated": False,
                        "jql": "project = ZZZ AND status = Done",
                    }
                ),
            )
            return
        route.continue_()

    with allure.step("Navigate with schemas + intercepted POST"):
        _route_schemas_get(page, ["Default_Jira_Cloud", "Custom_Schema"])
        page.route("**/api/filters", _handle_filters)
        _goto(page, live_server_url)
        _open_filter_tab(page)

    with allure.step("Fill required fields and pick Custom_Schema"):
        page.evaluate(
            "document.getElementById('filter-jql-builder').open = true;"
            "document.getElementById('filter-report-scope').open = true;"
        )
        page.locator("#filter-name").fill("Schema Test")
        page.locator("#jira-project").fill("ZZZ")
        page.locator("#jira-board-id").fill("99")
        page.locator("#sprint-count").fill("5")
        page.locator("#filter-schema-select").select_option("Custom_Schema")

    with allure.step("Click Save and wait for the POST to land"):
        page.locator("#btn-save-jira-filter").click()
        page.wait_for_function("() => !!window && true", timeout=3000)
        # Poll until captured body arrives
        for _ in range(30):
            if captured.get("body"):
                break
            page.wait_for_timeout(100)

    with allure.step("Captured body.params.schema_name matches the dropdown value"):
        body = captured.get("body") or {}
        assert body.get("name") == "Schema Test"
        params = body.get("params") or {}
        assert params.get("schema_name") == "Custom_Schema", (
            f"Expected schema_name=Custom_Schema, got {params.get('schema_name')!r}"
        )


# ---------------------------------------------------------------------------
# JFM-UI-012 — Filter Builder dropdown does not mutate localStorage
# ---------------------------------------------------------------------------


def test_filter_builder_schema_does_not_write_localstorage(page: Page, live_server_url: str):
    """Changing #filter-schema-select leaves localStorage.jira_schema_name untouched."""
    with allure.step("Navigate with two schemas + seed localStorage"):
        _route_schemas_get(page, ["Default_Jira_Cloud", "Custom_Schema"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER])
        page.evaluate("localStorage.setItem('jira_schema_name', 'Default_Jira_Cloud')")
        _open_filter_tab(page)

    with allure.step("Change the Filter Builder's schema dropdown"):
        page.locator("#filter-schema-select").select_option("Custom_Schema")
        expect(page.locator("#filter-schema-select")).to_have_value("Custom_Schema")

    with allure.step("localStorage key is unchanged"):
        stored = page.evaluate("localStorage.getItem('jira_schema_name')")
        assert stored == "Default_Jira_Cloud", (
            f"Expected localStorage.jira_schema_name to stay Default_Jira_Cloud, got {stored!r}"
        )


# ---------------------------------------------------------------------------
# JFM-UI-013 — Save disabled for the default filter
# ---------------------------------------------------------------------------


def test_save_disabled_when_default_filter_selected(page: Page, live_server_url: str):
    """#btn-save-jira-filter is disabled when Default_Jira_Filter is picked; re-enables otherwise."""
    with allure.step("Navigate with two filters"):
        _route_schemas_get(page, ["Default_Jira_Cloud"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER])
        _open_filter_tab(page)

    with allure.step("Default filter selected → Save disabled"):
        page.locator("#filter-name-select").select_option("Default_Jira_Filter")
        expect(page.locator("#btn-save-jira-filter")).to_be_disabled()

    with allure.step("Switch to — New filter — → Save re-enabled"):
        page.locator("#filter-name-select").select_option("__new__")
        expect(page.locator("#btn-save-jira-filter")).to_be_enabled()

    with allure.step("Switch to user filter → Save enabled"):
        page.locator("#filter-name-select").select_option("My Sprint Filter")
        expect(page.locator("#btn-save-jira-filter")).to_be_enabled()


# ---------------------------------------------------------------------------
# JFM-UI-014 — Loading a filter with JIRA_PROJECT auto-opens JQL Builder
# ---------------------------------------------------------------------------


def test_loading_filter_with_project_opens_jql_builder(page: Page, live_server_url: str):
    """Selecting a filter that has JIRA_PROJECT auto-expands the JQL Builder section."""
    with allure.step("Navigate with rich user filter"):
        _route_schemas_get(page, ["Default_Jira_Cloud", "Custom_Schema"])
        _goto(page, live_server_url, filters=[_DEFAULT_FILTER, _USER_FILTER_RICH])
        _open_filter_tab(page)

    with allure.step("Select the rich filter from the dropdown"):
        page.locator("#filter-name-select").select_option("Team Alpha")

    with allure.step("JQL Builder details section is open"):
        is_open = page.locator("#filter-jql-builder").evaluate("el => el.open")
        assert is_open, "Expected #filter-jql-builder to be open after loading a filter with JIRA_PROJECT"

    with allure.step("The four JQL Builder fields are visible"):
        expect(page.locator("#jira-project")).to_be_visible()
        expect(page.locator("#jira-team-id")).to_be_visible()
        expect(page.locator("#jira-issue-types")).to_be_visible()
        expect(page.locator("#jira-closed-sprints-only")).to_be_visible()
