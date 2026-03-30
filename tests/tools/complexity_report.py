"""
tests/tools/complexity_report.py
=================================
Analyses the source code under ``app/``, ``main.py``, and ``server.py`` and
produces a Markdown complexity report in ``generated/reports/``.

Metrics collected
-----------------
- **LOC / SLOC** — raw line counts (source, blank, comment, docstring) via radon
- **Cyclomatic Complexity (CC)** — per-function grade A–F via radon; module averages
- **Maintainability Index (MI)** — per-file score and rank A/B/C via radon
- **Dependency depth** — direct dep count from requirements.txt + pipdeptree tree depth
- **Test count** — extracted from tests/coverage/test_coverage.md (no recompute)

Usage
-----
    # Preview only (no file writes)
    python tests/tools/complexity_report.py --dry-run

    # Write report to generated/reports/complexity_<ISO-timestamp>.md
    python tests/tools/complexity_report.py

Refactor signals
----------------
Functions with CC grade C or worse (complexity >= 11) and files with MI < 65
are surfaced in a dedicated "Refactor Signals" section of the report.

Complexity thresholds (Python Web Developer reference)
-------------------------------------------------------
  Module SLOC   : Good < 300 | Watch 300-600 | Refactor > 600
  CC per function: Good A(1-5) | Watch B(6-10) | Refactor C-F(11+)
  MI per file   : Good A(>65) | Watch B(25-65) | Refactor C(<25)
  Direct deps   : Good < 15 | Watch 15-25 | Refactor > 25
  Dep tree depth: Good 1-2 | Watch 3 | Refactor > 3
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit
from radon.raw import analyze

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "generated" / "reports"
TEST_COVERAGE_MD = REPO_ROOT / "tests" / "coverage" / "test_coverage.md"
REQUIREMENTS_TXT = REPO_ROOT / "requirements.txt"

# Source paths to analyse (relative to REPO_ROOT)
SOURCE_PATHS: list[Path] = [
    REPO_ROOT / "app",
    REPO_ROOT / "main.py",
    REPO_ROOT / "server.py",
]

# ---------------------------------------------------------------------------
# CC grade thresholds
# ---------------------------------------------------------------------------

CC_WATCH_THRESHOLD = 6  # grade B — worth watching
CC_REFACTOR_THRESHOLD = 11  # grade C and above — refactor signal
MI_REFACTOR_THRESHOLD = 65  # below this → refactor signal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iter_python_files(paths: list[Path]) -> list[Path]:
    """Return all .py files under the given paths, sorted."""
    files: list[Path] = []
    for p in paths:
        if p.is_file() and p.suffix == ".py":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
    return sorted(files)


def _rel(path: Path) -> str:
    """Return path relative to REPO_ROOT as a POSIX string."""
    return path.relative_to(REPO_ROOT).as_posix()


# ---------------------------------------------------------------------------
# 1. Raw LOC
# ---------------------------------------------------------------------------


def collect_raw_loc(files: list[Path]) -> list[dict]:
    """Return per-file raw LOC data from radon."""
    rows = []
    for f in files:
        try:
            result = analyze(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:  # noqa: BLE001
            continue
        rows.append(
            {
                "file": _rel(f),
                "sloc": result.sloc,
                "blank": result.blank,
                "comments": result.comments,
                "doc_strings": result.multi,
                "total": result.loc,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# 2. Cyclomatic Complexity
# ---------------------------------------------------------------------------


def collect_cc(files: list[Path]) -> tuple[list[dict], list[dict]]:
    """Return (per_function_rows, module_average_rows) from radon CC analysis."""
    func_rows: list[dict] = []
    module_rows: list[dict] = []

    for f in files:
        try:
            blocks = cc_visit(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:  # noqa: BLE001
            continue
        if not blocks:
            continue

        module_complexities = []
        for block in blocks:
            grade = cc_rank(block.complexity)
            func_rows.append(
                {
                    "file": _rel(f),
                    "name": block.name,
                    "type": block.letter,  # F=function, M=method, C=class
                    "complexity": block.complexity,
                    "grade": grade,
                    "line": block.lineno,
                }
            )
            module_complexities.append(block.complexity)

        avg = sum(module_complexities) / len(module_complexities)
        module_rows.append(
            {
                "file": _rel(f),
                "avg_cc": round(avg, 1),
                "grade": cc_rank(avg),
                "max_cc": max(module_complexities),
                "functions": len(module_complexities),
            }
        )

    # Sort by average CC descending so worst modules appear first
    module_rows.sort(key=lambda r: r["avg_cc"], reverse=True)
    func_rows.sort(key=lambda r: r["complexity"], reverse=True)
    return func_rows, module_rows


# ---------------------------------------------------------------------------
# 3. Maintainability Index
# ---------------------------------------------------------------------------


def collect_mi(files: list[Path]) -> list[dict]:
    """Return per-file Maintainability Index from radon."""
    rows = []
    for f in files:
        try:
            score = mi_visit(f.read_text(encoding="utf-8", errors="replace"), multi=True)
        except Exception:  # noqa: BLE001
            continue
        rows.append(
            {
                "file": _rel(f),
                "mi": round(score, 1),
                "rank": mi_rank(score),
            }
        )
    rows.sort(key=lambda r: r["mi"])  # worst (lowest) first
    return rows


# ---------------------------------------------------------------------------
# 4. Dependencies
# ---------------------------------------------------------------------------


def collect_dependencies() -> dict:
    """Count direct runtime deps and compute max tree depth via pipdeptree."""
    # Direct count from requirements.txt
    direct: list[str] = []
    if REQUIREMENTS_TXT.exists():
        for line in REQUIREMENTS_TXT.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "-r", "--")):
                direct.append(stripped)

    # Tree depth via pipdeptree --json
    max_depth = _measure_pipdeptree_depth()

    return {
        "direct_count": len(direct),
        "direct_deps": direct,
        "max_tree_depth": max_depth,
    }


def _measure_pipdeptree_depth() -> int:
    """Run pipdeptree --json and return the maximum dependency tree depth."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pipdeptree", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return -1
        tree = json.loads(result.stdout)
    except Exception:  # noqa: BLE001
        return -1

    def _depth(node: dict) -> int:
        deps = node.get("dependencies", [])
        if not deps:
            return 1
        return 1 + max(_depth(d) for d in deps)

    return max((_depth(pkg) for pkg in tree), default=0)


