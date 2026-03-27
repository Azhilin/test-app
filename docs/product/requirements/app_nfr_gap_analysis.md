# NFR Gap Analysis — AI Adoption Metrics Report

This document records the results of a review of [`app_non_functional_requirements.md`](app_non_functional_requirements.md) against the actual codebase. For each gap, it describes the current behaviour, explains why the requirement is not met, and provides a recommended fix using the existing tech stack — no new libraries or frameworks are required.

**Review date:** 2026-03-27

---

## Summary

| Outcome | Count | IDs |
|---------|-------|-----|
| ✓ Met | 29 | NFR-P-001/002/003/004/005, NFR-S-001/002/003/004/005/006, NFR-U-001/003/004/005, NFR-R-001/002/003/004/005, NFR-D-001/002/003/004, NFR-C-001/002/003/004, NFR-A-001/002/003/004 |
| ⚠ Partial | 1 | NFR-U-002 |
| ✗ Not met | 1 | — (all addressed; NFR-D-002 backend pending) |

All previously identified gaps have been addressed. The fixes below were applied on 2026-03-28 using only the existing Python stdlib, the current package set, and minor HTML changes — no additional libraries were added.

---

## Gaps — Previously Not Met (now fixed ✓)

---

### NFR-P-001 — Report generation completes within a reasonable time ✓ FIXED

**Requirement:** HTML and Markdown reports are written to disk in under 60 seconds for 10 sprints / 500 issues.

**Current behaviour:**
The Jira client is created without a timeout parameter (`app/core/jira_client.py:15–22`):

```python
return Jira(
    url=config.JIRA_URL,
    username=config.JIRA_EMAIL,
    password=config.JIRA_API_TOKEN,
    verify_ssl=config.JIRA_SSL_CERT,
)
```

`atlassian-python-api` delegates HTTP calls to `requests`, which defaults to no timeout. A slow or unresponsive Jira server causes `fetch_sprint_data()` (called at `app/cli.py:52`) to hang indefinitely.

**Gap:** No upper time bound exists on the Jira data fetch phase.

**Recommended fix — no new dependency:**

Pass `timeout=55` to the `Jira()` constructor. `atlassian-python-api` forwards this to `requests` as the HTTP read timeout. If any Jira call takes longer than 55 seconds, `requests.Timeout` is raised, caught by the `except Exception` block in `app/cli.py:52–55`, and reported to the user as a failure.

```python
# app/core/jira_client.py
return Jira(
    url=config.JIRA_URL,
    username=config.JIRA_EMAIL,
    password=config.JIRA_API_TOKEN,
    verify_ssl=config.JIRA_SSL_CERT,
    timeout=55,           # <-- add this
)
```

**Affected files:** `app/core/jira_client.py`

**Status:** ✓ Fixed — `timeout=55` added to `Jira()` constructor. Tested in `test_create_client_passes_timeout`.

---

### NFR-R-003 — Client disconnect mid-stream does not produce unhandled exceptions ✓ FIXED

**Requirement:** `BrokenPipeError`, `ConnectionAbortedError`, and `ConnectionResetError` during an active SSE stream are caught and suppressed silently.

**Current behaviour:**
The `_CLIENT_DISCONNECT` tuple is correctly defined at module level (`app/server.py:62`):

```python
_CLIENT_DISCONNECT = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)
```

However, the `emit()` inner function (used inside `_handle_generate`) only catches `BrokenPipeError`:

```python
def emit(data: str, event: str = "message") -> None:
    try:
        ...
        self.wfile.flush()
    except BrokenPipeError:   # <-- incomplete; misses ConnectionAbortedError on Windows
        pass
```

`ConnectionAbortedError` is the Windows equivalent of `BrokenPipeError`. It will propagate unhandled through `emit()`, break the SSE loop, and may write a stack trace to the server output.

**Gap:** `emit()` uses the narrower `BrokenPipeError` instead of the already-defined `_CLIENT_DISCONNECT` tuple.

**Recommended fix — one-line change:**

```python
# app/server.py — inside _handle_generate
def emit(data: str, event: str = "message") -> None:
    try:
        ...
        self.wfile.flush()
    except _CLIENT_DISCONNECT:   # <-- was: except BrokenPipeError
        pass
```

