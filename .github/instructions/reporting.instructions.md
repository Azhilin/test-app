---
applyTo: "app/reporters/**/*.py,templates/**/*.j2,ui/**/*.html,app/server.py,server.py"
---

# Reporting and UI instructions

These files control report rendering, browser behavior, and server-facing UX.

- Keep HTML and Markdown reports logically consistent when adding or changing report sections.
- Prefer computing reusable values in Python rather than embedding complex branching in templates.
- `report_html.py` and `report_md.py` consume the same metrics dictionary, so presentation changes should respect shared data contracts.
- When a metric becomes user-visible, check whether the browser UI, report template, and server endpoints need matching updates.
- Preserve the local workflow: start a local server, open the browser UI, configure Jira, and generate reports.
- Do not treat generated report output as source; real templates and rendering logic belong in `templates/` and `app/reporters/`.
