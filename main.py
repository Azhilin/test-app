"""
Jira metrics report: fetch data from Jira Cloud, compute metrics, generate HTML and MD reports in parallel.
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

import config
import jira_client
import metrics
import report_html
import report_md

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _timestamp_folder_name(iso_timestamp: str) -> str:
    """Build a filesystem-safe folder name from ISO timestamp (e.g. 2026-03-18T17-27-30)."""
    # Use date and time up to seconds: YYYY-MM-DDTHH:MM:SS -> replace : with -
    prefix = (iso_timestamp or "")[:19]
    return prefix.replace(":", "-") if prefix else "report"


def main() -> int:
    errors = config.validate_config()
    if errors:
        for e in errors:
            print(f"Config error: {e}", file=sys.stderr)
        print("Copy .env.example to .env and set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN.", file=sys.stderr)
        return 1

    jira = jira_client.create_client()
    try:
        sprints, sprint_issues = jira_client.fetch_sprint_data(jira)
    except Exception as e:
        print(f"Failed to fetch Jira data: {e}", file=sys.stderr)
        return 1

    issue_keys = metrics.get_done_issue_keys_for_changelog(sprints, sprint_issues, max_count=100)
    issues_with_changelog = jira_client.get_issues_with_changelog(jira, issue_keys) if issue_keys else []
    metrics_dict = metrics.build_metrics_dict(sprints, sprint_issues, issues_with_changelog)

    folder_name = _timestamp_folder_name(metrics_dict["generated_at"])
    report_dir = REPORTS_DIR / folder_name
    report_dir.mkdir(parents=True, exist_ok=True)

    path_html = report_dir / "report.html"
    path_md = report_dir / "report.md"

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_html = executor.submit(report_html.generate_html, metrics_dict, path_html)
        f_md = executor.submit(report_md.generate_md, metrics_dict, path_md)
        wait([f_html, f_md])
        f_html.result()
        f_md.result()

    print(f"Reports written: {path_html}, {path_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
