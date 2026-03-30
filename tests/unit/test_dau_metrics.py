"""Unit tests for DAU metrics: compute_dau_metrics(), compute_dau_trend(),
_load_dau_records(), _dedup_by_user_week(), and build_metrics_dict integration.

Requirements covered:
    DAU-F-017, DAU-F-018, DAU-F-019, DAU-F-020, DAU-F-021, DAU-F-022,
    DAU-F-027, DAU-F-028, DAU-F-029
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from app.core.metrics import (
    _dedup_by_user_week,
    _load_dau_records,
    compute_dau_metrics,
    compute_dau_trend,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(dirpath: Path, filename: str, payload: dict) -> None:
    """Write a DAU response JSON file to dirpath."""
    (dirpath / filename).write_text(json.dumps(payload), encoding="utf-8")


def _response(
    username: str, usage: str, role: str = "Developer", week: str = "2026-W13", timestamp: str = "2026-03-27T10:00:00Z"
) -> dict:
    return {"username": username, "role": role, "usage": usage, "week": week, "timestamp": timestamp}


# ---------------------------------------------------------------------------
# DAU-F-017: reads all dau_*.json files
# ---------------------------------------------------------------------------


def test_empty_dir_returns_zero_count(tmp_path: Path) -> None:
    result = compute_dau_metrics(tmp_path)
    assert result["response_count"] == 0
    assert result["team_avg"] is None
    assert result["team_avg_pct"] is None
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
    assert result["team_avg_pct"] == pytest.approx(66.6, abs=0.1)


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
    assert dev == {"role": "Developer", "avg": 4.25, "avg_pct": 85.0, "count": 2}
    assert qa == {"role": "QA / Test Engineer", "avg": 1.5, "avg_pct": 30.0, "count": 1}


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
    assert result["breakdown"][0]["pct"] == pytest.approx(66.7, abs=0.1)
    assert result["breakdown"][1]["pct"] == pytest.approx(33.3, abs=0.1)


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
    assert "dau_trend" in result
    assert result["dau_trend"] == []


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


# ---------------------------------------------------------------------------
# DAU-F-027: _load_dau_records
# ---------------------------------------------------------------------------


def test_load_dau_records_returns_list(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260101T000000Z.json", _response("a", "Every day (5 days)"))
    _write(tmp_path, "dau_b_20260102T000000Z.json", _response("b", "Not used"))
    records = _load_dau_records(tmp_path)
    assert len(records) == 2
    assert all("username" in r for r in records)


def test_load_dau_records_skips_malformed(tmp_path: Path) -> None:
    (tmp_path / "dau_bad_20260101T000000Z.json").write_text("{bad", encoding="utf-8")
    _write(tmp_path, "dau_ok_20260102T000000Z.json", _response("ok", "Not used"))
    records = _load_dau_records(tmp_path)
    assert len(records) == 1


def test_load_dau_records_empty_dir(tmp_path: Path) -> None:
    assert _load_dau_records(tmp_path) == []


# ---------------------------------------------------------------------------
# DAU-F-028: _dedup_by_user_week
# ---------------------------------------------------------------------------


def test_dedup_keeps_latest_per_user_week() -> None:
    records = [
        {"username": "alice", "week": "2026-W13", "usage": "Not used", "timestamp": "2026-03-27T08:00:00Z"},
        {"username": "alice", "week": "2026-W13", "usage": "Every day (5 days)", "timestamp": "2026-03-27T16:00:00Z"},
        {"username": "bob", "week": "2026-W13", "usage": "Rarely (1\u20132 days)", "timestamp": "2026-03-27T09:00:00Z"},
    ]
    deduped = _dedup_by_user_week(records)
    assert len(deduped) == 2
    alice = next(r for r in deduped if r["username"] == "alice")
    assert alice["usage"] == "Every day (5 days)"


def test_dedup_different_weeks_kept_separate() -> None:
    records = [
        {"username": "alice", "week": "2026-W12", "usage": "Not used", "timestamp": "2026-03-20T10:00:00Z"},
        {"username": "alice", "week": "2026-W13", "usage": "Every day (5 days)", "timestamp": "2026-03-27T10:00:00Z"},
    ]
    deduped = _dedup_by_user_week(records)
    assert len(deduped) == 2


def test_dedup_empty_list() -> None:
    assert _dedup_by_user_week([]) == []


# ---------------------------------------------------------------------------
# DAU-F-029: compute_dau_trend
# ---------------------------------------------------------------------------


def test_compute_dau_trend_single_week(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260327T100000Z.json", _response("a", "Every day (5 days)", week="2026-W13"))
    _write(tmp_path, "dau_b_20260327T110000Z.json", _response("b", "Most days (3\u20134 days)", week="2026-W13"))
    trend = compute_dau_trend(tmp_path)
    assert len(trend) == 1
    row = trend[0]
    assert row["week"] == "2026-W13"
    assert row["response_count"] == 2
    assert row["team_avg"] == pytest.approx(4.25, abs=0.01)
    assert row["team_avg_pct"] == pytest.approx(85.0, abs=0.1)


def test_compute_dau_trend_multiple_weeks_sorted(tmp_path: Path) -> None:
    _write(tmp_path, "dau_a_20260320T100000Z.json", _response("a", "Not used", week="2026-W12"))
    _write(tmp_path, "dau_b_20260327T100000Z.json", _response("b", "Every day (5 days)", week="2026-W13"))
    trend = compute_dau_trend(tmp_path)
    assert len(trend) == 2
    assert trend[0]["week"] == "2026-W12"
    assert trend[1]["week"] == "2026-W13"


def test_compute_dau_trend_empty_dir(tmp_path: Path) -> None:
    assert compute_dau_trend(tmp_path) == []


def test_compute_dau_trend_dedup_applied(tmp_path: Path) -> None:
    """Two responses from same user in same week → only latest counts."""
    _write(
        tmp_path,
        "dau_a1_20260327T080000Z.json",
        _response("alice", "Not used", week="2026-W13", timestamp="2026-03-27T08:00:00Z"),
    )
    _write(
        tmp_path,
        "dau_a2_20260327T160000Z.json",
        _response("alice", "Every day (5 days)", week="2026-W13", timestamp="2026-03-27T16:00:00Z"),
    )
    trend = compute_dau_trend(tmp_path)
    assert len(trend) == 1
    assert trend[0]["response_count"] == 1
    assert trend[0]["team_avg"] == pytest.approx(5.0, abs=0.01)