# ---------------------------------------------------------------------------
# 5. Test count from test_coverage.md
# ---------------------------------------------------------------------------


def extract_test_count() -> int | None:
    """Extract total test count from the Test Pyramid block in test_coverage.md."""
    if not TEST_COVERAGE_MD.exists():
        return None
    content = TEST_COVERAGE_MD.read_text(encoding="utf-8")
    # Look for a line like "503 tests total"
    match = re.search(r"(\d+)\s+tests\s+total", content)
    if match:
        return int(match.group(1))
    return None


# ---------------------------------------------------------------------------
# 6. Refactor signals
# ---------------------------------------------------------------------------


def build_refactor_signals(func_rows: list[dict], mi_rows: list[dict], loc_rows: list[dict]) -> list[str]:
    """Return a list of human-readable signal strings for the report."""
    signals: list[str] = []

    for row in func_rows:
        if row["complexity"] >= CC_REFACTOR_THRESHOLD:
            signals.append(
                f"**CC {row['grade']}** `{row['file']}` → `{row['name']}()` "
                f"complexity={row['complexity']} (line {row['line']})"
            )

    for row in mi_rows:
        if row["mi"] < MI_REFACTOR_THRESHOLD:
            signals.append(f"**MI {row['rank']}** `{row['file']}` → MI={row['mi']}")

    for row in loc_rows:
        if row["sloc"] > 600:
            signals.append(f"**SLOC>600** `{row['file']}` → {row['sloc']} source lines")

    return signals


