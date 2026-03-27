# Jira Software Agile REST API 1.0

**Official reference:** <https://developer.atlassian.com/cloud/jira/software/rest/intro/>  
**OpenAPI spec:** <https://dac-static.atlassian.com/cloud/jira/software/swagger.v3.json>

---

## 1. About the Agile API

The Jira Software Agile REST API provides access to Scrum and Kanban board resources: boards, sprints, epics, and sprint issues. It is a **separate API** from the Jira Platform REST API (v2/v3) and uses a different base path.

**Base URL:**

```
https://<your-domain>.atlassian.net/rest/agile/1.0/
```

The symbolic alias `latest` resolves to the current version:

```
https://<your-domain>.atlassian.net/rest/agile/latest/
```

All calls in this project go through `atlassian-python-api`, which constructs the full URLs internally. See [atlassian-python-api.md](atlassian-python-api.md) for the library method signatures.

---

## 2. Authentication

See [authentication.md](authentication.md). The Agile API uses the same Basic auth (email + API token) as the Platform API.

---

## 3. Pagination

Agile API paginated responses use the same envelope as the Platform API:

```json
{
  "startAt": 0,
  "maxResults": 50,
  "total": 200,
  "isLast": false,
  "values": [ /* items */ ]
}
```

For sprint issue lists the envelope uses `"issues"` instead of `"values"`:

```json
{
  "startAt": 0,
  "maxResults": 50,
  "total": 120,
  "issues": [ /* issue objects */ ]
}
```

---

## 4. Endpoints Used by This Project

### 4.1 GET /rest/agile/1.0/board — Get All Boards

**Used in:** `app/jira_client.py` `get_board_id()` — discovers the first available board when `JIRA_BOARD_ID` is not configured.

**Official docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/#api-rest-agile-1-0-board-get>

**Request:**

```
GET https://<your-domain>.atlassian.net/rest/agile/1.0/board?startAt=0&maxResults=1
Authorization: Basic <base64(email:token)>
Accept: application/json
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `startAt` | integer | no | Zero-based start index (default: 0) |
| `maxResults` | integer | no | Max boards per page (default: 50) |
| `type` | string | no | Filter by board type: `scrum` or `kanban` |
| `name` | string | no | Filter boards by name (partial match) |
| `projectKeyOrId` | string | no | Filter boards by project |

**Response (200 OK):**

```json
{
  "maxResults": 1,
  "startAt": 0,
  "total": 5,
  "isLast": false,
  "values": [
    {
      "id": 84,
      "self": "https://your-domain.atlassian.net/rest/agile/1.0/board/84",
      "name": "Team Alpha Board",
      "type": "scrum",
      "location": {
        "projectId": 10000,
        "projectKey": "ALPHA",
        "projectName": "Alpha Project",
        "projectTypeKey": "software"
      }
    }
  ]
}
```

---

### 4.2 GET /rest/agile/1.0/board/{boardId}/sprint — Get Sprints for Board

**Used in:** `app/jira_client.py` `get_sprints()` — fetches closed and active sprints.

**Official docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/#api-rest-agile-1-0-board-boardid-sprint-get>

**Request:**

```
GET https://<your-domain>.atlassian.net/rest/agile/1.0/board/{boardId}/sprint
    ?state=closed&startAt=0&maxResults=10
Authorization: Basic <base64(email:token)>
Accept: application/json
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `boardId` | integer | yes (path) | Board ID |
| `state` | string | no | Filter by state: `future`, `active`, `closed` (comma-separated for multiple) |
| `startAt` | integer | no | Zero-based start index |
| `maxResults` | integer | no | Max sprints per page |

**Response (200 OK):**

```json
{
  "maxResults": 10,
  "startAt": 0,
  "total": 24,
  "isLast": false,
  "values": [
    {
      "id": 37,
      "self": "https://your-domain.atlassian.net/rest/agile/1.0/sprint/37",
      "state": "closed",
      "name": "Sprint 12",
      "startDate": "2026-02-01T09:00:00.000Z",
      "endDate": "2026-02-14T18:00:00.000Z",
      "completeDate": "2026-02-14T18:05:00.000Z",
      "originBoardId": 84,
      "goal": "Deliver feature X"
    }
  ]
}
```

**How this project calls it (`app/jira_client.py`):**

```python
result_closed = jira.get_all_sprints_from_board(
    board_id, state="closed", start=0, limit=config.JIRA_SPRINT_COUNT
)
result_active = jira.get_all_sprints_from_board(
    board_id, state="active", start=0, limit=10
)
```

> **Note:** The sprint dict returned by this project does **not** include a `state` field — `compute_velocity` does not filter by state. See `CLAUDE.md` for the canonical sprint dict shape.

---

### 4.3 GET /rest/agile/1.0/board/{boardId}/sprint/{sprintId}/issue — Get Issues for Sprint

**Used in:** `app/jira_client.py` `get_issues_for_sprint()` — paginated fetch of all issues in a sprint.

**Official docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/#api-rest-agile-1-0-board-boardid-sprint-sprintid-issue-get>

**Request:**

