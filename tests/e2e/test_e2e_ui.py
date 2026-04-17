"""Playwright E2E tests for the AI Adoption Manager UI.

These tests launch a real browser against the dev server and verify
tab navigation, form validation, localStorage persistence, SSE streaming,
and dynamic UI updates.

Run:
    pytest tests/test_e2e_ui.py -v            # headless
    pytest tests/test_e2e_ui.py -v --headed   # visual debug
"""

from __future__ import annotations

import json
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import _goto, _mock_filters_api

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Group 1: Page Load & Layout
# ---------------------------------------------------------------------------


def test_page_loads_with_title(page: Page, live_server_url: str):
    """Page loads with correct title and heading."""
    _goto(page, live_server_url)
    expect(page).to_have_title("AI Adoption Manager")
    expect(page.locator("h1")).to_have_text("AI Adoption Manager")


def test_default_tab_is_generate(page: Page, live_server_url: str):
    """Generate Report tab is active by default."""
    _goto(page, live_server_url)
    generate_tab = page.locator("#tab-generate")
    expect(generate_tab).to_have_attribute("aria-selected", "true")
    expect(page.locator("#panel-generate")).to_be_visible()
    expect(page.locator("#panel-connection")).to_be_hidden()
    expect(page.locator("#panel-filter")).to_be_hidden()


def test_all_three_tabs_visible(page: Page, live_server_url: str):
    """All three tab buttons are present in the tab bar."""
    _goto(page, live_server_url)
    expect(page.get_by_role("tab", name="Jira Connection")).to_be_visible()
    expect(page.get_by_role("tab", name="Filter Builder")).to_be_visible()
    expect(page.get_by_role("tab", name="Generate Report")).to_be_visible()


# ---------------------------------------------------------------------------
# Group 2: Tab Navigation
# ---------------------------------------------------------------------------


def test_click_connection_tab(page: Page, live_server_url: str):
    """Clicking Connection tab shows its panel and hides others."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()
    expect(page.locator("#tab-connection")).to_have_attribute("aria-selected", "true")
    expect(page.locator("#tab-generate")).to_have_attribute("aria-selected", "false")
    expect(page.locator("#panel-connection")).to_be_visible()
    expect(page.locator("#panel-generate")).to_be_hidden()


def test_click_filter_tab(page: Page, live_server_url: str):
    """Clicking Filter tab shows its panel and hides others."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Filter Builder").click()
    expect(page.locator("#tab-filter")).to_have_attribute("aria-selected", "true")
    expect(page.locator("#panel-filter")).to_be_visible()
    expect(page.locator("#panel-generate")).to_be_hidden()
    expect(page.locator("#panel-connection")).to_be_hidden()


def test_keyboard_arrow_right_navigation(page: Page, live_server_url: str):
    """ArrowRight on a focused tab activates the next tab."""
    _goto(page, live_server_url)
    # Tab order in DOM: connection(0), schema(1), filter(2), generate(3)
    page.get_by_role("tab", name="Jira Connection").click()
    expect(page.locator("#panel-connection")).to_be_visible()

    # Press ArrowRight → should move to Schema Setup tab
    page.keyboard.press("ArrowRight")
    expect(page.locator("#tab-schema")).to_have_attribute("aria-selected", "true")
    expect(page.locator("#panel-schema")).to_be_visible()
    expect(page.locator("#panel-connection")).to_be_hidden()


# ---------------------------------------------------------------------------
# Group 3: Connection Tab — Form & Validation
# ---------------------------------------------------------------------------


def test_save_connection_valid_inputs(page: Page, live_server_url: str):
    """Filling valid inputs, testing connection, then clicking Save shows confirmation flash."""
    with allure.step("Mock /api/test-connection to return a successful response"):
        page.route(
            "**/api/test-connection",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "displayName": "Test User", "emailAddress": "user@example.com"}),
            ),
        )
    with allure.step("Navigate to the Connection tab"):
        _goto(page, live_server_url)
        page.get_by_role("tab", name="Jira Connection").click()

    with allure.step("Fill in valid Jira credentials"):
        page.locator("#jira-url").fill("https://test.atlassian.net")
        page.locator("#jira-email").fill("user@example.com")
        page.locator("#jira-token").fill("test-token-123")

    with allure.step("Click Test Connection and assert Connected badge appears"):
        # Test Connection must succeed first to enable Save
        page.locator("#btn-test-conn").click()
        expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=5000)

    with allure.step("Click Save and assert confirmation flash + localStorage persistence"):
        page.locator("#btn-save-conn").click()

        # "Settings saved" flash should appear
        flash = page.locator("#save-confirm-conn")
        expect(flash).to_have_class(re.compile(r"visible"))

        # Values persisted to localStorage
        stored_url = page.evaluate("localStorage.getItem('jira_url')")
        assert stored_url == "https://test.atlassian.net"


