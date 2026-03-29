# Jira Data Fetching Requirements — Coverage Detail

> Source document: [docs/product/requirements/jira_data_fetching_requirements.md](../../../docs/product/requirements/jira_data_fetching_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 22 | **✅ Covered:** 16 | **🔶 Partial:** 1 | **❌ Gap:** 2 | **⬜ N/T:** 3 | **Functional:** 89%


#### Board Discovery

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JDF-B-001 | JIRA_BOARD_ID from config is used without making an API call | ✅ | `unit/test_jira_client.py::test_get_board_id_from_config` |
| JDF-B-002 | The first accessible board is auto-discovered when no JIRA_BOARD_ID is config... | ✅ | `unit/test_jira_client.py::test_get_board_id_from_api` |
| JDF-B-003 | An empty boards list raises a ValueError with an actionable message | ✅ | `unit/test_jira_client.py::test_get_board_id_no_boards_raises` |

#### Sprint Fetching

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JDF-SP-001 | Closed and active sprints are both returned | ✅ | `unit/test_jira_client.py::test_get_sprints_sorted_desc_by_start_date` |
| JDF-SP-002 | Sprints are sorted by startDate descending (newest first) | ✅ | `unit/test_jira_client.py::test_get_sprints_sorted_desc_by_start_date` |
| JDF-SP-003 | Sprint count is capped at JIRA_SPRINT_COUNT | ✅ | `unit/test_jira_client.py::test_get_sprints_capped_at_sprint_count` |
| JDF-SP-004 | An empty sprint list is tolerated without crashing | ✅ | `unit/test_jira_client.py::test_get_sprints_empty` |

#### Issue Fetching

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JDF-I-001 | All issues are retrieved across multiple pages | ✅ | `unit/test_jira_client.py::test_get_issues_for_sprint_pagination` |
| JDF-I-002 | A filter JQL constraint is applied when JIRA_FILTER_ID is set | ✅ | `unit/test_jira_client.py::test_fetch_sprint_data_passes_filter_jql_to_each_sprint` |
| JDF-I-003 | All sprint issues are returned when no filter is set | ✅ | `unit/test_jira_client.py::test_get_issues_for_sprint_single_page` |
| JDF-I-004 | An empty issue list for a sprint is tolerated | ✅ | `unit/test_jira_client.py::test_get_issues_for_sprint_empty` |
| JDF-I-005 | A network failure during pagination terminates the loop safely | ❌ | — |

#### Changelog Fetching

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JDF-CL-001 | Changelog with status transition history is returned per issue | ✅ | `unit/test_jira_client.py::test_get_issue_with_changelog_expand_param` |
| JDF-CL-002 | Fetching changelogs for multiple issues returns a list in key order | ✅ | `unit/test_jira_client.py::test_get_issues_with_changelog_multiple_keys` |
| JDF-CL-003 | A per-issue changelog failure logs a warning and appends {} | ✅ | `unit/test_jira_client.py::test_get_issues_with_changelog_skips_failures` |
| JDF-CL-004 | Changelog timestamps must be timezone-aware ISO-8601 strings | ❌ | — |

#### Filter JQL Resolution

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JDF-F-001 | A valid filter ID resolves to its JQL string | ✅ | `unit/test_jira_client.py::test_get_filter_jql_valid` |
| JDF-F-002 | A None filter ID returns an empty string without making an API call | ✅ | `unit/test_jira_client.py::test_get_filter_jql_none` |
| JDF-F-003 | An invalid or inaccessible filter ID returns an empty string without crashing | 🔶 | `unit/test_jira_client.py::test_get_filter_jql_api_error` |

#### Future Enhancements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JDF-FUT-001 | Log a warning when filter JQL fetch fails silently | ⬜ | — |
| JDF-FUT-002 | Automatic retry on HTTP 429 with exponential backoff | ⬜ | — |
| JDF-FUT-003 | Configurable issue page size via JIRA_FILTER_PAGE_SIZE env var | ⬜ | — |
