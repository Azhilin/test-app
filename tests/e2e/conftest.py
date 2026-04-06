"""E2E-layer fixtures."""

from __future__ import annotations

import sys
import threading
import time
import urllib.request

import allure
import pytest


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
