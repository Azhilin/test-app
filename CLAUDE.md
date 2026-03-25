# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Adoption Metrics Report tool — fetches sprint data from Jira Cloud and generates velocity/cycle-time reports in both HTML and Markdown formats.

## Commands

```bash
# Setup
pip install -r requirements.txt        # install into .venv
pip install -r requirements-dev.txt    # install + pytest for testing

# Generate reports (requires .env with Jira credentials)
python main.py                    # outputs to reports/<timestamp>/
python main.py --clean            # delete all generated reports and exit

# Dev server (serves UI + proxies Jira API to avoid CORS)
python server.py                  # http://localhost:8080
python server.py 9000             # custom port

# Run tests (no Jira connection required)
pytest tests/ -v
```

## Architecture

**Data flow:** `main.py` orchestrates the pipeline: fetch Jira data → compute metrics → generate HTML + MD reports in parallel (ThreadPoolExecutor).

Key modules (all under `app/`):
- `app/config.py` — loads `.env` via python-dotenv, exposes all `JIRA_*` settings as module-level constants, validates required credentials
- `app/jira_client.py` — wraps `atlassian-python-api` Jira client; fetches boards, sprints, issues, and changelogs. Supports optional `JIRA_FILTER_ID` to scope issues by saved filter JQL
- `app/metrics.py` — pure computation: velocity per sprint (story points of done issues), cycle time stats (from changelog transitions), extensible `compute_custom_trends` placeholder
- `app/report_html.py` — renders Jinja2 template (`templates/report.html.j2`) to HTML
- `app/report_md.py` — builds Markdown report with tables and bar chart visualization
- `server.py` — stdlib HTTP server serving `ui/index.html`, with `/api/test-connection` (POST) and `/api/generate` (SSE stream that runs `main.py` as subprocess)

**Reports output:** `reports/<ISO-timestamp>/report.html` and `report.md`

## Configuration

All config is via `.env` (see `.env.example`). Required: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`. Optional: `JIRA_BOARD_ID`, `JIRA_SPRINT_COUNT` (default 10), `JIRA_STORY_POINTS_FIELD` (default `customfield_10016`), `JIRA_FILTER_ID`.

## Tech Stack

Python 3.12+, atlassian-python-api, python-dotenv, pandas, jinja2, requests. Virtual env in `.venv/`. Test deps: pytest, pytest-mock (see `requirements-dev.txt`).

## Data Structures

Exact dict shapes crossing module boundaries:

**Sprint dict** (Jira API / `make_sprint` factory):
```python
{id: int, name: str, startDate: str|None, endDate: str|None}
# Note: no "state" field — compute_velocity does not filter by state
```

**Issue dict** (Jira API / `make_issue` factory):
```python
{key: str, fields: {status: {name: str}, customfield_10016: float|None, ...}}
```

**Issue-with-changelog dict** (`get_issues_with_changelog` / `make_issue_with_changelog`):
```python
{key: str, fields: {status: {name: str}},
 changelog: {histories: [{created: str (ISO-8601+tz), items: [{field, fromString, toString}]}]}}
# IMPORTANT: created timestamps must be timezone-aware (e.g. "2026-03-01T10:00:00+00:00")
# Naive datetimes cause _parse_iso() to return None → cycle time returns None
```

**metrics_dict** (built by `build_metrics_dict`, consumed by both reporters):
```python
{
    "generated_at": str,          # ISO-8601 UTC
    "velocity": [
        {sprint_id, sprint_name, start_date, end_date, velocity: float, issue_count: int}
    ],
    "cycle_time": {
        mean_days, median_days, min_days, max_days: float|None,
        sample_size: int,
        values: list[float]
    },
    "custom_trends": list[dict]   # see Extension Patterns below
}
```

## Testing Conventions

```bash
# Run all tests (Windows)
.venv/Scripts/pytest tests/ -v
# Run all tests (Mac/Linux)
.venv/bin/pytest tests/ -v
# Run subset
.venv/Scripts/pytest tests/ -v -k "test_velocity"
```

**Test factories** in `tests/conftest.py` are plain functions (not fixtures) — call directly in test body:
- `make_sprint(id, name="", start=None, end=None)` — omit state; metrics don't filter on it
- `make_issue(key, status="Done", points=5.0, story_points_field="customfield_10016")`
- `make_issue_with_changelog(key, in_progress_ts=None, done_ts=None)` — timestamps must be ISO-8601 with timezone offset

**Pytest fixtures** (inject via function arg, not call):
- `minimal_metrics_dict` — metrics dict with sample data
- `empty_metrics_dict` — metrics dict with no velocity/cycle-time data

**Config tests** use `importlib.reload(config)` with `monkeypatch.setenv(...) / delenv(...)` to re-parse module-level constants.

## Extension Patterns

**Adding a new metric:**
1. Add `compute_<name>(sprints, sprint_issues) -> list[dict]` to `app/metrics.py`; each dict must include `sprint_id` and `sprint_name` plus the metric value key. Follow the `compute_custom_trends` signature.
2. Call it in `build_metrics_dict()` and add result to the returned dict.
3. Add rendering in `app/report_md.py` (new section after `custom_trends`).
4. Add rendering in `templates/report.html.j2` (metrics context variable).
5. Add `tests/test_<name>.py` using `make_sprint()` and `make_issue()` factories.

**Adding a new config var:**
1. Add to `.env.example` with a comment.
2. Add `os.getenv()` in `app/config.py` as module-level constant.
3. Add to `validate_config()` if required.
4. Test in `tests/test_config.py` using `monkeypatch` + `importlib.reload(config)` pattern.
