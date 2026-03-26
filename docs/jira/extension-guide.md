# Extension Guide — Adding New Jira API Calls

This guide explains the step-by-step pattern for adding new Jira API calls to this project, following the existing architecture in `app/jira_client.py`, `app/config.py`, and `tests/`.

---

## 1. Architecture Overview

```
.env  ──►  app/config.py  ──►  app/jira_client.py  ──►  app/metrics.py
                                      │
                              atlassian-python-api
                                      │
                              Jira Cloud REST APIs
                          (Platform v2/v3, Agile 1.0)
```

All Jira API calls are centralised in `app/jira_client.py`. No other module calls the Jira API directly, except:
- `main.py` — one raw `_session.get` for filter name (legacy; prefer library methods)
- `server.py` — one `urllib.request` for connection test

---

## 2. Step-by-Step: Add a New Jira API Call

### Step 1 — Identify the Endpoint

Consult the relevant reference doc:
- [agile-api.md](agile-api.md) for boards, sprints, sprint issues
- [api-v2.md](api-v2.md) for filters, issues, projects (v2)
- [api-v3.md](api-v3.md) for current-user, ADF-rich-text operations
- [crud-operations.md](crud-operations.md) for the full operation catalogue
- [atlassian-python-api.md](atlassian-python-api.md) for the library method if one exists

### Step 2 — Add a Config Var (if needed)

If the new call requires a configurable parameter (e.g. a project key, label, or numeric ID), add it to `app/config.py`:

```python
# app/config.py
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "").strip() or None
```

And document it in `.env.example`:

```ini
# .env.example
# Optional: Jira project key to scope issue searches (e.g. ALPHA)
# JIRA_PROJECT_KEY=
```

If the var is required for the pipeline to function, add a check in `validate_config()`:

```python
def validate_config() -> list[str]:
    errors = []
    # ... existing checks ...
    if not JIRA_PROJECT_KEY:
        errors.append("JIRA_PROJECT_KEY is not set")
    return errors
```

### Step 3 — Add a Function to `app/jira_client.py`

Follow the existing function conventions:

```python
# app/jira_client.py

def get_project_issues(jira: Jira, project_key: str, jql: str = "") -> list[dict[str, Any]]:
    """Return all issues for a project matching optional JQL, paginated."""
    all_issues: list[dict[str, Any]] = []
    start = 0
    limit = 50
    base_jql = f"project = {project_key}"
    if jql:
        base_jql = f"{base_jql} AND ({jql})"
    while True:
        result = jira.jql(base_jql, start=start, limit=limit)
        issues = result.get("issues") or []
        all_issues.extend(issues)
        total = result.get("total", 0)
        if start + len(issues) >= total or len(issues) == 0:
            break
        start += len(issues)
    return all_issues
```

**Conventions to follow:**

| Convention | Example |
|-----------|---------|
| First argument is always `jira: Jira` | `def get_project_issues(jira: Jira, ...)` |
| Return type is always annotated | `-> list[dict[str, Any]]` |
| Paginate with `start`/`limit` loop | See `get_issues_for_sprint()` |
| Wrap in `try/except` when partial failure is acceptable | See `get_issues_with_changelog()` |
| Use `result.get("key") or []` (not `result["key"]`) | Defensive against missing keys |

### Step 4 — Call from `main.py` or `fetch_sprint_data`

Wire the new function into the data pipeline. If it is part of the sprint data fetch, add it to `fetch_sprint_data()`. If it is a standalone enrichment step, call it from `main.py` after `fetch_sprint_data`:

```python
# main.py
sprints, sprint_issues = jira_client.fetch_sprint_data(jira)

# New: fetch project-level issues for additional metric
if config.JIRA_PROJECT_KEY:
    project_issues = jira_client.get_project_issues(jira, config.JIRA_PROJECT_KEY)
else:
    project_issues = []
```

### Step 5 — Add a New Metric (if needed)

If the new data feeds a new metric, follow the extension pattern in `CLAUDE.md`:

1. Add `compute_<name>(sprints, sprint_issues) -> list[dict]` to `app/metrics.py`
2. Call it in `build_metrics_dict()` and include the result in the returned dict
3. Add rendering in `app/report_md.py`
4. Add rendering in `templates/report.html.j2`

### Step 6 — Write Tests

Add a test file `tests/test_<feature>.py`. Use the test factories from `tests/conftest.py`:

