"""E2E-layer fixtures and shared helpers."""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.request

import allure
import pytest
from playwright.sync_api import Page


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


# ---------------------------------------------------------------------------
# Browser launch configuration — headless by default
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, request):
    """Ensure tests always run headless; pass --headed to debug visually."""
    headed = request.config.getoption("--headed", default=False)
    return {**browser_type_launch_args, "headless": not headed}


@pytest.fixture
def page(page):
    """Yield the Playwright page and explicitly close it after each test."""
    yield page
    page.close()


# ---------------------------------------------------------------------------
# Allure screenshots — captured for every E2E test (pass and fail)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Shared UI helpers — used by test_e2e_ui.py and test_positive_e2e_flow.py
# ---------------------------------------------------------------------------


def _goto(page: Page, url: str) -> None:
    """Navigate with domcontentloaded wait and retry for flaky server."""
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
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return
        except Exception:
            if attempt == 2:
                raise


def _mock_schemas_api(page: Page, schemas: list[str] | None = None, details_by_name: dict | None = None) -> None:
    """Mock /api/schemas endpoints with support for both GET list and GET by-name routes."""
    if schemas is None:
        schemas = ["Default_Jira_Cloud"]
    if details_by_name is None:
        details_by_name = {
            "Default_Jira_Cloud": {
                "schema_name": "Default_Jira_Cloud",
                "fields": {"story_points": {"id": "customfield_10016", "type": "number"}},
            }
        }

    def _handle_schemas(route):
        url = route.request.url
        if "name=" in url:
            name_idx = url.find("name=") + 5
            name = url[name_idx:].split("&")[0]
            name = name.split("%20")[0] if "%" in name else name
            schema = details_by_name.get(name)
            if schema:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"ok": True, "schema": schema}),
                )
            else:
                route.fulfill(
                    status=404,
                    content_type="application/json",
                    body=json.dumps({"ok": False, "error": f"Schema '{name}' not found"}),
                )
        else:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"ok": True, "schemas": schemas}),
            )

    page.route("**/api/schemas**", _handle_schemas)


def _mock_filters_api(page: Page) -> None:
    """Intercept /api/filters with a stateful mock that tracks saved/deleted filters."""
    saved_filters: list[dict] = []

    def _handle_post(route):
        body = route.request.post_data_json
        name = body.get("name", "filter") if body else "filter"
        params = body.get("params", {}) if body else {}
        project = params.get("JIRA_PROJECT", "TEST")
        jql = f"project = {project} AND status = Done AND sprint in closedSprints()"
        slug = name.lower().replace(" ", "_")
        entry = {
            "filter_name": name,
            "slug": slug,
            "is_default": False,
            "jql": jql,
            "created_at": "2026-03-25T12:00:00",
            "params": params,
        }
        idx = next(
            (i for i, f in enumerate(saved_filters) if f["filter_name"].lower() == name.lower()),
            None,
        )
        updated = idx is not None
        if updated:
            saved_filters[idx] = entry
        else:
            saved_filters.append(entry)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "ok": True,
                    "updated": updated,
                    "jql": jql,
                    "slug": slug,
                    "created_at": "2026-03-25T12:00:00",
                }
            ),
        )

    def _handle_get(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True, "filters": list(saved_filters)}),
        )

    def _handle_delete(route):
        url = route.request.url
        slug = url.split("/api/filters/")[-1].split("?")[0]
        to_remove = [f for f in saved_filters if f.get("slug") == slug]
        for f in to_remove:
            saved_filters.remove(f)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"ok": True}),
        )

    page.route(
        "**/api/filters", lambda route: _handle_post(route) if route.request.method == "POST" else _handle_get(route)
    )
    page.route("**/api/filters/**", _handle_delete)


# ---------------------------------------------------------------------------
# Allure screenshots
# ---------------------------------------------------------------------------


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take a full-page screenshot after the test body runs and attach to Allure.

    Uses pytest_runtest_makereport so the ``page`` fixture is still alive
    when the screenshot is captured (fixture teardown has not started yet).
    Only fires during the ``call`` phase (the actual test body) and only for
    tests that have a ``page`` fixture.
    """
    yield
    if call.when != "call":
        return
    if "page" not in item.fixturenames:
        return
    try:
        page = item.funcargs.get("page")
        if page is None:
            return
        screenshot = page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=item.name,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        pass
