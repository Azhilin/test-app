---
applyTo: "app/core/**/*.py,main.py,config/jira_schema.json"
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
