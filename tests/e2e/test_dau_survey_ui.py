"""Playwright E2E tests for ui/dau_survey.html.

These tests load the standalone survey form via file:// URL and verify
page load, username validation, progress tracking, radio card interaction,
submit flow, and localStorage persistence.

Run:
    pytest tests/e2e/test_dau_survey_ui.py -v
    pytest tests/e2e/test_dau_survey_ui.py -v --headed
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SURVEY_URL = (Path(__file__).resolve().parents[2] / "ui" / "dau_survey.html").as_uri()

# Replaces window.showDirectoryPicker with a mock that stores written data in
# window.__savedFiles so tests can inspect the saved JSON payload.
# Also clears localStorage to prevent bleed between tests.
_SETUP_SCRIPT = """
    localStorage.clear();
    window.__savedFiles = {};
    window.showDirectoryPicker = async () => ({
        name: 'survey-folder',
        getFileHandle: async (name, _opts) => ({
            name: name,
            createWritable: async () => ({
                write: async (data) => { window.__savedFiles[name] = data; },
                close: async () => {}
            })
        })
    });
"""

# Same mock but WITHOUT clearing localStorage — used by the persistence test.
_MOCK_ONLY = """
    window.__savedFiles = {};
    window.showDirectoryPicker = async () => ({
        name: 'survey-folder',
        getFileHandle: async (name, _opts) => ({
            name: name,
            createWritable: async () => ({
                write: async (data) => { window.__savedFiles[name] = data; },
                close: async () => {}
            })
        })
    });
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _goto(page: Page) -> None:
    """Load the survey with FS API mocked and localStorage cleared."""
    page.add_init_script(_SETUP_SCRIPT)
    page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=15000)


def _fill_all(
    page: Page,
    username: str = "alice123",
    role: str = "Developer",
    card_index: int = 0,
) -> None:
    """Fill all three fields so the form reaches a fully valid state."""
    page.locator("#input-username").fill(username)
    page.locator("#select-role").select_option(value=role)
    page.locator(".radio-card").nth(card_index).click()


# ---------------------------------------------------------------------------
# Group 1: Page Load & Layout
# ---------------------------------------------------------------------------


def test_survey_page_loads_with_title(page: Page) -> None:
    """Page loads with the correct <title> and <h1>."""
    _goto(page)
    expect(page).to_have_title("AI Tool Usage Survey")
    expect(page.locator("h1")).to_have_text("AI Tool Usage Survey")


def test_form_visible_and_confirmation_hidden_on_load(page: Page) -> None:
    """Survey form is visible and the confirmation screen is hidden on load."""
    _goto(page)
    expect(page.locator("#survey-form")).to_be_visible()
    expect(page.locator("#confirmation")).to_be_hidden()


def test_submit_button_initially_disabled(page: Page) -> None:
    """Submit button is disabled before any fields are filled."""
    _goto(page)
    expect(page.locator("#btn-submit")).to_be_disabled()


# ---------------------------------------------------------------------------
# Group 2: Progress Bar
# ---------------------------------------------------------------------------


def test_progress_starts_at_zero(page: Page) -> None:
    """Progress label shows '0 of 3 answered' and bar width is 0% on load."""
    _goto(page)
    expect(page.locator("#progress-count")).to_have_text("0 of 3 answered")
    width = page.locator("#progress-fill").evaluate("el => el.style.width")
    assert width == "0%"


def test_progress_increments_with_each_field(page: Page) -> None:
    """Progress count advances 1 → 2 → 3 as each field is completed."""
    _goto(page)
    with allure.step("Fill username — expect progress '1 of 3 answered'"):
        page.locator("#input-username").fill("alice123")
        expect(page.locator("#progress-count")).to_have_text("1 of 3 answered")
    with allure.step("Select role — expect progress '2 of 3 answered'"):
        page.locator("#select-role").select_option(value="Developer")
        expect(page.locator("#progress-count")).to_have_text("2 of 3 answered")
    with allure.step("Click radio card — expect progress '3 of 3 answered'"):
        page.locator(".radio-card").first.click()
        expect(page.locator("#progress-count")).to_have_text("3 of 3 answered")


# ---------------------------------------------------------------------------
# Group 3: Username Validation
# ---------------------------------------------------------------------------


def test_username_valid_input_applies_valid_class(page: Page) -> None:
    """A valid alphanumeric username gets the is-valid class and no error text."""
    _goto(page)
    inp = page.locator("#input-username")
    inp.fill("alice123")
    expect(inp).to_have_class(re.compile(r"is-valid"))
    expect(page.locator("#username-error")).to_have_text("")