```
GET https://<your-domain>.atlassian.net/rest/agile/1.0/board/{boardId}/sprint/{sprintId}/issue
    ?jql=project%3DALPHA&startAt=0&maxResults=50
Authorization: Basic <base64(email:token)>
Accept: application/json
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `boardId` | integer | yes (path) | Board ID |
| `sprintId` | integer | yes (path) | Sprint ID |
| `jql` | string | no | Additional JQL filter (ANDed with sprint scope) |
| `startAt` | integer | no | Zero-based start index |
| `maxResults` | integer | no | Max issues per page (default: 50) |
| `fields` | string | no | Comma-separated field keys to include |
| `expand` | string | no | Expand options (e.g. `changelog`) |

**Response (200 OK):**

```json
{
  "startAt": 0,
  "maxResults": 50,
  "total": 23,
  "issues": [
    {
      "id": "10001",
      "key": "ALPHA-42",
      "self": "https://your-domain.atlassian.net/rest/agile/1.0/issue/10001",
      "fields": {
        "summary": "Implement login page",
        "status": {
          "id": "10002",
          "name": "Done",
          "statusCategory": { "key": "done", "name": "Done" }
        },
        "customfield_10016": 5.0,
        "assignee": {
          "accountId": "5b10a2844c20165700ede21g",
          "displayName": "Mia Kramer"
        },
        "issuetype": { "name": "Story" },
        "priority": { "name": "Medium" }
      }
    }
  ]
}
```

**Pagination loop used in this project:**

```python
start = 0
limit = 50
while True:
    result = jira.get_all_issues_for_sprint_in_board(
        board_id, sprint_id, jql=jql, start=start, limit=limit
    )
    issues = result.get("issues") or []
    all_issues.extend(issues)
    total = result.get("total", 0)
    if start + len(issues) >= total or len(issues) == 0:
        break
    start += len(issues)
```

---

### 4.4 GET /rest/api/2/issue/{issueIdOrKey}?expand=changelog — Get Issue with Changelog

**Used in:** `app/jira_client.py` `get_issue_with_changelog()` — fetches status transition history for cycle-time calculation.

> This endpoint is on the **Platform API v2**, not the Agile API, but is included here because it is called in the context of sprint issue processing.

**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues/#api-rest-api-2-issue-issueidorkey-get>

**Request:**

```
GET https://<your-domain>.atlassian.net/rest/api/2/issue/ALPHA-42?expand=changelog
Authorization: Basic <base64(email:token)>
Accept: application/json
```

**Changelog section of the response:**

```json
{
  "key": "ALPHA-42",
  "fields": { /* standard fields */ },
  "changelog": {
    "startAt": 0,
    "maxResults": 100,
    "total": 3,
    "histories": [
      {
        "id": "10001",
        "created": "2026-02-03T10:15:00.000+0000",
        "items": [
          {
            "field": "status",
            "fieldtype": "jira",
            "fromString": "To Do",
            "toString": "In Progress"
          }
        ]
      },
      {
        "id": "10002",
        "created": "2026-02-10T14:30:00.000+0000",
        "items": [
          {
            "field": "status",
            "fieldtype": "jira",
            "fromString": "In Progress",
            "toString": "Done"
          }
        ]
      }
    ]
  }
}
```

> **Important:** `created` timestamps must be timezone-aware ISO-8601 strings (e.g. `"2026-02-03T10:15:00.000+0000"`). Naive datetimes cause `_parse_iso()` in `app/metrics.py` to return `None`, resulting in `None` cycle time values.

---

## 5. Agile API — Additional Endpoints (Not Yet Used)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /rest/agile/1.0/board/{boardId}` | GET | Get a single board by ID |
| `POST /rest/agile/1.0/board` | POST | Create a new board |
| `DELETE /rest/agile/1.0/board/{boardId}` | DELETE | Delete a board |
| `GET /rest/agile/1.0/board/{boardId}/configuration` | GET | Get board configuration (estimation field, column mapping) |
| `GET /rest/agile/1.0/sprint/{sprintId}` | GET | Get a single sprint |
| `POST /rest/agile/1.0/sprint` | POST | Create a sprint |
| `POST /rest/agile/1.0/sprint/{sprintId}` | POST | Update a sprint |
| `DELETE /rest/agile/1.0/sprint/{sprintId}` | DELETE | Delete a sprint |
| `POST /rest/agile/1.0/sprint/{sprintId}/issue` | POST | Move issues to a sprint |
| `GET /rest/agile/1.0/board/{boardId}/epic` | GET | Get epics for a board |
| `GET /rest/agile/1.0/board/{boardId}/backlog` | GET | Get backlog issues |

For CRUD details on all entities, see [crud-operations.md](crud-operations.md).

---

## 6. Custom Fields in Agile Responses

Jira Software exposes several custom fields relevant to agile metrics:

| Field | Custom Field ID | Description |
|-------|----------------|-------------|
| Story Points | `customfield_10016` (typical Cloud default) | Numeric estimation value; field ID comes from the active schema in `config/jira_schema.json` |
| Sprint | `customfield_10020` | List of sprint objects the issue belongs to |
| Epic Link | `customfield_10014` | Key of the parent epic |
| Epic Name | `customfield_10011` | Name of the epic |

To find the correct custom field ID for your Jira instance:

```
GET /rest/api/2/field
```

Search the response for fields with `"custom": true` and match by `schema.custom` value (e.g. `"com.pyxis.greenhopper.jira:gh-sprint"` for Sprint).

---

## 7. Rate Limits

- No fixed published limit; enforced per-user per-instance.
- HTTP 429 response includes `Retry-After` header.
- This project fetches up to `JIRA_SPRINT_COUNT` (default 10) sprints and up to 100 changelogs per run — well within typical limits.
