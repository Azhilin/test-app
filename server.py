"""Entry point — delegates to app.server."""
import sys

from app.server import run, Server, Handler, PORT, ROOT, MIME, guess_mime  # re-exported for tests
from app.utils.logging_setup import setup_logging

if __name__ == "__main__":
    _logger, _log_file = setup_logging()
    _logger.info("AI Adoption Metrics — starting dev server")
    _logger.info("Log file: %s", _log_file)
    run()
