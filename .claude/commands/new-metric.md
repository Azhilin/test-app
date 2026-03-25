Add a new custom metric named $ARGUMENTS to the AI Adoption Metrics report.

Checklist:
1. app/metrics.py: Add compute_<name>(sprints, sprint_issues) -> list[dict]; each dict needs sprint_id, sprint_name, plus the metric value key. Follow the compute_custom_trends signature.
2. app/metrics.py: Call the new function in build_metrics_dict() and add result to the returned dict.
3. app/report_md.py: Add a Markdown section reading the new key from metrics_dict.
4. templates/report.html.j2: Add a section reading the new key from the metrics template variable.
5. tests/: Add test_<name>.py covering the computation function using make_sprint() and make_issue() from tests/conftest.py.
