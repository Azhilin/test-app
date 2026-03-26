# atlassian-python-api — Jira Module Reference

**Official docs:** <https://atlassian-python-api.readthedocs.io/jira.html>  
**PyPI:** <https://pypi.org/project/atlassian-python-api/>  
**GitHub:** <https://github.com/atlassian-api/atlassian-python-api>  
**Version pinned in this project:** `atlassian-python-api>=3.41.0` (`requirements.txt`)

---

## 1. Overview

`atlassian-python-api` is a Python wrapper around the Atlassian REST APIs. The `Jira` class (imported as `from atlassian import Jira`) handles:

- Session management and Basic auth header injection
- URL construction for both Platform API (`/rest/api/2/`) and Agile API (`/rest/agile/1.0/`)
- JSON serialisation/deserialisation
- Retry and error handling

The client defaults to **API v2** for Platform API calls unless `api_version` is passed to the constructor.

---

## 2. Client Construction

```python
from atlassian import Jira

jira = Jira(
    url="https://your-domain.atlassian.net",
    username="user@example.com",
    password="your_api_token",        # API token used as password
    # api_version=2,                  # default; change to 3 for ADF support
    # cloud=True,                     # auto-detected from URL; set explicitly if needed
)
```

**Constructor parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | required | Jira instance base URL |
| `username` | str | required | Atlassian account email |
| `password` | str | required | API token |
| `api_version` | int/str | `2` | Platform API version (`2` or `3`) |
| `cloud` | bool | auto | Set `True` for Jira Cloud |
| `timeout` | int | `75` | Request timeout in seconds |
| `verify_ssl` | bool | `True` | SSL certificate verification |

**How this project creates the client (`app/jira_client.py`):**

```python
from atlassian import Jira
from app import config

def create_client() -> Jira:
    return Jira(
        url=config.JIRA_URL,
        username=config.JIRA_EMAIL,
        password=config.JIRA_API_TOKEN,
    )
```

---

## 3. Methods Used by This Project

### 3.1 `get_all_agile_boards`

**Called in:** `get_board_id()` when `JIRA_BOARD_ID` is not configured.

```python
result = jira.get_all_agile_boards(
    board_name=None,    # optional: filter by name
    project_key=None,   # optional: filter by project
    board_type=None,    # optional: "scrum" or "kanban"
    start=0,
    limit=1,
)
# Returns: {"maxResults": 1, "startAt": 0, "total": N, "values": [{...}]}
board_id = int(result["values"][0]["id"])
```

**Underlying REST call:** `GET /rest/agile/1.0/board`  
**Atlassian docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/#api-rest-agile-1-0-board-get>

---

### 3.2 `get_all_sprints_from_board`

**Called in:** `get_sprints()` — once for `state="closed"`, once for `state="active"`.

```python
result = jira.get_all_sprints_from_board(
    board_id,           # int: board ID
    state="closed",     # optional: "future" | "active" | "closed"
    start=0,
    limit=10,           # JIRA_SPRINT_COUNT
)
# Returns: {"maxResults": 10, "startAt": 0, "total": N, "values": [{sprint}, ...]}
sprints = result.get("values") or []
```

**Underlying REST call:** `GET /rest/agile/1.0/board/{boardId}/sprint`  
**Atlassian docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/#api-rest-agile-1-0-board-boardid-sprint-get>

---

### 3.3 `get_filter`

**Called in:** `get_filter_jql()` when `JIRA_FILTER_ID` is set.

```python
f = jira.get_filter(filter_id)   # int: filter ID
# Returns: {"id": "10000", "name": "...", "jql": "project = ALPHA AND ...", ...}
jql = (f.get("jql") or "").strip()
```

**Underlying REST call:** `GET /rest/api/2/filter/{id}`  
**Atlassian docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-filters/#api-rest-api-2-filter-id-get>

---

### 3.4 `get_all_issues_for_sprint_in_board`

**Called in:** `get_issues_for_sprint()` — paginated loop.

```python
result = jira.get_all_issues_for_sprint_in_board(
    board_id,           # int
    sprint_id,          # int
    jql="",             # optional: additional JQL filter
    start=0,
    limit=50,
)
# Returns: {"startAt": 0, "maxResults": 50, "total": N, "issues": [{issue}, ...]}
issues = result.get("issues") or []
```

