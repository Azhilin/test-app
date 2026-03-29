---
name: logging-utils
description: Use when changing app/utils/logging_setup.py, app/utils/cert_utils.py, or adding a new module to app/utils/. Guides work on the SUCCESS log level, timestamped log output, PEM certificate validation, and shared utility conventions.
---

Use this skill for changes to shared utility modules in `app/utils/`.

**1. Open the smallest relevant context:**

- `app/utils/logging_setup.py`
- `app/utils/cert_utils.py`
- `app/cli.py` (primary consumer of `setup_logging()`)
- `main.py` (also calls `setup_logging()`)
- `tests/unit/` (files matching `test_logging*` or `test_cert*`)

**2. Understand the SUCCESS log level:**

- `SUCCESS_LEVEL = 25` sits between `INFO (20)` and `WARNING (30)`
- Registered at module import time with `logging.addLevelName(25, "SUCCESS")`
- Adds `.success(message)` method directly to `logging.Logger` instances
- Usage: `logger.success("...")` after the module is imported

**3. `setup_logging()` contract:**

- Signature: `setup_logging() -> tuple[logging.Logger, Path]`
- Creates `generated/logs/` automatically (does not fail if it already exists)
- Writes to `generated/logs/app-YYYYMMDD-HHMMSS.log` with format `[timestamp] [level] message`
- Mirrors output to stdout via a `StreamHandler`
- Must be called **once**, at the very top of each CLI entry point, before any `logging.getLogger()` calls produce output
- Returns `(root_logger, log_file_path)` — store the path if you need to surface it to the user

**4. `cert_utils.py`:**

- `validate_cert(cert_path: Path) -> dict`
- Depends on the `cryptography` library (not stdlib; must be in `requirements.txt`)
- Returns `{valid: bool, expires_at: str|None, days_remaining: int|None, subject: str|None}` on success
- Adds `error: str` key on any failure; **never raises**

**5. Adding a new utility module to `app/utils/`:**

- Keep utilities small and single-purpose
- Avoid importing from `app/core/` inside utility modules to prevent circular imports; utilities should be independently importable
- Export the public API from the module level: `from app.utils.<module> import <name>`
- Add tests in `tests/unit/test_<module_name>.py`

**6. Run utility tests:**

```bash
.venv/Scripts/pytest tests/unit/ -v -k "logging or cert"
```

**Token-efficiency:** do not load reporter, template, or Jira client files unless the utility change alters visible output or server behavior.
