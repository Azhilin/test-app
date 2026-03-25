"""Tests for main.py helper functions."""
from __future__ import annotations

from main import _timestamp_folder_name


def test_timestamp_folder_name_valid_iso():
    result = _timestamp_folder_name("2026-03-18T17:27:30+00:00")
    assert result == "2026-03-18T17-27-30"


def test_timestamp_folder_name_empty_string():
    result = _timestamp_folder_name("")
    assert result == "report"


def test_timestamp_folder_name_none():
    result = _timestamp_folder_name(None)
    assert result == "report"
