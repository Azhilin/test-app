---
name: schema-maintenance
description: Use this when working on Jira field schemas, config, or status mappings in this repository. It keeps schema JSON, Python helpers, and tests in sync.
---

Use this skill for work involving Jira field IDs, schema auto-detection, status lists, or environment-driven schema selection.

Follow this workflow:

1. Open the smallest relevant set:
   - `app/core/schema.py`
   - `config/jira_schema.json`
   - `app/core/config.py` if environment behavior is involved
   - related tests under `tests/unit/`
2. Determine whether the change affects:
   - default schema entries
   - known field patterns
   - known Jira field schemas
   - config selection or validation
3. Keep defaults synchronized between Python code and JSON config.
4. Update tests that prove:
   - field lookup behavior
   - status mapping behavior
   - config reload behavior when env vars change
5. Summarize any assumption introduced about Jira fields, names, or statuses.

Token-efficiency rules:

- Avoid loading reporters or UI files unless the schema change alters visible output or server endpoints.
- Reuse the existing schema terminology and field names already present in the repository.
