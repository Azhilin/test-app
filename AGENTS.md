# AGENTS.md

Assistant-neutral routing and token-efficiency layer for this repository.
All AI assistants (Claude, Copilot, Cursor, Gemini, etc.) should read this file.
Claude-specific guidance lives in `CLAUDE.md`.

## Authoritative References

Go directly to the source of truth — do not rely on summaries in other files:

| Topic | Authoritative file |
|-------|--------------------|
| All config variables (descriptions + defaults) | `.env.example` |
| Module responsibilities, data flow, layer diagram | `docs/development/architecture.md` |
| Sprint / Issue / metrics_dict dict shapes | `docs/development/architecture.md` |
| CI pipeline stages | `docs/development/pipeline.md` |
| Requirements index (which file to update per area) | `docs/product/requirements/README.md` |
| Metric definitions, required Jira fields, calculation logic | `docs/product/metrics/` |
| Test factories and fixtures | `tests/conftest.py` (root), `tests/unit/conftest.py`, `tests/component/conftest.py` |
| Auto-generated test coverage stats | `tests/coverage/test_coverage.md` |

## Module Map

| File | One-line purpose |
|------|-----------------|
| `main.py` | Thin CLI entry-point; delegates to `app.cli` |
| `server.py` | Thin server entry-point; delegates to `app.server` |
| `app/cli.py` | Full report pipeline: config → fetch → metrics → parallel HTML+MD output |
| `app/server.py` | Stdlib HTTPServer; serves `ui/index.html` and all `/api/*` routes |
| `app/core/config.py` | Loads `.env`, exposes all constants, `validate_config()` |
| `app/core/jira_client.py` | Jira REST wrapper; `fetch_sprint_data()` → `(sprints, sprint_issues)` |
| `app/core/metrics.py` | Pure metric functions; `build_metrics_dict()` → dict consumed by reporters |
| `app/core/schema.py` | Jira field schema registry backed by `config/jira_schema.json` |
| `app/reporters/report_html.py` | Renders `templates/report.html.j2` via Jinja2 |
| `app/reporters/report_md.py` | Builds Markdown report string and writes to disk |
| `app/utils/logging_setup.py` | `setup_logging()` → `(root_logger, log_file_path)`; custom SUCCESS level |
| `app/utils/cert_utils.py` | PEM certificate validation via `cryptography` library |
| `config/jira_schema.json` | Jira field/status definitions per instance (source-controlled) |
| `config/jira_filters.json` | Named JQL filter presets (source-controlled) |
| `templates/report.html.j2` | Jinja2 HTML report template |
| `tests/conftest.py` | Shared factories: `make_sprint`, `make_issue`, `make_issue_with_changelog`, `make_issue_with_labels` |
| `tests/tools/test_coverage.py` | Regenerates `tests/coverage/test_coverage.md`; run after adding/removing tests |

## Slash Commands (`.claude/commands/`)

Workflow helpers invoked via `/command` in Claude Code. All AI assistants can use these:

| Command | Purpose | When to use |
|---------|---------|------------|
| `/requirements` | Find and update requirement files by feature area | Before implementing a feature; to understand acceptance criteria |
| `/implement` | Full feature implementation workflow (7-step checklist) | Implementing a new feature or significant behavior change |
| `/fix` | Bug-fix loop with verification and requirement update | When tests fail or a bug is reported |
| `/sync` | Cross-layer alignment audit (requirements, code, tests, docs) | After completing a feature; periodic maintenance; before release |
| `/test` | Run full CI test suite (lint + type + security + unit + component) | After code changes; before commit |
| `/coverage` | Regenerate test coverage stats; decide whether to fix or remove tests | After adding/removing/renaming test functions |
| `/commit` | Create a git commit following project format rules | After all changes are complete and tested |
| `/lint` | Run lint + type checking + security scanning (no tests) | Quick feedback during development; also `--fix` flag for auto-correct |
| `/extend` | Reference guide: data structures, extension recipes, patterns | Adding a new metric, config var, schema field, or server endpoint |
| `/server` | Start the dev server and list all API routes | During development; serves UI + API proxies |

**When to recommend a command:** If the user's request maps to a workflow step (requirements → implement → test → fix bugs → verify → commit), invoke the matching command as context for Claude's work.

---

## Key Conventions

**Testing pyramid** (`tests/`):
- `unit/` — pure functions, no I/O, no mocks of external services
- `component/` — filesystem + HTTP, no inter-module orchestration
- `integration/` — real multi-module interactions (may need Jira credentials)
- `e2e/` — Playwright browser tests (requires Chromium)
- Run all stages: `python tests/runners/run_all_checks.py`

**Requirements tracking:**
- Every feature area has a `docs/product/requirements/<topic>_requirements.md` file.
- Status values are exactly `✓ Met`, `✗ Not met`, `⬜ N/T` — no other variants.
- Identify which file(s) to update using `docs/product/requirements/README.md`.
- Do not add rows or create new requirements files.

**Configuration system:**
- All config is read from `.env` (copied from `.env.example` at setup).
- New variables: add to `.env.example` first, then add `os.getenv()` in `app/core/config.py`.
- Config module uses module-level constants loaded at import time; tests must use `importlib.reload(config)` to observe env changes.

**Generated output:**
- `generated/` is gitignored; all runtime artifacts (reports, logs, tmp files) go here.
- Do not create disposable files in the project root or alongside source files.

**File placement conventions:**
- Application source: `app/` (core logic, reporters, utils)
- Persistent config: `config/` (JSON files, source-controlled)
- Test suite: `tests/` (layers: `unit/`, `component/`, `integration/`, `e2e/`)
- Docs: `docs/development/` (architecture, pipeline, API refs) and `docs/product/` (metrics, requirements, features)
- Temporary/generated artifacts: `generated/tmp/`, `generated/debug/`, `generated/reports/`
