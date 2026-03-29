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
- `app/cli.py` — primary CLI entry point; `--clean` and `--clean-logs` flags; parallel report generation
- `app/utils/` — shared utilities: `logging_setup.py` (SUCCESS level, `setup_logging()`), `cert_utils.py` (PEM validation)
- `app/reporters/` — HTML and Markdown output generation
- `templates/` — Jinja templates for rendered reports
- `ui/` — browser UI assets including `dau_survey.html` (client-side survey, File System Access API)
- `config/jira_schema.json` — Jira field and status mapping definitions
- `config/jira_filters.json` — named JQL filter presets with env-var-style parameter overrides
- `tests/` — `unit`, `component`, `integration`, and `e2e` layers
- `generated/` — reports (`generated/reports/`), logs (`generated/logs/`), temporary files, diagnostics

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
- Run the app: `python main.py` (delegates to `app/cli.py`; `--clean` removes reports, `--clean-logs` removes logs)
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

## Development workflow

For any non-trivial code change, follow these steps in order. See `.github/instructions/workflow.instructions.md` for full detail.

1. **Maintain requirements** — use `docs/product/requirements/README.md` to find the relevant file(s); update `Status` in affected rows. Do not add rows or create files.
2. **Maintain application functionality** — implement the feature, fix, or refactor.
3. **Maintain tests** — write or update tests in the narrowest layer that proves the behavior.
4. **Complete testing and verification** — run the test suite; fix all failures.
5. **Maintain test coverage** — run `python tests/tools/test_coverage.py` after adding, removing, or renaming test functions.
6. **Maintain project documentation** — update `docs/product/metrics/`, `docs/development/architecture.md`, `README.md`, or `docs/product/features/features.md` when behavior changes.

## Interaction style

**Provide recommendations proactively:**
- While working: flag related issues or improvement opportunities — describe them, don't implement them.
- Before implementing: propose design alternatives with trade-off explanations.
- After finishing: suggest logical follow-up tasks.

**Ask clarifying questions before acting when:**
- The task scope, edge cases, or expected behavior are ambiguous.
- A change touches multiple areas (core + reporters + tests + docs).
- A change might break existing metrics contracts, API shapes, or test expectations.

## Commit Messages

Format: `<type>: <short imperative summary>` (subject line ≤50 chars, no period)

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Rules:

- Imperative mood (`add`, not `added` or `adds`)
- No file names, line numbers, or implementation details in the subject
- Use a short body only when changes span multiple unrelated areas
