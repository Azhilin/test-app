"""Playwright E2E tests for the Jira Connection tab new functionality.

Covers:
  - Required-field red asterisk visibility
  - Save button disabled by default / enabled only after successful Test Connection
  - Field pre-population from GET /api/config (server-side .env values)
  - Status badge transitions (Testing → Connected / Error)
  - Save button enables after successful test; resets on field edit
  - Save POST payload correctness and flash confirmation
  - Corner cases: partial fields, token placeholder, token-with-equals round-trip

Run:
    pytest tests/e2e/test_e2e_connection.py -v
    pytest tests/e2e/test_e2e_connection.py -v --headed   # visual debug
"""

from __future__ import annotations

import json
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMPTY_CONFIG = {"ok": True, "configured": False, "config": {}}
_FULL_CONFIG = {
    "ok": True,
    "configured": True,
    "config": {
        "JIRA_URL": "https://prefilled.atlassian.net",
        "JIRA_EMAIL": "prefilled@example.com",
        "JIRA_API_TOKEN": "***",
    },
}
_TEST_CONN_SUCCESS = {"ok": True, "displayName": "Alice Smith", "emailAddress": "alice@example.com"}
_TEST_CONN_401 = {"ok": False, "httpStatus": 401, "error": "Unauthorized"}
_TEST_CONN_403 = {"ok": False, "httpStatus": 403, "error": "Forbidden"}


def _goto(page: Page, url: str, config: dict | None = None, cert_status: dict | None = None) -> None:
    """Navigate to the app, mocking /api/config, /api/reports, /api/filters, and /api/cert-status."""
    cfg = config if config is not None else _EMPTY_CONFIG
    cs = cert_status if cert_status is not None else {"exists": False, "path": "certs/jira_ca_bundle.pem"}
    page.route(
        "**/api/cert-status",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(cs),
        ),
    )
    page.route(
        "**/api/config",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(cfg),
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
    page.route(
        "**/api/filters",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"filters": []}),
        ),
    )
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return
        except Exception:
            if attempt == 2:
                raise


def _open_connection_tab(page: Page) -> None:
    page.get_by_role("tab", name="Jira Connection").click()


def _mock_test_conn(page: Page, response: dict, status: int = 200) -> None:
    page.route(
        "**/api/test-connection",
        lambda route: route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(response),
        ),
    )


def _fill_credentials(
    page: Page, url: str = "https://test.atlassian.net", email: str = "user@example.com", token: str = "test-token-abc"
) -> None:
    page.locator("#jira-url").fill(url)
    page.locator("#jira-email").fill(email)
    page.locator("#jira-token").fill(token)


def _run_test_connection_and_wait_success(page: Page) -> None:
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10000)


def _mock_cert_status(page: Page, response: dict, status: int = 200) -> None:
    """Route /api/cert-status to return a fixed JSON response."""
    page.route(
        "**/api/cert-status",
        lambda route: route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(response),
        ),
    )


def _mock_fetch_cert(page: Page, response: dict, status: int = 200) -> None:
    """Route /api/fetch-cert to return a fixed JSON response."""
    page.route(
        "**/api/fetch-cert",
        lambda route: route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(response),
        ),
    )


# ---------------------------------------------------------------------------
# Group 1: Required-field asterisks
# ---------------------------------------------------------------------------


def test_required_star_visible_on_jira_url_label(page: Page, live_server_url: str):
    """The Jira URL label has a visible red asterisk marking it as required."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    star = page.locator("label[for='jira-url'] .required-star")
    expect(star).to_be_visible()
    expect(star).to_have_text("*")


def test_required_star_visible_on_email_label(page: Page, live_server_url: str):
    """The User Email label has a visible red asterisk."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    star = page.locator("label[for='jira-email'] .required-star")
    expect(star).to_be_visible()
    expect(star).to_have_text("*")


def test_required_star_visible_on_token_label(page: Page, live_server_url: str):
    """The API Token label has a visible red asterisk."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    star = page.locator("label[for='jira-token'] .required-star")
    expect(star).to_be_visible()
    expect(star).to_have_text("*")


# ---------------------------------------------------------------------------
# Group 2: Save button — disabled on load
# ---------------------------------------------------------------------------


def test_save_button_disabled_on_load_with_empty_config(page: Page, live_server_url: str):
    """Save is disabled on page load when no config is set."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_save_button_disabled_on_load_even_with_prefilled_config(page: Page, live_server_url: str):
    """Save is disabled even when fields are pre-populated from server — Test Connection not yet run."""
    _goto(page, live_server_url, config=_FULL_CONFIG)
    _open_connection_tab(page)
    # Fields are filled but connectedOk is still false
    expect(page.locator("#btn-save-conn")).to_be_disabled()