```python
# tests/test_project_issues.py
from unittest.mock import MagicMock
from app.jira_client import get_project_issues
from tests.conftest import make_issue


def test_get_project_issues_returns_all_pages():
    jira = MagicMock()
    page1 = {"issues": [make_issue("ALPHA-1"), make_issue("ALPHA-2")], "total": 3}
    page2 = {"issues": [make_issue("ALPHA-3")], "total": 3}
    jira.jql.side_effect = [page1, page2]

    result = get_project_issues(jira, "ALPHA")

    assert len(result) == 3
    assert jira.jql.call_count == 2


def test_get_project_issues_empty():
    jira = MagicMock()
    jira.jql.return_value = {"issues": [], "total": 0}

    result = get_project_issues(jira, "ALPHA")

    assert result == []
```

**Test factories available in `tests/conftest.py`:**

| Factory | Usage |
|---------|-------|
| `make_sprint(id, name, start, end)` | Create a sprint dict |
| `make_issue(key, status, points, story_points_field)` | Create an issue dict |
| `make_issue_with_changelog(key, in_progress_ts, done_ts)` | Create an issue dict with changelog |

**Pytest fixtures (inject via function arg):**

| Fixture | Contents |
|---------|---------|
| `minimal_metrics_dict` | Metrics dict with sample data |
| `empty_metrics_dict` | Metrics dict with no velocity/cycle-time data |

### Step 7 — Update Test Coverage

After adding tests, regenerate `tests/test_coverage.md`:

```bash
python tests/tools/test_coverage.py
```

Never hand-edit the Test Pyramid block or Count column in `test_coverage.md`.

---

## 3. Using Raw `_session` for Unsupported Endpoints

When `atlassian-python-api` does not provide a wrapper method, use the underlying `requests.Session`:

```python
# GET example
response = jira._session.get(
    f"{config.JIRA_URL}/rest/api/2/filter/search",
    params={"filterName": "Team Alpha", "maxResults": 10}
)
response.raise_for_status()
data = response.json()

# POST example
response = jira._session.post(
    f"{config.JIRA_URL}/rest/api/2/filter",
    json={"name": "New Filter", "jql": "project = ALPHA"}
)
response.raise_for_status()
created = response.json()
```

The session already has the `Authorization: Basic ...` header set.

---

## 4. Adding a New Config Var — Checklist

- [ ] Add `os.getenv(...)` in `app/config.py` as a module-level constant
- [ ] Add to `.env.example` with a descriptive comment
- [ ] Add to `validate_config()` if required
- [ ] Test in `tests/test_config.py` using `monkeypatch` + `importlib.reload(config)` pattern

**Config test pattern:**

```python
# tests/test_config.py
import importlib
from app import config


def test_jira_project_key_defaults_to_none(monkeypatch):
    monkeypatch.delenv("JIRA_PROJECT_KEY", raising=False)
    importlib.reload(config)
    assert config.JIRA_PROJECT_KEY is None


def test_jira_project_key_reads_from_env(monkeypatch):
    monkeypatch.setenv("JIRA_PROJECT_KEY", "ALPHA")
    importlib.reload(config)
    assert config.JIRA_PROJECT_KEY == "ALPHA"
```

---

## 5. Quick Reference: Which API to Use

| What you want to do | API | Library method or endpoint |
|--------------------|-----|---------------------------|
| List boards | Agile 1.0 | `jira.get_all_agile_boards()` |
| List sprints | Agile 1.0 | `jira.get_all_sprints_from_board()` |
| Get issues in sprint | Agile 1.0 | `jira.get_all_issues_for_sprint_in_board()` |
| Get issue + changelog | Platform v2 | `jira.get_issue(key, expand="changelog")` |
| Search issues (JQL) | Platform v2 | `jira.jql(query)` |
| Get saved filter | Platform v2 | `jira.get_filter(id)` |
| Create/update issue | Platform v2 | `jira.issue_create(fields)` / `jira.issue_update(key, fields)` |
| Transition issue status | Platform v2 | `jira.set_issue_status(key, status_name)` |
| Validate credentials | Platform v3 | `GET /rest/api/3/myself` (see `server.py`) |
| List projects | Platform v2 | `jira.get_all_projects()` |
| Create sprint | Agile 1.0 | `jira.create_sprint(name, board_id, start, end, goal)` |
| Move issues to sprint | Agile 1.0 | `jira.add_issues_to_sprint(sprint_id, keys)` |

For full endpoint details, see [crud-operations.md](crud-operations.md).
