"""Unit tests for app.cli.main orchestration branches."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

import app.cli as cli

pytestmark = pytest.mark.unit


def test_main_returns_1_when_config_invalid(monkeypatch, capsys):
    create_client = MagicMock()

    monkeypatch.setattr(cli.config, "validate_config", lambda: ["JIRA_URL is not set"])
    monkeypatch.setattr(cli.jira_client, "create_client", create_client)
    monkeypatch.setattr("sys.argv", ["main.py"])

    rc = cli.main()

    assert rc == 1
    assert "Config error: JIRA_URL is not set" in capsys.readouterr().err
    create_client.assert_not_called()


def test_main_returns_1_when_fetch_sprint_data_fails(monkeypatch, capsys):
    mock_jira = object()

    monkeypatch.setattr(cli.config, "validate_config", lambda: [])
    monkeypatch.setattr(cli.jira_client, "create_client", lambda: mock_jira)
    monkeypatch.setattr(
        cli.jira_client,
        "fetch_sprint_data",
        lambda jira: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr("sys.argv", ["main.py"])

    rc = cli.main()

    assert rc == 1
    assert "Failed to fetch Jira data: boom" in capsys.readouterr().err


def test_main_keeps_running_when_filter_name_lookup_fails(monkeypatch, tmp_path):
    mock_jira = MagicMock()
    mock_jira._session.get.side_effect = RuntimeError("filter lookup failed")
    captured_metrics: list[dict] = []

    def _capture_html(metrics_dict, output_path):
        captured_metrics.append(metrics_dict.copy())

    monkeypatch.setattr(cli.config, "validate_config", lambda: [])
    monkeypatch.setattr(cli.config, "JIRA_FILTER_ID", 42)
    monkeypatch.setattr(cli.jira_client, "create_client", lambda: mock_jira)
    monkeypatch.setattr(cli.jira_client, "fetch_sprint_data", lambda jira: ([], {}))
    monkeypatch.setattr(cli.metrics, "get_done_issue_keys_for_changelog", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        cli.metrics,
        "build_metrics_dict",
        lambda *args, **kwargs: {
            "generated_at": "2026-03-26T10:00:00+00:00",
            "velocity": [],
            "cycle_time": {"sample_size": 0, "values": []},
            "custom_trends": [],
        },
    )
    monkeypatch.setattr(cli.jira_client, "get_filter_jql", lambda jira: "project = TEST")
    monkeypatch.setattr(cli.report_html, "generate_html", _capture_html)
    monkeypatch.setattr(cli.report_md, "generate_md", lambda metrics_dict, output_path: None)
    monkeypatch.setattr(cli, "REPORTS_DIR", tmp_path / "generated" / "reports")
    monkeypatch.setattr("sys.argv", ["main.py"])

    rc = cli.main()

    assert rc == 0
    assert captured_metrics
    assert captured_metrics[0]["filter_id"] == 42
    assert captured_metrics[0]["filter_jql"] == "project = TEST"
    assert "filter_name" not in captured_metrics[0]


# ---------------------------------------------------------------------------
# Parallel report generation (NFR-P-002)
# ---------------------------------------------------------------------------


def test_main_generates_reports_in_parallel(monkeypatch, tmp_path):
    """main() must use ThreadPoolExecutor(max_workers=2) for parallel report generation."""
    monkeypatch.setattr(cli.config, "validate_config", lambda: [])
    monkeypatch.setattr(cli.config, "JIRA_FILTER_ID", None)
    monkeypatch.setattr(cli.jira_client, "create_client", lambda: MagicMock())
    monkeypatch.setattr(cli.jira_client, "fetch_sprint_data", lambda jira: ([], {}))
    monkeypatch.setattr(cli.metrics, "get_done_issue_keys_for_changelog", lambda *a, **kw: [])
    monkeypatch.setattr(
        cli.metrics,
        "build_metrics_dict",
        lambda *a, **kw: {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "velocity": [],
            "cycle_time": {"sample_size": 0, "values": []},
            "custom_trends": [],
        },
    )
    monkeypatch.setattr(cli.report_html, "generate_html", lambda m, p: None)
    monkeypatch.setattr(cli.report_md, "generate_md", lambda m, p: None)
    monkeypatch.setattr(cli, "REPORTS_DIR", tmp_path / "generated" / "reports")
    monkeypatch.setattr("sys.argv", ["main.py"])

    with patch("app.cli.ThreadPoolExecutor", wraps=ThreadPoolExecutor) as mock_tpe:
        rc = cli.main()

    assert rc == 0
    mock_tpe.assert_called_once_with(max_workers=2)
