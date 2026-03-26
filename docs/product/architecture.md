# Architecture — AI Adoption Metrics Report

> A reference for Python developers working on or extending this tool.

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Layout](#3-project-layout)
4. [Architecture & Module Map](#4-architecture--module-map)
5. [Data Flow](#5-data-flow)
6. [Configuration Reference](#6-configuration-reference)
7. [Dev Server API Routes](#7-dev-server-api-routes)
8. [Report Output](#8-report-output)
9. [Testing Strategy](#9-testing-strategy)
10. [Extension Patterns](#10-extension-patterns)
11. [Setup & Running](#11-setup--running)

---

## 1. Product Overview

**AI Adoption Metrics Report** connects to Jira Cloud via its REST API, fetches sprint and issue data, computes engineering metrics, and generates self-contained reports in two formats:

| Format | Output |
|--------|--------|
| HTML | Interactive report with charts (`report.html`) |
| Markdown | Plain-text summary with tables (`report.md`) |

### Metrics computed

| Metric | Description |
|--------|-------------|
| **Velocity trend** | Story points of done issues per sprint |
| **Cycle time** | Days from "In Progress" to "Done" per issue (mean, median, min, max) |
| **AI assistance trend** | Per-sprint percentage of done story points carrying the AI-assisted label |
| **AI usage breakdown** | Distribution of AI tool labels and AI use-case labels across AI-assisted issues |

Both the browser UI (`server.py`) and the CLI (`main.py`) produce the same reports from the same pipeline.

---

## 2. Technology Stack

### Runtime

| Package | Version | Role |
|---------|---------|------|
| Python | 3.12+ | Language runtime |
| [atlassian-python-api](https://atlassian-python-api.readthedocs.io/) | >=3.41.0 | Jira Cloud REST client (boards, sprints, issues, changelogs) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | >=1.0.0 | `.env` file loading |
| [Jinja2](https://jinja.palletsprojects.com/) | >=3.1.0 | HTML report templating |
| [requests](https://docs.python-requests.org/) | >=2.28.0 | Transitive HTTP dependency (used by atlassian-python-api) |
| [pandas](https://pandas.pydata.org/) | >=2.0.0 | Available for future metric computation (not yet used in core pipeline) |
| [cryptography](https://cryptography.io/) | >=42.0.0 | PEM certificate validation (`app/utils/cert_utils.py`) |

### Dev / test

| Package | Version | Role |
|---------|---------|------|
| [pytest](https://docs.pytest.org/) | >=8.0.0 | Test runner |
| [pytest-mock](https://pytest-mock.readthedocs.io/) | >=3.12.0 | `mocker` fixture for mocking |
| [pytest-playwright](https://playwright.dev/python/) | >=0.6.2 | Browser-based E2E tests |
| Chromium | (installed by Playwright) | E2E browser |

### Stdlib modules used

`argparse`, `base64`, `concurrent.futures`, `http.server`, `json`, `os`, `pathlib`, `shutil`, `ssl`, `subprocess`, `sys`, `threading`, `urllib`, `webbrowser`

---

## 3. Project Layout

```
test-app/                          ← project root
│
├── main.py                        ← thin CLI entry-point (delegates to app.cli)
├── server.py                      ← thin server entry-point (delegates to app.server)
│
├── app/                           ← application package
│   ├── __init__.py
│   ├── cli.py                     ← CLI pipeline orchestration
│   ├── server.py                  ← dev HTTP server (stdlib HTTPServer)
│   │
│   ├── core/                      ← business logic & infrastructure
│   │   ├── __init__.py
│   │   ├── config.py              ← env/dotenv loading, validation, constants
│   │   ├── jira_client.py         ← Jira REST API wrapper
│   │   └── metrics.py             ← pure metric computation functions
│   │
│   ├── reporters/                 ← output formatters
│   │   ├── __init__.py
│   │   ├── report_html.py         ← Jinja2 HTML report renderer
│   │   └── report_md.py           ← Markdown report builder
│   │
│   └── utils/                     ← shared utilities
│       ├── __init__.py
│       └── cert_utils.py          ← PEM certificate validation
│
├── templates/
│   └── report.html.j2             ← Jinja2 HTML template
│
├── ui/
│   └── index.html                 ← single-file browser UI (served by app.server)
│
├── tests/                         ← pytest suite
│   ├── conftest.py                ← shared factories + server_url fixture
│   ├── unit/                      ← pure-function tests, no I/O
│   ├── component/                 ← filesystem + HTTP tests, no inter-module orchestration
│   ├── integration/               ← multi-module integration tests
│   ├── e2e/                       ← Playwright browser tests
│   └── tools/
│       └── test_coverage.py       ← auto-generates tests/test_coverage.md
│
├── docs/                          ← reference docs (Jira/Confluence API guides)
├── certs/                         ← optional TLS bundle (jira_ca_bundle.pem)
├── generated/                     ← report output (gitignored)
│   └── reports/
│       └── <ISO-timestamp>/
│           ├── report.html
│           └── report.md
│
├── tools/                         ← helper scripts (fetch_ssl_cert.py, diagnostics)
├── requirements.txt               ← runtime dependencies
├── requirements-dev.txt           ← runtime + test dependencies
├── pyproject.toml                 ← pytest config + Playwright config
├── .env.example                   ← configuration template copied to .env during setup
├── project_setup.bat              ← one-time Windows setup script
└── start_app.bat                  ← Windows launcher (starts server.py)
```

---

## 4. Architecture & Module Map

### Layer diagram

```
┌─────────────────────────────────────────────────────┐
│  Entry points (root)                                │
│  main.py  ──►  app/cli.py                           │
│  server.py ──► app/server.py                        │
└────────────────────┬────────────────────────────────┘
                     │
       ┌─────────────▼──────────────┐
       │  app/core/                 │
       │  config.py   ← dotenv      │
       │  jira_client.py ← Jira API │
       │  metrics.py  ← pure logic  │
       └─────────────┬──────────────┘
                     │ metrics_dict
       ┌─────────────▼──────────────┐
       │  app/reporters/            │
       │  report_html.py ← Jinja2   │
       │  report_md.py  ← str build │
       └─────────────┬──────────────┘
                     │
       ┌─────────────▼──────────────┐
       │  generated/reports/        │
       │  <timestamp>/report.html   │
       │  <timestamp>/report.md     │
       └────────────────────────────┘

  app/utils/cert_utils.py  ← used by app/server.py (/api/cert-status)
  templates/report.html.j2 ← used by app/reporters/report_html.py
  ui/index.html            ← served by app/server.py at /
```

### Module responsibilities

| Module | Responsibility |
|--------|----------------|
| `app/core/config.py` | Loads `.env` from project root via `python-dotenv`. Exposes all `JIRA_*` and `AI_*` constants as module-level names. `validate_config()` returns a list of error strings. |
| `app/core/jira_client.py` | Wraps `atlassian-python-api`. `create_client()` returns an authenticated `Jira` instance. `fetch_sprint_data()` returns `(sprints, sprint_issues)`. Handles pagination and optional filter JQL. |
| `app/core/metrics.py` | Pure functions: `compute_velocity`, `compute_cycle_time`, `compute_ai_assistance_trend`, `compute_ai_usage_details`, `compute_custom_trends` (placeholder). `build_metrics_dict()` assembles all results into a single dict consumed by both reporters. |
| `app/reporters/report_html.py` | Renders `templates/report.html.j2` via Jinja2. Accepts a `section_visibility` dict to hide/show individual report sections. |
| `app/reporters/report_md.py` | Builds a Markdown string (velocity bar chart, tables, cycle time stats) and writes to disk. |
| `app/utils/cert_utils.py` | `validate_cert(Path)` — parses a PEM file with `cryptography`, returns a dict: `{valid, expires_at, days_remaining, subject}` (plus `error` on failure). |
| `app/cli.py` | Orchestrates the full report pipeline. Validates config, fetches Jira data, computes metrics, enriches with filter metadata, and generates HTML + MD in parallel via `ThreadPoolExecutor(max_workers=2)`. |
| `app/server.py` | Stdlib `HTTPServer` dev server. Serves the UI, proxies Jira test-connection (avoids CORS), streams `main.py` output as SSE, and exposes config/cert management APIs. |
| `main.py` | Thin entry-point — re-exports `main`, `_parse_args`, `_timestamp_folder_name` from `app.cli` for test compatibility. |
| `server.py` | Thin entry-point — re-exports `run`, `Server`, `Handler`, `PORT`, `ROOT`, `MIME`, `guess_mime` from `app.server` for test compatibility. |

### Key data structures

**Sprint dict** (from Jira API / `make_sprint` factory):
```python
{"id": int, "name": str, "startDate": str | None, "endDate": str | None}
```

**Issue dict** (from Jira API / `make_issue` factory):
```python
{"key": str, "fields": {"status": {"name": str}, "customfield_10016": float | None, ...}}
```

**Issue-with-changelog dict**:
```python
{
    "key": str,
    "fields": {"status": {"name": str}},
    "changelog": {
        "histories": [
            {"created": str,  # ISO-8601 with timezone — must be tz-aware
             "items": [{"field": str, "fromString": str, "toString": str}]}
        ]
    }
}
```

**metrics_dict** (built by `build_metrics_dict`, consumed by both reporters):
```python
{
    "generated_at": str,           # ISO-8601 UTC
    "velocity": [
        {"sprint_id": int, "sprint_name": str, "start_date": str | None,
         "end_date": str | None, "velocity": float, "issue_count": int}
    ],
    "cycle_time": {
        "mean_days": float | None, "median_days": float | None,
        "min_days": float | None, "max_days": float | None,
        "sample_size": int, "values": list[float]
    },
    "ai_assistance_trend": [
        {"sprint_id": int, "sprint_name": str, "start_date": str | None,
         "end_date": str | None, "total_sp": float, "ai_sp": float, "ai_pct": float}
    ],
    "ai_usage_details": {
        "ai_assisted_issue_count": int,
        "tool_breakdown": [{"label": str, "count": int, "pct": float}],
        "action_breakdown": [{"label": str, "count": int, "pct": float}]
    },
    "custom_trends": list[dict],   # extensible; empty by default
    "ai_assisted_label": str,
    "ai_exclude_labels": list[str],
    "filter_name": str | None,     # enriched after Jira fetch
    "filter_id": int | None,
    "filter_jql": str | None,
    "project_key": str | None,
}
```

---

## 5. Data Flow

### CLI pipeline (`main.py` / `app/cli.py`)

```
python main.py
      │
      ▼
app.core.config.validate_config()
      │  errors → stderr + exit 1
      ▼
app.core.jira_client.create_client()
      │
      ▼
app.core.jira_client.fetch_sprint_data(jira)
      │  → sprints: list[dict]
      │  → sprint_issues: dict[sprint_id, list[issue]]
      ▼
app.core.metrics.get_done_issue_keys_for_changelog(...)
      │  → up to 100 done-issue keys, most recent first
      ▼
app.core.jira_client.get_issues_with_changelog(jira, keys)
      │  → issues_with_changelog: list[dict]
      ▼
app.core.metrics.build_metrics_dict(sprints, sprint_issues, issues_with_changelog)
      │  → metrics_dict: dict
      ▼
  [optional] enrich with filter name/JQL via Jira REST
      │
      ▼
  ThreadPoolExecutor(max_workers=2)
      ├── app.reporters.report_html.generate_html(metrics_dict, path_html)
      └── app.reporters.report_md.generate_md(metrics_dict, path_md)
      │
      ▼
generated/reports/<YYYY-MM-DDTHH-MM-SS>/
      ├── report.html
      └── report.md
```

### Dev server flow (`server.py` / `app/server.py`)

```
browser → GET /             → serve ui/index.html
browser → POST /api/config  → write .env fields
browser → POST /api/test-connection → proxy to Jira /rest/api/3/myself
browser → GET /api/generate → spawn subprocess: python main.py
                               stream stdout/stderr as SSE events
browser → GET /api/cert-status → app.utils.cert_utils.validate_cert(...)
browser → POST /api/fetch-cert → ssl.get_server_certificate → certs/jira_ca_bundle.pem
browser → GET /generated/reports/... → serve static report files
```

---

## 6. Configuration Reference

All configuration is read from a `.env` file in the project root (or from environment variables). Copy `.env.example` to `.env` to get started.

### Required

| Variable | Type | Description |
|----------|------|-------------|
| `JIRA_URL` | `str` | Base URL of your Jira instance, e.g. `https://your-domain.atlassian.net` |
| `JIRA_EMAIL` | `str` | Atlassian account email |
| `JIRA_API_TOKEN` | `str` | API token from [Atlassian security settings](https://id.atlassian.com/manage-profile/security/api-tokens) |

### Optional

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JIRA_BOARD_ID` | `int` | first available board | Numeric board ID; auto-detected if unset |
| `JIRA_SPRINT_COUNT` | `int` | `10` | Number of past sprints to include |
| `JIRA_STORY_POINTS_FIELD` | `str` | `customfield_10016` | Jira custom field key for story points |
| `JIRA_FILTER_ID` | `int` | `None` | Saved filter ID; when set, only matching issues are included |
| `PORT` | `int` | `8080` | Dev server port |
| `AI_ASSISTED_LABEL` | `str` | `AI_assistance` | Issue label marking AI-assisted work |
| `AI_EXCLUDE_LABELS` | `str` | `` | Comma-separated labels excluded from the AI% denominator |
| `AI_TOOL_LABELS` | `str` | `` | Comma-separated labels identifying AI tools (e.g. `AI_Tool_Copilot,AI_Tool_ChatGPT`) |
| `AI_ACTION_LABELS` | `str` | `` | Comma-separated labels identifying AI use-cases (e.g. `AI_Case_CodeGen,AI_Case_Review`) |

### SSL / TLS

If your Jira instance uses a custom CA, place the PEM bundle at `certs/jira_ca_bundle.pem`. The config module auto-detects this file and passes its path as `verify_ssl` to the Jira client. To fetch and save the certificate:

```bash
# CLI
python tools/fetch_ssl_cert.py

# UI: click "Fetch Certificate" on the Jira Connection tab
```

---

## 7. Dev Server API Routes

All routes are served by `app/server.py` (stdlib `HTTPServer`). CORS headers (`Access-Control-Allow-Origin: *`) are included on all JSON responses.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` or `/index.html` | Serve `ui/index.html` |
| `GET` | `/api/config` | Return current `.env` values (token masked as `***`) |
| `POST` | `/api/config` | Write `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` to `.env` |
| `POST` | `/api/test-connection` | Proxy credentials test to `JIRA_URL/rest/api/3/myself` |
| `GET` | `/api/generate` | Run `main.py` as subprocess; stream stdout/stderr as SSE |
| `GET` | `/api/cert-status` | Return cert existence and validity from `certs/jira_ca_bundle.pem` |
| `POST` | `/api/fetch-cert` | Fetch TLS cert from Jira host via `ssl.get_server_certificate` and save to `certs/` |
| `GET` | `/generated/reports/<path>` | Serve any file under `generated/reports/` |
| `OPTIONS` | `*` | CORS preflight (returns 204) |

### SSE event types (`GET /api/generate`)

| Event | Meaning |
|-------|---------|
| `message` | A line of stdout/stderr from `main.py` |
| `done` | `main.py` exited with code 0; data is `__done__` |
| `error` | `main.py` exited non-zero or raised; data is `__error__:<message>` |
| `close` | Stream is closing |

---

## 8. Report Output

Each run writes to a new timestamped directory:

```
generated/
└── reports/
    └── 2026-03-26T14-30-00/    ← YYYY-MM-DDTHH-MM-SS (colons replaced with dashes)
        ├── report.html          ← fully self-contained HTML (inline CSS + Chart.js)
        └── report.md            ← Markdown with ASCII bar chart and tables
```

To delete all generated reports:

```bash
python main.py --clean
```

The `generated/` directory is gitignored.

---

## 9. Testing Strategy

### Test pyramid

```
E2E          (Playwright, real browser)       tests/e2e/
Integration  (real module interactions)       tests/integration/
Component    (filesystem + HTTP, no mocks)    tests/component/
Unit         (pure functions, no I/O)         tests/unit/
```

Current counts (run `python tests/tools/test_coverage.py` to refresh):

| Layer | Count | Files |
|-------|-------|-------|
| Unit | ~115 | test_cert_validation, test_config, test_imports, test_jira_client, test_main_helpers, test_metrics |
| Component | ~76 | test_contracts, test_report_html, test_report_md, test_server |
| Integration | ~6 | test_integration |
| E2E | ~24 | test_e2e, test_e2e_ui |

### Running tests

```bash
# All unit + component (fast; no Jira connection)
.venv/Scripts/pytest tests/unit/ tests/component/ -v

# Single layer
.venv/Scripts/pytest tests/unit/ -v
.venv/Scripts/pytest tests/component/ -v

# By marker
.venv/Scripts/pytest -m unit -v
.venv/Scripts/pytest -m "not e2e" -v

# Integration (requires real Jira credentials in .env)
.venv/Scripts/pytest tests/integration/ -v

# E2E (requires Playwright browsers installed)
.venv/Scripts/pytest tests/e2e/ -v

# Regenerate tests/test_coverage.md
python tests/tools/test_coverage.py
```

### Key test helpers (`tests/conftest.py`)

These are plain functions (not pytest fixtures) — call them directly in test bodies:

```python
make_sprint(id, name="", start=None, end=None) -> dict
make_issue(key, status="Done", points=5.0, story_points_field="customfield_10016") -> dict
make_issue_with_changelog(key, in_progress_ts=None, done_ts=None) -> dict
make_issue_with_labels(key, status="Done", points=5.0, labels=None, ...) -> dict
```

Timestamps passed to `make_issue_with_changelog` **must be timezone-aware ISO-8601** strings (e.g. `"2026-03-01T10:00:00+00:00"`). Naive datetimes cause `_parse_iso()` to return `None`, making cycle time return `None`.

### Pytest fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `server_url` | function | Starts a real `Server` on a random port in a daemon thread; yields base URL; shuts down after test |
| `mock_jira` | function | `MagicMock` pre-configured as a Jira client (in `tests/unit/conftest.py`) |
| `minimal_metrics_dict` | function | Metrics dict with sample data (in `tests/component/conftest.py`) |
| `empty_metrics_dict` | function | Metrics dict with no velocity/cycle-time data |

### Config tests pattern

`app/core/config` uses module-level constants loaded at import time. To test different env values:

```python
import importlib, os
from unittest.mock import patch

def _reload_config(env: dict):
    with patch.dict(os.environ, env, clear=True):
        import app.core.config as cfg
        importlib.reload(cfg)
        return cfg
```

---

## 10. Extension Patterns

### Adding a new metric

1. Add `compute_<name>(sprints, sprint_issues) -> list[dict]` to `app/core/metrics.py`. Each dict must include `sprint_id` and `sprint_name` plus the metric value key.
2. Call it in `build_metrics_dict()` and include the result in the returned dict.
3. Add rendering in `app/reporters/report_md.py` (new section after `custom_trends`).
4. Add rendering in `templates/report.html.j2`.
5. Add `tests/unit/test_<name>.py` using `make_sprint()` and `make_issue()` factories.

### Adding a new config variable

1. Add to `.env.example` with a descriptive comment.
2. Add `os.getenv(...)` in `app/core/config.py` as a module-level constant.
3. Add to `validate_config()` if the variable is required.
4. Test in `tests/unit/test_config.py` using `monkeypatch` + `importlib.reload(config)` pattern.

### Extending the dev server

Add a new method `_handle_<name>(self)` to the `Handler` class in `app/server.py`, then route to it from `do_GET` or `do_POST`. Cover it with a test in `tests/component/test_server.py` using the `server_url` fixture.

---

## 11. Setup & Running

### First-time setup (Windows)

```bat
:: Installs Python 3.12 (per-user), creates .venv, installs requirements.txt, bootstraps .env
project_setup.bat
```

### Cross-platform setup

```bash
python3.12 -m venv .venv
# Windows:
.venv\Scripts\pip install -r requirements.txt
# macOS/Linux:
.venv/bin/pip install -r requirements.txt
```

### Configure credentials

```bash
cp .env.example .env
# Edit .env and set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
```

### Run the browser UI (recommended)

```bat
:: Windows shortcut — starts server.py and opens http://localhost:8080
start_app.bat
```

```bash
# Cross-platform
.venv/Scripts/python server.py        # Windows
.venv/bin/python server.py            # macOS/Linux
python server.py 9000                 # custom port
```

### Generate reports via CLI

```bash
.venv/Scripts/python main.py          # generate reports
.venv/Scripts/python main.py --clean  # delete all generated reports
```

### Install dev dependencies and run tests

```bash
.venv/Scripts/pip install -r requirements-dev.txt

# Unit + component tests (no Jira connection needed)
.venv/Scripts/pytest tests/unit/ tests/component/ -v

# Install Playwright browsers (for E2E tests)
.venv/Scripts/playwright install chromium
.venv/Scripts/pytest tests/e2e/ -v
```

---

## See Also

- [`README.md`](../README.md) — user-facing quickstart
- [`CLAUDE.md`](../CLAUDE.md) — AI assistant guidance and coding conventions
- [`docs/jira/`](../docs/jira/) — Jira REST API reference notes
- [`docs/confluence/`](../docs/confluence/) — Confluence API reference notes
- [`tests/test_coverage.md`](../tests/test_coverage.md) — auto-generated test count table
- [`.env.example`](../.env.example) — all configuration variables with comments
