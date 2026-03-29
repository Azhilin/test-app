---
name: metric-development
description: Use this when adding, changing, or debugging a metric in the AI Adoption Metrics Report project. It guides work across metrics computation, report rendering, and tests without loading unrelated repo context.
---

Use this skill for changes centered on sprint metrics, trend calculations, and the metrics dictionary.

Follow this workflow:

1. Start with the smallest relevant context:
   - `app/core/metrics.py`
   - related tests in `tests/unit/`
   - any renderer files that consume the changed metric
2. Identify the metric contract:
   - inputs used by the computation
   - output keys expected by reporters or templates
   - any schema-driven field or status dependencies
3. Implement in `app/core/metrics.py` first.
4. If output structure changes, update:
   - `app/reporters/report_md.py`
   - `app/reporters/report_html.py`
   - `templates/report.html.j2`
5. Add or update targeted tests using existing test factories from `tests/conftest.py`.
6. Validate with the narrowest pytest selection that proves the behavior.

Token-efficiency rules:

- Prefer file references over pasted code.
- Do not load UI or server files unless the metric becomes user-visible there.
- Do not bring full Jira client context into scope unless the task truly changes data acquisition.
