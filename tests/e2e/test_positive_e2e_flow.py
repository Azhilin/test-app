"""Positive end-to-end user flow for the AI Adoption Manager.

Covers the complete sequential journey a first-time user would follow:
  Phase 1 — App launch: page loads with correct title and active tab
  Phase 2 — Jira Connection: fill credentials → test → save
  Phase 3 — Filter Builder: name + project → save → filter appears in list
  Phase 4 — Data Retrieval: board ID + sprint count → save → preview sprints
  Phase 5 — Generate Report: select filter → SSE stream → report link appears

Run:
    pytest tests/e2e/test_positive_e2e_flow.py -v
    pytest tests/e2e/test_positive_e2e_flow.py -v --headed
"""

from __future__ import annotations

import json
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import _goto, _mock_filters_api, _mock_schemas_api

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------

_JIRA_URL = "https://test.atlassian.net"
_JIRA_EMAIL = "test@example.com"
_JIRA_TOKEN = "test-api-token-abc123"
_PROJECT_KEY = "TEST"
_FILTER_NAME = "E2E Sprint Filter"
_BOARD_ID = "42"
_SPRINT_COUNT = "5"
_REPORT_TS = "2026-04-07T12-00-00"

# SSE body satisfies two JS patterns in runGenerateSSE():
#   1. data.match(/generated[\\/]reports[\\/]([\dT:-]+)[\\/]/)  → sets lastReportTs
#   2. /reports written/i.test(data) + .html match             → sets lastHtmlFile
_SSE_BODY = (
    "data: Starting report generation\n\n"
    "data: Fetching sprint data\n\n"
    f"data: Reports written: generated/reports/{_REPORT_TS}/report.html, "
    f"generated/reports/{_REPORT_TS}/report.md\n\n"
    "event: done\ndata: \n\n"
)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


