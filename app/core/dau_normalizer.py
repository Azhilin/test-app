"""
DAU response normalizer.

Reads raw survey JSON files from a source directory (recursively), enriches each
record with the ISO ``week`` field (derived from ``timestamp`` when absent),
deduplicates to one record per ``(username, week)`` keeping the latest submission,
and writes the clean set to a normalized output directory that mirrors the source
folder structure.

Called automatically by ``app/cli.py`` before metric computation so that both
``compute_dau_metrics`` and ``compute_dau_trend`` always work from consistent data.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _derive_iso_week(iso_ts: str) -> str:
    """Return ISO week string (e.g. ``'2026-W15'``) from an ISO 8601 timestamp."""
    dt = datetime.fromisoformat(iso_ts).astimezone(timezone.utc)
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _compact_timestamp(iso_ts: str) -> str:
    """Convert ``'2026-03-30T05:47:29+00:00'`` → ``'20260330T054729Z'`` for filenames."""
    dt = datetime.fromisoformat(iso_ts).astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _normalize_dir(files: list[Path], out_dir: Path) -> tuple[int, int]:
    """Enrich, deduplicate, and write records from *files* into *out_dir*.

    Returns ``(records_written, raw_files_read)``.
    """
    # Load raw records
    records: list[dict] = []
    for fpath in files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
            records.append(data)
        except Exception as exc:  # nosec B112
            logger.warning("DAU normaliser: skipping malformed file %s — %s", fpath.name, exc)

    # Enrich: add week if missing
    for rec in records:
        if not rec.get("week"):
            try:
                rec["week"] = _derive_iso_week(rec["timestamp"])
            except Exception as exc:
                logger.warning(
                    "DAU normaliser: cannot derive week for record (username=%s): %s",
                    rec.get("username"),
                    exc,
                )

    # Deduplicate: latest timestamp per (username, week)
    best: dict[tuple[str, str], dict] = {}
    for rec in records:
        key = (rec.get("username", ""), rec.get("week", ""))
        existing = best.get(key)
        if existing is None or rec.get("timestamp", "") > existing.get("timestamp", ""):
            best[key] = rec

    # Write normalized files
    for rec in best.values():
        try:
            filename = f"dau_{rec['username']}_{_compact_timestamp(rec['timestamp'])}.json"
        except Exception:
            filename = f"dau_{rec.get('username', 'unknown')}_{rec.get('week', 'unknown')}.json"
        (out_dir / filename).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return len(best), len(records)


def normalize_dau_responses(raw_dir: str | Path, normalized_dir: str | Path) -> int:
    """Enrich, deduplicate, and write DAU survey responses to *normalized_dir*.

    Walks *raw_dir* recursively. For each subdirectory that contains ``dau_*.json``
    files, a matching subdirectory is created under *normalized_dir* and the records
    from that directory are processed independently (enriched, deduplicated, written).

    Steps:
    1. Create *normalized_dir* if it does not exist.
    2. Remove any existing ``dau_*.json`` files from *normalized_dir* recursively (prevent stale data).
    3. Discover all ``dau_*.json`` files under *raw_dir* at any nesting level.
    4. Group files by their parent directory relative to *raw_dir*.
    5. For each group: enrich, deduplicate, and write to the mirrored output subdirectory.

    Returns the total number of records written across all subdirectories.
    """
    raw_path = Path(raw_dir)
    norm_path = Path(normalized_dir)

    # Wipe and recreate normalized dir for a clean slate on every run
    if norm_path.exists():
        shutil.rmtree(norm_path)
    norm_path.mkdir(parents=True, exist_ok=True)

    # Group source files by their directory relative to raw_path
    by_rel_dir: dict[Path, list[Path]] = {}
    for fpath in sorted(raw_path.rglob("dau_*.json")):
        rel_dir = fpath.parent.relative_to(raw_path)
        by_rel_dir.setdefault(rel_dir, []).append(fpath)

    total_written = 0
    total_raw = 0
    for rel_dir, files in sorted(by_rel_dir.items()):
        out_dir = norm_path / rel_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        written, raw_count = _normalize_dir(files, out_dir)
        total_written += written
        total_raw += raw_count

    logger.info(
        "DAU normalisation: %d raw file(s) → %d record(s) written to %s",
        total_raw,
        total_written,
        norm_path,
    )
    return total_written