# ---------------------------------------------------------------------------
# Group 3: Pre-population from GET /api/config
# ---------------------------------------------------------------------------


def test_fields_prepopulated_from_server_config(page: Page, live_server_url: str):
    """URL and email fields are populated from the server config on load."""
    _goto(page, live_server_url, config=_FULL_CONFIG)
    _open_connection_tab(page)
    expect(page.locator("#jira-url")).to_have_value("https://prefilled.atlassian.net")
    expect(page.locator("#jira-email")).to_have_value("prefilled@example.com")


def test_token_placeholder_updated_when_server_token_exists(page: Page, live_server_url: str):
    """When server returns '***' for token, placeholder text changes to indicate a saved token."""
    _goto(page, live_server_url, config=_FULL_CONFIG)
    _open_connection_tab(page)
    token_input = page.locator("#jira-token")
    # The token field should be empty (masked on server) but placeholder updated
    expect(token_input).to_have_value("")
    placeholder = token_input.get_attribute("placeholder")
    assert placeholder and "saved" in placeholder.lower(), (
        f"Expected placeholder to mention saved token, got: {placeholder!r}"
    )


def test_fields_empty_when_config_not_configured(page: Page, live_server_url: str):
    """All three fields are empty when server config returns no values."""
    _goto(page, live_server_url, config=_EMPTY_CONFIG)
    _open_connection_tab(page)
    expect(page.locator("#jira-url")).to_have_value("")
    expect(page.locator("#jira-email")).to_have_value("")
    expect(page.locator("#jira-token")).to_have_value("")


def test_partial_config_populates_only_present_fields(page: Page, live_server_url: str):
    """Only fields present in the server config are filled; absent fields remain empty."""
    partial_config = {
        "ok": True,
        "configured": False,
        "config": {"JIRA_URL": "https://partial.atlassian.net"},
    }
    _goto(page, live_server_url, config=partial_config)
    _open_connection_tab(page)
    expect(page.locator("#jira-url")).to_have_value("https://partial.atlassian.net")
    expect(page.locator("#jira-email")).to_have_value("")


# ---------------------------------------------------------------------------
# Group 4: Test Connection → status badge transitions
# ---------------------------------------------------------------------------


def test_badge_shows_connected_on_success(page: Page, live_server_url: str):
    """Badge transitions to 'Connected' after a successful Test Connection."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10000)
    expect(page.locator("#conn-status-detail")).to_contain_text("Alice Smith")


def test_badge_shows_error_on_401(page: Page, live_server_url: str):
    """Badge shows 'Error' and mentions authentication failure for a 401 response."""
    _mock_test_conn(page, _TEST_CONN_401)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Error", timeout=10000)
    expect(page.locator("#conn-status-detail")).to_contain_text("Authentication failed")


def test_badge_shows_error_on_403(page: Page, live_server_url: str):
    """Badge shows 'Error' and mentions access denied for a 403 response."""
    _mock_test_conn(page, _TEST_CONN_403)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Error", timeout=10000)
    expect(page.locator("#conn-status-detail")).to_contain_text("403")


def test_badge_shows_error_when_fields_empty(page: Page, live_server_url: str):
    """Clicking Test Connection with empty fields shows error badge without hitting the server."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    page.locator("#jira-url").fill("")
    page.locator("#jira-email").fill("")
    page.locator("#jira-token").fill("")
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Error")
    expect(page.locator("#conn-status-detail")).to_contain_text("Fill in URL, email")


# ---------------------------------------------------------------------------
# Group 5: Save button gate — enabled / disabled logic
# ---------------------------------------------------------------------------