def test_validation_error_empty_fields(page: Page, live_server_url: str):
    """Clicking Test Connection with empty fields shows validation errors via badge."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    # Clear any pre-filled values
    page.locator("#jira-url").fill("")
    page.locator("#jira-email").fill("")
    page.locator("#jira-token").fill("")

    # Save is disabled until Test Connection succeeds — trigger validation via Test Connection
    page.locator("#btn-test-conn").click()

    badge = page.locator("#conn-status-badge")
    expect(badge).to_have_text("Error")
    detail = page.locator("#conn-status-detail")
    expect(detail).to_contain_text("Fill in URL, email")
    # Save button must remain disabled
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_validation_error_invalid_url(page: Page, live_server_url: str):
    """Invalid URL: Test Connection still proceeds but Jira call fails; Save remains disabled."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    page.locator("#jira-url").fill("not-a-url")
    page.locator("#jira-email").fill("user@example.com")
    page.locator("#jira-token").fill("some-token")

    # Save is disabled; Test Connection attempts the call and returns an error for invalid URL
    page.locator("#btn-test-conn").click()

    badge = page.locator("#conn-status-badge")
    expect(badge).to_have_text("Error", timeout=5000)
    # Save button must remain disabled regardless
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_token_show_hide_toggle(page: Page, live_server_url: str):
    """Eye button toggles token input between password and text."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    token_input = page.locator("#jira-token")
    expect(token_input).to_have_attribute("type", "password")

    page.locator("#btn-toggle-token").click()
    expect(token_input).to_have_attribute("type", "text")

    page.locator("#btn-toggle-token").click()
    expect(token_input).to_have_attribute("type", "password")


# ---------------------------------------------------------------------------
# Group 4: Connection Tab — Test Connection
# ---------------------------------------------------------------------------


def test_test_connection_missing_fields(page: Page, live_server_url: str):
    """Test Connection with empty fields shows error in badge."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    page.locator("#jira-url").fill("")
    page.locator("#jira-email").fill("")
    page.locator("#jira-token").fill("")
    page.locator("#btn-test-conn").click()

    badge = page.locator("#conn-status-badge")
    expect(badge).to_have_text("Error")
    detail = page.locator("#conn-status-detail")
    expect(detail).to_contain_text("Fill in URL, email")


def test_test_connection_unreachable_server(page: Page, live_server_url: str):
    """Test Connection with unreachable Jira shows error after attempt (mocked — no real DNS)."""
    # Mock the server-side test-connection call so the test stays fast without a real DNS lookup.
    page.route(
        "**/api/test-connection",
        lambda route: route.fulfill(
            status=502,
            content_type="application/json",
            body=json.dumps({"ok": False, "error": "Connection refused — host unreachable"}),
        ),
    )
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    page.locator("#jira-url").fill("https://nonexistent-jira-12345.atlassian.net")
    page.locator("#jira-email").fill("user@example.com")
    page.locator("#jira-token").fill("fake-token")
    page.locator("#btn-test-conn").click()

    badge = page.locator("#conn-status-badge")
    expect(badge).to_have_text("Error", timeout=5000)
    detail = page.locator("#conn-status-detail")
    expect(detail).not_to_be_empty()


# ---------------------------------------------------------------------------
# Group 5: Filter Tab — Save & List
# ---------------------------------------------------------------------------


