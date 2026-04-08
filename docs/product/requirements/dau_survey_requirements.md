# DAU Survey Requirements — AI Adoption Metrics Report

This document defines the functional and non-functional requirements for the Daily Active Usage
(DAU) survey feature. Requirements are intended for implementation and testing.

For the metric definition, scoring rationale, and `compute_dau_metrics()` output shape see
[`docs/product/metrics/dau_metric.md`](../metrics/dau_metric.md).

---

## Table of Contents

1. [Survey UI](#1-survey-ui)
2. [Submission and Storage](#2-submission-and-storage)
3. [Metrics Computation](#3-metrics-computation)
4. [Report Rendering](#4-report-rendering)
5. [Non-Functional Requirements](#5-non-functional-requirements)

---

## 1. Survey UI

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| DAU-F-001 | Username is a required text field | Submitting without a username is not possible; the Submit button remains disabled until a valid username is entered | ✓ Met |
| DAU-F-002 | Username accepts only alphanumeric characters, minimum 2 characters | Entering a username with spaces, special characters, or fewer than 2 characters shows an inline error message and marks the field as invalid; the Submit button stays disabled | ✓ Met |
| DAU-F-003 | Username is persisted across sessions via `localStorage` | On returning to the survey page in the same browser, the username field is pre-filled with the last submitted value | ✓ Met |
| DAU-F-004 | Role is a required dropdown with exactly 5 options | The dropdown contains: Developer, QA / Test Engineer, Business Analyst, Delivery Manager / Lead, Other; selecting one advances the progress count | ✓ Met |
| DAU-F-005 | Usage frequency is a required radio selection with exactly 4 options | The radio group contains: "Every day (5 days)", "Most days (3–4 days)", "Rarely (1–2 days)", "Not used"; each card displays the corresponding score badge | ✓ Met |
| DAU-F-006 | Progress bar reflects number of completed fields out of 3 | Progress label reads "N of 3 answered" and the fill width updates immediately when each field is completed or cleared | ✓ Met |
| DAU-F-007 | Submit button is disabled until all 3 fields are valid | `btn-submit` carries `disabled` and `aria-disabled="true"` until username is valid, role is selected, and usage is selected; a tooltip explains why it is disabled | ✓ Met |
| DAU-F-008 | Confirmation screen is shown after a successful save | The form panel is hidden and the confirmation panel is displayed; it shows the submitted username, role, usage answer, score, and timestamp | ✓ Met |
| DAU-F-009 | Keyboard navigation works within the radio group | Pressing ArrowDown / ArrowRight advances focus and selection to the next radio card; ArrowUp / ArrowLeft moves to the previous one | ✓ Met |

---

## 2. Submission and Storage

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| DAU-F-010 | Survey data is saved via the File System Access API when supported | Clicking Submit on a browser that supports `window.showDirectoryPicker` opens a directory picker; after the user selects a folder the file is written there without any server request | ✓ Met |
| DAU-F-011 | Survey data falls back to a browser download when the FS API is unavailable | On browsers where `window.showDirectoryPicker` is undefined, clicking Submit triggers a browser file download; no server request is made | ✓ Met |
| DAU-F-012 | If the FS API directory picker is cancelled, the form remains intact | An `AbortError` from `showDirectoryPicker` results in no file save and no navigation; the survey form stays visible and submittable | ✓ Met |
| DAU-F-013 | If the FS API call fails for a non-cancel reason, the app falls back to download | Any error other than `AbortError` from `showDirectoryPicker` silently triggers the browser download fallback and shows the confirmation screen | ✓ Met |
| DAU-F-014 | Output filename encodes the respondent and submission time | The saved filename follows the pattern `dau_<username>_<timestamp>.json` where `<timestamp>` is compact ISO-8601 UTC with no separators (e.g. `dau_alice123_20260327T130340Z.json`) | ✓ Met |
| DAU-F-015 | Submission payload matches the defined schema | The written JSON object contains exactly: `username` (string), `role` (string), `usage` (string), `score` (number), `timestamp` (ISO-8601 string with `+00:00` offset). The `week` field is absent from the raw survey payload — it is derived from `timestamp` and added during the normalization step (`normalize_dau_responses`) | ✓ Met |
| DAU-F-016 | Response files are saved to `generated/` by default | When team members follow the default workflow, response files are placed in the project's `generated/` directory so that `compute_dau_metrics()` can locate them without configuration | ✗ Not met |

---

## 3. Metrics Computation

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| DAU-F-017 | `compute_dau_metrics(responses_dir)` reads all `dau_*.json` files from the given directory and deduplicates to one record per `(username, week)` | Calling the function with a directory containing 3 response files from distinct `(username, week)` pairs returns `response_count` of 3; multiple files from the same user in the same week are deduplicated (latest timestamp wins); calling it with an empty or missing directory returns `response_count` of 0 and `team_avg` of `None` | ✓ Met |
| DAU-F-018 | `compute_dau_metrics` maps each `usage` answer to its score and computes the team average | Given responses with scores 5, 3.5, and 1.5, `team_avg` equals `10.0 / 3 ≈ 3.33`; given all "Not used" responses, `team_avg` equals `0.0` | ✓ Met |
| DAU-F-019 | `compute_dau_metrics` returns a `by_role` list with per-role averages and counts | A response set containing 2 Developers (scores 5 and 3.5) and 1 QA (score 1.5) returns `by_role` with entries `{"role": "Developer", "avg": 4.25, "count": 2}` and `{"role": "QA / Test Engineer", "avg": 1.5, "count": 1}` | ✓ Met |
| DAU-F-020 | `compute_dau_metrics` returns a `breakdown` list with per-answer counts | Given 2 "Every day" responses and 1 "Not used" response, `breakdown` contains `{"answer": "Every day (5 days)", "count": 2}` and `{"answer": "Not used", "count": 1}` | ✓ Met |
| DAU-F-021 | `build_metrics_dict()` calls `compute_dau_metrics()` and includes a `"dau"` key | The dict returned by `build_metrics_dict()` always contains a `"dau"` key whose value matches the shape defined in `dau_metric.md` | ✓ Met |
| DAU-F-022 | The responses directory is configurable via `DAU_RESPONSES_DIR` environment variable | Setting `DAU_RESPONSES_DIR=/custom/path` causes `compute_dau_metrics` to read from that path; if unset, the default is `generated/` | ✓ Met |

---

## 4. Report Rendering

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| DAU-F-023 | The HTML report includes a DAU section | The rendered HTML contains a `<section>` with team DAU average, response count, a per-role table, and a horizontal bar chart for the usage-frequency breakdown using Chart.js | ✓ Met |
| DAU-F-024 | The HTML report DAU section is omitted when there are no responses | When `metrics["dau"]["response_count"]` is 0, the DAU section is not rendered and no placeholder text is shown | ✓ Met |
| DAU-F-025 | The Markdown report includes a `## Daily Active Usage (DAU)` section | The generated `report.md` contains a summary table with team average and response count followed by a per-role breakdown table | ✓ Met |
| DAU-F-026 | The Markdown DAU section is omitted when there are no responses | When `response_count` is 0, the DAU section is absent from `report.md` | ✓ Met |

---

## 5. Non-Functional Requirements

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| DAU-NFR-001 | All survey data is stored locally; no data is sent to any external service | Submitting the survey produces no outgoing network requests; verified by inspecting the browser's Network panel — zero requests are made on clicking Save | ✓ Met |
| DAU-NFR-002 | Response files are excluded from version control | All files matching `dau_*.json` are listed in `.gitignore`; running `git check-ignore -v generated/dau_alice_20260327T130340Z.json` confirms the file is ignored | ✗ Not met |
| DAU-NFR-003 | No server process is required to submit the survey | The survey page can be opened directly as a local file (`file://` URL) and submitted successfully without a running server; the FS API or download fallback operates purely in the browser | ✓ Met |
| DAU-NFR-004 | Survey page styling is consistent with the existing report aesthetic | Visual variables (accent colour `#0052CC`, font stack, card borders, shadow) match the HTML report template | ✓ Met |
| DAU-NFR-005 | Form fields carry ARIA labels and the confirmation screen uses a live region | `aria-required="true"` is present on all required fields; the confirmation `<div>` has `role="region"` and `aria-live="polite"`; verified with an accessibility tree inspection | ✓ Met |
