# Jira Connection Requirements — AI Adoption Metrics Report

This document defines requirements for establishing and validating a connection to Jira Cloud, including credential validation, the test-connection API endpoint, SSL/TLS certificate handling, and client timeouts. It covers both the CLI (`main.py`) and Server/UI (`app/server.py`) surfaces.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Configuration & Validation](#2-configuration--validation)
3. [Test-Connection Endpoint](#3-test-connection-endpoint)
4. [SSL / TLS Certificate Handling](#4-ssl--tls-certificate-handling)
5. [Client Timeouts](#5-client-timeouts)
6. [Future Enhancements](#6-future-enhancements)

---

## 1. Authentication

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JCR-A-001 | Valid Basic Auth credentials are accepted by Jira | `POST /api/test-connection` with correct `url`, `email`, and `token` returns `{"ok": true, "displayName": "...", "emailAddress": "..."}` and HTTP 200 | ✓ Met | `test_test_connection_valid_creds` |
| JCR-A-002 | An invalid API token is rejected with a clear error | `POST /api/test-connection` with a wrong token returns `{"ok": false, "httpStatus": 401}` and HTTP 200 | ✓ Met | `test_test_connection_http_error` |
| JCR-A-003 | An unrecognised Jira email is rejected with a clear error | `POST /api/test-connection` with an unrecognised email returns `{"ok": false, "httpStatus": 401}` and HTTP 200 | ✓ Met | `test_test_connection_http_error` |
| JCR-A-004 | The API token is never echoed in any server response | No JSON field or response body produced by the server contains the raw value of `JIRA_API_TOKEN`; `GET /api/config` always returns `"JIRA_API_TOKEN": "***"` | ✓ Met | — |
| JCR-A-005 | Credentials are sanitised before logging or raising exceptions | The `_sanitise_error()` helper replaces `JIRA_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` with `***` in any exception message or log entry produced by `jira_client.py` | ✓ Met | — |

---

## 2. Configuration & Validation

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JCR-C-001 | Missing `JIRA_URL` is detected before any network call | `validate_config()` returns an error message for a missing `JIRA_URL`; the CLI exits with code 1 without making any HTTP request | ✓ Met | `test_validate_config_missing_url`, `test_main_pipeline_config_fail` |
| JCR-C-002 | Missing `JIRA_EMAIL` is detected before any network call | `validate_config()` returns an error message for a missing `JIRA_EMAIL`; the CLI exits with code 1 without making any HTTP request | ✓ Met | `test_validate_config_missing_email` |
| JCR-C-003 | Missing `JIRA_API_TOKEN` is detected before any network call | `validate_config()` returns an error message for a missing `JIRA_API_TOKEN`; the CLI exits with code 1 without making any HTTP request | ✓ Met | `test_validate_config_missing_token` |
| JCR-C-004 | `JIRA_URL` trailing slashes are stripped automatically | A `JIRA_URL` value with one or more trailing slashes is normalised during config load; no double-slash URL is ever passed to the Jira client | ✓ Met | `test_jira_url_trailing_slash_stripped`, `test_jira_url_multiple_trailing_slashes_stripped` |
| JCR-C-005 | `JIRA_BOARD_ID` is optional | When `JIRA_BOARD_ID` is absent from `.env`, the application auto-discovers the first accessible board without raising an error | ✓ Met | `test_get_board_id_from_api` |
| JCR-C-006 | `JIRA_SPRINT_COUNT` defaults to 10 when not set | When `JIRA_SPRINT_COUNT` is absent from `.env`, `config.JIRA_SPRINT_COUNT` evaluates to `10` | ✓ Met | `test_sprint_count_default` |
| JCR-C-007 | `JIRA_FILTER_ID` is optional | When `JIRA_FILTER_ID` is absent, issues are fetched without a filter JQL constraint and no error is raised | ✓ Met | `test_filter_id_empty` |

---

## 3. Test-Connection Endpoint

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JCR-T-001 | Valid credentials return user details | `POST /api/test-connection` with correct `url`, `email`, and `token` returns HTTP 200 and `{"ok": true, "displayName": "...", "emailAddress": "..."}` | ✓ Met | `test_test_connection_valid_creds`, `test_server_test_connection_json_shape` |
| JCR-T-002 | Missing required fields return HTTP 400 | `POST /api/test-connection` with any of `url`, `email`, or `token` absent from the request body returns HTTP 400 | ✓ Met | `test_test_connection_missing_fields` |
| JCR-T-003 | Malformed JSON body returns HTTP 400 | `POST /api/test-connection` with a body that is not valid JSON returns HTTP 400 | ✓ Met | `test_test_connection_invalid_json` |
| JCR-T-004 | An empty request body returns HTTP 400 | `POST /api/test-connection` with no Content-Length and no body returns HTTP 400 | ✓ Met | `test_test_connection_empty_body` |
| JCR-T-005 | An unreachable host returns `ok: false` with an error message | When the Jira URL is unreachable (DNS failure, refused connection), the endpoint returns HTTP 200 and `{"ok": false, "error": "..."}` containing a human-readable description | ✓ Met | `test_test_connection_http_error` |
| JCR-T-006 | Jira HTTP 401 / 403 is surfaced to the caller | When Jira returns 401 or 403, the endpoint returns HTTP 200 and `{"ok": false, "httpStatus": 401}` or `{"ok": false, "httpStatus": 403}` respectively | ✓ Met | `test_test_connection_http_error` |
| JCR-T-007 | The test-connection request times out after at most 12 seconds | The `urllib.request.urlopen` call inside `_handle_test_connection` uses a timeout of 12 seconds; no request can hang indefinitely | ✓ Met | — |
| JCR-T-008 | An unexpected server-side exception returns HTTP 500 | If `_handle_test_connection` raises an unhandled exception, the server returns HTTP 500 with `{"ok": false, "error": "..."}` | ✓ Met | — |

---

## 4. SSL / TLS Certificate Handling

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JCR-SSL-001 | A custom CA bundle is used when present | When `certs/jira_ca_bundle.pem` exists, `config.JIRA_SSL_CERT` returns its absolute path and the Jira client is created with `verify_ssl=<path>` | ✓ Met | `test_jira_ssl_cert_returns_path_when_file_exists`, `test_create_client_passes_verify_ssl` |
| JCR-SSL-002 | The system CA store is used when no custom cert is present | When `certs/jira_ca_bundle.pem` is absent, `config.JIRA_SSL_CERT` returns `True` and the Jira client uses the system certificate store | ✓ Met | `test_jira_ssl_cert_returns_true_when_no_file` |
| JCR-SSL-003 | Certificate validity is reported by `cert_utils.validate_cert()` | `validate_cert()` returns a dict with `valid` (bool), `expires_at` (YYYY-MM-DD string), `days_remaining` (int), and `subject` (str); on parse failure it returns `{"valid": False, "error": "..."}` | ✓ Met | `test_cert_status_with_valid_cert_returns_enriched_fields` |
| JCR-SSL-004 | The test-connection request uses the same SSL context as the Jira client | `_jira_ssl_context()` is called inside `_handle_test_connection`; both code paths read from `config.JIRA_SSL_CERT` | ✓ Met | — |
| JCR-SSL-005 | An expired custom CA bundle is reported but does not block client creation | When the PEM file is structurally valid but its `not_valid_after` date has passed, `validate_cert()` returns `{"valid": False, "days_remaining": <negative>}` and the Jira client is still created without error | ⚠ Gap — creation not blocked | — |
| JCR-SSL-006 | Fetch Certificate happy path delivers a parseable, valid cert badge | POST `/api/fetch-cert` with a reachable Jira URL returns `{"ok": true}`; the saved bundle includes both the server cert chain and the Windows CA store (ROOT + CA stores via `ssl.enum_certificates`); a subsequent GET `/api/cert-status` returns `{"exists": true, "valid": true}`; the UI badge transitions from "No certificate" (neutral) to "Valid" (success) | ✓ Met | `test_fetch_cert_success_updates_badge`, `test_positive_e2e_fetch_cert_then_badge_shows_valid`, `test_fetch_cert_saves_pem_without_crlf_line_endings` |
| JCR-SSL-007 | Standard Jira Cloud positive E2E: absent cert file is an acceptable state | When `certs/jira_ca_bundle.pem` is absent, the Connection tab loads with cert badge showing "No certificate" (neutral); Test Connection and Save complete successfully without requiring a cert | ✓ Met | `test_positive_e2e_no_cert_is_acceptable_state` |

---

## 5. Client Timeouts

| ID | Requirement | Acceptance Criterion | Status | Tests |
|----|-------------|----------------------|--------|-------|
| JCR-TO-001 | The Jira API client uses a 55-second connection timeout | `create_client()` passes `timeout=55` to the `atlassian-python-api` `Jira` constructor; any Jira REST call that takes longer than 55 seconds raises a timeout error | ✓ Met | `test_create_client_returns_jira_instance` |
| JCR-TO-002 | The test-connection endpoint enforces a 12-second timeout | `_handle_test_connection` passes `timeout=12` to `urllib.request.urlopen`; a host that does not respond within 12 seconds triggers a `socket.timeout`, returning `{"ok": false, "error": "..."}` | ✓ Met | — |

---

## 6. Future Enhancements

| ID | Requirement | Rationale | Status |
|----|-------------|-----------|--------|
| JCR-FUT-001 | OAuth 2.0 3LO authentication support | Enables integration with corporate Jira instances that disallow API tokens in favour of OAuth flows | Proposed |
| JCR-FUT-002 | Configurable test-connection timeout via `JIRA_TEST_CONNECTION_TIMEOUT` env var | The fixed 12-second timeout is too short on high-latency corporate proxies; an env var would allow tuning without code changes | Proposed |
| JCR-FUT-003 | Block report generation when `certs/jira_ca_bundle.pem` is expired | An expired custom cert is currently only flagged in the UI cert-status badge; the client is still created and will silently fail. Blocking early gives a clearer error | Proposed |
| JCR-FUT-004 | Automatic retry on HTTP 429 (rate-limit) with exponential backoff | Jira Cloud enforces rate limits; a retry strategy would improve resilience for large instances or repeated report runs | Proposed |