def test_save_filter_missing_required_fields(page: Page, live_server_url: str):
    """Save Filter with empty fields shows error in filter log."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Filter Builder").click()

    page.locator("#filter-name").fill("")
    _open_jql_builder(page)
    page.locator("#jira-project").fill("")
    page.locator("#btn-save-jira-filter").click()

    log = page.locator("#filter-log-output")
    expect(log).to_contain_text("Filter Name is required")


def test_save_filter_success(page: Page, live_server_url: str):
    """Saving a filter with valid inputs shows JQL and adds to list."""
    _mock_filters_api(page)
    _goto(page, live_server_url)
    # Clear any leftover localStorage filters
    page.evaluate("localStorage.removeItem('jira_saved_filters')")

    page.get_by_role("tab", name="Filter Builder").click()
    page.locator("#filter-name").fill("My Test Filter")
    _open_jql_builder(page)
    page.locator("#jira-project").fill("TEST")
    _set_board_settings(page)
    page.locator("#btn-save-jira-filter").click()

    log = page.locator("#filter-log-output")
    # Should show JQL and saved confirmation
    expect(log).to_contain_text("project = TEST", timeout=5000)
    expect(log).to_contain_text("Saved", timeout=5000)

    # Filter should appear in the saved filters list
    filters_list = page.locator("#filters-list")
    expect(filters_list.locator("li")).to_have_count(1, timeout=3000)
    expect(filters_list).to_contain_text("My Test Filter")

    # Filter should also appear in Generate tab dropdown
    page.get_by_role("tab", name="Generate Report").click()
    select = page.locator("#generate-filter-select")
    options = select.locator("option")
    # At least 2 options: placeholder + saved filter
    count = options.count()
    assert count >= 2, f"Expected at least 2 options in dropdown, got {count}"


def test_remove_filter(page: Page, live_server_url: str):
    """Removing a saved filter makes it disappear from the list."""
    _mock_filters_api(page)
    _goto(page, live_server_url)
    page.evaluate("localStorage.removeItem('jira_saved_filters')")

    page.get_by_role("tab", name="Filter Builder").click()
    page.locator("#filter-name").fill("Temp Filter")
    _open_jql_builder(page)
    page.locator("#jira-project").fill("TEMP")
    _set_board_settings(page)
    page.locator("#btn-save-jira-filter").click()

    filters_list = page.locator("#filters-list")
    expect(filters_list.locator("li")).to_have_count(1, timeout=5000)

    # Click the Remove button on the filter
    filters_list.locator("li").first.get_by_role("button", name="Remove").click()
    expect(filters_list.locator("li")).to_have_count(0, timeout=3000)


# ---------------------------------------------------------------------------
# Group 6: Generate Tab — Report Generation
# ---------------------------------------------------------------------------


def test_generate_without_filter_selected(page: Page, live_server_url: str):
    """Generate without a filter selected shows error and marks dropdown invalid."""
    _goto(page, live_server_url)
    # Clear filters so dropdown has no selection
    page.evaluate("localStorage.removeItem('jira_saved_filters')")
    _goto(page, live_server_url)

    # Ensure Generate tab is active
    page.get_by_role("tab", name="Generate Report").click()
    select = page.locator("#generate-filter-select")
    # Ensure placeholder (empty value) is selected
    expect(select).to_have_value("")

    page.locator("#btn-generate").click()

    err = page.locator("#err-generate-filter")
    expect(err).to_have_class(re.compile(r"visible"))
    expect(select).to_have_class(re.compile(r"invalid"))


def test_generate_with_filter_sse_streaming(page: Page, live_server_url: str):
    """Generate with a filter triggers SSE, shows log output, re-enables button."""
    _mock_filters_api(page)
    _goto(page, live_server_url)
    page.evaluate("localStorage.removeItem('jira_saved_filters')")

    # First save a filter
    page.get_by_role("tab", name="Filter Builder").click()
    page.locator("#filter-name").fill("SSE Test Filter")
    _open_jql_builder(page)
    page.locator("#jira-project").fill("SSETEST")
    _set_board_settings(page)
    page.locator("#btn-save-jira-filter").click()

    # Wait for filter to be saved
    expect(page.locator("#filter-log-output")).to_contain_text("Saved", timeout=5000)

    # Switch to Generate tab and select the filter
    page.get_by_role("tab", name="Generate Report").click()
    select = page.locator("#generate-filter-select")
    # Select the first non-placeholder option
    page.wait_for_timeout(500)
    select.select_option(index=1)

    btn = page.locator("#btn-generate")
    page.locator("#btn-generate").click()

    # Button should show "Generating…" and be disabled
    expect(btn).to_contain_text("Generating", timeout=3000)
    expect(btn).to_be_disabled()

    # Log panel should get output (either success or error — we don't have Jira creds)
    log = page.locator("#log-output")
    expect(log).not_to_be_empty(timeout=3000)

    # Button should re-enable after SSE completes
    expect(btn).to_be_enabled(timeout=15000)


def test_log_clear_button(page: Page, live_server_url: str):
    """Clear button empties the log output panel."""
    _mock_filters_api(page)
    _goto(page, live_server_url)
    page.evaluate("localStorage.removeItem('jira_saved_filters')")

    # Save a filter and generate to produce log output
    page.get_by_role("tab", name="Filter Builder").click()
    page.locator("#filter-name").fill("Clear Test Filter")
    _open_jql_builder(page)
    page.locator("#jira-project").fill("CLR")
    _set_board_settings(page)
    page.locator("#btn-save-jira-filter").click()
    expect(page.locator("#filter-log-output")).to_contain_text("Saved", timeout=5000)

    page.get_by_role("tab", name="Generate Report").click()
    select = page.locator("#generate-filter-select")
    page.wait_for_timeout(500)
    select.select_option(index=1)
    page.locator("#btn-generate").click()

    # Wait for generation to complete
    log = page.locator("#log-output")
    expect(log).not_to_be_empty(timeout=3000)
    btn = page.locator("#btn-generate")
    expect(btn).to_be_enabled(timeout=15000)

    # Now clear
    page.locator("#btn-clear-log").click()
    expect(log).to_be_empty()


# ---------------------------------------------------------------------------
# Group 7: SSL Certificate Panel
# ---------------------------------------------------------------------------


def _mock_cert_status(page: Page, payload: dict) -> None:
    """Register a route mock for /api/cert-status returning *payload*."""
    page.route(
        "**/api/cert-status",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        ),
    )


def test_cert_status_badge_no_cert(page: Page, live_server_url: str):
    """When /api/cert-status reports no cert, the badge shows 'No certificate'."""
    _mock_cert_status(page, {"exists": False, "path": "certs/jira_ca_bundle.pem"})
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("No certificate", timeout=5000)


def test_cert_status_badge_valid_cert(page: Page, live_server_url: str):
    """When /api/cert-status reports a valid cert, the badge shows 'Valid'."""
    _mock_cert_status(
        page,
        {
            "exists": True,
            "path": "certs/jira_ca_bundle.pem",
            "valid": True,
            "expires_at": "2027-01-01T00:00:00+00:00",
            "days_remaining": 90,
            "subject": "CN=test.atlassian.net",
        },
    )
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("Valid", timeout=5000)


def test_fetch_cert_button_success(page: Page, live_server_url: str):
    """Clicking Fetch Certificate logs success and updates the badge to 'Valid'."""
    # First call (page load): no cert.  Second call (after fetch): cert valid.
    call_count = {"n": 0}

    def _cert_status_handler(route):
        call_count["n"] += 1
        if call_count["n"] == 1:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"exists": False, "path": "certs/jira_ca_bundle.pem"}),
            )
        else:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "exists": True,
                        "path": "certs/jira_ca_bundle.pem",
                        "valid": True,
                        "expires_at": "2027-01-01T00:00:00+00:00",
                        "days_remaining": 90,
                        "subject": "CN=test.atlassian.net",
                    }
                ),
            )

    page.route("**/api/cert-status", _cert_status_handler)
    page.route(
        "**/api/fetch-cert",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "path": "certs/jira_ca_bundle.pem", "host": "test.atlassian.net"}),
        ),
    )

    _goto(page, live_server_url)
    page.get_by_role("tab", name="Jira Connection").click()

    # Provide a Jira URL so the fetch button doesn't short-circuit
    page.locator("#jira-url").fill("https://test.atlassian.net")
    page.locator("#btn-fetch-cert").click()

    cert_log = page.locator("#cert-log-output")
    expect(cert_log).to_contain_text("Certificate saved", timeout=5000)

    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("Valid", timeout=5000)


# ---------------------------------------------------------------------------
# Group 8: Report Options — radios, checkboxes, localStorage, Generate state
# (RG-PT-001, RG-PT-004, RG-ET-001, RG-ET-004, RG-MT-001, RG-MT-005,
#  RG-MT-006, RG-RO-003)
# ---------------------------------------------------------------------------


def _open_report_options(page: Page) -> None:
    """Ensure the Report Options <details> panel is expanded."""
    details = page.locator("#report-options")
    if not details.get_attribute("open"):
        details.locator("summary").click()
        page.wait_for_timeout(200)


def _open_jql_builder(page: Page) -> None:
    """Expand the JQL Builder <details> so #jira-project is interactable."""
    details = page.locator("#filter-jql-builder")
    if not details.evaluate("el => el.open"):
        page.locator("#filter-jql-builder summary").click()


