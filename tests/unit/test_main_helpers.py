"""Tests for main.py helper functions."""
from __future__ import annotations

import pytest

import sys
from unittest.mock import patch

from main import _timestamp_folder_name, _parse_args

pytestmark = pytest.mark.unit


def test_timestamp_folder_name_valid_iso():
    result = _timestamp_folder_name("2026-03-18T17:27:30+00:00")
    assert result == "2026-03-18T17-27-30"


def test_timestamp_folder_name_empty_string():
    result = _timestamp_folder_name("")
    assert result == "report"


def test_timestamp_folder_name_none():
    result = _timestamp_folder_name(None)
    assert result == "report"


def test_parse_args_no_args():
    with patch.object(sys, "argv", ["main.py"]):
        args = _parse_args()
    assert args.clean is False


def test_parse_args_clean_flag():
    with patch.object(sys, "argv", ["main.py", "--clean"]):
        args = _parse_args()
    assert args.clean is True
