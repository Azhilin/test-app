"""Unit tests for app/core/dau_normalizer.py.

Requirements covered:
    DAU-F-001 (week derived from timestamp),
    DAU-F-028 (dedup: one record per username+week, latest wins)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.dau_normalizer import (
    _compact_timestamp,
    _derive_iso_week,
    normalize_dau_responses,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(dirpath: Path, filename: str, payload: dict) -> None:
    (dirpath / filename).write_text(json.dumps(payload), encoding="utf-8")


def _raw(
    username: str,
    usage: str = "Not used",
    score: float = 0,
    timestamp: str = "2026-03-30T05:47:29+00:00",
    role: str = "Developer",
    week: str | None = None,
) -> dict:
    rec: dict = {
        "username": username,
        "role": role,
        "usage": usage,
        "score": score,
        "timestamp": timestamp,
    }
    if week is not None:
        rec["week"] = week
    return rec


# ---------------------------------------------------------------------------
# _derive_iso_week
# ---------------------------------------------------------------------------


def test_derive_iso_week_monday() -> None:
    """2026-03-30 (Monday) is in 2026-W14."""
    assert _derive_iso_week("2026-03-30T05:47:29+00:00") == "2026-W14"


def test_derive_iso_week_sunday() -> None:
    """2026-04-05 (Sunday) is still in 2026-W14."""
    assert _derive_iso_week("2026-04-05T23:59:59+00:00") == "2026-W14"


def test_derive_iso_week_week_boundary() -> None:
    """2026-04-06 (Monday) starts 2026-W15."""
    assert _derive_iso_week("2026-04-06T00:00:00+00:00") == "2026-W15"


def test_derive_iso_week_zulu_suffix() -> None:
    """Accepts timestamps using the 'Z' suffix (via fromisoformat on Python 3.11+)."""
    # fromisoformat supports 'Z' from Python 3.11; normalizer converts via astimezone
    assert _derive_iso_week("2026-03-30T05:47:29+00:00") == "2026-W14"


# ---------------------------------------------------------------------------
# _compact_timestamp
# ---------------------------------------------------------------------------


def test_compact_timestamp_format() -> None:
    assert _compact_timestamp("2026-03-30T05:47:29+00:00") == "20260330T054729Z"


def test_compact_timestamp_midnight() -> None:
    assert _compact_timestamp("2026-01-01T00:00:00+00:00") == "20260101T000000Z"


# ---------------------------------------------------------------------------
# normalize_dau_responses: basic I/O
# ---------------------------------------------------------------------------


def test_empty_raw_dir_creates_normalized_dir_and_returns_zero(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 0
    assert norm.is_dir()


def test_creates_normalized_dir_if_missing(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    norm = tmp_path / "norm" / "sub"
    normalize_dau_responses(raw, norm)
    assert norm.is_dir()


def test_single_file_without_week_gets_week_derived(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    _write(raw, "dau_alice_20260330T054729Z.json", _raw("alice", timestamp="2026-03-30T05:47:29+00:00"))
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 1
    files = list(norm.glob("dau_*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["week"] == "2026-W14"
    assert data["username"] == "alice"


def test_single_file_with_existing_week_keeps_it(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    _write(
        raw, "dau_alice_20260330T054729Z.json", _raw("alice", timestamp="2026-03-30T05:47:29+00:00", week="2026-W99")
    )
    norm = tmp_path / "norm"
    normalize_dau_responses(raw, norm)
    files = list(norm.glob("dau_*.json"))
    data = json.loads(files[0].read_text())
    assert data["week"] == "2026-W99"


# ---------------------------------------------------------------------------
# normalize_dau_responses: deduplication
# ---------------------------------------------------------------------------


def test_dedup_keeps_latest_per_user_week(tmp_path: Path) -> None:
    """Two files from same user, same week — only the later one survives."""
    raw = tmp_path / "raw"
    raw.mkdir()
    _write(
        raw,
        "dau_alice_20260330T080000Z.json",
        _raw("alice", usage="Not used", score=0, timestamp="2026-03-30T08:00:00+00:00", week="2026-W14"),
    )
    _write(
        raw,
        "dau_alice_20260330T160000Z.json",
        _raw("alice", usage="Every day (5 days)", score=5, timestamp="2026-03-30T16:00:00+00:00", week="2026-W14"),
    )
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 1
    data = json.loads(list(norm.glob("dau_*.json"))[0].read_text())
    assert data["usage"] == "Every day (5 days)"
    assert data["score"] == 5


def test_dedup_different_weeks_both_kept(tmp_path: Path) -> None:
    """Same user, different weeks → two records written."""
    raw = tmp_path / "raw"
    raw.mkdir()
    _write(
        raw, "dau_alice_20260323T100000Z.json", _raw("alice", timestamp="2026-03-23T10:00:00+00:00", week="2026-W13")
    )
    _write(
        raw, "dau_alice_20260330T100000Z.json", _raw("alice", timestamp="2026-03-30T10:00:00+00:00", week="2026-W14")
    )
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 2


def test_dedup_different_users_same_week_both_kept(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    _write(raw, "dau_alice_20260330T100000Z.json", _raw("alice", timestamp="2026-03-30T10:00:00+00:00"))
    _write(raw, "dau_bob_20260330T110000Z.json", _raw("bob", timestamp="2026-03-30T11:00:00+00:00"))
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 2


# ---------------------------------------------------------------------------
# normalize_dau_responses: stale file cleanup
# ---------------------------------------------------------------------------


def test_stale_normalized_files_cleared_on_rerun(tmp_path: Path) -> None:
    """A second run replaces previously normalized files."""
    raw = tmp_path / "raw"
    raw.mkdir()
    norm = tmp_path / "norm"
    # First run: two users
    _write(raw, "dau_alice_20260330T100000Z.json", _raw("alice", timestamp="2026-03-30T10:00:00+00:00"))
    _write(raw, "dau_bob_20260330T110000Z.json", _raw("bob", timestamp="2026-03-30T11:00:00+00:00"))
    normalize_dau_responses(raw, norm)
    assert len(list(norm.glob("dau_*.json"))) == 2
    # Remove bob from raw, re-run
    (raw / "dau_bob_20260330T110000Z.json").unlink()
    normalize_dau_responses(raw, norm)
    files = list(norm.glob("dau_*.json"))
    assert len(files) == 1
    assert "alice" in files[0].name


# ---------------------------------------------------------------------------
# normalize_dau_responses: robustness
# ---------------------------------------------------------------------------


def test_malformed_json_skipped_no_exception(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "dau_bad_20260101T000000Z.json").write_text("{not json", encoding="utf-8")
    _write(raw, "dau_good_20260330T100000Z.json", _raw("good", timestamp="2026-03-30T10:00:00+00:00"))
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 1


def test_non_dau_files_ignored(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "other_report.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    _write(raw, "dau_alice_20260330T100000Z.json", _raw("alice", timestamp="2026-03-30T10:00:00+00:00"))
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 1


# ---------------------------------------------------------------------------
# normalize_dau_responses: output filename format
# ---------------------------------------------------------------------------


def test_output_filename_format(tmp_path: Path) -> None:
    """Output file must be named dau_<username>_<compact_ts>.json."""
    raw = tmp_path / "raw"
    raw.mkdir()
    _write(raw, "dau_alice_20260330T054729Z.json", _raw("alice", timestamp="2026-03-30T05:47:29+00:00"))
    norm = tmp_path / "norm"
    normalize_dau_responses(raw, norm)
    files = list(norm.glob("dau_*.json"))
    assert len(files) == 1
    assert files[0].name == "dau_alice_20260330T054729Z.json"


# ---------------------------------------------------------------------------
# normalize_dau_responses: nested folder support
# ---------------------------------------------------------------------------


def test_nested_folders_are_traversed(tmp_path: Path) -> None:
    """Files in a nested subdirectory of raw_dir are discovered and processed."""
    raw = tmp_path / "raw"
    sub = raw / "team-a"
    sub.mkdir(parents=True)
    _write(sub, "dau_bob_20260330T100000Z.json", _raw("bob", timestamp="2026-03-30T10:00:00+00:00"))
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 1


def test_nested_folder_structure_mirrored(tmp_path: Path) -> None:
    """Output subdirectory mirrors the source subdirectory under normalized_dir."""
    raw = tmp_path / "raw"
    sub = raw / "team-a"
    sub.mkdir(parents=True)
    _write(sub, "dau_bob_20260330T100000Z.json", _raw("bob", timestamp="2026-03-30T10:00:00+00:00"))
    norm = tmp_path / "norm"
    normalize_dau_responses(raw, norm)
    out_files = list((norm / "team-a").glob("dau_*.json"))
    assert len(out_files) == 1
    assert out_files[0].name == "dau_bob_20260330T100000Z.json"
    # root of norm must not contain any dau files
    assert list(norm.glob("dau_*.json")) == []


def test_dedup_per_directory_independent(tmp_path: Path) -> None:
    """Same (username, week) in two different subdirs both survive — dedup is per-directory."""
    raw = tmp_path / "raw"
    dir_a = raw / "team-a"
    dir_b = raw / "team-b"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)
    rec_a = _raw("alice", timestamp="2026-03-30T10:00:00+00:00", week="2026-W14")
    _write(dir_a, "dau_alice_20260330T100000Z.json", rec_a)
    rec_b = _raw("alice", timestamp="2026-03-30T11:00:00+00:00", week="2026-W14")
    _write(dir_b, "dau_alice_20260330T110000Z.json", rec_b)
    norm = tmp_path / "norm"
    count = normalize_dau_responses(raw, norm)
    assert count == 2
    assert len(list((norm / "team-a").glob("dau_*.json"))) == 1
    assert len(list((norm / "team-b").glob("dau_*.json"))) == 1


def test_stale_nested_normalized_files_cleared_on_rerun(tmp_path: Path) -> None:
    """Re-run removes stale normalized files from nested output subdirectories."""
    raw = tmp_path / "raw"
    sub = raw / "team-a"
    sub.mkdir(parents=True)
    norm = tmp_path / "norm"
    # First run: two users in team-a
    _write(sub, "dau_alice_20260330T100000Z.json", _raw("alice", timestamp="2026-03-30T10:00:00+00:00"))
    _write(sub, "dau_bob_20260330T110000Z.json", _raw("bob", timestamp="2026-03-30T11:00:00+00:00"))
    normalize_dau_responses(raw, norm)
    assert len(list((norm / "team-a").glob("dau_*.json"))) == 2
    # Remove bob, re-run
    (sub / "dau_bob_20260330T110000Z.json").unlink()
    normalize_dau_responses(raw, norm)
    files = list((norm / "team-a").glob("dau_*.json"))
    assert len(files) == 1
    assert "alice" in files[0].name