def test_save_enabled_after_successful_test_connection(page: Page, live_server_url: str):
    """Save button becomes enabled after all fields filled and Test Connection succeeds."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)
    expect(page.locator("#btn-save-conn")).to_be_enabled()


def test_save_remains_disabled_after_failed_test_connection(page: Page, live_server_url: str):
    """Save button stays disabled when Test Connection returns an error."""
    _mock_test_conn(page, _TEST_CONN_401)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Error", timeout=10000)
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_save_disabled_after_editing_url_following_success(page: Page, live_server_url: str):
    """Editing the URL field after a successful test resets connectedOk and disables Save."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)
    expect(page.locator("#btn-save-conn")).to_be_enabled()

    # Edit URL — should reset connectedOk
    page.locator("#jira-url").fill("https://changed.atlassian.net")
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_save_disabled_after_editing_email_following_success(page: Page, live_server_url: str):
    """Editing the email field after a successful test resets connectedOk and disables Save."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)
    expect(page.locator("#btn-save-conn")).to_be_enabled()

    page.locator("#jira-email").fill("new@email.com")
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_save_disabled_after_editing_token_following_success(page: Page, live_server_url: str):
    """Editing the token field after a successful test resets connectedOk and disables Save."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)
    expect(page.locator("#btn-save-conn")).to_be_enabled()

    page.locator("#jira-token").fill("new-token")
    expect(page.locator("#btn-save-conn")).to_be_disabled()


def test_save_not_enabled_when_token_missing_despite_success(page: Page, live_server_url: str):
    """Save stays disabled when token is empty even after a successful test (all fields required)."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    page.locator("#jira-url").fill("https://test.atlassian.net")
    page.locator("#jira-email").fill("user@example.com")
    page.locator("#jira-token").fill("")  # token empty
    page.locator("#btn-test-conn").click()
    # Test Connection is blocked client-side when fields are missing
    expect(page.locator("#conn-status-badge")).to_have_text("Error")
    expect(page.locator("#btn-save-conn")).to_be_disabled()


# ---------------------------------------------------------------------------
# Group 6: Save button → POST to /api/config + flash confirmation
# ---------------------------------------------------------------------------


def test_save_posts_correct_payload(page: Page, live_server_url: str):
    """Clicking Save sends the correct JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN to POST /api/config."""
    captured: list[dict] = []

    def _intercept_config_post(route):
        body = route.request.post_data_json or {}
        captured.append(body)
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True}))

    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)

    # Override the config route for POSTs only (GET already mocked by _goto)
    page.route(
        "**/api/config",
        lambda route: (
            _intercept_config_post(route)
            if route.request.method == "POST"
            else route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(_EMPTY_CONFIG),
            )
        ),
    )

    _open_connection_tab(page)
    _fill_credentials(page, url="https://save-test.atlassian.net", email="save@test.com", token="savetoken123")
    _run_test_connection_and_wait_success(page)
    page.locator("#btn-save-conn").click()

    # Wait for save-confirm flash
    expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=3000)

    assert len(captured) == 1, f"Expected 1 POST to /api/config, got {len(captured)}"
    payload = captured[0]
    assert payload.get("JIRA_URL") == "https://save-test.atlassian.net"
    assert payload.get("JIRA_EMAIL") == "save@test.com"
    assert payload.get("JIRA_API_TOKEN") == "savetoken123"


def test_save_shows_flash_confirmation(page: Page, live_server_url: str):
    """'Settings saved' flash appears after clicking Save."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)
    page.locator("#btn-save-conn").click()
    expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=3000)


def test_save_with_new_token_sends_real_token(page: Page, live_server_url: str):
    """When saving with a newly typed token, the POST payload contains the typed token verbatim.

    The server pre-loads URL and email (JIRA_API_TOKEN='***' → hasServerToken=true). The user
    types a new token, passes Test Connection, then saves. JIRA_API_TOKEN in the POST body must
    be the new token value, not '***'.
    """
    captured: list[dict] = []

    def _intercept_config_post(route):
        body = route.request.post_data_json or {}
        captured.append(body)
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True}))

    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url, config=_FULL_CONFIG)
    page.route(
        "**/api/config",
        lambda route: (
            _intercept_config_post(route)
            if route.request.method == "POST"
            else route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(_FULL_CONFIG),
            )
        ),
    )

    _open_connection_tab(page)
    page.locator("#jira-token").fill("newtoken456")
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10000)

    page.locator("#btn-save-conn").click()
    expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=3000)

    assert len(captured) >= 1
    assert captured[-1].get("JIRA_API_TOKEN") == "newtoken456"


