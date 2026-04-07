"""
Jira metrics report: fetch data from Jira Cloud, compute metrics, generate HTML and MD reports in parallel.
"""

from __future__ import annotations

import argparse
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

from app.core import config, jira_client, metrics
from app.core import schema as schema_mod
from app.core.dau_normalizer import normalize_dau_responses
from app.reporters import report_html, report_md
from app.utils.logging_setup import SUCCESS_LEVEL

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "generated" / "reports"
LOGS_DIR = PROJECT_ROOT / "generated" / "logs"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--clean", action="store_true", help="Delete the generated/reports/ directory and exit")
    p.add_argument("--clean-logs", action="store_true", help="Delete the generated/logs/ directory and exit")
    return p.parse_args()


def _timestamp_folder_name(iso_timestamp: str) -> str:
    """Build a filesystem-safe folder name from ISO timestamp (e.g. 2026-03-18T17-27-30)."""
    # Use date and time up to seconds: YYYY-MM-DDTHH:MM:SS -> replace : with -
    prefix = (iso_timestamp or "")[:19]
    return prefix.replace(":", "-") if prefix else "report"


def main() -> int:
    args = _parse_args()
    if args.clean:
        if REPORTS_DIR.exists():
            shutil.rmtree(REPORTS_DIR)
            logger.info("generated/reports folder removed.")
        else:
            logger.info("generated/reports folder does not exist.")
        return 0
    if args.clean_logs:
        if LOGS_DIR.exists():
            shutil.rmtree(LOGS_DIR)
            logger.info("generated/logs folder removed.")
        else:
            logger.info("generated/logs folder does not exist.")
        return 0

    errors = config.validate_config()
    if errors:
        for e in errors:
            logger.error("Config error: %s", e)
        logger.error("Copy .env.example to .env and set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN.")
        return 1

    jira = jira_client.create_client()
    try:
        if config.PROJECT_TYPE == "KANBAN":
            sprints, sprint_issues = jira_client.fetch_kanban_data(jira)
        else:
            sprints, sprint_issues = jira_client.fetch_sprint_data(jira)
    except Exception as e:
        logger.error("Failed to fetch Jira data: %s", jira_client._sanitise_error(str(e)))
        if "certificate verify failed" in str(e).lower():
            logger.error(
                "SSL certificate verification failed. "
                "Open the browser UI \u2192 Jira Connection tab \u2192 click 'Fetch Certificate', "
                "then re-run the report. Or run: python tools/fetch_ssl_cert.py"
            )
        return 1

    active_schema = schema_mod.get_active_schema(schema_name=config.JIRA_SCHEMA_NAME)

    if config.METRIC_DAU or config.METRIC_DAU_TREND:
        normalize_dau_responses(config.DAU_RESPONSES_DIR, config.DAU_NORMALIZED_DIR)

    metrics_dict = metrics.build_metrics_dict(sprints, sprint_issues, schema=active_schema)

    # Enrich with filter metadata for display in the report header
    if config.JIRA_FILTER_ID is not None:
        metrics_dict["filter_id"] = config.JIRA_FILTER_ID
        filter_jql = jira_client.get_filter_jql(jira)
        if filter_jql:
            metrics_dict["filter_jql"] = filter_jql
        try:
            f = jira._session.get(f"{config.JIRA_URL}/rest/api/2/filter/{config.JIRA_FILTER_ID}").json()
            metrics_dict["filter_name"] = f.get("name") or None
        except Exception:  # nosec B110
            pass  # filter name is non-critical metadata; failure is safe to ignore
    if config.JIRA_PROJECT:
        metrics_dict["project_key"] = config.JIRA_PROJECT

    folder_name = _timestamp_folder_name(metrics_dict["generated_at"])
    report_dir = REPORTS_DIR / folder_name
    report_dir.mkdir(parents=True, exist_ok=True)

    path_html = report_dir / "report.html"
    path_md = report_dir / "report.md"

    section_visibility = {
        "velocity_trend": config.METRIC_VELOCITY,
        "ai_assistance_trend": config.METRIC_AI_ASSISTANCE_TREND,
        "ai_usage_details": config.METRIC_AI_USAGE_DETAILS,
        "dau": config.METRIC_DAU,
        "dau_trend": config.METRIC_DAU_TREND,
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_html = executor.submit(report_html.generate_html, metrics_dict, path_html, section_visibility)
        f_md = executor.submit(report_md.generate_md, metrics_dict, path_md, section_visibility)
        wait([f_html, f_md])
        f_html.result()
        f_md.result()

    logger.log(SUCCESS_LEVEL, "Reports written: %s, %s", path_html, path_md)
    return 0