def _set_board_settings(page: Page, board_id: str = "42", sprint_count: str = "5") -> None:
    """Pre-populate board ID and sprint count so saveJiraFilter() validation passes."""
    page.evaluate(
        f"document.getElementById('jira-board-id').value = '{board_id}';"
        f"document.getElementById('sprint-count').value = '{sprint_count}';"
    )


def test_project_type_radios_visible(page: Page, live_server_url: str):
    """Filter Builder tab shows SCRUM / KANBAN radio buttons (RG-PT-001)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Filter Builder").click()

    scrum = page.locator('input[name="filter-project-type"][value="SCRUM"]')
    kanban = page.locator('input[name="filter-project-type"][value="KANBAN"]')
    expect(scrum).to_be_visible()
    expect(kanban).to_be_visible()
    # SCRUM is checked by default
    expect(scrum).to_be_checked()


def test_estimation_type_radios_visible(page: Page, live_server_url: str):
    """Filter Builder tab shows StoryPoints / JiraTickets radio buttons (RG-ET-001)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Filter Builder").click()

    sp = page.locator('input[name="filter-estimation-type"][value="StoryPoints"]')
    jt = page.locator('input[name="filter-estimation-type"][value="JiraTickets"]')
    expect(sp).to_be_visible()
    expect(jt).to_be_visible()
    # StoryPoints is checked by default
    expect(sp).to_be_checked()