def test_username_rejects_underscore(page: Page) -> None:
    """Username containing '_' shows an inline error and gets is-error class."""
    _goto(page)
    inp = page.locator("#input-username")
    inp.fill("alice_123")
    expect(inp).to_have_class(re.compile(r"is-error"))
    expect(page.locator("#username-error")).to_contain_text("Only letters and digits are allowed")


def test_username_rejects_space(page: Page) -> None:
    """Username containing a space shows an inline error."""
    _goto(page)
    inp = page.locator("#input-username")
    inp.fill("alice 123")
    expect(inp).to_have_class(re.compile(r"is-error"))
    expect(page.locator("#username-error")).to_contain_text("Only letters and digits are allowed")


def test_username_too_short_shows_error(page: Page) -> None:
    """Single-character username triggers the 'at least 2 characters' error."""
    _goto(page)
    inp = page.locator("#input-username")
    inp.fill("a")
    expect(inp).to_have_class(re.compile(r"is-error"))
    expect(page.locator("#username-error")).to_contain_text("at least 2")


# ---------------------------------------------------------------------------
# Group 4: Submit Button State
# ---------------------------------------------------------------------------


def test_submit_enabled_only_when_all_fields_are_valid(page: Page) -> None:
    """Submit button stays disabled with 2 of 3 fields and enables at 3 of 3."""
    _goto(page)
    page.locator("#input-username").fill("alice123")
    page.locator("#select-role").select_option(value="Developer")
    expect(page.locator("#btn-submit")).to_be_disabled()
    page.locator(".radio-card").first.click()
    expect(page.locator("#btn-submit")).to_be_enabled()


# ---------------------------------------------------------------------------
# Group 5: Radio Card Selection
# ---------------------------------------------------------------------------


def test_radio_card_click_marks_it_selected(page: Page) -> None:
    """Clicking the second radio card adds 'selected' only to that card."""
    _goto(page)
    cards = page.locator(".radio-card")
    cards.nth(1).click()
    expect(cards.nth(1)).to_have_class(re.compile(r"selected"))
    expect(cards.nth(0)).not_to_have_class(re.compile(r"selected"))
    expect(cards.nth(2)).not_to_have_class(re.compile(r"selected"))


def test_radio_card_keyboard_navigation(page: Page) -> None:
    """ArrowDown key moves selection from the first to the second radio card."""
    _goto(page)
    # Focus the first hidden radio input directly via JS to bypass visibility check.
    page.evaluate("document.querySelectorAll('.radio-card input')[0].focus()")
    page.keyboard.press("ArrowDown")
    expect(page.locator(".radio-card").nth(1)).to_have_class(re.compile(r"selected"))


# ---------------------------------------------------------------------------
# Group 6: Submit & Confirmation
# ---------------------------------------------------------------------------


def test_submit_hides_form_and_shows_confirmation(page: Page) -> None:
    """Clicking submit replaces the form with the confirmation screen."""
    _goto(page)
    _fill_all(page)
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    expect(page.locator("#survey-form")).to_be_hidden()


def test_confirmation_displays_submitted_data(page: Page) -> None:
    """Confirmation table reflects the exact username and role that were submitted."""
    _goto(page)
    _fill_all(page, username="bob42", role="QA / Test Engineer")
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    expect(page.locator("#conf-username")).to_have_text("bob42")
    expect(page.locator("#conf-role")).to_have_text("QA / Test Engineer")


def test_submit_writes_valid_json_to_mocked_fs(page: Page) -> None:
    """After submit the mocked FS receives valid JSON with all required fields."""
    _goto(page)
    _fill_all(page, username="charlie99")
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    raw = page.evaluate("() => Object.values(window.__savedFiles)[0]")
    assert raw is not None, "No file was written to the mocked FS"
    data = json.loads(raw)
    assert data["username"] == "charlie99"
    assert data["role"] == "Developer"
    assert data["usage"] == "Every day (5 days)"
    assert data["score"] == 5
    assert "timestamp" in data
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$", data["timestamp"]), (
        f"timestamp format unexpected: {data['timestamp']}"
    )
    assert "week" in data
    assert re.match(r"^\d{4}-W\d{2}$", data["week"]), f"week format unexpected: {data['week']}"