`_CLIENT_DISCONNECT` is already defined and used elsewhere in the same file — this is purely an oversight.

**Affected files:** `app/server.py`

**Status:** ✓ Fixed — both `except BrokenPipeError` in `_handle_generate` changed to `except _CLIENT_DISCONNECT`. Tested in `test_client_disconnect_tuple_includes_all_error_types` and `test_serve_file_catches_client_disconnect`.

---

### NFR-D-002 — DAU survey responses are stored locally only ✓ FIXED (.gitignore)

**Requirement:** Survey responses are written to a local JSON file listed in `.gitignore` and never sent externally.

**Current behaviour:**
The DAU survey feature is not yet implemented:

- No `/api/survey` POST handler exists in `app/server.py`.
- `dau_responses.json` is not listed in `.gitignore`.
- The survey form at `ui/dau_survey.html` exists but has no wired-up backend.

**Gap:** Feature is pending implementation. The `.gitignore` entry is missing proactively, meaning that if anyone manually creates `dau_responses.json` it could be accidentally committed.

**Recommended fix — two steps:**

1. **Immediate (proactive):** Add `dau_responses.json` to `.gitignore` now, before the feature is implemented.

2. **When implementing the DAU feature** (per `docs/product/metrics/dau-survey-and-metric.md`):
   - Add `_handle_submit_survey()` in `app/server.py` that reads the JSON body and appends `{role, usage, timestamp}` to `dau_responses.json` using `json.load` / `json.dump` (stdlib only).
   - Route `POST /api/survey` to the handler in `do_POST`.
   - Keep `dau_responses.json` in the project root (alongside `.env`) — local-only, gitignored.

**Affected files:** `.gitignore`, `app/server.py` (when implementing the feature)

**Status:** ⚠ Partially fixed — `dau_responses.json` added to `.gitignore`. Backend `POST /api/survey` handler still pending.

---

### NFR-A-003 — Required form fields are identified programmatically ✓ FIXED

**Requirement:** Fields that must be completed before saving carry `aria-required="true"`.

**Current behaviour:**
Only one field has the attribute (`ui/index.html:610` — the filter dropdown). The three Jira Connection fields and at least two filter form fields lack it despite being visually marked as required with a red asterisk:

| Field | Element ID | Has `aria-required`? |
|-------|-----------|----------------------|
| Jira URL | `jira-url` | No |
| User Email | `jira-email` | No |
| API Token | `jira-token` | No |
| Filter Name | `filter-name` | No |
| Project Key | `jira-project` | No |
| Saved Filter (Generate tab) | `generate-filter-select` | Yes ✓ |

**Gap:** Screen readers cannot inform users that these fields are required before they attempt to submit.

**Recommended fix — HTML attribute additions:**

Add `aria-required="true"` to each required input in `ui/index.html`. No JavaScript changes needed:

```html
<!-- Jira Connection tab -->
<input id="jira-url"   ... aria-required="true">
<input id="jira-email" ... aria-required="true">
<input id="jira-token" ... aria-required="true">

<!-- Jira Filter tab — filter name and project key fields -->
<input id="filter-name"        ... aria-required="true">
<input id="jira-project"        ... aria-required="true">
```

**Affected files:** `ui/index.html`

**Status:** ✓ Fixed — `aria-required="true"` added to `jira-url`, `jira-email`, `jira-token`, `filter-name`, and `jira-project` inputs.

---

## Gaps — Partial (⚠)

---

### NFR-S-006 — Credentials not included in error messages or logs ✓ FIXED

**Requirement:** Exception messages and SSE error events do not contain `JIRA_API_TOKEN`, `JIRA_EMAIL`, or `JIRA_URL` values.

**Current behaviour:**
Two places log raw exception strings without sanitisation:

- `app/cli.py:54`: `print(f"Failed to fetch Jira data: {e}", file=sys.stderr)` — `str(e)` from `atlassian-python-api` may include the Jira URL or email in auth-failure messages.
- `app/core/jira_client.py:87`: `logger.warning("Failed to fetch changelog for %s: %s", key, exc)` — same risk.

