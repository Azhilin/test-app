"""Entry point — delegates to app.cli."""
import sys

from app.cli import main, _parse_args, _timestamp_folder_name  # re-exported for tests
from app.utils.logging_setup import setup_logging

if __name__ == "__main__":
    _logger, _log_file = setup_logging()
    _logger.info("AI Adoption Metrics — starting CLI run")
    _logger.info("Log file: %s", _log_file)
    sys.exit(main())
