# Jira Schema Requirements — Coverage Detail

> Source document: [docs/product/requirements/jira_schema_requirements.md](../../../docs/product/requirements/jira_schema_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 29 | **✅ Covered:** 23 | **🔶 Partial:** 0 | **❌ Gap:** 2 | **⬜ N/T:** 4 | **Functional:** 92%


#### Schema Loading

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-L-001 | All schema entries are loaded from config/jira_schema.json | ✅ | `unit/test_schema.py::test_load_schemas_returns_list_from_file` |
| JSR-L-002 | A missing schema file returns an empty list | ✅ | `unit/test_schema.py::test_load_schemas_missing_file` |
| JSR-L-003 | Malformed JSON in the schema file returns an empty list | ✅ | `unit/test_schema.py::test_load_schemas_invalid_json` |
| JSR-L-004 | A schema can be retrieved by name | ✅ | `unit/test_schema.py::test_get_schema_found`, `unit/test_schema.py::test_get_schema_not_found` |

#### Active Schema Resolution

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-R-001 | A named schema is returned when an explicit name is given | ✅ | `unit/test_schema.py::test_get_active_schema_by_name` |
| JSR-R-002 | Default_Jira_Cloud is used as a fallback when no name is given | ✅ | `unit/test_schema.py::test_get_active_schema_falls_back_to_default` |
| JSR-R-003 | The hardcoded _DEFAULT_SCHEMA is returned when the file is absent | ✅ | `unit/test_schema.py::test_get_active_schema_no_file_returns_hardcoded_default`, `unit/test_schema.py::test_get_active_schema_hardcoded_uses_builtin_story_points` |
| JSR-R-004 | A non-existent named schema falls back to the default silently | ❌ | — |

#### Schema Save & Delete

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-SD-001 | A new schema is appended to the file | ✅ | `unit/test_schema.py::test_save_schema_appends_new` |
| JSR-SD-002 | An existing schema is updated in-place | ✅ | `unit/test_schema.py::test_save_schema_updates_existing` |
| JSR-SD-003 | The parent directory is created if absent | ✅ | `unit/test_schema.py::test_save_schema_creates_file` |
| JSR-SD-004 | Default_Jira_Cloud cannot be deleted | ✅ | `unit/test_schema.py::test_delete_schema_refuses_default` |
| JSR-SD-005 | Deleting a non-existent schema name returns False | ✅ | `unit/test_schema.py::test_delete_schema_not_found` |

#### Field ID & JQL Name Lookups

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-F-001 | get_field_id() returns the Jira field ID for a known field key | ✅ | `unit/test_schema.py::test_get_field_id` |
| JSR-F-002 | get_field_id() returns None for an unknown field key | ✅ | `unit/test_schema.py::test_get_field_id` |
| JSR-F-003 | get_field_jql_name() falls back to id when jql_name is absent | ✅ | `unit/test_schema.py::test_get_field_jql_name_falls_back_to_id`, `unit/test_schema.py::test_get_field_jql_name_with_explicit_jql_name` |

#### Status Mappings

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-SM-001 | get_done_statuses() returns the configured done status list | ✅ | `unit/test_schema.py::test_get_done_statuses` |
| JSR-SM-002 | get_in_progress_statuses() returns the configured in-progress list | ✅ | `unit/test_schema.py::test_get_in_progress_statuses` |
| JSR-SM-003 | Default done statuses are returned when status_mapping is absent | ✅ | `unit/test_schema.py::test_get_done_statuses_defaults` |
| JSR-SM-004 | Default in-progress statuses are returned when status_mapping is absent | ✅ | `unit/test_schema.py::test_get_in_progress_statuses_defaults` |

#### Auto-Detection from Jira Fields

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-AD-001 | Sprint field is detected by schema.custom identifier | ✅ | `unit/test_schema.py::test_build_schema_from_fields_detects_sprint` |
| JSR-AD-002 | Story-points field is detected by name pattern when schema.custom is absent | ✅ | `unit/test_schema.py::test_build_schema_from_fields_detects_story_points_by_name` |
| JSR-AD-003 | Undetected fields retain their _DEFAULT_SCHEMA values | ✅ | `unit/test_schema.py::test_build_schema_from_fields_preserves_defaults_for_missing` |
| JSR-AD-004 | The team field's jql_name is preserved through auto-detection | ✅ | `unit/test_schema.py::test_build_schema_from_fields_preserves_team_jql_name` |
| JSR-AD-005 | Null or structurally incomplete entries in the Jira fields response are toler... | ❌ | — |

#### Future Enhancements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JSR-FUT-001 | Validate schema entries on load and surface missing required keys as warnings | ⬜ | — |
| JSR-FUT-002 | Block duplicate schema_name values on save | ⬜ | — |
| JSR-FUT-003 | Add a get_schema_names() convenience function | ⬜ | — |
| JSR-FUT-004 | Emit a warning when a non-existent named schema falls back to the default | ⬜ | — |
