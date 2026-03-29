# Jira Connection Requirements — Coverage Detail

> Source document: [docs/product/requirements/jira_connection_requirements.md](../../../docs/product/requirements/jira_connection_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 33 | **✅ Covered:** 23 | **🔶 Partial:** 0 | **❌ Gap:** 6 | **⬜ N/T:** 4 | **Functional:** 79%


#### Authentication

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JCR-A-001 | Valid Basic Auth credentials are accepted by Jira | ✅ | `component/test_server.py::test_test_connection_valid_creds` |
| JCR-A-002 | An invalid API token is rejected with a clear error | ✅ | `component/test_server.py::test_test_connection_http_error` |
| JCR-A-003 | An unrecognised Jira email is rejected with a clear error | ✅ | `component/test_server.py::test_test_connection_http_error` |
| JCR-A-004 | The API token is never echoed in any server response | ❌ | — |
| JCR-A-005 | Credentials are sanitised before logging or raising exceptions | ✅ | `unit/test_jira_client.py::test_sanitise_error_replaces_url`, `unit/test_jira_client.py::test_sanitise_error_replaces_email_and_token`, `unit/test_jira_client.py::test_sanitise_error_handles_none_config_values` |

#### Configuration & Validation

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JCR-C-001 | Missing JIRA_URL is detected before any network call | ✅ | `unit/test_config.py::test_validate_config_missing_url`, `integration/test_integration.py::test_main_pipeline_config_fail` |
| JCR-C-002 | Missing JIRA_EMAIL is detected before any network call | ✅ | `unit/test_config.py::test_validate_config_missing_email` |
| JCR-C-003 | Missing JIRA_API_TOKEN is detected before any network call | ✅ | `unit/test_config.py::test_validate_config_missing_token` |
| JCR-C-004 | JIRA_URL trailing slashes are stripped automatically | ✅ | `unit/test_config.py::test_jira_url_trailing_slash_stripped`, `unit/test_config.py::test_jira_url_multiple_trailing_slashes_stripped` |
| JCR-C-005 | JIRA_BOARD_ID is optional; app auto-discovers the first board | ✅ | `unit/test_jira_client.py::test_get_board_id_from_api` |
| JCR-C-006 | JIRA_SPRINT_COUNT defaults to 10 when not set | ✅ | `unit/test_config.py::test_sprint_count_default` |
| JCR-C-007 | JIRA_FILTER_ID is optional; absent value causes no error | ✅ | `unit/test_config.py::test_filter_id_empty` |

#### Test-Connection Endpoint

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JCR-T-001 | Valid credentials return user details | ✅ | `component/test_server.py::test_test_connection_valid_creds`, `integration/test_integration.py::test_server_test_connection_json_shape` |
| JCR-T-002 | Missing required fields return HTTP 400 | ✅ | `component/test_server.py::test_test_connection_missing_fields` |
| JCR-T-003 | Malformed JSON body returns HTTP 400 | ✅ | `component/test_server.py::test_test_connection_invalid_json` |
| JCR-T-004 | An empty request body returns HTTP 400 | ✅ | `component/test_server.py::test_test_connection_empty_body` |
| JCR-T-005 | An unreachable host returns ok: false with an error message | ✅ | `component/test_server.py::test_test_connection_http_error` |
| JCR-T-006 | Jira HTTP 401 / 403 is surfaced to the caller | ✅ | `component/test_server.py::test_test_connection_http_error` |
| JCR-T-007 | The test-connection request times out after at most 12 seconds | ❌ | — |
| JCR-T-008 | An unexpected server-side exception returns HTTP 500 | ❌ | — |

#### SSL / TLS Certificate Handling

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JCR-SSL-001 | A custom CA bundle is used when present | ✅ | `unit/test_config.py::test_jira_ssl_cert_returns_path_when_file_exists`, `unit/test_jira_client.py::test_create_client_passes_verify_ssl` |
| JCR-SSL-002 | The system CA store is used when no custom cert is present | ✅ | `unit/test_config.py::test_jira_ssl_cert_returns_true_when_no_file` |
| JCR-SSL-003 | Certificate validity is reported by cert_utils.validate_cert() | ✅ | `component/test_server.py::test_cert_status_with_valid_cert_returns_enriched_fields` |
| JCR-SSL-004 | The test-connection request uses the same SSL context as the Jira client | ❌ | — |
| JCR-SSL-005 | An expired custom CA bundle is reported but does not block client creation | ❌ | — |
| JCR-SSL-006 | Fetch Certificate happy path delivers a parseable, valid cert badge | ✅ | `e2e/test_e2e_connection.py::test_fetch_cert_success_updates_badge`, `e2e/test_e2e_connection.py::test_positive_e2e_fetch_cert_then_badge_shows_valid`, `component/test_server.py::test_fetch_cert_saves_pem_without_crlf_line_endings` |
| JCR-SSL-007 | Standard Jira Cloud positive E2E: absent cert file is an acceptable state | ✅ | `e2e/test_e2e_connection.py::test_positive_e2e_no_cert_is_acceptable_state` |

#### Client Timeouts

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JCR-TO-001 | The Jira API client uses a 55-second connection timeout | ✅ | `unit/test_jira_client.py::test_create_client_returns_jira_instance` |
| JCR-TO-002 | The test-connection endpoint enforces a 12-second timeout | ❌ | — |

#### Future Enhancements

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| JCR-FUT-001 | OAuth 2.0 3LO authentication support | ⬜ | — |
| JCR-FUT-002 | Configurable test-connection timeout via JIRA_TEST_CONNECTION_TIMEOUT env var | ⬜ | — |
| JCR-FUT-003 | Block report generation when certs/jira_ca_bundle.pem is expired | ⬜ | — |
| JCR-FUT-004 | Automatic retry on HTTP 429 with exponential backoff | ⬜ | — |
