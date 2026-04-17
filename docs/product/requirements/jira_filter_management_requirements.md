# Jira Filter Management Requirements — AI Adoption Metrics Report

This document defines requirements for the Jira filter management system: the default filter template shipped in `config/jira_filters.json`, server-side filter persistence via `/api/filters` endpoints, and UI behaviour for filter name pre-population and the saved-filter list.

---

## Table of Contents

1. [Default Filter Template](#1-default-filter-template)
2. [Filter Persistence — Server API](#2-filter-persistence--server-api)
3. [UI — Filter Name Pre-population](#3-ui--filter-name-pre-population)
4. [UI — Filter List Behaviour](#4-ui--filter-list-behaviour)
5. [UI — Active Schema & Filter Editing](#5-ui--active-schema--filter-editing)
6. [Future Enhancements](#6-future-enhancements)

---

## 1. Default Filter Template

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JFM-D-001 | A default filter template named `Default_Jira_Filter` ships with the project | `config/jira_filters.json` exists in the repository and contains exactly one entry with `"filter_name": "Default_Jira_Filter"` and `"is_default": true` | ✓ Met | — |
| JFM-D-002 | The default filter pre-sets sensible parameter defaults | The default entry has `JIRA_CLOSED_SPRINTS_ONLY=true` and `schema_name=Default_Jira_Cloud`; `JIRA_PROJECT` is intentionally blank (instance-specific) | ✓ Met | — |
| JFM-D-003 | The default filter is always returned by `GET /api/filters` | A `GET /api/filters` response always includes the `Default_Jira_Filter` entry, even after all user-saved filters are deleted | ✓ Met | — |
| JFM-D-004 | The default filter cannot be deleted | `DELETE /api/filters/<slug>` for the default filter returns HTTP 200 with `{"ok": false, "error": "Cannot delete the default filter"}` and leaves `config/jira_filters.json` unchanged | ✓ Met | — |

---

## 2. Filter Persistence — Server API

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JFM-P-001 | `GET /api/filters` returns all saved filters from `config/jira_filters.json` | Response is `{"ok": true, "filters": [{filter_name, jql, created_at, slug, is_default}…]}`; entries are ordered with the default filter first, then user filters newest-first | ✓ Met | — |
| JFM-P-002 | `GET /api/filters` initialises the config file from the default template if it is missing | When `config/jira_filters.json` does not exist, the server creates it with the default entry and returns it in the response without error | ✓ Met | — |
| JFM-P-003 | `POST /api/filters` creates a new filter entry when the name does not already exist | A POST with a new `name` appends a new entry to `config/jira_filters.json`; response includes `{"ok": true, "updated": false, "jql": "...", "slug": "...", "created_at": "..."}` | ✓ Met | — |
| JFM-P-004 | `POST /api/filters` updates an existing entry when the name matches (upsert) | A POST with a `name` that matches an existing entry replaces it in place; response includes `{"ok": true, "updated": true, …}` | ✓ Met | — |
| JFM-P-005 | `POST /api/filters` rejects a missing `JIRA_PROJECT` | When `params.JIRA_PROJECT` is absent or blank, the endpoint returns HTTP 200 with `{"ok": false, "error": "JIRA_PROJECT is required to build a JQL filter"}` | ✓ Met | — |
| JFM-P-006 | `POST /api/filters` builds correct JQL from params | The generated JQL always includes `status = Done`, plus `project =`/`IN`, optional `Team[Team] =`/`IN`, optional `type IN`, and `sprint in closedSprints()` when `JIRA_CLOSED_SPRINTS_ONLY` is truthy | ✓ Met | — |
| JFM-P-007 | `POST /api/filters` uses the schema's team JQL field name when `schema_name` is provided, and stores `schema_name` on the saved filter | If `params.schema_name` resolves to a schema with a `team.jql_name` field, that name is used in the `Team[…]` JQL clause instead of `Team[Team]`; the saved entry on disk preserves `params.schema_name` verbatim for later round-trip reads | ✓ Met | — |
| JFM-P-008 | `DELETE /api/filters/<slug>` removes the matching entry from `config/jira_filters.json` | The entry with `slug == <slug>` is removed from the array and the file is rewritten; response is `{"ok": true}` | ✓ Met | — |
| JFM-P-009 | `DELETE /api/filters/<slug>` returns 404 for an unknown slug | When no entry matches the slug, the response is HTTP 200 with `{"ok": false, "error": "Filter not found"}` | ✓ Met | — |
| JFM-P-010 | Filter data persists across application restarts | Entries written to `config/jira_filters.json` via `POST /api/filters` are present in the `GET /api/filters` response after the server process is restarted | ✓ Met | — |
| JFM-P-011 | `GET /api/generate?filter=<slug>` exports the filter's `params.schema_name` as `JIRA_SCHEMA_NAME` on the subprocess environment | When the selected filter's `params.schema_name` is non-empty, the value is set on the subprocess env and overrides any value from `config/defaults.env` or `.env`, making the active filter the source of truth for schema selection in UI runs | ✓ Met | — |
| JFM-P-012 | Each filter entry stores a `report_name` field; it defaults to the filter name on creation | A newly created filter in `config/jira_filters.json` includes `"report_name"` equal to the filter name when `report_name` is not provided in the POST body | ✓ Met | `test_post_filter_report_name_defaults_to_filter_name` |
| JFM-P-013 | `POST /api/filters` accepts and persists a custom `report_name` | When the POST body includes `"report_name"`, the persisted entry stores that value; subsequent `GET /api/filters` returns it unchanged | ✓ Met | `test_post_filter_round_trip_preserves_report_name` |
| JFM-P-014 | `GET /api/generate?filter=<slug>&report_name=<value>` passes the report name to `main.py` as `REPORT_NAME` and updates the stored filter | When `report_name` query param is supplied and differs from the stored value, the filter JSON is updated and `REPORT_NAME` env var is set for the subprocess | ✓ Met | `test_generate_exports_report_name_to_subprocess` |

---

## 3. UI — Filter Name Pre-population

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JFM-UI-001 | The Filter Name field is pre-populated on page load when empty | On page load, if the Filter Name input is empty, it is set to `Default_Jira_Filter_<YYYY-MM-DD>` using today's local date | ✓ Met | — |
| JFM-UI-002 | Pre-population does not overwrite a previously entered or saved value | If Filter Name already has a value (from localStorage or user input), the default pre-population is skipped | ✓ Met | — |

---

## 4. UI — Filter List Behaviour

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JFM-UI-003 | Saved filters from `config/jira_filters.json` are loaded and displayed on page load | `GET /api/filters` is called on startup; all returned entries appear in the filter list and in the Generate Report tab dropdown | ✓ Met | — |
| JFM-UI-004 | The default filter (`Default_Jira_Filter`) does not show a Remove button | In the rendered filter list, the entry with `is_default: true` renders without a Remove button | ✓ Met | — |
| JFM-UI-005 | Non-default user filters show a Remove button | All filter entries with `is_default: false` render with a Remove button that calls `DELETE /api/filters/<slug>` | ✓ Met | — |
| JFM-UI-006 | Removing a filter via the Remove button updates the list immediately | After a successful DELETE, the filter list and the Generate Report dropdown are re-rendered without the removed entry | ✓ Met | — |

---

## 5. UI — Active Schema & Filter Editing

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JFM-UI-007 | An Active Schema dropdown is shown on the Filter Builder tab | `#filter-schema-select` is populated from `GET /api/schemas`; the selection reflects the currently-selected filter's `params.schema_name`, or `Default_Jira_Cloud` when "— New filter —" is active | ✗ Not met | — |
| JFM-UI-008 | The Filter Name field is a dropdown that lists existing filters | `#filter-name-select` lists every entry returned by `GET /api/filters` plus a leading `— New filter —` option; the default filter is labelled with a `(default)` suffix | ✗ Not met | — |
| JFM-UI-009 | Selecting an existing filter loads it into the form for editing | Picking a filter in `#filter-name-select` populates the form from its `params` (project, team, issue types, board, sprint count, radios, Active Schema) and hides `#filter-name` with its value mirroring the filter name | ✗ Not met | — |
| JFM-UI-010 | Selecting "— New filter —" resets the form to a blank-template state | Picking `__new__` in `#filter-name-select` unhides `#filter-name`, pre-populates it per JFM-UI-001, and clears every param field (Active Schema resets to `Default_Jira_Cloud`, radios reset to `SCRUM` / `StoryPoints`) | ✗ Not met | — |
| JFM-UI-011 | Save uses the schema chosen in the Filter Builder dropdown | `POST /api/filters` request body sets `params.schema_name` equal to the value of `#filter-schema-select` at the moment of save — independent of the Schema Setup tab's selection | ✗ Not met | — |
| JFM-UI-012 | The Filter Builder's schema dropdown does not mutate localStorage or Schema Setup state | Changing `#filter-schema-select` leaves `localStorage.jira_schema_name` unchanged and does not alter the `#schema-select` value on the Schema Setup tab | ✗ Not met | — |
| JFM-UI-013 | The default filter is read-only in the UI | When `Default_Jira_Filter` is selected in `#filter-name-select`, the Save button is disabled; it re-enables when any other entry (including `— New filter —`) is selected | ✗ Not met | — |

---

## 6. Future Enhancements

| ID | Requirement | Rationale | Status |
|----|-------------|-----------|--------|
| JFM-FUT-001 | Apply the selected filter's params to `.env` before running `main.py` | `GET /api/generate?filter=<slug>` now applies the filter's `JIRA_PROJECT`, `JIRA_TEAM_ID` etc. to the subprocess environment before spawning `main.py`; the `.env` file is not modified | ✓ Met |
| JFM-FUT-002 | Allow reordering of saved filters in the UI | Users who maintain many filters would benefit from drag-to-reorder or explicit up/down controls | Proposed |
| JFM-FUT-003 | Export / import filter config as a downloadable JSON file | Enables sharing filter configs across team members or machines without manual file editing | Proposed |
