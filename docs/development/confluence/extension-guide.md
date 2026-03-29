# Extension Guide — Adding New Confluence API Calls

This guide explains the step-by-step pattern for adding new Confluence API calls to this project, following the same architecture used for Jira in `app/jira_client.py` and `app/config.py`.

---

## 1. Architecture Overview

```
.env  ──►  app/config.py  ──►  app/confluence_client.py  ──►  app/metrics.py
                                         │
                                 atlassian-python-api
                                         │
                            Confluence Cloud REST APIs
                              (v1: /wiki/rest/api/,
                               v2: /wiki/api/v2/)
```

All Confluence API calls should be centralised in `app/confluence_client.py` (to be created). No other module should call the Confluence API directly, mirroring the pattern in `app/jira_client.py`.

---

## 2. Step 1 — Create `app/confluence_client.py`

This file does not yet exist. Create it following the exact same structure as `app/jira_client.py`:

```python
"""Confluence Cloud API client wrapper."""
from __future__ import annotations

from typing import Any

from atlassian import Confluence

from app import config


def create_client() -> Confluence:
    """Create and return an authenticated Confluence client."""
    return Confluence(
        url=config.CONFLUENCE_URL,   # defaults to JIRA_URL — see config.py
        username=config.JIRA_EMAIL,
        password=config.JIRA_API_TOKEN,
    )
```

Add `CONFLUENCE_URL` to `app/config.py` (see Step 2 below).

---

## 3. Step 2 — Add Config Vars (if needed)

If the new call requires a configurable parameter, add it to `app/config.py`:

```python
# app/config.py

# Confluence base URL — defaults to JIRA_URL (same Atlassian Cloud domain)
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "").rstrip("/") or JIRA_URL

# Optional: default Confluence space key for read/write operations
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "").strip() or None
```

Document new vars in `.env.example`:

```ini
# .env.example

# Optional: Confluence base URL if different from JIRA_URL
# CONFLUENCE_URL=

# Optional: Default Confluence space key (e.g. TEAM)
# CONFLUENCE_SPACE_KEY=
```

If the var is required for the pipeline to function, add a check in `validate_config()`:

```python
def validate_config() -> list[str]:
    errors = []
    # ... existing checks ...
    if not CONFLUENCE_SPACE_KEY:
        errors.append("CONFLUENCE_SPACE_KEY is not set")
    return errors
```

**Config test pattern** (same as Jira config tests):

```python
# tests/test_config.py
import importlib
from app import config


def test_confluence_space_key_defaults_to_none(monkeypatch):
    monkeypatch.delenv("CONFLUENCE_SPACE_KEY", raising=False)
    importlib.reload(config)
    assert config.CONFLUENCE_SPACE_KEY is None


def test_confluence_space_key_reads_from_env(monkeypatch):
    monkeypatch.setenv("CONFLUENCE_SPACE_KEY", "TEAM")
    importlib.reload(config)
    assert config.CONFLUENCE_SPACE_KEY == "TEAM"
```

---

## 4. Step 3 — Add a Function to `app/confluence_client.py`

Follow the same conventions as `app/jira_client.py`:

```python
# app/confluence_client.py

def get_pages_in_space(
    confluence: Confluence, space_key: str, limit: int = 100
) -> list[dict[str, Any]]:
    """Return all pages in the given space (paginated)."""
    all_pages: list[dict[str, Any]] = []
    start = 0
    while True:
        result = confluence.get_all_pages_from_space(
            space_key, start=start, limit=limit, expand="version"
        )
        pages = result.get("results") or []
        all_pages.extend(pages)
        total = result.get("size", 0)
        if total < limit or len(pages) == 0:
            break
        start += len(pages)
    return all_pages
```

**Conventions to follow:**

| Convention | Example |
|-----------|---------|
| First argument is always `confluence: Confluence` | `def get_pages_in_space(confluence: Confluence, ...)` |
| Return type is always annotated | `-> list[dict[str, Any]]` |
| Paginate with `start`/`limit` loop (v1) or cursor loop (v2) | See pagination patterns below |
| Wrap in `try/except` when partial failure is acceptable | See `get_issues_with_changelog()` in `jira_client.py` |
| Use `result.get("key") or []` (not `result["key"]`) | Defensive against missing keys |

---

## 5. Step 4 — Pagination Patterns

### v1 Offset-Based Pagination

```python
def get_all_space_pages(confluence: Confluence, space_key: str) -> list[dict]:
    all_pages = []
    start = 0
    limit = 100
    while True:
        result = confluence.get_all_pages_from_space(space_key, start=start, limit=limit)
        pages = result.get("results") or []
        all_pages.extend(pages)
        if len(pages) < limit:
            break
        start += len(pages)
    return all_pages
```

### v2 Cursor-Based Pagination (raw `_session`)

```python
def get_all_pages_v2(confluence: Confluence, space_id: str) -> list[dict]:
    all_pages = []
    url = f"{config.CONFLUENCE_URL}/wiki/api/v2/pages"
    params: dict = {"space-id": space_id, "limit": 250}
    while url:
        response = confluence._session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        all_pages.extend(data.get("results") or [])
        next_link = data.get("_links", {}).get("next")
        url = f"{config.CONFLUENCE_URL}{next_link}" if next_link else None
        params = {}  # cursor is embedded in the next URL
    return all_pages
```

---

## 6. Step 5 — Using Raw `_session` for Unsupported Endpoints