def test_metric_toggle_checkboxes_visible(page: Page, live_server_url: str):
    """Generate tab shows metric toggle checkboxes, all checked by default (RG-MT-001)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Generate Report").click()
    _open_report_options(page)

    metric_ids = [
        "rpt-metric-velocity",
        "rpt-metric-ai-trend",
        "rpt-metric-ai-usage",
        "rpt-metric-dau",
        "rpt-metric-dau-trend",
    ]
    for mid in metric_ids:
        cb = page.locator(f"#{mid}")
        expect(cb).to_be_visible()
        expect(cb).to_be_checked()


def test_project_type_persists_in_localstorage(page: Page, live_server_url: str):
    """Project type selection persists across page reloads via localStorage (RG-PT-004)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Filter Builder").click()

    # Select KANBAN
    page.locator('input[name="filter-project-type"][value="KANBAN"]').check()
    page.wait_for_timeout(300)

    # Reload page (route mocks persist across navigation)
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("tab", name="Filter Builder").click()

    expect(page.locator('input[name="filter-project-type"][value="KANBAN"]')).to_be_checked()


def test_estimation_type_persists_in_localstorage(page: Page, live_server_url: str):
    """Estimation type selection persists across page reloads via localStorage (RG-ET-004)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Filter Builder").click()

    # Select JiraTickets
    page.locator('input[name="filter-estimation-type"][value="JiraTickets"]').check()
    page.wait_for_timeout(300)

    # Reload page
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("tab", name="Filter Builder").click()

    expect(page.locator('input[name="filter-estimation-type"][value="JiraTickets"]')).to_be_checked()


def test_metric_toggles_persist_in_localstorage(page: Page, live_server_url: str):
    """Metric toggle state persists across page reloads via localStorage (RG-MT-005)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Generate Report").click()
    _open_report_options(page)

    # Uncheck velocity and DAU
    page.locator("#rpt-metric-velocity").uncheck()
    page.locator("#rpt-metric-dau").uncheck()
    page.wait_for_timeout(300)

    # Reload page
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("tab", name="Generate Report").click()
    _open_report_options(page)

    expect(page.locator("#rpt-metric-velocity")).not_to_be_checked()
    expect(page.locator("#rpt-metric-dau")).not_to_be_checked()
    # Others remain checked
    expect(page.locator("#rpt-metric-ai-trend")).to_be_checked()