**Underlying REST call:** `GET /rest/agile/1.0/board/{boardId}/sprint/{sprintId}/issue`  
**Atlassian docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/#api-rest-agile-1-0-board-boardid-sprint-sprintid-issue-get>

---

### 3.5 `get_issue`

**Called in:** `get_issue_with_changelog()` — fetches a single issue with changelog for cycle-time calculation.

```python
issue = jira.get_issue(
    issue_key,          # str: e.g. "ALPHA-42"
    expand="changelog", # include changelog histories
)
# Returns full issue dict including changelog.histories list
```

**Underlying REST call:** `GET /rest/api/2/issue/{issueIdOrKey}?expand=changelog`  
**Atlassian docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues/#api-rest-api-2-issue-issueidorkey-get>

---

## 4. Internal Session Access

The library exposes its underlying `requests.Session` as `jira._session`. This project uses it in `main.py` to make a raw API call that the library does not wrap:

```python
# main.py — fetch filter name for report header
f = jira._session.get(
    f"{config.JIRA_URL}/rest/api/2/filter/{config.JIRA_FILTER_ID}"
).json()
```

> `_session` is a private attribute. Prefer using library methods where available; use `_session` only when no wrapper method exists.

---

## 5. Additional Methods Available (Not Yet Used)

These methods are available in `atlassian-python-api` and may be useful for extending this project. See [crud-operations.md](crud-operations.md) for the corresponding REST endpoints.

### Issues

```python
jira.issue(key)                                    # GET /rest/api/2/issue/{key}
jira.issue_create(fields)                          # POST /rest/api/2/issue
jira.issue_update(key, fields, update=None)        # PUT /rest/api/2/issue/{key}
jira.issue_transition(key, status)                 # POST /rest/api/2/issue/{key}/transitions
jira.get_issue_transitions(key)                    # GET /rest/api/2/issue/{key}/transitions
jira.get_issue_changelog(key)                      # GET /rest/api/2/issue/{key}/changelog
jira.jql(jql_query)                                # GET /rest/api/2/search?jql=...
jira.issue_add_comment(key, body)                  # POST /rest/api/2/issue/{key}/comment
jira.assign_issue(key, account_id)                 # PUT /rest/api/2/issue/{key}/assignee
jira.set_issue_status(key, status_name)            # POST /rest/api/2/issue/{key}/transitions
```

### Boards

```python
jira.get_agile_board(board_id)                     # GET /rest/agile/1.0/board/{boardId}
jira.create_agile_board(name, type, filter_id)     # POST /rest/agile/1.0/board
jira.delete_agile_board(board_id)                  # DELETE /rest/agile/1.0/board/{boardId}
jira.get_agile_board_configuration(board_id)       # GET /rest/agile/1.0/board/{boardId}/configuration
```

### Sprints

```python
jira.create_sprint(name, board_id, start, end, goal)  # POST /rest/agile/1.0/sprint
jira.rename_sprint(sprint_id, name, start, end)       # POST /rest/agile/1.0/sprint/{sprintId}
jira.add_issues_to_sprint(sprint_id, issue_keys)      # POST /rest/agile/1.0/sprint/{sprintId}/issue
```

### Users

```python
jira.myself()                                      # GET /rest/api/2/myself
jira.user(account_id)                              # GET /rest/api/2/user?accountId=...
jira.user_find_by_user_string(query="...")         # GET /rest/api/2/user/search
```

### Projects

```python
jira.get_all_projects()                            # GET /rest/api/2/project
jira.project(key)                                  # GET /rest/api/2/project/{key}
jira.update_project(key, data)                     # PUT /rest/api/2/project/{key}
jira.delete_project(key)                           # DELETE /rest/api/2/project/{key}
```

### Filters

```python
jira.get_filter(filter_id)                         # GET /rest/api/2/filter/{id}  ← used
# No create_filter or update_filter in the library; use raw _session.post/put
```

---

## 6. Error Handling Pattern

```python
def get_issues_with_changelog(jira, issue_keys):
    out = []
    for key in issue_keys:
        try:
            out.append(jira.get_issue(key, expand="changelog"))
        except Exception:
            out.append({})   # tolerate individual failures; metrics handle missing data
    return out
```

The library raises `requests.exceptions.HTTPError` (wrapped in `atlassian.errors.ApiError` in newer versions) for non-2xx responses. Always wrap calls in `try/except Exception` when partial failure is acceptable.
