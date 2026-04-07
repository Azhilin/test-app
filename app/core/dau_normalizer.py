"""
DAU response normalizer.

Reads raw survey JSON files from a source directory, enriches each record
with the ISO ``week`` field (derived from ``timestamp`` when absent), deduplicates
to one record per ``(username, week)`` keeping the latest submission, and writes
the clean set to a normalized output directory.

Called automatically by ``app/cli.py`` before metric computation so that both
``compute_dau_metrics`` and ``compute_dau_trend`` always work from consistent data.
"""

from __future__ import annotations

import json
import logging
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


def normalize_dau_responses(raw_dir: str | Path, normalized_dir: str | Path) -> int:
    """Enrich, deduplicate, and write DAU survey responses to *normalized_dir*.

    Steps:
    1. Create *normalized_dir* if it does not exist.
    2. Remove any existing ``dau_*.json`` files from *normalized_dir* (prevent stale data).
    3. Load all ``dau_*.json`` files from *raw_dir*; skip malformed files with a warning.
    4. For each record: use ``week`` if present and non-empty, otherwise derive from ``timestamp``.
    5. Deduplicate: keep the record with the latest ``timestamp`` per ``(username, week)``.
    6. Write each surviving record as ``dau_<username>_<compact_ts>.json`` in *normalized_dir*.

    Returns the number of records written.
    """
    raw_path = Path(raw_dir)
    norm_path = Path(normalized_dir)
    norm_path.mkdir(parents=True, exist_ok=True)

    # Clear stale normalized files
    for stale in norm_path.glob("dau_*.json"):
        stale.unlink()

    # Load raw records
    records: list[dict] = []
    for fpath in sorted(raw_path.glob("dau_*.json")):
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
        (norm_path / filename).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    count = len(best)
    logger.info(
        "DAU normalisation: %d raw file(s) → %d record(s) written to %s",
        len(records),
        count,
        norm_path,
    )
    return count
