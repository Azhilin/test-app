#!/usr/bin/env python3
"""
app.server package — HTTP dev server for the AI Adoption Metrics UI.

Usage:
    python server.py          # listens on http://localhost:8080
    python server.py 9000     # custom port
"""

import logging
import webbrowser

from dotenv import load_dotenv

# load_dotenv() MUST be called before importing ._base so that HOST/PORT
# in _base.py read the .env-populated os.environ values.
load_dotenv()

from ._base import (  # noqa: E402
    ROOT,
    HOST,
    PORT,
    MIME,
    _CLIENT_DISCONNECT,
    guess_mime,
    HandlerBase,
    Server,
)
from .connection_handlers import ConnectionHandlerMixin
from .config_handlers import ConfigHandlerMixin
from .cert_handlers import CertHandlerMixin
from .schema_handlers import SchemaHandlerMixin
from .filter_handlers import FilterHandlerMixin
from .generate_handlers import GenerateHandlerMixin

# Re-exported for backward-compatible test patching (mirrors old flat-module namespace).
# Tests patch e.g. srv.subprocess.Popen, srv.urllib.request.urlopen, srv.ssl.create_default_context,
# srv.config.JIRA_SSL_CERT, and srv.dotenv_values.  Importing the module objects here makes those
# attribute paths valid; patching them affects the real objects seen by all submodules.
import ssl  # noqa: E402
import subprocess  # noqa: E402
import urllib  # noqa: E402
import urllib.request  # noqa: E402

from app.core import config  # noqa: E402
from dotenv import dotenv_values  # noqa: E402

logger = logging.getLogger(__name__)


class Handler(
    ConnectionHandlerMixin,
    ConfigHandlerMixin,
    CertHandlerMixin,
    SchemaHandlerMixin,
    FilterHandlerMixin,
    GenerateHandlerMixin,
    HandlerBase,
):
    pass


def run(port: int = PORT, host: str = HOST) -> None:
    """Start the HTTP server on the given port."""
    server = Server((host, port), Handler)
    url = (
        f"http://localhost:{port}"
        if host in {"127.0.0.1", "localhost"}
        else f"http://{host}:{port}"
    )
    logger.info("AI Adoption Metrics — dev server")
    logger.info("Listening on %s", url)
    logger.info("Press Ctrl+C to stop.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")


if __name__ == "__main__":
    run()