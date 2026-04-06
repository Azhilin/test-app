# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Cross-assistant alignment

- `AGENTS.md` is the assistant-neutral routing and token-efficiency layer for this repository.
- Use `AGENTS.md` for shared repo conventions, authoritative doc pointers, and module map.
- Keep this file focused on Claude-specific interaction style, workflow, and unique implementation detail.
- When project structure or workflow conventions change, update `AGENTS.md` first, then refresh this file only where Claude-specific guidance would drift.

## Development Workflow

For any non-trivial code change (new feature, behavioral fix, refactor), follow these steps in order:

1. **Maintain requirements** — identify the relevant file(s) using `docs/product/requirements/README.md` (lists all files and their ID prefixes); update the `Status` column (`✓ Met`, `✗ Not met`, `⬜ N/T`) for rows whose acceptance criterion is affected. Do not add rows or create new files.
2. **Maintain application functionality** — implement the feature, fix, or refactor.
3. **Maintain tests** — write or update tests in the narrowest layer that proves the changed behavior.
4. **Complete testing and verification** — run `python tests/runners/run_all_checks.py`; fix all failures before proceeding.
5. **Maintain test coverage** — run `python tests/tools/test_coverage.py` after adding, removing, or renaming test functions.
6. **Maintain project documentation** — update relevant docs when behavior changes:
   - `docs/product/metrics/` — when metric behavior or output shape changes
   - `docs/development/architecture.md` — when modules are added or restructured
   - `README.md` — when setup steps, commands, or project purpose changes
   - `docs/product/features/features.md` — when UI or user-visible behavior changes

## Interaction Style

**Provide recommendations proactively:**
- While working: flag related issues or improvement opportunities — describe them, don't implement them.
- Before implementing: propose design alternatives with trade-off explanations before starting.
- After finishing: suggest logical follow-up tasks (e.g. "the metric doc may also need updating").

**Ask clarifying questions before acting when:**
- The task scope, edge cases, or expected behavior are ambiguous.
- A change touches multiple areas (core + reporters + tests + docs) — ask about priorities or constraints.
- A change might break existing metrics contracts, API shapes, or test expectations.

## Coding Standards

### Design Principles (Python code)

