"""E2E-layer fixtures."""
from __future__ import annotations

import sys
import threading
import time
import urllib.request

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