def test_generate_button_disabled_when_all_metrics_unchecked(page: Page, live_server_url: str):
    """Generate button is disabled when all metric checkboxes are unchecked (RG-MT-006)."""
    _goto(page, live_server_url)
    page.get_by_role("tab", name="Generate Report").click()
    _open_report_options(page)

    metric_ids = [
        "rpt-metric-velocity",
        "rpt-metric-ai-trend",
        "rpt-metric-ai-usage",
        "rpt-metric-dau",
        "rpt-metric-dau-trend",
    ]
    # Uncheck all metrics
    for mid in metric_ids:
        page.locator(f"#{mid}").uncheck()

    btn = page.locator("#btn-generate")
    expect(btn).to_be_disabled()

    # Error message visible
    err = page.locator("#err-no-metrics")
    expect(err).to_have_class(re.compile(r"visible"))

    # Re-check one — button should re-enable
    page.locator("#rpt-metric-velocity").check()
    expect(btn).to_be_enabled()


def test_reports_list_links_only_html(page: Page, live_server_url: str):
    """Reports list shows only HTML links, no MD files (RG-RO-003)."""
    # Override /api/reports to return entries with HTML files
    page.route(
        "**/api/reports",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "reports": [
                        {"ts": "2026-03-25T12-00-00", "html_file": "report.html"},
                        {"ts": "2026-03-24T10-00-00", "html_file": "report.html"},
                    ]
                }
            ),
        ),
    )
    page.route(
        "**/api/config",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "configured": True, "config": {}}),
        ),
    )
    page.goto(live_server_url, wait_until="domcontentloaded", timeout=5000)

    reports_list = page.locator("#reports-list")
    links = reports_list.locator("a")
    expect(links.first).to_be_visible(timeout=5000)

    count = links.count()
    assert count == 2, f"Expected 2 report links, got {count}"

    for i in range(count):
        href = links.nth(i).get_attribute("href") or ""
        assert href.endswith(".html"), f"Report link should be .html, got: {href}"
        assert ".md" not in href, f"Report link should not reference .md: {href}"


# ---------------------------------------------------------------------------
# Accessibility: ARIA attributes (NFR-A-002, NFR-A-003, NFR-A-004)
# ---------------------------------------------------------------------------


def test_dynamic_regions_have_aria_live(page: Page, live_server_url: str):
    """Key dynamic regions carry aria-live so screen readers announce updates (NFR-A-002)."""
    _goto(page, live_server_url)

    live_ids = [
        "log-output",
        "filter-log-output",
        "schema-status",
        "conn-status-badge",
        "save-confirm-conn",
        "cert-status-badge",
    ]
    for element_id in live_ids:
        locator = page.locator(f"#{element_id}")
        attr = locator.get_attribute("aria-live")
        assert attr in ("polite", "assertive"), (
            f"#{element_id} must have aria-live='polite' or 'assertive', got {attr!r}"
        )


def test_required_fields_have_aria_required(page: Page, live_server_url: str):
    """All required form inputs carry aria-required='true' (NFR-A-003)."""
    _goto(page, live_server_url)

    required_ids = [
        "generate-filter-select",
        "filter-name",
        "jira-url",
        "jira-email",
        "jira-token",
    ]
    for element_id in required_ids:
        expect(page.locator(f"#{element_id}")).to_have_attribute("aria-required", "true")


def test_decorative_icons_have_aria_hidden(page: Page, live_server_url: str):
    """All required-star spans carry aria-hidden='true' (NFR-A-004)."""
    _goto(page, live_server_url)

    stars = page.locator(".required-star")
    star_count = stars.count()
    assert star_count > 0, "Expected at least one .required-star element"

    for i in range(star_count):
        attr = stars.nth(i).get_attribute("aria-hidden")
        assert attr == "true", f".required-star[{i}] must have aria-hidden='true', got {attr!r}"
