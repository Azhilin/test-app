# Non-Functional Requirements — AI Adoption Metrics Report

This document defines the quality attributes the AI Adoption Metrics Report tool must satisfy. Each requirement includes a measurable acceptance criterion so that it can be verified during development and testing.

---

## Table of Contents

1. [Performance](#1-performance)
2. [Security](#2-security)
3. [Usability](#3-usability)
4. [Reliability & Error Handling](#4-reliability--error-handling)
5. [Data Privacy](#5-data-privacy)
6. [Compatibility](#6-compatibility)
7. [Accessibility](#7-accessibility)

---

## 1. Performance

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-P-001 | Report generation completes within a reasonable time | HTML and Markdown reports are both written to disk in under 60 seconds for a dataset of 10 sprints and up to 500 issues | ✗ Not met |
| NFR-P-002 | HTML and Markdown reports are generated in parallel | Both report files are produced using `ThreadPoolExecutor(max_workers=2)`; generation of one report does not block the other | ✓ Met |
| NFR-P-003 | The Jira connection test completes or times out promptly | The test-connection request times out after no more than 12 seconds; a result (success or failure) is shown to the user within that window | ✓ Met |
| NFR-P-004 | Live progress output reaches the browser with minimal delay | SSE events from the report generation subprocess are forwarded to the browser output panel within 1 second of being written to stdout/stderr | ✓ Met |
| NFR-P-005 | Data fetch volume is bounded to prevent runaway API calls | Sprint count is capped at `JIRA_SPRINT_COUNT` (default 10); issues are fetched in pages of 50; changelog is limited to the 100 most recent done issues | ✓ Met |

---

## 2. Security

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-S-001 | The API token is never exposed in server responses | `GET /api/config` always returns `"JIRA_API_TOKEN": "***"` regardless of the value stored in `.env`; the real token is never included in any JSON response | ✓ Met |
| NFR-S-002 | Path traversal attacks on the report file server are prevented | Any request to `/generated/reports/` whose resolved path falls outside the reports directory is rejected with HTTP 404; no file outside that directory is ever served | ✓ Met |
| NFR-S-003 | The HTTP server is not reachable from other machines by default | The server binds exclusively to `127.0.0.1`; connections originating from any IP other than localhost are refused | ✓ Met |
| NFR-S-004 | Schema file requests are restricted to safe filenames and extensions | Filenames containing `/` or `\` are rejected; only `.json` files are served from the schemas directory | ✓ Met |
| NFR-S-005 | Sensitive configuration is excluded from version control | `.env` and any `.env.backup-*` files are listed in `.gitignore`; neither is ever committed to the repository | ✓ Met |
| NFR-S-006 | Credentials are not included in error messages or logs | Exception messages, CLI stderr output, and SSE error events do not contain the values of `JIRA_API_TOKEN`, `JIRA_EMAIL`, or `JIRA_URL` | ⚠ Partial |

---

## 3. Usability

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-U-001 | Report generation progress is visible in real time | The output panel on the Generate Report tab displays each line from the generation subprocess as it is produced, with no buffering delay visible to the user | ✓ Met |
| NFR-U-002 | Jira credentials are remembered between sessions | After clicking Save on the Jira Connection tab, credentials pre-fill on the next browser session without any re-entry | ⚠ Partial |
| NFR-U-003 | Generated reports are usable without the app running | Each HTML report is a fully self-contained file (inline CSS, Chart.js, and data); it opens correctly in a browser with no server or internet connection | ✓ Met |
| NFR-U-004 | Past reports are discoverable from the UI | The Last Generated Reports list on the Generate Report tab shows all previously created reports sorted newest first, each with a direct link to open the HTML report | ✓ Met |
| NFR-U-005 | Error states are communicated clearly to the user | Connection failures, missing credentials, and report generation errors each display a human-readable message in the relevant output panel or status badge; no raw stack trace is shown to the user | ✓ Met |

---

## 4. Reliability & Error Handling

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-R-001 | Missing required configuration is detected before any Jira call is made | `validate_config()` runs before `create_client()`; if any required variable (`JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`) is absent, the CLI prints an actionable error message and exits with code 1 without making any network request | ✓ Met |
| NFR-R-002 | A Jira connectivity failure does not crash the server process | A failed Jira API call during report generation is caught, reported to the browser as an SSE error event, and the server continues to handle subsequent requests normally | ✓ Met |
| NFR-R-003 | A client disconnecting mid-stream does not produce unhandled exceptions | `BrokenPipeError`, `ConnectionAbortedError`, and `ConnectionResetError` during an active SSE stream or file download are caught and suppressed silently; no stack trace is written to the server output | ✗ Not met |
| NFR-R-005 | The SSE stream always closes cleanly | Whether generation succeeds or fails, the stream always sends a final `event: close` event and the response is flushed before the connection ends | ✓ Met |

---

## 5. Data Privacy

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-D-001 | All user credentials are stored on the local machine only | `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` are written only to `.env` on the local filesystem; no credential value is transmitted to any service other than the configured Jira Cloud instance | ✓ Met |
| NFR-D-002 | DAU survey responses are stored locally only | Survey responses are written to a local JSON file that is listed in `.gitignore` and never sent to any external service | ✓ Met |
| NFR-D-003 | The application collects no usage telemetry | No analytics, crash reporting, or usage data is sent anywhere; the only outbound network connections are to the Jira Cloud instance configured in `JIRA_URL` | ✓ Met |
| NFR-D-004 | Credential backup files are excluded from version control | Any `.env.backup-*` files created during setup or reinstall are covered by `.gitignore` patterns and cannot be accidentally committed | ✓ Met |

---

## 6. Compatibility

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-C-001 | The application runs on Python 3.10, 3.11, and 3.12 | All unit and component tests pass without modification on Python 3.10, 3.11, and 3.12 | ⚠ Partial |
| NFR-C-002 | Windows installation requires no administrator rights | `project_setup.bat` completes successfully when run as a standard user; no UAC elevation prompt appears at any point during setup | ✓ Met |
| NFR-C-003 | The browser UI functions correctly in all supported browsers | The Generate Report, Jira Connection, and Jira Filter tabs operate correctly in Chrome 90+, Edge 90+, Firefox 88+, and Safari 14+ with JavaScript enabled | ✓ Met |
| NFR-C-004 | The CLI and browser UI produce identical reports from the same data | Running `python main.py` and triggering generation via `GET /api/generate` with the same Jira credentials and filter configuration produce reports with identical metric values | ✓ Met |

---

## 7. Accessibility

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| NFR-A-001 | All interactive UI regions have semantic ARIA roles | Every tab (`role="tab"`), tab panel (`role="tabpanel"`), output log (`role="log"`), alert (`role="alert"`), and status indicator (`role="status"`) carries the correct ARIA role attribute | ✓ Met |
| NFR-A-002 | Dynamic content updates are announced to screen readers | Output panels and status indicators that update without a page reload carry `aria-live="polite"` so that screen readers announce new content without interrupting the user | ✓ Met |
| NFR-A-003 | Required form fields are identified programmatically | Fields that must be completed before saving (Jira URL, email, API token) carry `aria-required="true"` so that assistive technologies communicate the requirement to users | ✗ Not met |
| NFR-A-004 | Decorative elements are hidden from assistive technology | Icons and visual-only elements carry `aria-hidden="true"` to prevent screen readers from announcing them as meaningful content | ✓ Met |
