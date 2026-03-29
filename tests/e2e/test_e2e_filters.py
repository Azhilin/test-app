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
    "params": {"JIRA_PROJECT": "", "JIRA_FILTER_STATUS": "Done"},
}

_USER_FILTER = {
    "filter_name": "My Sprint Filter",
    "slug": "my_sprint_filter",
    "is_default": False,
    "jql": "project = ABC AND status = Done AND sprint in closedSprints()",
    "created_at": "2026-03-01T10:00:00",
    "params": {"JIRA_PROJECT": "ABC"},
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
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return
        except Exception:
            if attempt == 2:
                raise


def _route_filters_get(page: Page, filters: list) -> None:
    """Mock GET /api/filters to return the given filter list."""
    page.route(
        "**/api/filters",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "filters": filters}),
        )
        if route.request.method == "GET"
        else route.continue_(),
    )


def _open_filter_tab(page: Page) -> None:
    page.get_by_role("tab", name="Jira Filter").click()
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
        page.get_by_role("tab", name="Jira Filter").click()
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
        page.route("**/api/filters/**", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True}),
        ))
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
