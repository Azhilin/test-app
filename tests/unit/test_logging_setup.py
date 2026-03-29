"""Unit tests for app.utils.logging_setup.

Covers: SUCCESS level registration, .success() method injection,
setup_logging() return values, file/directory creation, log level,
handler attachment, format, and SUCCESS-level file output.
"""

import logging
import re

import pytest

import app.utils.logging_setup as logging_setup
from app.utils.logging_setup import SUCCESS_LEVEL, setup_logging


# ---------------------------------------------------------------------------
# Fixture: reset root logger state around every test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_root_logger():
    """Save and restore root logger state so tests cannot bleed into each other.

    Without this fixture, each call to setup_logging() adds handlers to the
    module-level root logger, causing handler accumulation across tests and
    Windows file-lock errors when pytest tries to clean up tmp_path.
    """
    root = logging.getLogger()
    original_level = root.level
    original_handlers = root.handlers[:]
    yield
    # Remove any handlers added during the test and close them
    for handler in root.handlers[:]:
        if handler not in original_handlers:
            root.removeHandler(handler)
            handler.close()
    root.handlers[:] = original_handlers
    root.level = original_level


# ---------------------------------------------------------------------------
# SUCCESS level constants
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_success_level_value():
    assert SUCCESS_LEVEL == 25


@pytest.mark.unit
def test_success_level_name_registered():
    assert logging.getLevelName(SUCCESS_LEVEL) == "SUCCESS"


@pytest.mark.unit
def test_logger_has_success_method():
    logger = logging.getLogger("test.success_method")
    assert callable(getattr(logger, "success", None))


# ---------------------------------------------------------------------------
# setup_logging() return values
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_setup_logging_returns_logger_and_path(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    result = setup_logging()
    assert isinstance(result, tuple) and len(result) == 2
    logger, log_file = result
    assert isinstance(logger, logging.Logger)
    from pathlib import Path
    assert isinstance(log_file, Path)


@pytest.mark.unit
def test_setup_logging_creates_log_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    _, log_file = setup_logging()
    assert log_file.exists()


@pytest.mark.unit
def test_setup_logging_log_filename_matches_pattern(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    _, log_file = setup_logging()
    assert re.match(r"app-\d{8}-\d{6}\.log$", log_file.name)


@pytest.mark.unit
def test_setup_logging_creates_log_directory(tmp_path, monkeypatch):
    nested = tmp_path / "deeply" / "nested" / "logs"
    monkeypatch.setattr(logging_setup, "_LOG_DIR", nested)
    setup_logging()
    assert nested.is_dir()


# ---------------------------------------------------------------------------
# Root logger configuration
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_setup_logging_sets_debug_level(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    logger, _ = setup_logging()
    assert logger.level == logging.DEBUG


@pytest.mark.unit
def test_setup_logging_attaches_file_handler(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    logger, _ = setup_logging()
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) >= 1


@pytest.mark.unit
def test_setup_logging_attaches_stream_handler(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    logger, _ = setup_logging()
    stream_handlers = [
        h for h in logger.handlers
        if type(h) is logging.StreamHandler
    ]
    assert len(stream_handlers) >= 1


# ---------------------------------------------------------------------------
# Log format
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_log_file_format(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    _, log_file = setup_logging()

    test_logger = logging.getLogger("test.format")
    test_logger.info("format check message")

    # Flush all handlers so the write is visible on disk
    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert re.search(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[INFO\] format check message",
        content,
    )


# ---------------------------------------------------------------------------
# SUCCESS-level file output
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_success_level_message_written_to_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)
    _, log_file = setup_logging()

    test_logger = logging.getLogger("test.success_output")
    test_logger.success("pipeline complete")  # type: ignore[attr-defined]

    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert "[SUCCESS] pipeline complete" in content


# ---------------------------------------------------------------------------
# Security: credentials must not appear in log output
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_credentials_not_in_log_output(tmp_path, monkeypatch):
    """JIRA_API_TOKEN, JIRA_EMAIL, and JIRA_URL values must never appear in logs."""
    fake_token = "s3cr3t-api-tok3n"
    fake_email = "user@example.com"
    fake_url = "https://jira.example.com"

    monkeypatch.setenv("JIRA_API_TOKEN", fake_token)
    monkeypatch.setenv("JIRA_EMAIL", fake_email)
    monkeypatch.setenv("JIRA_URL", fake_url)
    monkeypatch.setattr(logging_setup, "_LOG_DIR", tmp_path)

    _, log_file = setup_logging()

    test_logger = logging.getLogger("test.credentials")
    test_logger.info("Starting pipeline run")
    test_logger.info("Connecting to Jira instance")

    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert fake_token not in content
    assert fake_email not in content
    assert fake_url not in content