# ---------------------------------------------------------------------------
# 7. Report rendering
# ---------------------------------------------------------------------------

_THRESHOLDS_TABLE = """\
### Reference Thresholds

| Metric | Good | Watch | Refactor |
|--------|------|-------|----------|
| Module SLOC | < 300 | 300–600 | > 600 |
| Cyclomatic Complexity (per function) | Grade A (1–5) | Grade B (6–10) | Grade C–F (11+) |
| Maintainability Index (per file) | A (> 65) | B (25–65) | C (< 25) |
| Direct runtime dependencies | < 15 | 15–25 | > 25 |
| Dependency tree depth | 1–2 levels | 3 levels | > 3 |
"""


def render_report(
    loc_rows: list[dict],
    func_rows: list[dict],
    module_cc_rows: list[dict],
    mi_rows: list[dict],
    dep_data: dict,
    test_count: int | None,
    signals: list[str],
    generated_at: str,
) -> str:
    lines: list[str] = []

    lines.append("# Complexity Report — AI Adoption Metrics Report")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")

    # ── Summary ──────────────────────────────────────────────────────────────
    total_sloc = sum(r["sloc"] for r in loc_rows)
    total_files = len(loc_rows)
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Source files analysed | {total_files} |")
    lines.append(f"| Total SLOC | {total_sloc} |")
    lines.append(f"| Direct runtime dependencies | {dep_data['direct_count']} |")
    lines.append(f"| Dependency tree depth (max) | {dep_data['max_tree_depth']} |")
    lines.append(f"| Test functions | {test_count if test_count is not None else 'n/a'} |")
    lines.append(f"| Refactor signals | {len(signals)} |")
    lines.append("")

    # ── Refactor signals ─────────────────────────────────────────────────────
    lines.append("## Refactor Signals")
    lines.append("")
    if signals:
        for s in signals:
            lines.append(f"- {s}")
    else:
        lines.append("_No refactor signals — all metrics within thresholds._")
    lines.append("")

    # ── LOC ──────────────────────────────────────────────────────────────────
    lines.append("## Lines of Code (LOC)")
    lines.append("")
    lines.append("| File | SLOC | Blank | Comments | Docstrings | Total |")
    lines.append("|------|-----:|------:|---------:|-----------:|------:|")
    for r in sorted(loc_rows, key=lambda x: x["sloc"], reverse=True):
        flag = " ⚠️" if r["sloc"] > 600 else (" 👀" if r["sloc"] > 300 else "")
        lines.append(
            f"| `{r['file']}`{flag} | {r['sloc']} | {r['blank']} | "
            f"{r['comments']} | {r['doc_strings']} | {r['total']} |"
        )
    loc_total = {
        "sloc": sum(r["sloc"] for r in loc_rows),
        "blank": sum(r["blank"] for r in loc_rows),
        "comments": sum(r["comments"] for r in loc_rows),
        "doc_strings": sum(r["doc_strings"] for r in loc_rows),
        "total": sum(r["total"] for r in loc_rows),
    }
    lines.append(
        f"| **TOTAL** | **{loc_total['sloc']}** | {loc_total['blank']} | "
        f"{loc_total['comments']} | {loc_total['doc_strings']} | {loc_total['total']} |"
    )
    lines.append("")

    # ── CC per module ─────────────────────────────────────────────────────────
    lines.append("## Cyclomatic Complexity — Module Averages")
    lines.append("")
    lines.append("| File | Avg CC | Grade | Max CC | Functions |")
    lines.append("|------|-------:|-------|-------:|----------:|")
    for r in module_cc_rows:
        flag = " ⚠️" if r["grade"] in ("C", "D", "E", "F") else (" 👀" if r["grade"] == "B" else "")
        lines.append(f"| `{r['file']}`{flag} | {r['avg_cc']} | {r['grade']} | {r['max_cc']} | {r['functions']} |")
    lines.append("")

    # ── CC per function (top 20 worst) ───────────────────────────────────────
    top_funcs = [r for r in func_rows if r["complexity"] >= CC_WATCH_THRESHOLD][:20]
    if top_funcs:
        lines.append("## Cyclomatic Complexity — Top Functions (CC ≥ 6)")
        lines.append("")
        lines.append("| File | Function | Type | CC | Grade | Line |")
        lines.append("|------|----------|------|----|-------|-----:|")
        for r in top_funcs:
            flag = " ⚠️" if r["complexity"] >= CC_REFACTOR_THRESHOLD else " 👀"
            lines.append(
                f"| `{r['file']}`{flag} | `{r['name']}` | {r['type']} | "
                f"{r['complexity']} | {r['grade']} | {r['line']} |"
            )
        lines.append("")

    # ── MI per file ───────────────────────────────────────────────────────────
    lines.append("## Maintainability Index (MI)")
    lines.append("")
    lines.append("| File | MI | Rank |")
    lines.append("|------|---:|------|")
    for r in mi_rows:
        flag = " ⚠️" if r["rank"] == "C" else (" 👀" if r["rank"] == "B" else "")
        lines.append(f"| `{r['file']}`{flag} | {r['mi']} | {r['rank']} |")
    lines.append("")

    # ── Dependencies ─────────────────────────────────────────────────────────
    lines.append("## Dependencies")
    lines.append("")
    dep_flag = " ⚠️" if dep_data["direct_count"] > 25 else (" 👀" if dep_data["direct_count"] > 15 else "")
    depth_flag = " ⚠️" if dep_data["max_tree_depth"] > 3 else (" 👀" if dep_data["max_tree_depth"] == 3 else "")
    lines.append(f"- **Direct runtime deps:** {dep_data['direct_count']}{dep_flag}")
    lines.append(f"- **Max transitive tree depth:** {dep_data['max_tree_depth']}{depth_flag}")
    lines.append("")
    lines.append("| # | Package |")
    lines.append("|---|---------|")
    for i, dep in enumerate(dep_data["direct_deps"], 1):
        lines.append(f"| {i} | `{dep}` |")
    lines.append("")

    # ── Reference thresholds ─────────────────────────────────────────────────
    lines.append(_THRESHOLDS_TABLE)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(dry_run: bool = False) -> None:
    files = _iter_python_files(SOURCE_PATHS)

    print(f"Analysing {len(files)} source files...")

    loc_rows = collect_raw_loc(files)
    func_rows, module_cc_rows = collect_cc(files)
    mi_rows = collect_mi(files)
    dep_data = collect_dependencies()
    test_count = extract_test_count()
    signals = build_refactor_signals(func_rows, mi_rows, loc_rows)

    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_text = render_report(
        loc_rows,
        func_rows,
        module_cc_rows,
        mi_rows,
        dep_data,
        test_count,
        signals,
        generated_at,
    )

    # ── Console summary ───────────────────────────────────────────────────────
    total_sloc = sum(r["sloc"] for r in loc_rows)
    print()
    print(f"  Source files  : {len(files)}")
    print(f"  Total SLOC    : {total_sloc}")
    print(f"  Direct deps   : {dep_data['direct_count']}")
    print(f"  Dep tree depth: {dep_data['max_tree_depth']}")
    print(f"  Tests total   : {test_count if test_count is not None else 'n/a'}")
    print(f"  Refactor flags: {len(signals)}")
    print()

    if signals:
        print("  [!] Refactor signals:")
        for s in signals:
            # Strip markdown markers and non-ASCII chars for plain console output
            plain = re.sub(r"\*\*|\`", "", s)
            plain = re.sub(r"[^\x00-\x7F]+", "", plain)
            print(f"      {plain.strip()}")
        print()

    if dry_run:
        print("[dry-run] No files written.")
        print()
        print(report_text)
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = REPORTS_DIR / f"complexity_{ts}.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"  Report written → {out_path.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    # Ensure stdout handles Unicode on Windows consoles
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _dry = "--dry-run" in sys.argv
    main(dry_run=_dry)
