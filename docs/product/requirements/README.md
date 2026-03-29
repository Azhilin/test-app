# Requirements Index — AI Adoption Metrics Report

Quick-lookup guide for AI agents and developers. Use this to identify which file to open for a given area and which requirement IDs to look up when updating status.

---

## Requirements files

All standard requirements files follow the naming convention `<topic>_requirements.md` and use the table format `| ID | Requirement | Acceptance Criterion | Status |`.

| File | Topic area | ID prefix(es) |
|------|-----------|---------------|
| [`app_non_functional_requirements.md`](app_non_functional_requirements.md) | Performance, security, usability, reliability, data privacy, compatibility, accessibility | `NFR-P-`, `NFR-S-`, `NFR-U-`, `NFR-R-`, `NFR-D-`, `NFR-C-`, `NFR-A-` |
| [`dau_survey_requirements.md`](dau_survey_requirements.md) | DAU survey UI, file save, metric computation, report rendering | `DAU-F-`, `DAU-NFR-` |
| [`jira_connection_requirements.md`](jira_connection_requirements.md) | Authentication, config validation, SSL | `JCR-A-`, `JCR-C-`, `JCR-SSL-` |
| [`jira_data_fetching_requirements.md`](jira_data_fetching_requirements.md) | Board discovery, sprint fetching, issue fetching, changelog, filter scoping | `JDF-B-`, `JDF-SP-`, `JDF-IS-`, `JDF-CL-`, `JDF-F-` |
| [`jira_filter_management_requirements.md`](jira_filter_management_requirements.md) | Default filter, CRUD operations, UI behaviour | `JFM-D-`, `JFM-C-`, `JFM-U-` |
| [`jira_schema_requirements.md`](jira_schema_requirements.md) | Schema loading, field lookup, status mapping, auto-detection | `JSR-L-`, `JSR-F-`, `JSR-S-`, `JSR-D-` |
| [`logging_requirements.md`](logging_requirements.md) | Log file creation, log level, log format, log cleanup | `LOG-` |
| [`installation_requirements.md`](installation_requirements.md) | Zip contents, setup steps, uninstall | *(no standard ID — uses descriptive sections)* |
| [`technical_requirements.md`](technical_requirements.md) | OS compatibility, Python version, dependencies | *(no standard ID — uses descriptive sections)* |

---

## Status values

Use exactly these three values in the `Status` column — no other variations:

| Value | Meaning |
|-------|---------|
| `✓ Met` | Acceptance criterion is satisfied and verified |
| `✗ Not met` | Acceptance criterion is not yet satisfied |
| `⬜ N/T` | Not yet tested; implementation may exist but is unverified |

---

## Companion documents (not requirements files)

| File | Purpose |
|------|---------|
| [`app_nfr_gap_analysis.md`](app_nfr_gap_analysis.md) | Gap analysis against `app_non_functional_requirements.md` — records findings, recommended fixes, and resolution notes. Not a requirements file; do not update Status rows here. |

---

## How to use this index during the development workflow

**Step 1 (Maintain requirements):** look up the relevant file(s) in the table above. Open the file, find the row(s) whose acceptance criterion is affected by the change, and update the `Status` column. Do not add rows or create new files.

When the change affects NFRs (performance, security, reliability, etc.) → open `app_non_functional_requirements.md`.
When the change affects a specific feature area → open the matching `<topic>_requirements.md`.
When the change affects multiple areas → update all relevant files.