def test_save_with_server_token_sends_star_token(page: Page, live_server_url: str):
    """When JIRA_API_TOKEN is saved on the server ('***') and the user leaves the token field
    empty, Test Connection proceeds (hasServerToken=true bypasses the empty-token guard) and
    Save POSTs '***' as JIRA_API_TOKEN — signaling the server to keep the existing stored token.
    """
    captured: list[dict] = []

    def _intercept_config_post(route):
        body = route.request.post_data_json or {}
        captured.append(body)
        route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True}))

    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url, config=_FULL_CONFIG)
    page.route(
        "**/api/config",
        lambda route: (
            _intercept_config_post(route)
            if route.request.method == "POST"
            else route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(_FULL_CONFIG),
            )
        ),
    )

    _open_connection_tab(page)
    # Token field empty — hasServerToken=true means the guard allows Test Connection
    expect(page.locator("#jira-token")).to_have_value("")
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10000)
    expect(page.locator("#btn-save-conn")).to_be_enabled()

    page.locator("#btn-save-conn").click()
    expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=3000)

    assert len(captured) >= 1
    assert captured[-1].get("JIRA_API_TOKEN") == "***", (
        f"Expected '***' when preserving server token, got {captured[-1].get('JIRA_API_TOKEN')!r}"
    )


# ---------------------------------------------------------------------------
# Group 7: Corner cases
# ---------------------------------------------------------------------------


def test_can_re_test_after_field_edit_to_re_enable_save(page: Page, live_server_url: str):
    """After editing a field (disabling Save), running Test Connection again re-enables Save."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)
    expect(page.locator("#btn-save-conn")).to_be_enabled()

    # Edit → Save disabled
    page.locator("#jira-url").fill("https://changed.atlassian.net")
    expect(page.locator("#btn-save-conn")).to_be_disabled()

    # Re-run Test Connection → Save re-enabled
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10000)
    expect(page.locator("#btn-save-conn")).to_be_enabled()


def test_save_persists_values_to_localstorage(page: Page, live_server_url: str):
    """After Save, field values are stored in localStorage."""
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page, url="https://ls-test.atlassian.net", email="ls@test.com", token="lstoken")
    _run_test_connection_and_wait_success(page)
    page.locator("#btn-save-conn").click()
    expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=3000)

    stored_url = page.evaluate("localStorage.getItem('jira_url')")
    stored_email = page.evaluate("localStorage.getItem('jira_email')")
    assert stored_url == "https://ls-test.atlassian.net"
    assert stored_email == "ls@test.com"


def test_badge_neutral_on_initial_load(page: Page, live_server_url: str):
    """Status badge shows neutral/configured state on initial load, not 'Connected'."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    badge = page.locator("#conn-status-badge")
    # Should be neutral or "Configured", never "Connected" without an actual test
    badge_text = badge.inner_text()
    assert badge_text not in ("Connected",), (
        f"Badge should not show 'Connected' on load without running Test Connection; got {badge_text!r}"
    )


def test_multiple_test_connection_attempts_last_result_wins(page: Page, live_server_url: str):
    """Running Test Connection twice with different mock outcomes reflects the last result."""
    call_count = [0]

    def _flaky(route):
        call_count[0] += 1
        if call_count[0] == 1:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(_TEST_CONN_401))
        else:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(_TEST_CONN_SUCCESS))

    page.route("**/api/test-connection", _flaky)
    _goto(page, live_server_url)
    _open_connection_tab(page)
    _fill_credentials(page)

    # First attempt → error
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Error", timeout=10000)
    expect(page.locator("#btn-save-conn")).to_be_disabled()

    # Second attempt → success
    page.locator("#btn-test-conn").click()
    expect(page.locator("#conn-status-badge")).to_have_text("Connected", timeout=10000)
    expect(page.locator("#btn-save-conn")).to_be_enabled()


# ---------------------------------------------------------------------------
# Group 8: Reload persistence (NFR-U-002)
# ---------------------------------------------------------------------------


def test_saved_credentials_prefill_on_reload(page: Page, live_server_url: str):
    """URL and email fields are re-populated from server config after a page reload."""
    _goto(page, live_server_url, config=_FULL_CONFIG)
    _open_connection_tab(page)
    # Verify initial prefill
    expect(page.locator("#jira-url")).to_have_value("https://prefilled.atlassian.net")
    expect(page.locator("#jira-email")).to_have_value("prefilled@example.com")

    # Reload the page — route intercepts remain active so /api/config still returns _FULL_CONFIG
    page.reload(wait_until="domcontentloaded")
    _open_connection_tab(page)

    # Fields must still be prefilled from the server config after reload
    expect(page.locator("#jira-url")).to_have_value("https://prefilled.atlassian.net")
    expect(page.locator("#jira-email")).to_have_value("prefilled@example.com")


# ---------------------------------------------------------------------------
# Group 9: SSL / TLS Certificate section
# ---------------------------------------------------------------------------