| Principle | Project-specific application |
|-----------|------------------------------|
| **Single Responsibility** | Each module has one job: `metrics.py` computes only, reporters render only, `config.py` reads env only. Never add fetch logic to a reporter. |
| **Open/Closed** | Extend via the Extension Patterns below (new metric, new schema field, new server handler) — don't modify existing function signatures. |
| **DRY** | Shared test data → `conftest.py` factories. Shared field definitions → `config/jira_schema.json`. Never duplicate a computation across reporters. |
| **KISS** | Prefer stdlib and plain `dict` over frameworks and custom classes. `HTTPServer` not Flask; `dict` contracts not dataclasses unless type safety is critical. |
| **YAGNI** | Implement what the task requires; flag (don't build) future needs. No speculative parameters or generalization. |

### Logging Conventions (extends `app/utils/logging_setup.py`)

- Acquire logger per module: `logger = logging.getLogger(__name__)` — never use root logger directly or `print()`.
- Level guidance:
  - `DEBUG` — internal state and raw data dumps
  - `INFO` — flow milestones (started, fetched N items)
  - `SUCCESS` (level 25) — user-visible positive outcomes (report written, server ready)
  - `WARNING` — recoverable problems (missing optional field, fallback used)
  - `ERROR` — failures that stop the current operation
- Never log credential values (Jira tokens, passwords). Log keys and URLs only.
- Log at the call site, not deep inside helpers — keep helper functions side-effect-free.

### UI Design Conventions (for `templates/report.html.j2` and `ui/index.html`)

- **No logic in templates**: `.j2` files receive pre-computed data only; all conditionals and loops that involve business logic belong in `report_html.py`.
- **Semantic HTML**: use `<section>`, `<table>`, `<figure>`, `<nav>` — not bare `<div>` wrappers.
- **Responsive layout**: avoid fixed-width `px` values for containers; prefer `%`, `rem`, or CSS Grid/Flexbox.
- **Accessibility**: include `aria-label` on interactive controls; maintain WCAG AA color contrast (4.5:1 for normal text).

## Generated and Temporary Files

- Place temporary, scratch, diagnostic, and AI-generated working files under `generated/`.
- Do not create ad hoc files in the repository root or alongside source files unless explicitly asked.
- Prefer `generated/tmp/` for one-off temporary files, `generated/debug/` for diagnostics, and `generated/reports/` for report artifacts.
- Delete disposable generated files before finishing when they are no longer needed.
- Do not move or duplicate real source files into `generated/`; this applies only to disposable/generated artifacts.

## Commands

```bash
# Setup
pip install -r requirements.txt        # install into .venv
pip install -r requirements-dev.txt    # install + pytest for testing

# Generate reports (requires .env with Jira credentials)
python main.py                    # delegates to app/cli.py; outputs to generated/reports/<timestamp>/
python main.py --clean            # delete all generated/reports/ and exit
python main.py --clean-logs       # delete all generated/logs/ and exit

# Dev server (serves UI + proxies Jira API to avoid CORS)
python server.py                  # http://localhost:8080
python server.py 9000             # custom port

# Run all CI checks in parallel (lint + unit + component + windows + security)
python tests/runners/run_all_checks.py
python tests/runners/run_all_checks.py --integration   # also run integration tests
python tests/runners/run_all_checks.py --e2e           # also run e2e tests
python tests/runners/run_all_checks.py --all           # run everything

# Run a specific pytest subset directly
pytest tests/ -v

# Update tests/coverage/test_coverage.md after adding/removing tests (never hand-edit it)
python tests/tools/test_coverage.py
python tests/tools/test_coverage.py --dry-run   # preview only
```

## Quick Reference Commands

- Commit message format → `/commit`
- Test factories, fixtures, and conventions → `/test`
- Extension recipes and data structures → `/extend`

## Key Files Quick Reference

Full module responsibilities and data-flow diagrams are in `docs/development/architecture.md`. This table is a quick-lookup map.

| File | Purpose |
|------|---------|
| `main.py` | Thin entry-point; delegates to `app/cli.py` |
| `server.py` | Thin entry-point; delegates to `app/server.py` |
| `app/cli.py` | CLI pipeline: validate config → fetch → compute → parallel HTML+MD report generation |
| `app/core/config.py` | Loads `.env` via python-dotenv; all `JIRA_*` / `AI_*` constants; `validate_config()` |
| `app/core/jira_client.py` | Jira REST wrapper; `fetch_sprint_data()` → `(sprints, sprint_issues)` |
| `app/core/metrics.py` | Pure computation; `build_metrics_dict()` assembles the dict both reporters consume |
| `app/core/schema.py` | Jira field schema registry; load/save/query `config/jira_schema.json` |
| `app/reporters/report_html.py` | Renders `templates/report.html.j2` via Jinja2 |
| `app/reporters/report_md.py` | Builds Markdown report string and writes to disk |
| `app/server.py` | Stdlib HTTPServer; serves `ui/index.html` and all `/api/*` routes |
| `app/utils/logging_setup.py` | `setup_logging()` → `(root_logger, log_file_path)`; custom `SUCCESS_LEVEL=25` |
| `app/utils/cert_utils.py` | `validate_cert(Path)` → `{valid, expires_at, days_remaining, subject}` |
| `config/jira_schema.json` | Jira field/status definitions per instance; ships `Default_Jira_Cloud` entry |
| `config/jira_filters.json` | Named JQL filter registry; source-controlled |
| `templates/report.html.j2` | Jinja2 HTML report template |
| `tests/conftest.py` | Shared factories: `make_sprint`, `make_issue`, `make_issue_with_changelog`, `make_issue_with_labels` |
| `.env.example` | Source of truth for all config variables with inline comments |



