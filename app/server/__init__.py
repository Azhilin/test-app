#!/usr/bin/env python3
"""
app.server package — HTTP dev server for the AI Adoption Metrics UI.

Usage:
    python server.py          # listens on http://localhost:8080
    python server.py 9000     # custom port
"""

import logging
import os as _os
import ssl  # noqa: F401
import subprocess  # noqa: F401  # nosec B404
import urllib  # noqa: F401
import urllib.request  # noqa: F401
import webbrowser
from pathlib import Path

from dotenv import dotenv_values as _dotenv_values
from dotenv import dotenv_values as dotenv_values

# Merge defaults (committed) and secrets (.env): .env wins over defaults.env,
# but both yield to values already present in os.environ (tests / CI).
# MUST run before importing ._base so HOST/PORT are populated when _base reads os.environ.
_srv_root = Path(__file__).resolve().parent.parent.parent
for _k, _v in {
    **_dotenv_values(_srv_root / "config" / "defaults.env"),
    **_dotenv_values(_srv_root / ".env"),
}.items():
    if _k not in _os.environ and _v is not None:
        _os.environ[_k] = _v

# Re-exported for backward-compatible test patching (mirrors old flat-module namespace).
# Tests patch e.g. srv.subprocess.Popen, srv.urllib.request.urlopen, srv.ssl.create_default_context,
# srv.config.JIRA_SSL_CERT, and srv.dotenv_values.  Importing the module objects here makes those
# attribute paths valid; patching them affects the real objects seen by all submodules.
from app.core import config as config  # noqa: E402, I001

from ._base import (  # noqa: E402
    _CLIENT_DISCONNECT as _CLIENT_DISCONNECT,
    guess_mime as guess_mime,
    HandlerBase,
    HOST,
    MIME as MIME,
    PORT,
    ROOT as ROOT,
    Server,
)
from .cert_handlers import CertHandlerMixin  # noqa: E402
from .config_handlers import ConfigHandlerMixin  # noqa: E402
from .connection_handlers import ConnectionHandlerMixin  # noqa: E402
from .data_handlers import DataHandlerMixin  # noqa: E402
from .filter_handlers import FilterHandlerMixin  # noqa: E402
from .generate_handlers import GenerateHandlerMixin  # noqa: E402
from .schema_handlers import SchemaHandlerMixin  # noqa: E402

logger = logging.getLogger(__name__)


class Handler(
    ConnectionHandlerMixin,
    ConfigHandlerMixin,
    CertHandlerMixin,
    SchemaHandlerMixin,
    FilterHandlerMixin,
    DataHandlerMixin,
    GenerateHandlerMixin,
    HandlerBase,
):
    pass


def run(port: int = PORT, host: str = HOST) -> None:
    """Start the HTTP server on the given port."""
    server = Server((host, port), Handler)
    url = f"http://localhost:{port}" if host in {"127.0.0.1", "localhost"} else f"http://{host}:{port}"
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
