# Logging Requirements — Coverage Detail

> Source document: [docs/product/requirements/logging_requirements.md](../../../docs/product/requirements/logging_requirements.md)  
> Back to summary: [tests/coverage/test_coverage.md](../test_coverage.md)

**Total:** 18 | **✅ Covered:** 16 | **🔶 Partial:** 0 | **❌ Gap:** 0 | **⬜ N/T:** 2 | **Functional:** 100%


#### Log File

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-01 | Each application run writes a unique timestamped log file | ✅ | `unit/test_logging_setup.py::test_setup_logging_creates_log_file`, `unit/test_logging_setup.py::test_setup_logging_log_filename_matches_pattern` |
| LOG-02 | The log directory is created automatically if it does not exist | ✅ | `unit/test_logging_setup.py::test_setup_logging_creates_log_directory` |

#### Log Format

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-03 | All log lines follow a consistent structured format | ✅ | `unit/test_logging_setup.py::test_log_file_format` |
| LOG-04 | File and console output use the same formatter | ✅ | `unit/test_logging_setup.py::test_log_file_format` |

#### Output Channels

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-05 | All log output reaches both a log file and stdout | ✅ | `unit/test_logging_setup.py::test_setup_logging_attaches_file_handler`, `unit/test_logging_setup.py::test_setup_logging_attaches_stream_handler` |
| LOG-06 | Log files are written in UTF-8 encoding | ✅ | `unit/test_logging_setup.py::test_log_file_format` |

#### Log Levels

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-07 | The root logger captures all severity levels by default | ✅ | `unit/test_logging_setup.py::test_setup_logging_sets_debug_level` |
| LOG-08 | A custom SUCCESS level is defined with numeric value 25 | ✅ | `unit/test_logging_setup.py::test_success_level_value` |
| LOG-09 | The SUCCESS level name is registered with the logging system | ✅ | `unit/test_logging_setup.py::test_success_level_name_registered` |
| LOG-10 | Logger instances expose a .success() convenience method | ✅ | `unit/test_logging_setup.py::test_logger_has_success_method` |

#### Entry-Point Integration

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-11 | setup_logging() is invoked from the CLI entry point | ✅ | `unit/test_logging_setup.py::test_setup_logging_returns_logger_and_path` |
| LOG-12 | setup_logging() is invoked from the server entry point | ✅ | `unit/test_logging_setup.py::test_setup_logging_returns_logger_and_path` |

#### Code Quality

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-13 | Entry-point modules use the logging system instead of print() | ✅ | `unit/test_imports.py::test_import_app_logging_setup` |
| LOG-14 | Log call sites use lazy %-style argument formatting | ✅ | `unit/test_logging_setup.py::test_log_file_format` |

#### Security

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-15 | Sensitive credentials are not written to log files | ✅ | `unit/test_logging_setup.py::test_credentials_not_in_log_output` |

#### Performance

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-16 | Logging overhead does not measurably slow report generation | ⬜ | — |

#### Log Retention

| ID | Requirement | Status | Tests |
|----|-------------|--------|-------|
| LOG-17 | Log files from previous runs are preserved across runs | ✅ | `unit/test_logging_setup.py::test_setup_logging_creates_log_file` |
| LOG-18 | Log files are excluded from version control | ⬜ | — |
