---
applyTo: "app/core/**/*.py,app/cli.py,app/utils/**/*.py,main.py,config/jira_schema.json,config/jira_filters.json"
---

# Core logic instructions

The core of this project lives in `app/core/` and is the source of truth for configuration, Jira access, schema mapping, and metric computation.

- Keep computation code in `metrics.py` pure where possible; avoid mixing data fetching or presentation logic into metrics helpers.
- Preserve schema-driven behavior. If a feature depends on Jira field IDs or status names, prefer reading them from schema helpers instead of hard-coding values.
- `schema.py` and `config/jira_schema.json` must stay aligned when default fields or known mappings change.
- `config.py` exposes module-level constants from environment variables. If config behavior changes, update tests using the existing `importlib.reload(config)` pattern.
- Reuse existing helpers for issue shapes, sprint shapes, and story-point access rather than introducing alternate dict contracts.
- When adding or changing metrics, keep the downstream contract in mind: reporters and tests depend on stable keys and list/dict shapes.
- For new sprint trend metrics, include `sprint_id` and `sprint_name` in each result row and follow the existing `compute_custom_trends` style.
- CLI entry points (`app/cli.py`, `main.py`) must call `setup_logging()` from `app/utils.logging_setup` before any other logging calls. `setup_logging()` returns `(root_logger, log_file_path)` and creates `generated/logs/` automatically; store the path if you need to surface it to the user.
- `config/jira_filters.json` is source-controlled (named JQL presets + env-var-style overrides). Keep aligned with `app/core/config.py` when filter-related env vars change; do not treat as generated output.