def test_submit_timestamp_format(page: Page) -> None:
    """Timestamp in saved JSON must be ISO 8601 +00:00 format, no milliseconds."""
    _goto(page)
    _fill_all(page)
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    raw = page.evaluate("() => Object.values(window.__savedFiles)[0]")
    assert raw is not None
    data = json.loads(raw)
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$",
        data["timestamp"],
    ), f"Bad timestamp format: {data['timestamp']}"


def test_submit_week_field_format(page: Page) -> None:
    """Saved JSON must contain 'week' field in YYYY-WNN format."""
    _goto(page)
    _fill_all(page)
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    raw = page.evaluate("() => Object.values(window.__savedFiles)[0]")
    assert raw is not None
    data = json.loads(raw)
    assert "week" in data, "'week' field missing from payload"
    assert re.match(r"^\d{4}-W\d{2}$", data["week"]), f"Bad week format: {data['week']}"


# ---------------------------------------------------------------------------
# Group 7: localStorage
# ---------------------------------------------------------------------------


def test_username_saved_to_localstorage_after_submit(page: Page) -> None:
    """Username is persisted in localStorage when submit succeeds."""
    _goto(page)
    _fill_all(page, username="dave77")
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    stored = page.evaluate("() => localStorage.getItem('dau_username')")
    assert stored == "dave77"


def test_username_restored_from_localstorage_on_page_load(page: Page) -> None:
    """A username stored in localStorage is pre-filled in the input on load."""
    page.add_init_script(_MOCK_ONLY + "\nlocalStorage.setItem('dau_username', 'eve88');")
    page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=15000)
    expect(page.locator("#input-username")).to_have_value("eve88")


# ---------------------------------------------------------------------------
# Group 8: Filename, FS API Fallback & Error Handling (DAU-F-010 to F-014)
# ---------------------------------------------------------------------------


def test_filename_matches_dau_username_timestamp_pattern(page: Page) -> None:
    """Saved filename follows dau_<username>_<timestamp>.json pattern (DAU-F-014)."""
    _goto(page)
    _fill_all(page, username="alice123")
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    filename = page.evaluate("() => Object.keys(window.__savedFiles)[0]")
    assert filename is not None
    assert re.match(r"^dau_alice123_\d{8}T\d{6}Z\.json$", filename), f"Unexpected filename: {filename}"


def test_fs_api_abort_keeps_form_intact(page: Page) -> None:
    """AbortError from showDirectoryPicker leaves the form visible (DAU-F-012)."""
    page.add_init_script(
        "localStorage.clear();"
        "window.__savedFiles = {};"
        "window.showDirectoryPicker = async () => {"
        "  throw new DOMException('User aborted', 'AbortError');"
        "};"
    )
    page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=15000)
    _fill_all(page)
    page.locator("#btn-submit").click()
    page.wait_for_timeout(500)
    expect(page.locator("#survey-form")).to_be_visible()
    expect(page.locator("#confirmation")).to_be_hidden()


def test_fs_api_non_abort_error_falls_back_to_download(page: Page) -> None:
    """Non-AbortError from showDirectoryPicker silently falls back to download (DAU-F-013)."""
    page.add_init_script(
        "localStorage.clear();"
        "window.__savedFiles = {};"
        "window.__downloadClicked = false;"
        "window.showDirectoryPicker = async () => { throw new Error('disk full'); };"
        "var _origClick = HTMLAnchorElement.prototype.click;"
        "HTMLAnchorElement.prototype.click = function() {"
        "  window.__downloadClicked = true;"
        "  _origClick.call(this);"
        "};"
    )
    page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=15000)
    _fill_all(page)
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    clicked = page.evaluate("() => window.__downloadClicked")
    assert clicked is True, "Browser download fallback was not triggered"


def test_fs_api_unavailable_falls_back_to_download(page: Page) -> None:
    """When showDirectoryPicker is undefined the app uses browser download (DAU-F-011)."""
    page.add_init_script(
        "localStorage.clear();"
        "window.__savedFiles = {};"
        "window.__downloadClicked = false;"
        "delete window.showDirectoryPicker;"
        "var _origClick = HTMLAnchorElement.prototype.click;"
        "HTMLAnchorElement.prototype.click = function() {"
        "  window.__downloadClicked = true;"
        "  _origClick.call(this);"
        "};"
    )
    page.goto(SURVEY_URL, wait_until="domcontentloaded", timeout=15000)
    _fill_all(page)
    page.locator("#btn-submit").click()
    expect(page.locator("#confirmation")).to_be_visible(timeout=3000)
    clicked = page.evaluate("() => window.__downloadClicked")
    assert clicked is True, "Browser download fallback was not triggered"