@allure.feature("End-to-End User Journey")
@allure.story("Positive flow: from app launch to report generation")
@allure.severity(allure.severity_level.BLOCKER)
def test_positive_end_to_end_flow(page: Page, live_server_url: str) -> None:
    """Complete positive user journey: configure → filter → preview → generate."""

    # ------------------------------------------------------------------
    # Phase 1 — App Launch
    # ------------------------------------------------------------------
    with allure.step("Phase 1 — App launch: set up boot mocks and navigate"):
        # Schemas and filters must be mocked before _goto so that the boot-time
        # loadSchemas() / loadFilters() calls resolve immediately.
        _mock_schemas_api(page, schemas=[], details_by_name={})
        _mock_filters_api(page)
        page.route(
            "**/api/cert-status",
            lambda r: r.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"exists": False}),
            ),
        )
        _goto(page, live_server_url)

        expect(page).to_have_title("AI Adoption Manager")
        expect(page.locator("#tab-generate")).to_have_attribute("aria-selected", "true")
        expect(page.locator("#panel-generate")).to_be_visible()

    # ------------------------------------------------------------------
    # Phase 2 — Jira Connection
    # ------------------------------------------------------------------
    with allure.step("Phase 2 — Jira Connection: fill credentials, test, save"):
        page.route(
            "**/api/test-connection",
            lambda r: r.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "ok": True,
                        "displayName": "Test User",
                        "emailAddress": _JIRA_EMAIL,
                    }
                ),
            ),
        )
        # POST /api/config override (GET is already mocked by _goto)
        page.route(
            "**/api/config",
            lambda r: (
                r.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"ok": True}),
                )
                if r.request.method == "POST"
                else r.continue_()
            ),
        )

        with allure.step("Navigate to Connection tab"):
            page.get_by_role("tab", name="Jira Connection").click()
            expect(page.locator("#panel-connection")).to_be_visible()

        with allure.step("Fill credentials"):
            page.locator("#jira-url").fill(_JIRA_URL)
            page.locator("#jira-email").fill(_JIRA_EMAIL)
            page.locator("#jira-token").fill(_JIRA_TOKEN)

        with allure.step("Test Connection → badge shows Connected"):
            page.locator("#btn-test-conn").click()
            expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10_000)

        with allure.step("Save credentials → confirmation flash appears"):
            expect(page.locator("#btn-save-conn")).to_be_enabled()
            page.locator("#btn-save-conn").click()
            expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=5_000)

        with allure.step("Assert credentials persisted to localStorage"):
            assert page.evaluate("localStorage.getItem('jira_url')") == _JIRA_URL
            assert page.evaluate("localStorage.getItem('jira_email')") == _JIRA_EMAIL

    # ------------------------------------------------------------------
    # Phase 3 — Filter Builder
    # ------------------------------------------------------------------
    with allure.step("Phase 3 — Filter Builder: save a filter"):
        # _mock_filters_api is already registered from Phase 1 boot setup.

        with allure.step("Navigate to Filter Builder tab"):
            page.get_by_role("tab", name="Filter Builder").click()
            expect(page.locator("#panel-filter")).to_be_visible()

        with allure.step("Enter filter name and project key"):
            page.locator("#filter-jql-builder summary").click()
            page.locator("#filter-name").fill(_FILTER_NAME)
            page.locator("#jira-project").fill(_PROJECT_KEY)

        with allure.step("Enter board ID and sprint count"):
            page.locator("#filter-board-settings summary").click()
            page.locator("#jira-board-id").fill(_BOARD_ID)
            page.locator("#sprint-count").fill(_SPRINT_COUNT)

        with allure.step("Click Save Filter"):
            page.locator("#btn-save-jira-filter").click()

        with allure.step("Assert filter log shows JQL and Saved confirmation"):
            expect(page.locator("#filter-log-output")).to_contain_text(f"project = {_PROJECT_KEY}", timeout=5_000)
            expect(page.locator("#filter-log-output")).to_contain_text("Saved", timeout=5_000)

        with allure.step("Assert filter appears in the saved filters list"):
            expect(page.locator("#filters-list").locator("li")).to_have_count(1, timeout=5_000)
            expect(page.locator("#filters-list")).to_contain_text(_FILTER_NAME)

    # ------------------------------------------------------------------
    # Phase 4 — Board Settings
    # ------------------------------------------------------------------
    with allure.step("Phase 4 — Board Settings: save board ID and sprint count"):
        # Board settings (jira-board-id, sprint-count) live in the Filter Builder tab
        # inside the collapsible #filter-board-settings section. Fields were already
        # filled in Phase 3; clicking Save Data Settings persists them to the server.
        with allure.step("Click Save Data Settings → confirmation flash appears"):
            page.locator("#btn-save-data").click()
            expect(page.locator("#save-confirm-data")).to_have_class(re.compile(r"visible"), timeout=5_000)

    # ------------------------------------------------------------------
    # Phase 5 — Generate Report
    # ------------------------------------------------------------------
    with allure.step("Phase 5 — Generate Report: select filter, run, assert report link"):
        page.route(
            "**/api/generate**",
            lambda r: r.fulfill(
                status=200,
                content_type="text/event-stream; charset=utf-8",
                headers={"Cache-Control": "no-cache"},
                body=_SSE_BODY,
            ),
        )
        # Override the empty /api/reports mock set by _goto with the post-generate list.
        page.route(
            "**/api/reports",
            lambda r: r.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"reports": [{"ts": _REPORT_TS, "html_file": "report.html"}]}),
            ),
        )

        with allure.step("Navigate to Generate Report tab"):
            page.get_by_role("tab", name="Generate Report").click()
            expect(page.locator("#panel-generate")).to_be_visible()

        with allure.step("Select saved filter from dropdown"):
            gen_select = page.locator("#generate-filter-select")
            expect(gen_select).to_contain_text(_FILTER_NAME, timeout=5_000)
            gen_select.select_option(label=_FILTER_NAME)
            expect(gen_select).not_to_have_class(re.compile(r"invalid"))

        with allure.step("Click Generate Report → button enters busy state"):
            btn = page.locator("#btn-generate")
            btn.click()
            expect(btn).to_be_disabled(timeout=5_000)
            expect(btn).to_contain_text("Generating")

        with allure.step("Assert SSE output streams into log"):
            log = page.locator("#log-output")
            expect(log).to_contain_text("Starting report generation", timeout=10_000)
            expect(log).to_contain_text("Reports written")

        with allure.step("Assert generation completes and button re-enables"):
            expect(log).to_contain_text("Done", timeout=10_000)
            expect(btn).to_be_enabled(timeout=10_000)

        with allure.step("Assert report link appears in Last Generated Reports"):
            reports_list = page.locator("#reports-list")
            expect(reports_list.locator("li")).to_have_count(1, timeout=10_000)
            link = reports_list.locator("a").first
            expect(link).to_be_visible()
            href = link.get_attribute("href") or ""
            assert _REPORT_TS in href, f"Report link href should contain timestamp, got: {href!r}"
            assert href.endswith(".html"), f"Report link should be .html, got: {href!r}"
