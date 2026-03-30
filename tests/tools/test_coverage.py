"""
tests/tools/test_coverage.py
============================
Counts test cases per layer using AST analysis (handles @pytest.mark.parametrize
expansions) and rewrites the Test Pyramid block + Count column in
tests/coverage/test_coverage.md.

Usage
-----
    # Preview only (no file writes)
    python tests/tools/test_coverage.py --dry-run

    # Update tests/coverage/test_coverage.md in-place
    python tests/tools/test_coverage.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

from tests.tools.requirements_map import (
    ALL_REQUIREMENTS,
    _derive_status,
)

# ---------------------------------------------------------------------------
# Repository layout
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"
MD_FILE = TESTS_DIR / "coverage" / "test_coverage.md"
COVERAGE_REQS_DIR = TESTS_DIR / "coverage" / "requirements"

# Mapping: ALL_REQUIREMENTS key → detail file path
_DETAIL_FILES: dict[str, Path] = {
    "technical_requirements": COVERAGE_REQS_DIR / "technical_requirements_coverage.md",
    "installation_requirements": COVERAGE_REQS_DIR / "installation_requirements_coverage.md",
    "app_non_functional_requirements": COVERAGE_REQS_DIR / "app_non_functional_requirements_coverage.md",
    "dau_survey_requirements": COVERAGE_REQS_DIR / "dau_survey_requirements_coverage.md",
    "jira_connection_requirements": COVERAGE_REQS_DIR / "jira_connection_requirements_coverage.md",
    "jira_data_fetching_requirements": COVERAGE_REQS_DIR / "jira_data_fetching_requirements_coverage.md",
    "jira_schema_requirements": COVERAGE_REQS_DIR / "jira_schema_requirements_coverage.md",
    "jira_filter_management_requirements": COVERAGE_REQS_DIR / "jira_filter_management_requirements_coverage.md",
    "logging_requirements": COVERAGE_REQS_DIR / "logging_requirements_coverage.md",
    "report_generation_requirements": COVERAGE_REQS_DIR / "report_generation_requirements_coverage.md",
}

# Mapping: ALL_REQUIREMENTS key → source document (relative to repo root)
_SOURCE_DOCS: dict[str, str] = {
    "technical_requirements": "docs/product/requirements/technical_requirements.md",
    "installation_requirements": "docs/product/requirements/installation_requirements.md",
    "app_non_functional_requirements": "docs/product/requirements/app_non_functional_requirements.md",
    "dau_survey_requirements": "docs/product/requirements/dau_survey_requirements.md",
    "jira_connection_requirements": "docs/product/requirements/jira_connection_requirements.md",
    "jira_data_fetching_requirements": "docs/product/requirements/jira_data_fetching_requirements.md",
    "jira_schema_requirements": "docs/product/requirements/jira_schema_requirements.md",
    "jira_filter_management_requirements": "docs/product/requirements/jira_filter_management_requirements.md",
    "logging_requirements": "docs/product/requirements/logging_requirements.md",
    "report_generation_requirements": "docs/product/requirements/report_generation_requirements.md",
}

# Layer name → folder (relative to TESTS_DIR), description, path label
LAYERS: list[dict] = [
    {
        "name": "Unit",
        "folder": TESTS_DIR / "unit",
        "description": "(pure functions, no I/O)",
        "path_label": "→ tests/unit/",
    },
    {
        "name": "Component",
        "folder": TESTS_DIR / "component",
        "description": "(filesystem, HTTP, data shapes)",
        "path_label": "→ tests/component/",
    },
    {
        "name": "Integration",
        "folder": TESTS_DIR / "integration",
        "description": "(cross-module flows, subprocess)",
        "path_label": "→ tests/integration/",
    },
    {
        "name": "E2E",
        "folder": TESTS_DIR / "e2e",
        "description": "(Playwright browser UI)",
        "path_label": "→ tests/e2e/",
    },
]

# ---------------------------------------------------------------------------
# AST counting
# ---------------------------------------------------------------------------


def _parametrize_expansion(func_node: ast.FunctionDef) -> int:
    """Return the number of test cases produced by @parametrize decorators.

    Handles stacked decorators (product of case counts).
    Falls back to 1 (= the function itself counts as 1 case) when no
    parametrize decorator is found or the cases list cannot be parsed.
    """
    total = 1
    for deco in func_node.decorator_list:
        # Support both `@pytest.mark.parametrize(...)` and bare
        # `@parametrize(...)` style references.
        if not isinstance(deco, ast.Call):
            continue
        func = deco.func
        if isinstance(func, ast.Attribute) and func.attr == "parametrize":
            pass  # matched
        elif isinstance(func, ast.Name) and func.id == "parametrize":
            pass  # matched
        else:
            continue

        if len(deco.args) < 2:
            continue

        cases_arg = deco.args[1]
        if isinstance(cases_arg, (ast.List, ast.Tuple)):
            total *= len(cases_arg.elts)

    return total


def count_tests_in_file(filepath: Path) -> int:
    """Count the number of logical test cases in a single Python test file."""
    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return 0

    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                total += _parametrize_expansion(node)
    return total


# ---------------------------------------------------------------------------
# Stats collection
# ---------------------------------------------------------------------------


def collect_stats() -> tuple[list[dict], int]:
    """Collect per-layer stats.

    Returns a list of layer dicts (LAYERS order preserved) each augmented with:
        "files": dict[Path, int]   — per-file counts
        "total": int               — layer total
    and the grand total across all layers.
    """
    grand_total = 0
    result = []
    for layer in LAYERS:
        folder: Path = layer["folder"]
        files: dict[Path, int] = {}
        for py_file in sorted(folder.glob("test_*.py")):
            count = count_tests_in_file(py_file)
            files[py_file] = count
        layer_total = sum(files.values())
        grand_total += layer_total
        result.append({**layer, "files": files, "total": layer_total})
    return result, grand_total


# ---------------------------------------------------------------------------
# Pyramid builder
# ---------------------------------------------------------------------------

# The pyramid template keeps the exact ASCII art shape from test_coverage.md.
# Placeholders: {e2e_n}, {e2e_pct}, {e2e_desc}, {e2e_path},
#               {int_n},  {int_pct},  {int_desc},  {int_path},
#               {cmp_n}, {cmp_pct}, {cmp_desc}, {cmp_path},
#               {unit_n}, {unit_pct}, {unit_desc}, {unit_path},
#               {total}

_PYRAMID_TEMPLATE = """\
```text
              /  E2E  \\              {e2e_n} tests  ({e2e_pct}%)  {e2e_desc}  {e2e_path}
             /----------\\
            / Integration \\           {int_n} tests   ({int_pct}%)  {int_desc}       {int_path}
           /----------------\\
          /    Component      \\      {cmp_n} tests  ({cmp_pct}%)  {cmp_desc}        {cmp_path}
         /--------------------\\
        /        Unit            \\   {unit_n} tests  ({unit_pct}%)  {unit_desc}               {unit_path}
       /------------------------\\
                                     ────────────────
                                     {total} tests total
```"""


def _pct(n: int, total: int) -> int:
    """Integer percentage, rounded."""
    return round(n / total * 100) if total else 0


def build_pyramid(stats: list[dict], grand_total: int) -> str:
    """Render the pyramid code block string from current stats."""
    by_name = {s["name"]: s for s in stats}
    e2e = by_name["E2E"]
    intg = by_name["Integration"]
    cmp = by_name["Component"]
    unit = by_name["Unit"]

    return _PYRAMID_TEMPLATE.format(
        e2e_n=e2e["total"],
        e2e_pct=_pct(e2e["total"], grand_total),
        e2e_desc=e2e["description"],
        e2e_path=e2e["path_label"],
        int_n=intg["total"],
        int_pct=_pct(intg["total"], grand_total),
        int_desc=intg["description"],
        int_path=intg["path_label"],
        cmp_n=cmp["total"],
        cmp_pct=_pct(cmp["total"], grand_total),
        cmp_desc=cmp["description"],
        cmp_path=cmp["path_label"],
        unit_n=unit["total"],
        unit_pct=_pct(unit["total"], grand_total),
        unit_desc=unit["description"],
        unit_path=unit["path_label"],
        total=grand_total,
    )


# ---------------------------------------------------------------------------
# Markdown updater
# ---------------------------------------------------------------------------


def _update_pyramid_block(md: str, new_pyramid: str) -> str:
    """Replace the fenced code block that immediately follows '## Test Pyramid'."""
    pattern = r"(## Test Pyramid\s+)```.*?```"

    def _replacer(m: re.Match) -> str:
        return m.group(1) + new_pyramid

    updated, count = re.subn(pattern, _replacer, md, count=1, flags=re.DOTALL)
    if count == 0:
        raise ValueError("Could not locate '## Test Pyramid' + fenced block in markdown.")
    return updated


def _update_file_table_counts(md: str, stats: list[dict]) -> str:
    """Update Count cells in the '## Test Files' table for every tracked file."""
    for layer in stats:
        for filepath, count in layer["files"].items():
            # The table uses paths like `unit/test_foo.py` (relative to tests/)
            rel = filepath.relative_to(TESTS_DIR).as_posix()
            # Match the table row:  | `unit/test_foo.py`  | Layer  |  <count>  |
            # We replace the count cell (third pipe-delimited cell on that row).
            pattern = r"(\|\s+`" + re.escape(rel) + r"`[^|]*\|[^|]*\|)\s*[~\d]+\s*(\|)"
            replacement = rf"\g<1> {count:>4}  \2"
            md = re.sub(pattern, replacement, md)
    return md


def update_md(stats: list[dict], grand_total: int, dry_run: bool = False, req_stats: dict | None = None) -> None:
    """Read test_coverage.md, apply all updates, write back (or print).

    Expected section order in tests/coverage/test_coverage.md:
      1. Requirements Coverage  (summary table + links to detail files)
      2. Test Pyramid           (ASCII art counts block)
      3. Coverage Matrix        (module × layer table)
      4. Running Tests          (pytest commands)
      5. Test Files             (file × layer × count table)
    """
    md = MD_FILE.read_text(encoding="utf-8")

    new_pyramid = build_pyramid(stats, grand_total)
    md = _update_pyramid_block(md, new_pyramid)
    md = _update_file_table_counts(md, stats)

    if req_stats is not None:
        req_section = build_requirements_summary(req_stats)
        md = _update_requirements_section(md, req_section)
        write_detail_files(req_stats, dry_run=dry_run)

    if dry_run:
        sys.stdout.buffer.write(md.encode("utf-8"))
    else:
        MD_FILE.write_text(md, encoding="utf-8")
        print(f"Updated: {MD_FILE}")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(stats: list[dict], grand_total: int) -> None:
    """Print a human-readable summary to stdout."""
    print(f"\n{'Layer':<14} {'Tests':>6}  {'%':>5}  Files")
    print("-" * 44)
    for layer in stats:
        pct = _pct(layer["total"], grand_total)
        file_list = ", ".join(p.name for p in layer["files"])
        print(f"{layer['name']:<14} {layer['total']:>6}  {pct:>4}%  {file_list}")
    print("-" * 44)
    print(f"{'TOTAL':<14} {grand_total:>6}")
    print()


def print_requirements_report(req_stats: dict) -> None:
    """Print requirements-coverage summary to stdout."""
    o = req_stats["overall"]
    print("Requirements Coverage")
    print("-" * 55)
    print(f"  {'Source':<28} {'Tot':>4} {'OK':>3} {'Par':>4} {'Gap':>4} {'N/T':>4} {'Func%':>6}")
    for src in req_stats["sources"]:
        s = src["summary"]
        print(
            f"  {src['name']:<28} {s['total']:>4} {s['covered']:>3} "
            f"{s['partial']:>4} {s['gap']:>4} {s['nt']:>4} {s['func_pct']:>5}%"
        )
    print("-" * 55)
    print(
        f"  {'ALL':<28} {o['total']:>4} {o['covered']:>3} "
        f"{o['partial']:>4} {o['gap']:>4} {o['nt']:>4} {o['func_pct']:>5}%"
    )
    print()


# ---------------------------------------------------------------------------
# Requirements coverage
# ---------------------------------------------------------------------------

_STATUS_ICON = {
    "covered": "✅",
    "partial": "🔶",
    "gap": "❌",
    "not-testable": "⬜",
}


def collect_requirements_stats() -> dict:
    """Process ALL_REQUIREMENTS and return summary + per-source details.

    Returns dict with keys:
        "sources": list of {name, reqs: list[dict], summary: dict}
        "overall": summary dict with total/covered/partial/gap/nt/func_pct
    """
    sources = []
    overall = {"total": 0, "covered": 0, "partial": 0, "gap": 0, "nt": 0, "functional": 0}

    for source_key, reqs in ALL_REQUIREMENTS.items():
        name = source_key.replace("_", " ").title()
        summary = {"total": 0, "covered": 0, "partial": 0, "gap": 0, "nt": 0, "functional": 0}
        enriched = []

        for req in reqs:
            status = _derive_status(req)
            enriched.append({**req, "status": status})
            summary["total"] += 1
            if status == "covered":
                summary["covered"] += 1
            elif status == "partial":
                summary["partial"] += 1
            elif status == "gap":
                summary["gap"] += 1
            else:
                summary["nt"] += 1
            if req["type"] == "functional":
                summary["functional"] += 1

        func_testable = summary["covered"] + summary["partial"] + summary["gap"]
        summary["func_pct"] = (
            round((summary["covered"] + summary["partial"]) / func_testable * 100) if func_testable else 0
        )

        sources.append({"key": source_key, "name": name, "reqs": enriched, "summary": summary})

        for k in ("total", "covered", "partial", "gap", "nt", "functional"):
            overall[k] += summary[k]

    func_testable = overall["covered"] + overall["partial"] + overall["gap"]
    overall["func_pct"] = round((overall["covered"] + overall["partial"]) / func_testable * 100) if func_testable else 0

    return {"sources": sources, "overall": overall}


def build_requirements_summary(req_stats: dict) -> str:
    """Render the Requirements Coverage summary table with links to detail files."""
    lines: list[str] = []

    # ── Summary table ───────────────────────────────────────────────────
    lines.append("### Summary\n")
    lines.append("| Source | Total | ✅ Covered | 🔶 Partial | ❌ Gap | ⬜ N/T | Functional % | Detail |")
    lines.append("|--------|-------|-----------|------------|-------|--------|--------------|--------|")
    for src in req_stats["sources"]:
        s = src["summary"]
        key = src["key"]
        detail_link = f"[→ detail](requirements/{key}_coverage.md)"
        lines.append(
            f"| {src['name']} | {s['total']} | {s['covered']} | "
            f"{s['partial']} | {s['gap']} | {s['nt']} | {s['func_pct']}% | {detail_link} |"
        )
    o = req_stats["overall"]
    lines.append(
        f"| **All** | **{o['total']}** | **{o['covered']}** | "
        f"**{o['partial']}** | **{o['gap']}** | **{o['nt']}** | **{o['func_pct']}%** |  |"
    )

    return "\n".join(lines)


def build_coverage_detail(src: dict, source_doc: str) -> str:
    """Render a standalone coverage detail markdown file for one requirement source."""
    lines: list[str] = []
    lines.append(f"# {src['name']} — Coverage Detail\n")
    lines.append(
        f"> Source document: [{source_doc}](../../../{source_doc})  \n"
        f"> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)\n"
    )
    s = src["summary"]
    lines.append(
        f"**Total:** {s['total']} | **✅ Covered:** {s['covered']} | "
        f"**🔶 Partial:** {s['partial']} | **❌ Gap:** {s['gap']} | "
        f"**⬜ N/T:** {s['nt']} | **Functional:** {s['func_pct']}%\n"
    )

    # ── Group rows by section ────────────────────────────────────────────
    current_section: str | None = None
    section_rows: list[str] = []

    def _flush() -> None:
        if current_section is not None:
            lines.append(f"\n#### {current_section}\n")
            lines.append("| ID | Requirement | Status | Tests |")
            lines.append("|----|-------------|--------|-------|")
            lines.extend(section_rows)

    for req in src["reqs"]:
        section = req.get("section", "")
        if section != current_section:
            _flush()
            current_section = section
            section_rows.clear()
        icon = _STATUS_ICON[req["status"]]
        tests_cell = ", ".join(f"`{t}`" for t in req["tests"]) if req["tests"] else "—"
        desc = req["description"]
        if len(desc) > 80:
            desc = desc[:77] + "..."
        section_rows.append(f"| {req['id']} | {desc} | {icon} | {tests_cell} |")
    _flush()

    return "\n".join(lines) + "\n"


def write_detail_files(req_stats: dict, dry_run: bool = False) -> None:
    """Write per-source coverage detail files to COVERAGE_REQS_DIR."""
    COVERAGE_REQS_DIR.mkdir(parents=True, exist_ok=True)
    for src in req_stats["sources"]:
        key = src["key"]
        if key not in _DETAIL_FILES:
            continue
        path = _DETAIL_FILES[key]
        content = build_coverage_detail(src, _SOURCE_DOCS[key])
        if dry_run:
            print(f"  [dry-run] Would write: {path.relative_to(REPO_ROOT).as_posix()}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  Written: {path.relative_to(REPO_ROOT).as_posix()}")


def _update_requirements_section(md: str, new_content: str) -> str:
    """Replace everything between '## Requirements Coverage' and the next
    '## ' heading (or end of file)."""
    pattern = r"(## Requirements Coverage\n)\s*(?:.*?)(?=\n## |\Z)"
    replacement = r"\g<1>\n" + new_content + "\n"
    updated, count = re.subn(pattern, replacement, md, count=1, flags=re.DOTALL)
    if count == 0:
        raise ValueError("Could not locate '## Requirements Coverage' section in markdown.")
    return updated


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    stats, grand_total = collect_stats()
    req_stats = collect_requirements_stats()

    print_report(stats, grand_total)
    print_requirements_report(req_stats)
    update_md(stats, grand_total, dry_run=dry_run, req_stats=req_stats)

    if dry_run:
        print("\n[dry-run] No files were modified.")


if __name__ == "__main__":
    main()
