# AGENTS.md

## Goal

Help Copilot and other coding agents work accurately in this repository while using as little context as practical.

## Working style

- Start by classifying the task before reading files: `core/schema`, `reporting/ui`, `tests`, or `docs/config`.
- Read the smallest relevant file set first, then expand only if the task proves cross-cutting.
- Prefer exact path references such as `@app/core/schema.py` or `@tests/unit/test_config.py` rather than broad, repo-wide context.
- Reuse existing helpers, fixtures, factories, and file conventions before inventing new abstractions.

## Task routing

- **Metrics, schema, Jira, config:** focus on `app/core/`, `config/jira_schema.json`, `config/jira_filters.json`, and the matching unit tests.
- **Utilities (logging, certs, new helpers):** focus on `app/utils/`, `app/cli.py` (consumer), and `tests/unit/` for the affected utility.
- **Rendering or presentation changes:** focus on `app/reporters/`, `templates/`, and any affected UI or server surface.
- **Browser/server work:** inspect `server.py`, `app/server.py`, `ui/`, and the related tests before touching shared core logic.
- **Tests:** choose the narrowest test layer that fits the change. Use factories from `tests/conftest.py` directly in test bodies.
- **Filter presets:** `config/jira_filters.json` is source-controlled (named JQL presets + env-var-style overrides); treat it like `config/jira_schema.json`, not generated output.

## Development workflow

For any non-trivial code change (new feature, behavioral fix, refactor), follow these steps in order:

1. **Maintain requirements** — identify the relevant file(s) using `docs/product/requirements/README.md` (lists all files and their ID prefixes); update the `Status` column (`✓ Met`, `✗ Not met`, `⬜ N/T`) for rows whose acceptance criterion is affected. Do not add rows or create new files.
2. **Maintain application functionality** — implement the feature, fix, or refactor.
3. **Maintain tests** — write or update tests in the narrowest layer that proves the changed behavior.
4. **Complete testing and verification** — run the test suite and `tests/runners/run_lint.bat`; fix all failures before proceeding. The pre-commit hook enforces lint automatically on `git commit` once installed.
5. **Maintain test coverage** — run `python tests/tools/test_coverage.py` after adding, removing, or renaming test functions.
6. **Maintain project documentation** — update relevant docs when behavior changes:
   - `docs/product/metrics/` — when metric behavior or output shape changes
   - `docs/development/architecture.md` — when modules are added or restructured
   - `README.md` — when setup steps, commands, or project purpose changes
   - `docs/product/features/features.md` — when UI or user-visible behavior changes

## Interaction style

**Provide recommendations proactively:**
- While working: flag related issues or improvement opportunities — describe them, don't implement them.
- Before implementing: propose design alternatives with trade-off explanations before starting.
- After finishing: suggest logical follow-up tasks (e.g. "the metric doc may also need updating").

**Ask clarifying questions before acting when:**
- The task scope, edge cases, or expected behavior are ambiguous.
- A change touches multiple areas (core + reporters + tests + docs) — ask about priorities or constraints.
- A change might break existing metrics contracts, API shapes, or test expectations.

## Commit messages

Format: `<type>: <short imperative summary>` (subject line ≤50 chars, no period)

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Use a body only when changes span multiple unrelated areas — 1–3 short bullets, no paragraphs. Imperative mood ("add", not "added"); no file names or line numbers in the subject.

## Token-efficiency rules

- Keep default prompts scoped to one task and one area of the repo.
- Prefer follow-up prompts that build on already-open context instead of restating the whole problem.
- Do not paste generated reports or large logs unless the exact content matters for the decision.
- Use path-specific instruction files under `.github/instructions/` for deeper conventions instead of growing `.github/copilot-instructions.md`.

## Repository facts worth remembering

- `main.py` calls `setup_logging()` then delegates to `app/cli.py`, which orchestrates the full pipeline. AI metrics env vars (`AI_ASSISTED_LABEL`, `AI_EXCLUDE_LABELS`, `AI_TOOL_LABELS`, `AI_ACTION_LABELS`, `DAU_RESPONSES_DIR`) are loaded in `app/core/config.py`.
- `config/jira_schema.json` is source-controlled and important; it is not a disposable generated file.
- `config/jira_filters.json` is source-controlled (named JQL filter presets); not generated output.
- Generated artifacts belong under `generated/`. `generated/logs/` holds timestamped run logs; delete with `python main.py --clean-logs`.
- If tests are added, removed, or renamed, refresh coverage stats with `python tests/tools/test_coverage.py`.