_NO_CERT_STATUS = {"exists": False, "path": "certs/jira_ca_bundle.pem"}
_VALID_CERT_STATUS = {
    "exists": True,
    "valid": True,
    "days_remaining": 30,
    "path": "certs/jira_ca_bundle.pem",
    "expires_at": "2026-12-31",
    "subject": "CN=*.atlassian.net",
}
_EXPIRING_CERT_STATUS = {**_VALID_CERT_STATUS, "days_remaining": 5}
_EXPIRED_CERT_STATUS = {
    "exists": True,
    "valid": False,
    "path": "certs/jira_ca_bundle.pem",
    "expires_at": "2025-01-01",
    "subject": "CN=*.atlassian.net",
}
_UNREADABLE_CERT_STATUS = {
    "exists": True,
    "valid": False,
    "expires_at": None,
    "days_remaining": None,
    "subject": None,
    "error": "Permission denied reading cert file",
    "path": "certs/jira_ca_bundle.pem",
}


def test_cert_badge_shows_no_certificate_when_no_cert(page: Page, live_server_url: str):
    """Badge shows 'No certificate' (neutral) when /api/cert-status returns exists=false."""
    _goto(page, live_server_url, cert_status=_NO_CERT_STATUS)
    _open_connection_tab(page)
    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("No certificate", timeout=5000)
    expect(badge).to_have_class(re.compile(r"badge-neutral"))


def test_cert_badge_shows_valid_when_cert_valid(page: Page, live_server_url: str):
    """Badge shows 'Valid' (success) when cert exists, is valid, and expires in > 7 days."""
    _goto(page, live_server_url, cert_status=_VALID_CERT_STATUS)
    _open_connection_tab(page)
    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("Valid", timeout=5000)
    expect(badge).to_have_class(re.compile(r"badge-success"))


def test_cert_badge_shows_expiring_soon(page: Page, live_server_url: str):
    """Badge shows 'Expiring soon · Nd' (warning) when days_remaining <= 7."""
    _goto(page, live_server_url, cert_status=_EXPIRING_CERT_STATUS)
    _open_connection_tab(page)
    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("Expiring soon \u00b7 5d", timeout=5000)
    expect(badge).to_have_class(re.compile(r"badge-warning"))


def test_cert_badge_shows_expired_when_cert_invalid(page: Page, live_server_url: str):
    """Badge shows 'Certificate expired' (error) when cert exists but valid=false."""
    _goto(page, live_server_url, cert_status=_EXPIRED_CERT_STATUS)
    _open_connection_tab(page)
    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("Certificate expired", timeout=5000)
    expect(badge).to_have_class(re.compile(r"badge-error"))


def test_cert_badge_shows_unreadable_on_error(page: Page, live_server_url: str):
    """Badge shows 'Certificate unreadable' (error) when cert-status returns an error key."""
    _goto(page, live_server_url, cert_status=_UNREADABLE_CERT_STATUS)
    _open_connection_tab(page)
    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("Certificate unreadable", timeout=5000)
    expect(badge).to_have_class(re.compile(r"badge-error"))


def test_fetch_cert_button_label_is_fetch_when_no_cert(page: Page, live_server_url: str):
    """Fetch Certificate button shows 'Fetch Certificate' text when no cert exists."""
    _goto(page, live_server_url, cert_status=_NO_CERT_STATUS)
    _open_connection_tab(page)
    expect(page.locator("#btn-fetch-cert")).to_contain_text("Fetch Certificate", timeout=5000)


def test_fetch_cert_button_label_is_refresh_when_cert_valid(page: Page, live_server_url: str):
    """Fetch Certificate button shows 'Refresh Certificate' text when a valid cert exists."""
    _goto(page, live_server_url, cert_status=_VALID_CERT_STATUS)
    _open_connection_tab(page)
    expect(page.locator("#btn-fetch-cert")).to_contain_text("Refresh Certificate", timeout=5000)


def test_fetch_cert_requires_url_to_be_filled(page: Page, live_server_url: str):
    """Clicking Fetch Certificate without a Jira URL shows a warning in the cert log."""
    _goto(page, live_server_url)  # _EMPTY_CONFIG — jira-url field is empty
    _open_connection_tab(page)
    page.locator("#btn-fetch-cert").click()
    expect(page.locator("#cert-log-output")).to_contain_text("Enter the Jira URL", timeout=3000)


