"""Centralized logging configuration for the application.

Call setup_logging() once at the top of each entry point (main.py, server.py).
Every run writes a timestamped log file to generated/logs/app-YYYYMMDD-HHMMSS.log
and mirrors output to stdout.

Custom level SUCCESS (25) sits between INFO (20) and WARNING (30).
Usage: logging.getLogger(__name__).success("message")
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Custom SUCCESS level
# ---------------------------------------------------------------------------

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _success(self: logging.Logger, message: str, *args: object, **kwargs: object) -> None:
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


logging.Logger.success = _success  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "generated" / "logs"


def setup_logging() -> tuple[logging.Logger, Path]:
    """Configure the root logger with a file handler and a stream handler.

    Creates generated/logs/ if it does not exist.
    Returns (root_logger, log_file_path).
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = _LOG_DIR / f"app-{timestamp}.log"

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    return root, log_file
