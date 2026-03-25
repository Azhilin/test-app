"""Smoke tests: confirm all app.* modules import cleanly and expose expected callables."""
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_import_app_config():
    from app import config
    assert callable(config.validate_config)


def test_import_app_metrics():
    from app import metrics
    assert callable(metrics.compute_velocity)
    assert callable(metrics.compute_cycle_time)
    assert callable(metrics.build_metrics_dict)
    assert callable(metrics.get_done_issue_keys_for_changelog)


def test_import_app_report_md():
    from app import report_md
    assert callable(report_md.generate_md)
    assert callable(report_md._md_table)


def test_import_app_report_html():
    from app import report_html
    assert callable(report_html.generate_html)
    assert report_html.TEMPLATES_DIR.is_dir()


def test_import_app_jira_client():
    from app import jira_client
    assert callable(jira_client.create_client)
    assert callable(jira_client.fetch_sprint_data)


def test_main_imports_resolve():
    """Import main.py via importlib without executing it — confirms 'from app import ...' resolves."""
    main_path = Path(__file__).resolve().parent.parent / "main.py"
    spec = importlib.util.spec_from_file_location("main", main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
    assert callable(module._parse_args)
