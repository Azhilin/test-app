"""Unit tests for compute_dau_metrics() and the DAU integration with build_metrics_dict().

Requirements covered:
    DAU-F-017, DAU-F-018, DAU-F-019, DAU-F-020, DAU-F-021, DAU-F-022
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from app.core.metrics import compute_dau_metrics

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(dirpath: Path, filename: str, payload: dict) -> None:
    """Write a DAU response JSON file to dirpath."""
    (dirpath / filename).write_text(json.dumps(payload), encoding="utf-8")


def _response(username: str, usage: str, role: str = "Developer") -> dict:
    return {"username": username, "role": role, "usage": usage}


# ---------------------------------------------------------------------------
# DAU-F-017: reads all dau_*.json files
# ---------------------------------------------------------------------------


def test_empty_dir_returns_zero_count(tmp_path: Path) -> None:
    result = compute_dau_metrics(tmp_path)
    assert result["response_count"] == 0
    assert result["team_avg"] is None
    assert result["by_role"] == []
    assert result["breakdown"] == []


def test_missing_dir_returns_zero_count(tmp_path: Path) -> None:
    result = compute_dau_metrics(tmp_path / "nonexistent")
    assert result["response_count"] == 0
    assert result["team_avg"] is None


def test_three_response_files_counted(tmp_path: Path) -> None:
    for i in range(3):
        _write(tmp_path, f"dau_user{i}_20260101T000000Z.json", _response(f"user{i}", "Not used"))
    result = compute_dau_metrics(tmp_path)
    assert result["response_count"] == 3


def test_non_dau_files_are_ignored(tmp_path: Path) -> None:
    """Files not matching dau_*.json should not be read."""
    _write(tmp_path, "dau_user1_20260101T000000Z.json", _response("user1", "Not used"))
    (tmp_path / "other_report.json").write_text(json.dumps({"usage": "Every day (5 days)"}))
    result = compute_dau_metrics(tmp_path)
    assert result["response_count"] == 1


# ---------------------------------------------------------------------------
# DAU-F-018: score mapping and team average
# ---------------------------------------------------------------------------


def test_mixed_scores_correct_avg(tmp_path: Path) -> None:
    """5.0 + 3.5 + 1.5 = 10.0 / 3 ≈ 3.33"""
    _write(tmp_path, "dau_a_20260101T000000Z.json", _response("a", "Every day (5 days)"))
    _write(tmp_path, "dau_b_20260102T000000Z.json", _response("b", "Most days (3\u20134 days)"))
    _write(tmp_path, "dau_c_20260103T000000Z.json", _response("c", "Rarely (1\u20132 days)"))
    result = compute_dau_metrics(tmp_path)
    assert result["response_count"] == 3
    assert result["team_avg"] == pytest.approx(3.33, abs=0.01)


def test_all_not_used_avg_is_zero(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260101T000000Z.json", _response("a", "Not used"))
    _write(tmp_path, "dau_b_20260102T000000Z.json", _response("b", "Not used"))
    result = compute_dau_metrics(tmp_path)
    assert result["team_avg"] == 0.0


def test_unknown_usage_falls_back_to_zero(tmp_path: Path) -> None:
    """An unrecognised usage string counts as score 0."""
    _write(tmp_path, "dau_x_20260101T000000Z.json", {"username": "x", "role": "Dev", "usage": "Weekly"})
    result = compute_dau_metrics(tmp_path)
    assert result["team_avg"] == 0.0


# ---------------------------------------------------------------------------
# DAU-F-019: by_role breakdown
# ---------------------------------------------------------------------------


def test_by_role_sorted_alphabetically(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260101T000000Z.json", _response("a", "Every day (5 days)", role="QA / Test Engineer"))
    _write(tmp_path, "dau_b_20260102T000000Z.json", _response("b", "Most days (3\u20134 days)", role="Developer"))
    _write(tmp_path, "dau_c_20260103T000000Z.json", _response("c", "Every day (5 days)", role="Developer"))
    result = compute_dau_metrics(tmp_path)
    roles = [r["role"] for r in result["by_role"]]
    assert roles == sorted(roles)


def test_by_role_correct_avg_and_count(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260101T000000Z.json", _response("a", "Every day (5 days)", role="Developer"))
    _write(tmp_path, "dau_b_20260102T000000Z.json", _response("b", "Most days (3\u20134 days)", role="Developer"))
    _write(tmp_path, "dau_c_20260103T000000Z.json", _response("c", "Rarely (1\u20132 days)", role="QA / Test Engineer"))
    result = compute_dau_metrics(tmp_path)
    dev = next(r for r in result["by_role"] if r["role"] == "Developer")
    qa = next(r for r in result["by_role"] if r["role"] == "QA / Test Engineer")
    assert dev == {"role": "Developer", "avg": 4.25, "count": 2}
    assert qa == {"role": "QA / Test Engineer", "avg": 1.5, "count": 1}


# ---------------------------------------------------------------------------
# DAU-F-020: breakdown by answer
# ---------------------------------------------------------------------------


def test_breakdown_sorted_descending_by_count(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260101T000000Z.json", _response("a", "Every day (5 days)"))
    _write(tmp_path, "dau_b_20260102T000000Z.json", _response("b", "Every day (5 days)"))
    _write(tmp_path, "dau_c_20260103T000000Z.json", _response("c", "Not used"))
    result = compute_dau_metrics(tmp_path)
    counts = [b["count"] for b in result["breakdown"]]
    assert counts == sorted(counts, reverse=True)
    assert result["breakdown"][0]["answer"] == "Every day (5 days)"
    assert result["breakdown"][0]["count"] == 2


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------


def test_malformed_json_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "dau_bad_20260101T000000Z.json").write_text("{not valid json", encoding="utf-8")
    _write(tmp_path, "dau_good_20260102T000000Z.json", _response("good", "Not used"))
    result = compute_dau_metrics(tmp_path)
    assert result["response_count"] == 1


# ---------------------------------------------------------------------------
# DAU-F-021 + DAU-F-022: build_metrics_dict integration and env-var override
# ---------------------------------------------------------------------------


def test_build_metrics_dict_includes_dau_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAU_RESPONSES_DIR", str(tmp_path))
    import app.core.config as config
    importlib.reload(config)
    from app.core.metrics import build_metrics_dict
    result = build_metrics_dict([], {}, [])
    assert "dau" in result
    assert result["dau"]["response_count"] == 0


def test_dau_responses_dir_env_var_overrides_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "dau_alice_20260327T130340Z.json", _response("alice", "Every day (5 days)"))
    monkeypatch.setenv("DAU_RESPONSES_DIR", str(tmp_path))
    import app.core.config as config
    importlib.reload(config)
    from app.core import metrics as metrics_mod
    importlib.reload(metrics_mod)
    result = metrics_mod.compute_dau_metrics(config.DAU_RESPONSES_DIR)
    assert result["response_count"] == 1
    assert result["team_avg"] == 5.0