When `atlassian-python-api` does not provide a wrapper method, use the underlying `requests.Session`. The session already carries `Authorization: Basic ...`:

```python
# GET example — v2 endpoint
response = confluence._session.get(
    f"{config.CONFLUENCE_URL}/wiki/api/v2/spaces",
    params={"keys": config.CONFLUENCE_SPACE_KEY, "limit": 1},
)
response.raise_for_status()
space_id = response.json()["results"][0]["id"]

# POST example — create a page via v2
response = confluence._session.post(
    f"{config.CONFLUENCE_URL}/wiki/api/v2/pages",
    json={
        "spaceId": space_id,
        "status": "current",
        "title": "New Report",
        "body": {"representation": "storage", "value": "<p>Content</p>"},
    },
)
response.raise_for_status()
created = response.json()

# POST example — v1 endpoint requiring XSRF header
response = confluence._session.post(
    f"{config.CONFLUENCE_URL}/wiki/rest/api/content/{page_id}/label",
    json=[{"prefix": "global", "name": "sprint-report"}],
    headers={"X-Atlassian-Token": "no-check"},
)
response.raise_for_status()
```

---

## 7. Step 6 — Wire into the Pipeline (if needed)

If the new Confluence call is part of the report generation pipeline, call it from `main.py` after the Jira data fetch:

```python
# main.py
import app.confluence_client as confluence_client

# Existing Jira fetch
sprints, sprint_issues = jira_client.fetch_sprint_data(jira)

# New: publish report to Confluence
if config.CONFLUENCE_SPACE_KEY:
    confluence = confluence_client.create_client()
    confluence_client.publish_report(confluence, metrics_dict, config.CONFLUENCE_SPACE_KEY)
```

---

## 8. Step 7 — Write Tests

Add a test file `tests/test_confluence_<feature>.py`. Mock the `Confluence` client with `MagicMock`:

```python
# tests/test_confluence_pages.py
from unittest.mock import MagicMock
from app.confluence_client import get_pages_in_space


def test_get_pages_in_space_returns_all_pages():
    confluence = MagicMock()
    page1 = {"id": "1", "title": "Page 1", "type": "page"}
    page2 = {"id": "2", "title": "Page 2", "type": "page"}
    # First call returns 2 pages (limit=2, size=2 → stop)
    confluence.get_all_pages_from_space.return_value = {
        "results": [page1, page2],
        "size": 2,
    }

    result = get_pages_in_space(confluence, "TEAM", limit=100)

    assert len(result) == 2
    assert result[0]["id"] == "1"
    confluence.get_all_pages_from_space.assert_called_once_with(
        "TEAM", start=0, limit=100, expand="version"
    )


def test_get_pages_in_space_empty():
    confluence = MagicMock()
    confluence.get_all_pages_from_space.return_value = {"results": [], "size": 0}

    result = get_pages_in_space(confluence, "TEAM")

    assert result == []
```

---

## 9. Step 8 — Update Test Coverage

After adding tests, regenerate `tests/coverage/test_coverage.md`:

```bash
python tests/tools/test_coverage.py
```

Never hand-edit the Test Pyramid block or Count column in `test_coverage.md`.

---

## 10. Adding a New Config Var — Checklist

- [ ] Add `os.getenv(...)` in `app/config.py` as a module-level constant
- [ ] Add to `.env.example` with a descriptive comment
- [ ] Add to `validate_config()` if required
- [ ] Test in `tests/test_config.py` using `monkeypatch` + `importlib.reload(config)` pattern

---

## 11. Quick Reference: Which API and Method to Use

| What you want to do | API | Library method or endpoint |
|--------------------|-----|---------------------------|
| Check if page exists | v1 | `confluence.page_exists(space, title)` |
| Get page by title | v1 | `confluence.get_page_by_title(space, title)` |
| Get page by ID | v1 | `confluence.get_page_by_id(page_id, expand)` |
| Create page | v1 | `confluence.create_page(space, title, body, parent_id)` |
| Update page | v1 | `confluence.update_page(page_id, title, body)` |
| Create or update page | v1 | `confluence.update_or_create(parent_id, title, body)` |
| Append to page | v1 | `confluence.append_page(page_id, title, append_body)` |
| Delete page | v1 | `confluence.remove_page(page_id)` |
| Upload attachment | v1 | `confluence.attach_file(filename, page_id=id)` |
| Add label | v1 | `confluence.set_page_label(page_id, label)` |
| Add comment | v1 | `confluence.add_comment(page_id, text)` |
| Search content (CQL) | v1 | `confluence.cql(cql, limit)` |
| List spaces | v1 | `confluence.get_all_spaces(limit)` |
| Get space | v1 | `confluence.get_space(space_key)` |
| List all pages in space | v1 | `confluence.get_all_pages_from_space(space)` |
| List pages (v2, cursor) | v2 raw | `confluence._session.get("/wiki/api/v2/pages", ...)` |
| Create page (v2) | v2 raw | `confluence._session.post("/wiki/api/v2/pages", json={...})` |
| Resolve space key → ID | v2 raw | `GET /wiki/api/v2/spaces?keys={key}` |
| Grant space permission | v1 | `confluence.set_permissions_to_user_for_space(key, user, ops)` |
| Add user to group | v1 | `confluence.add_user_to_group(username, group_name)` |

For full endpoint details, see [crud-operations.md](crud-operations.md).  
For v2 endpoint reference, see [rest-v2.md](rest-v2.md).  
For all library methods, see [atlassian-python-api.md](atlassian-python-api.md).
