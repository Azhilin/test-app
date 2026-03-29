# Logging Requirements — AI Adoption Metrics Report

This document defines the requirements for the application's logging subsystem, implemented in `app/utils/logging_setup.py`. Each requirement includes a measurable acceptance criterion so that it can be verified during development and testing.

---

## Table of Contents

1. [Log File](#1-log-file)
2. [Log Format](#2-log-format)
3. [Output Channels](#3-output-channels)
4. [Log Levels](#4-log-levels)
5. [Entry-Point Integration](#5-entry-point-integration)
6. [Code Quality](#6-code-quality)
7. [Security](#7-security)
8. [Performance](#8-performance)
9. [Log Retention](#9-log-retention)

---

## 1. Log File

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-01 | Each application run writes a unique timestamped log file | A new log file named `app-YYYYMMDD-HHMMSS.log` is created in `generated/logs/` each time `setup_logging()` is called; no two runs share the same filename | ✓ Met |
| LOG-02 | The log directory is created automatically if it does not exist | `setup_logging()` calls `_LOG_DIR.mkdir(parents=True, exist_ok=True)` before opening the log file; invocation succeeds even when `generated/logs/` is absent | ✓ Met |

---

## 2. Log Format

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-03 | All log lines follow a consistent structured format | Every log line is formatted as `[YYYY-MM-DD HH:MM:SS] [LEVEL] message` using `logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")` | ✓ Met |
| LOG-04 | File and console output use the same formatter | A single formatter configuration (identical `fmt` and `datefmt`) is applied to both the `FileHandler` and the `StreamHandler`; output appearance is consistent across both channels | ✓ Met |

---

## 3. Output Channels

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-05 | All log output reaches both a log file and stdout | `setup_logging()` attaches a `FileHandler` and a `StreamHandler` to the root logger; every message emitted at or above `DEBUG` is written to both | ✓ Met |
| LOG-06 | Log files are written in UTF-8 encoding | The `FileHandler` is opened with `encoding="utf-8"`; non-ASCII characters in log messages are stored and retrieved without corruption | ✓ Met |

---

## 4. Log Levels

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-07 | The root logger captures all severity levels by default | `setup_logging()` sets `root.setLevel(logging.DEBUG)`; no `DEBUG` or `INFO` records are silently discarded at the logger level | ✓ Met |
| LOG-08 | A custom SUCCESS level is defined with numeric value 25 | `SUCCESS_LEVEL = 25` is defined at module level; its value is strictly between `logging.INFO` (20) and `logging.WARNING` (30) | ✓ Met |
| LOG-09 | The SUCCESS level name is registered with the logging system | `logging.addLevelName(25, "SUCCESS")` is called at import time; `logging.getLevelName(25)` returns `"SUCCESS"` | ✓ Met |
| LOG-10 | Logger instances expose a `.success()` convenience method | All `logging.Logger` instances have a `.success(message, *args, **kwargs)` method that emits a record at `SUCCESS_LEVEL`; the method is a no-op when the logger is not enabled for `SUCCESS_LEVEL` | ✓ Met |

---

## 5. Entry-Point Integration

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-11 | `setup_logging()` is invoked from the CLI entry point | `app/cli.py` calls `setup_logging()` before any business logic runs; all CLI output (info, success, errors) is captured in the log file for every run | ✓ Met |
| LOG-12 | `setup_logging()` is invoked from the server entry point | `app/server.py` calls `setup_logging()` before the HTTP server starts; all server-side log messages are captured in the log file from server startup | ✓ Met |

---

## 6. Code Quality

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-13 | Entry-point modules use the logging system instead of `print()` | `app/cli.py` and `app/server.py` contain no bare `print()` calls; all user-facing output is emitted via `logging.getLogger(__name__)` | ✓ Met |
| LOG-14 | Log call sites use lazy %-style argument formatting | Log calls pass a `%s`/`%d` format string and separate arguments rather than pre-interpolated f-strings or string concatenation; argument formatting is deferred until the record is actually emitted | ✓ Met |

---

## 7. Security

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-15 | Sensitive credentials are not written to log files | The Jira API token, email address, and instance URL are never passed as arguments to any log call; inspecting a generated log file reveals none of `JIRA_API_TOKEN`, `JIRA_EMAIL`, or `JIRA_URL` values | ✓ Met |

---

## 8. Performance

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-16 | Logging overhead does not measurably slow report generation | The latency added by `setup_logging()` and per-message handler dispatch is not detectable against baseline report generation time; no synchronous flush is inserted between every log line | ⬜ N/T |

---

## 9. Log Retention

| ID | Requirement | Acceptance Criterion | Status |
|----|-------------|----------------------|--------|
| LOG-17 | Log files from previous runs are preserved across runs | `setup_logging()` never deletes, truncates, or overwrites existing files in `generated/logs/`; old log files accumulate until manually removed | ✓ Met |
| LOG-18 | Log files are excluded from version control | `generated/` (and therefore `generated/logs/`) is listed in `.gitignore`; no log file can be accidentally committed to the repository | ✓ Met |