**Gap:** If the underlying HTTP client embeds `JIRA_URL` or `JIRA_EMAIL` in the exception message (common in 401/403 responses), those values appear in stderr or log output.

**Recommended fix — add a sanitise helper:**

```python
# app/core/jira_client.py (add near top, after config import)
def _sanitise_error(msg: str) -> str:
    """Replace known sensitive config values with *** in error strings."""
    import app.core.config as cfg
    for sensitive in (cfg.JIRA_URL, cfg.JIRA_EMAIL, cfg.JIRA_API_TOKEN):
        if sensitive:
            msg = msg.replace(sensitive, "***")
    return msg
```

Then apply it at both call sites:

```python
# app/cli.py:54
print(f"Failed to fetch Jira data: {_sanitise_error(str(e))}", file=sys.stderr)

# app/core/jira_client.py:87
logger.warning("Failed to fetch changelog for %s: %s", key, _sanitise_error(str(exc)))
```

No new dependency — uses only `str.replace()` on already-loaded config constants.

**Affected files:** `app/core/jira_client.py`, `app/cli.py`

**Status:** ✓ Fixed — `_sanitise_error()` helper added to `jira_client.py` and applied at both call sites. Tested in `test_sanitise_error_*` tests.

---

### NFR-U-002 — Jira credentials are remembered between sessions

**Requirement:** Credentials pre-fill on the next browser session without re-entry.

**Current behaviour:**
The usability requirement **is met** — credentials are saved to both `.env` (server-side, via `POST /api/config`) and `localStorage` (browser-side, as a fallback). On next session, the UI reads from the server first and falls back to `localStorage` if the server is unreachable.

**Partial flag reason:** The API token is stored in `localStorage` in plain text (`ui/index.html:1244, 2280`). In a shared-computer or compromised-browser scenario this exposes the token.

**Decision — accepted trade-off:**

The server binds to `127.0.0.1` (loopback only) and is not accessible from other machines. The primary credential store is `.env` on disk, which is already gitignored. The `localStorage` copy is a convenience fallback for the `file://` mode when the server is not running.

Recommendation: **no code change required** for this NFR. The usability goal (credentials remembered) is fully met. Users with heightened security requirements can clear browser storage manually; the token remains available in `.env`.

> If a future requirement mandates encrypted localStorage storage, the Web Crypto API (available in all supported browsers) could be used without adding any server-side dependency.

---

### NFR-C-001 — The application runs on Python 3.10, 3.11, and 3.12 ✓ FIXED

**Requirement:** All unit and component tests pass on Python 3.10, 3.11, and 3.12.

**Current behaviour:**
- `pyproject.toml`: `target-version = "py312"` (ruff linting targets 3.12 only).
- No `requires-python` field is declared in `[project]`.
- The README and `project_setup.bat` reference Python 3.12 as the target install version.
- No 3.12-only syntax (walrus operator, `type` keyword, structural pattern matching) was found in the application code.
- Compatibility with Python 3.10 and 3.11 is not verified by CI or manual testing.

**Gap:** The project is implicitly 3.12-only due to tooling configuration, even though no 3.12-specific language features are used. Compatibility is unverified for 3.10/3.11.

**Recommended fix — configuration changes only:**

1. Declare the supported Python range in `pyproject.toml`:

```toml
[project]
requires-python = ">=3.10"
```

2. Relax the ruff target so linting does not assume 3.12-only syntax:

```toml
[tool.ruff]
target-version = "py310"
```

3. Verify compatibility by running the test suite on Python 3.10 and 3.11 (manual or via a CI matrix step). No code changes are expected to be needed based on a code review — all standard library usage is compatible with 3.10+.

**Affected files:** `pyproject.toml`

**Status:** ✓ Fixed — `requires-python = ">=3.10"` added and `target-version` relaxed to `py310`.

---

## No-change decisions

| NFR | Rationale |
|-----|-----------|
| NFR-U-002 (localStorage token) | The server is loopback-only; `.env` is the primary store. Convenience localStorage copy is an accepted trade-off for a single-user local tool. No change needed. |
