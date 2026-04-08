# Jira Data Fetching Requirements — AI Adoption Metrics Report

This document defines requirements for fetching Jira data used in metrics computation: board discovery, sprint and issue retrieval, changelog fetching, and saved-filter JQL resolution. All behaviour described here is implemented in `app/core/jira_client.py`.

---

## Table of Contents

1. [Board Discovery](#1-board-discovery)
2. [Sprint Fetching](#2-sprint-fetching)
3. [Issue Fetching](#3-issue-fetching)
4. [Changelog Fetching](#4-changelog-fetching)
5. [Filter JQL Resolution](#5-filter-jql-resolution)
6. [Future Enhancements](#6-future-enhancements)

---

## 1. Board Discovery

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JDF-B-001 | `JIRA_BOARD_ID` from config is used without making an API call | When `config.JIRA_BOARD_ID` is set, `get_board_id()` returns it immediately without calling `jira.boards()` | ✓ Met | `test_get_board_id_from_config` |
| JDF-B-002 | The first accessible board is auto-discovered when no `JIRA_BOARD_ID` is configured | When `config.JIRA_BOARD_ID` is `None`, `get_board_id()` calls `jira.boards()` and returns the `id` of the first entry in the response | ✓ Met | `test_get_board_id_from_api` |
| JDF-B-003 | An empty boards list raises a `ValueError` with an actionable message | When `jira.boards()` returns an empty list, `get_board_id()` raises `ValueError` with a message that suggests setting `JIRA_BOARD_ID` or checking account access | ✓ Met | `test_get_board_id_no_boards_raises` |

---

## 2. Sprint Fetching

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JDF-SP-001 | Closed and active sprints are both returned | `get_sprints()` fetches sprints in both `closed` and `active` states and combines them into a single list | ✗ Not met | `test_get_sprints_sorted_desc_by_start_date` |
| JDF-SP-002 | Sprints are sorted by `startDate` descending (newest first) | The list returned by `get_sprints()` is ordered so that the sprint with the most recent `startDate` appears first | ✓ Met | `test_get_sprints_sorted_desc_by_start_date` |
| JDF-SP-003 | Sprint count is capped at `JIRA_SPRINT_COUNT` | `get_sprints()` returns at most `config.JIRA_SPRINT_COUNT` sprints (default 10); excess sprints are discarded after sorting | ✓ Met | `test_get_sprints_capped_at_sprint_count` |
| JDF-SP-004 | An empty sprint list is tolerated without crashing | When the board has no sprints, `get_sprints()` returns an empty list and no exception is raised | ✓ Met | `test_get_sprints_empty` |

---

## 3. Issue Fetching

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JDF-I-001 | All issues are retrieved across multiple pages | `get_issues_for_sprint()` fetches pages of 50 issues in a loop until the Jira API returns `None` or fewer than 50 results; no issues are omitted | ✓ Met | `test_get_issues_for_sprint_pagination` |
| JDF-I-002 | A filter JQL constraint is applied when `JIRA_FILTER_ID` is set | When a non-empty JQL string is derived from `JIRA_FILTER_ID`, it is appended to the sprint JQL with `AND` before querying Jira | ✓ Met | `test_fetch_sprint_data_passes_filter_jql_to_each_sprint` |
| JDF-I-003 | All sprint issues are returned when no filter is set | When `JIRA_FILTER_ID` is absent, `get_issues_for_sprint()` fetches issues using the sprint JQL only, without any additional filter | ✓ Met | `test_get_issues_for_sprint_single_page` |
| JDF-I-004 | An empty issue list for a sprint is tolerated | When a sprint contains no issues, the function returns an empty list and no exception is raised | ✓ Met | `test_get_issues_for_sprint_empty` |
| JDF-I-005 | A network failure during pagination terminates the loop safely | When `jira.jql()` returns `None` (simulating a network or API failure), the pagination loop breaks and the issues collected so far are returned without raising an exception | ✓ Met | — |

---

## 4. Filter JQL Resolution

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JDF-F-001 | A valid filter ID resolves to its JQL string | `get_filter_jql()` calls `jira.get_filter(id)` and returns the `jql` field from the response; the resulting JQL is then used to scope issue fetching | ✓ Met | `test_get_filter_jql_valid` |
| JDF-F-002 | A `None` filter ID returns an empty string without making an API call | When `filter_id` is `None`, `get_filter_jql()` returns `""` immediately without calling `jira.get_filter()` | ✓ Met | `test_get_filter_jql_none` |
| JDF-F-003 | An invalid or inaccessible filter ID returns an empty string without crashing | When `jira.get_filter()` raises any exception (e.g. 403, 404, network error), `get_filter_jql()` catches it, logs a sanitised `logger.warning`, and returns `""` so that issue fetching proceeds without a filter | ✓ Met | `test_get_filter_jql_api_error` |

---

## 6. Future Enhancements

| ID | Requirement | Rationale | Status |
|----|-------------|-----------|--------|
| JDF-FUT-001 | Log a warning when filter JQL fetch fails silently | `get_filter_jql()` swallows all exceptions with no trace; adding `logger.warning(...)` would make filter misconfiguration diagnosable without breaking the pipeline | ✓ Implemented |
| JDF-FUT-002 | Automatic retry on HTTP 429 (rate-limit) with exponential backoff | `get_issues_for_sprint()` and `get_issue_with_changelog()` make many sequential API calls; rate-limit errors currently cause silent failures or empty results | Proposed |
| JDF-FUT-003 | Configurable issue page size via `JIRA_FILTER_PAGE_SIZE` env var | The page size is hardcoded to 50; a configurable value would improve throughput on instances with high request latency or large payloads | Proposed |
