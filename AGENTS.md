# AGENTS.md

## Goal

Help Copilot and other coding agents work accurately in this repository while using as little context as practical.

## Working style

- Start by classifying the task before reading files: `core/schema`, `reporting/ui`, `tests`, or `docs/config`.
- Read the smallest relevant file set first, then expand only if the task proves cross-cutting.
- Prefer exact path references such as `@app/core/schema.py` or `@tests/unit/test_config.py` rather than broad, repo-wide context.
- Reuse existing helpers, fixtures, factories, and file conventions before inventing new abstractions.

## Task routing

- **Metrics, schema, Jira, config:** focus on `app/core/`, `config/jira_schema.json`, and the matching unit tests.
- **Rendering or presentation changes:** focus on `app/reporters/`, `templates/`, and any affected UI or server surface.
- **Browser/server work:** inspect `server.py`, `app/server.py`, `ui/`, and the related tests before touching shared core logic.
- **Tests:** choose the narrowest test layer that fits the change. Use factories from `tests/conftest.py` directly in test bodies.

## Token-efficiency rules

- Keep default prompts scoped to one task and one area of the repo.
- Prefer follow-up prompts that build on already-open context instead of restating the whole problem.
- Do not paste generated reports or large logs unless the exact content matters for the decision.
- Use path-specific instruction files under `.github/instructions/` for deeper conventions instead of growing `.github/copilot-instructions.md`.

## Repository facts worth remembering

- `main.py` orchestrates Jira fetch -> metrics computation -> HTML and Markdown report generation.
- `config/jira_schema.json` is source-controlled and important; it is not a disposable generated file.
- Generated artifacts belong under `generated/`.
- If tests are added, removed, or renamed, refresh coverage stats with `python tests/tools/test_coverage.py`.
