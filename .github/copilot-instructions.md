# Project Instructions

## Repository purpose

This repository generates AI adoption, velocity, and cycle-time reports from Jira Cloud data.
It supports both a CLI-style report pipeline and a local browser UI backed by a lightweight server.

## Keep default context lean

Use this file for repository-wide rules only.
Rely on `.github/instructions/*.instructions.md` for area-specific detail so Copilot does not load deep implementation guidance for every task.
Prefer exact file references such as `@app/core/metrics.py` or `@tests/unit/test_schema.py` instead of pasting large code blocks or logs into prompts.

## Project structure

- `app/core/` — config loading, Jira access, schemas, and metric computation
- `app/reporters/` — HTML and Markdown output generation
- `templates/` — Jinja templates for rendered reports
- `ui/` — browser UI assets
- `config/jira_schema.json` — Jira field and status mapping definitions
- `tests/` — `unit`, `component`, `integration`, and `e2e` layers
- `generated/` — reports, temporary files, and diagnostics

## Editing expectations

Make precise changes in the smallest relevant area before expanding scope.
Preserve schema-driven behavior and reuse existing helpers and test factories instead of duplicating patterns.
If a metrics data shape or report section changes, keep HTML and Markdown outputs logically aligned.

## Generated and temporary files

Place temporary, scratch, diagnostic, or AI-generated working files under `generated/`, not in the repository root or next to source files.

Use these locations by default:

- `generated/tmp/` for one-off temporary files
- `generated/debug/` for diagnostic output
- `generated/reports/` for report artifacts

Delete disposable files before finishing a task when they are no longer needed.
Do not move real source files into `generated/`; this applies only to generated or temporary artifacts.

## Validation commands

- Setup: `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`
- Run the app: `python main.py`
- Run the local server: `python server.py`
- Run tests on Windows: `.venv/Scripts/pytest tests/ -v`

Choose the smallest relevant validation for the task instead of defaulting to the full suite for every change.

## Test Coverage Stats — never hand-edit

`tests/coverage/test_coverage.md` contains auto-generated statistics. Do not edit the Test Pyramid block or the Count column by hand.

When tests are added, removed, or renamed, run:

```bash
python tests/tools/test_coverage.py
```

Use `python tests/tools/test_coverage.py --dry-run` to preview changes without writing.

## Commit Messages

Format: `<type>: <short imperative summary>` (subject line ≤50 chars, no period)

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Rules:

- Imperative mood (`add`, not `added` or `adds`)
- No file names, line numbers, or implementation details in the subject
- Use a short body only when changes span multiple unrelated areas