def test_fetch_cert_success_updates_badge(page: Page, live_server_url: str):
    """After a successful POST /api/fetch-cert, loadCertStatus re-runs and badge shows Valid."""
    _mock_fetch_cert(page, {"ok": True, "path": "certs/jira_ca_bundle.pem"})
    _goto(page, live_server_url, cert_status=_NO_CERT_STATUS)
    _open_connection_tab(page)
    expect(page.locator("#cert-status-badge")).to_have_text("No certificate", timeout=5000)

    # Override cert-status so the post-fetch reload returns a valid cert
    _mock_cert_status(page, _VALID_CERT_STATUS)
    page.locator("#jira-url").fill("https://test.atlassian.net")
    page.locator("#btn-fetch-cert").click()
    expect(page.locator("#cert-status-badge")).to_have_text("Valid", timeout=8000)


def test_fetch_cert_failure_shows_error_in_log(page: Page, live_server_url: str):
    """When POST /api/fetch-cert returns ok=false, the error message appears in the cert log."""
    _mock_fetch_cert(page, {"ok": False, "error": "Connection timed out"})
    _goto(page, live_server_url)
    _open_connection_tab(page)
    page.locator("#jira-url").fill("https://test.atlassian.net")
    page.locator("#btn-fetch-cert").click()
    expect(page.locator("#cert-log-output")).to_contain_text("Connection timed out", timeout=5000)


def test_btn_clear_cert_log_clears_log_output(page: Page, live_server_url: str):
    """Clicking the Clear button empties the certificate log."""
    _goto(page, live_server_url)
    _open_connection_tab(page)
    # Generate a log entry by clicking Fetch with no URL filled
    page.locator("#btn-fetch-cert").click()
    expect(page.locator("#cert-log-output")).to_contain_text("Enter the Jira URL", timeout=3000)

    page.locator("#btn-clear-cert-log").click()
    expect(page.locator("#cert-log-output")).to_have_text("")


# ---------------------------------------------------------------------------
# Group 10: Positive E2E acceptance tests (JCR-SSL-006, JCR-SSL-007)
# ---------------------------------------------------------------------------


def test_positive_e2e_no_cert_is_acceptable_state(page: Page, live_server_url: str):
    """Full positive E2E: absent cert file (neutral badge) is a valid operational state.

    Steps: load Connection tab → badge shows 'No certificate' (neutral) → fill credentials
    → Test Connection succeeds → Save button enabled → save confirmation appears.
    Cert badge must remain neutral throughout — no cert is required for standard Jira Cloud.
    Covers JCR-SSL-007.
    """
    _mock_test_conn(page, _TEST_CONN_SUCCESS)
    _goto(page, live_server_url, cert_status=_NO_CERT_STATUS)
    _open_connection_tab(page)

    # Cert badge is neutral — this is an acceptable, non-error state
    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("No certificate", timeout=5000)
    expect(badge).to_have_class(re.compile(r"badge-neutral"))

    _fill_credentials(page)
    _run_test_connection_and_wait_success(page)

    # Save is now enabled — cert absence did not block it
    expect(page.locator("#btn-save-conn")).to_be_enabled()
    page.locator("#btn-save-conn").click()
    expect(page.locator("#save-confirm-conn")).to_have_class(re.compile(r"visible"), timeout=3000)

    # Cert badge has not changed to an error state
    expect(badge).not_to_have_class(re.compile(r"badge-error"))


def test_positive_e2e_fetch_cert_then_badge_shows_valid(page: Page, live_server_url: str):
    """Full positive E2E: Fetch Certificate → badge transitions from 'No certificate' to 'Valid'.

    Steps: load with no cert → badge neutral → fill URL → click Fetch Certificate
    → /api/fetch-cert returns ok=true → /api/cert-status re-polled → badge shows 'Valid'.
    Covers JCR-SSL-006.
    """
    _mock_fetch_cert(page, {"ok": True, "path": "certs/jira_ca_bundle.pem"})
    _goto(page, live_server_url, cert_status=_NO_CERT_STATUS)
    _open_connection_tab(page)

    badge = page.locator("#cert-status-badge")
    expect(badge).to_have_text("No certificate", timeout=5000)

    # Override cert-status so the post-fetch reload returns a valid cert
    _mock_cert_status(page, _VALID_CERT_STATUS)

    page.locator("#jira-url").fill("https://test.atlassian.net")
    page.locator("#btn-fetch-cert").click()

    expect(badge).to_have_text("Valid", timeout=8000)
    expect(badge).to_have_class(re.compile(r"badge-success"))

