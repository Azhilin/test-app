# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Adoption Metrics Report tool — fetches sprint data from Jira Cloud and generates velocity/cycle-time reports in both HTML and Markdown formats.

## Cross-assistant alignment

- `AGENTS.md` is the assistant-neutral routing and token-efficiency layer for this repository.
- Use `AGENTS.md` for shared repo behavior and task scoping; keep this file focused on Claude-specific guidance plus the richer project architecture detail that helps implementation.
- When project structure or workflow conventions change, update shared repo facts in `AGENTS.md` first, then refresh this file only where Claude-specific guidance would otherwise drift.

## Generated and Temporary Files

- Place temporary, scratch, diagnostic, and AI-generated working files under `generated/`.
- Do not create ad hoc files in the repository root or alongside source files unless the user explicitly asks.
- Prefer `generated/tmp/` for one-off temporary files, `generated/debug/` for diagnostics, and `generated/reports/` for report artifacts.
- Delete disposable generated files before finishing when they are no longer needed.
- Do not move or duplicate real source files into `generated/`; this applies only to disposable/generated artifacts.

## Commands

```bash
# Setup
pip install -r requirements.txt        # install into .venv
pip install -r requirements-dev.txt    # install + pytest for testing

# Generate reports (requires .env with Jira credentials)
python main.py                    # outputs to generated/reports/<timestamp>/
python main.py --clean            # delete all generated reports and exit

# Dev server (serves UI + proxies Jira API to avoid CORS)
python server.py                  # http://localhost:8080
python server.py 9000             # custom port

# Run tests (no Jira connection required)
pytest tests/ -v

# Update tests/coverage/test_coverage.md after adding/removing tests (never hand-edit it)
python tests/tools/test_coverage.py
python tests/tools/test_coverage.py --dry-run   # preview only
```

## Commit Messages

Format: `<type>: <short imperative summary>` (subject line ≤50 chars, no period)

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Add a body only when changes span multiple unrelated areas — use 1–3 short bullets, no paragraphs:

```
refactor: extract schema detection into standalone module

- Move field ID lookup out of jira_client
- Add KNOWN_FIELD_SCHEMAS registry in schema.py
- Update metrics to accept schema-driven done_statuses
```

Rules:
- Imperative mood ("add", not "added" or "adds")
- No file names, line numbers, or implementation details in the subject
- Single-area changes need no body: `fix: handle missing story points field gracefully`

## Architecture

**Data flow:** `main.py` orchestrates the pipeline: fetch Jira data → compute metrics → generate HTML + MD reports in parallel (ThreadPoolExecutor).

Key modules (all under `app/`):
- `app/core/config.py` — loads `.env` via python-dotenv, exposes all `JIRA_*` settings as module-level constants, validates required credentials
- `app/core/jira_client.py` — wraps `atlassian-python-api` Jira client; fetches boards, sprints, issues, and changelogs. Supports optional `JIRA_FILTER_ID` to scope issues by saved filter JQL
- `app/core/metrics.py` — pure computation: velocity per sprint (story points of done issues), cycle time stats (from changelog transitions), extensible `compute_custom_trends` placeholder. Accepts optional schema-driven field IDs and status lists
- `app/core/schema.py` — loads/saves/queries Jira field schemas from `config/jira_schema.json`. Provides field ID lookups, status mapping accessors, and auto-detection from Jira's `/rest/api/2/field` response
- `app/reporters/report_html.py` — renders Jinja2 template (`templates/report.html.j2`) to HTML
- `app/reporters/report_md.py` — builds Markdown report with tables and bar chart visualization
- `app/server.py` — stdlib HTTP server serving `ui/index.html`, with `/api/test-connection` (POST), `/api/generate` (SSE), `/api/schemas` (GET/POST/DELETE)

**Config files:**
- `config/jira_schema.json` — Jira field schema definitions (field IDs, status mappings) per Jira instance. Ships with a `Default_Jira_Cloud` entry. Not a generated file — lives alongside source

**Reports output:** `generated/reports/<ISO-timestamp>/report.html` and `report.md`

## Configuration

All config is via `.env` (see `.env.example`). Required: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`. Optional: `JIRA_BOARD_ID`, `JIRA_SPRINT_COUNT` (default 10), `JIRA_SCHEMA_NAME` (which entry in `config/jira_schema.json` to use for CLI), `JIRA_FILTER_ID`.

**Schema system:** `config/jira_schema.json` defines field mappings and status categories per Jira instance. The UI's "Jira Field Schema" card (Filter tab) lets users select or auto-fetch schemas. `metrics.py` reads story points and other field IDs from the active schema; if the JSON file is missing, a built-in default schema is used (`schema.DEFAULT_STORY_POINTS_FIELD_ID` for bare `_get_story_points` calls without a schema).

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
    "schema_name": str|None,      # active schema name, or None if default
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

**Schema dict** (entries in `config/jira_schema.json`, loaded by `app/core/schema.py`):
```python
{
    "schema_name": str,           # unique identifier, e.g. "Default_Jira_Cloud"
    "description": str,
    "jira_url_pattern": str,      # optional URL pattern for auto-matching
    "fields": {
        "<field_key>": {          # e.g. "story_points", "sprint", "team"
            "id": str,            # Jira field ID (e.g. "customfield_10016")
            "type": str,          # "number", "string", "array"
            "jql_name": str|None, # optional JQL field name (e.g. "Team[Team]")
            "description": str
        }
    },
    "status_mapping": {
        "done_statuses": list[str],        # e.g. ["Done", "Closed", "Resolved", "Complete"]
        "in_progress_statuses": list[str]  # e.g. ["In Progress"]
    }
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

**Test coverage stats** in `tests/coverage/test_coverage.md` are auto-generated — never edit the
Test Pyramid block or the Count column by hand. The script also writes per-requirements-source detail
files to `tests/coverage/requirements/` (one file per `*_requirements.md`). Run the script instead
(see `.github/copilot-instructions.md`).

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
1. Add `compute_<name>(sprints, sprint_issues) -> list[dict]` to `app/core/metrics.py`; each dict must include `sprint_id` and `sprint_name` plus the metric value key. Follow the `compute_custom_trends` signature. Accept optional schema-driven parameters (e.g. `done_statuses`) if the metric depends on configurable field IDs or status names.
2. Call it in `build_metrics_dict()` and add result to the returned dict.
3. Add rendering in `app/reporters/report_md.py` (new section after `custom_trends`).
4. Add rendering in `templates/report.html.j2` (metrics context variable).
5. Add `tests/unit/test_<name>.py` using `make_sprint()` and `make_issue()` factories.

**Adding a new Jira field to the schema:**
1. Add the field entry to `_DEFAULT_SCHEMA["fields"]` in `app/core/schema.py`.
2. Add the same entry to the default schema in `config/jira_schema.json`.
3. If the field has a known `schema.custom` identifier, add it to `KNOWN_FIELD_SCHEMAS` in `schema.py`.
4. If it should be detected by name, add patterns to `KNOWN_NAME_PATTERNS` in `schema.py`.
5. Add tests in `tests/unit/test_schema.py`.

**Adding a new config var:**
1. Add to `.env.example` with a comment.
2. Add `os.getenv()` in `app/core/config.py` as module-level constant.
3. Add to `validate_config()` if required.
4. Test in `tests/unit/test_config.py` using `monkeypatch` + `importlib.reload(config)` pattern.
