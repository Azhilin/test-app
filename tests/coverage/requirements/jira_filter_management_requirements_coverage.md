# Jira Filter Management Requirements — Coverage Detail

> Source document: [docs/product/requirements/jira_filter_management_requirements.md](../../../docs/product/requirements/jira_filter_management_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 23 | **✅ Covered:** 21 | **🔶 Partial:** 0 | **❌ Gap:** 0 | **⬜ N/T:** 2 | **Functional:** 100%


#### Default Filter Template

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JFM-D-001 | Default_Jira_Filter entry ships in config/jira_filters.json | ✅ | `tests/unit/test_filter_handlers.py::test_default_filter_entry_is_present_and_correct`, `tests/component/test_server_filters.py::test_get_filters_default_is_first` |
| JFM-D-002 | Default filter pre-sets sensible parameter defaults | ✅ | `tests/unit/test_filter_handlers.py::test_default_filter_entry_is_present_and_correct` |
| JFM-D-003 | Default filter is always returned by GET /api/filters | ✅ | `tests/unit/test_filter_handlers.py::test_load_filters_injects_default_when_absent_from_file`, `tests/component/test_server_filters.py::test_get_filters_always_includes_default_after_user_delete` |
| JFM-D-004 | Default filter cannot be deleted | ✅ | `tests/unit/test_filter_handlers.py::test_delete_default_filter_is_blocked`, `tests/component/test_server_filters.py::test_delete_default_filter_returns_error` |

#### Filter Persistence — Server API

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JFM-P-001 | GET /api/filters returns all saved filters ordered default-first | ✅ | `tests/component/test_server_filters.py::test_get_filters_default_is_first` |
| JFM-P-002 | GET /api/filters initialises config file from default template if missing | ✅ | `tests/unit/test_filter_handlers.py::test_load_filters_creates_file_when_missing` |
| JFM-P-003 | POST /api/filters creates a new filter entry when name is new | ✅ | `tests/unit/test_filter_handlers.py::test_post_filter_creates_new_entry`, `tests/component/test_server_filters.py::test_post_filter_creates_new_and_get_returns_it` |
| JFM-P-004 | POST /api/filters updates existing entry when name matches (upsert) | ✅ | `tests/unit/test_filter_handlers.py::test_post_filter_updates_existing_entry`, `tests/component/test_server_filters.py::test_post_filter_upserts_on_duplicate_name` |
| JFM-P-005 | POST /api/filters rejects missing JIRA_PROJECT | ✅ | `tests/unit/test_filter_handlers.py::test_post_filter_rejects_blank_project` |
| JFM-P-006 | POST /api/filters builds correct JQL from params | ✅ | `tests/unit/test_filter_handlers.py::test_build_jql_from_params[params0-project = PROJ-None]`, `tests/unit/test_filter_handlers.py::test_build_jql_from_params[params1-project IN (A, B)-None]`, `tests/unit/test_filter_handlers.py::test_build_jql_from_params[params2-"Team[Team]" = T1-None]`, `tests/unit/test_filter_handlers.py::test_build_jql_from_params[params3-status IN (Done, Closed)-None]`, `tests/unit/test_filter_handlers.py::test_build_jql_from_params[params4-project = PROJ-sprint in closedSprints()]`, `tests/unit/test_filter_handlers.py::test_build_jql_from_params[params5-type IN (Story, Bug)-None]` |
| JFM-P-007 | POST /api/filters uses schema team JQL field name when schema_name provided | ✅ | `tests/unit/test_filter_handlers.py::test_post_filter_uses_schema_team_jql_field` |
| JFM-P-008 | DELETE /api/filters/<slug> removes the matching entry | ✅ | `tests/component/test_server_filters.py::test_delete_filter_removes_entry` |
| JFM-P-009 | DELETE /api/filters/<slug> returns 404-style error for unknown slug | ✅ | `tests/unit/test_filter_handlers.py::test_delete_unknown_slug_returns_not_found`, `tests/component/test_server_filters.py::test_delete_unknown_slug_returns_not_found` |
| JFM-P-010 | Filter data persists across application restarts | ✅ | `tests/unit/test_filter_handlers.py::test_filter_data_persists_across_loads`, `tests/component/test_server_filters.py::test_filter_persists_across_server_restart` |

#### UI — Filter Name Pre-population

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JFM-UI-001 | Filter Name field is pre-populated on page load when empty | ✅ | `tests/e2e/test_e2e_filters.py::test_filter_name_prepopulated_on_empty_load` |
| JFM-UI-002 | Pre-population does not overwrite a previously entered or saved value | ✅ | `tests/e2e/test_e2e_filters.py::test_filter_name_not_overwritten_after_user_edit` |

#### UI — Filter List Behaviour

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JFM-UI-003 | Saved filters loaded and displayed on page load | ✅ | `tests/e2e/test_e2e_filters.py::test_filter_list_displayed_on_load` |
| JFM-UI-004 | Default filter does not show a Remove button | ✅ | `tests/e2e/test_e2e_filters.py::test_default_filter_has_no_remove_button` |
| JFM-UI-005 | Non-default user filters show a Remove button | ✅ | `tests/e2e/test_e2e_filters.py::test_user_filter_has_remove_button` |
| JFM-UI-006 | Removing a filter via the Remove button updates the list immediately | ✅ | `tests/e2e/test_e2e_filters.py::test_remove_filter_updates_list` |

#### Future Enhancements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JFM-FUT-001 | Apply selected filter params to .env before running main.py | ✅ | `tests/unit/test_filter_handlers.py::test_generate_applies_filter_params_to_subprocess_env` |
| JFM-FUT-002 | Allow reordering of saved filters in the UI | ⬜ | — |
| JFM-FUT-003 | Export / import filter config as a downloadable JSON file | ⬜ | — |
