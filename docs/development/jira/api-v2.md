# Jira Platform REST API v2

**Official reference:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/intro/>  
**OpenAPI spec:** <https://dac-static.atlassian.com/cloud/jira/platform/swagger.v3.json>  
**Postman collection:** <https://developer.atlassian.com/cloud/jira/platform/jiracloud.2.postman.json>

---

## 1. About v2

Jira Platform REST API v2 is the stable, widely-supported version of the Jira Cloud platform API. It offers the same operations as v3 but returns plain text strings for rich text fields instead of [Atlassian Document Format (ADF)](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/). This project uses v2 for one explicit call and implicitly via `atlassian-python-api` defaults.

**Base URL:**

```
https://<your-domain>.atlassian.net/rest/api/2/
```

---

## 2. Authentication

See [authentication.md](authentication.md). All v2 calls in this project use HTTP Basic auth (email + API token).

---

## 3. Endpoints Used by This Project

### 3.1 GET /rest/api/2/filter/{id} — Get Filter

**Used in:** `main.py` (line 67) — fetches filter name for report header metadata.

**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-filters/#api-rest-api-2-filter-id-get>

**Request:**

```
GET https://<your-domain>.atlassian.net/rest/api/2/filter/{id}
Authorization: Basic <base64(email:token)>
Accept: application/json
```

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `id` | integer | path | yes | Numeric ID of the saved filter |
| `expand` | string | query | no | Comma-separated list of properties to expand (e.g. `sharedUsers,subscriptions`) |

**Minimal response (200 OK):**

```json
{
  "id": "10000",
  "name": "My Team Filter",
  "description": "Issues for team Alpha",
  "owner": {
    "accountId": "5b10a2844c20165700ede21g",
    "displayName": "Mia Kramer"
  },
  "jql": "project = ALPHA AND sprint in openSprints()",
  "viewUrl": "https://your-domain.atlassian.net/issues/?filter=10000",
  "searchUrl": "https://your-domain.atlassian.net/rest/api/2/search?jql=...",
  "favourite": false,
  "sharePermissions": [],
  "editPermissions": []
}
```

**How it is called in this project:**

```python
# main.py
f = jira._session.get(
    f"{config.JIRA_URL}/rest/api/2/filter/{config.JIRA_FILTER_ID}"
).json()
metrics_dict["filter_name"] = f.get("name") or None
```

**Required permissions:** The user must own the filter or it must be shared with them.

---

## 4. Pagination

v2 paginated responses use this envelope:

```json
{
  "startAt": 0,
  "maxResults": 50,
  "total": 200,
  "isLast": false,
  "values": [ /* items */ ]
}
```

| Field | Description |
|-------|-------------|
| `startAt` | Zero-based index of the first item in this page |
| `maxResults` | Maximum items per page (may be lower than requested) |
| `total` | Total items across all pages (may change between requests) |
| `isLast` | `true` when this is the final page (not always present) |

**Pagination pattern used in this project** (`app/jira_client.py`):

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

## 5. Expansion

Append `?expand=<property>` to include additional data:

```
GET /rest/api/2/issue/PROJ-1?expand=changelog,names,renderedFields
```

This project uses `expand=changelog` when fetching issues for cycle-time calculation:

```python
jira.get_issue(issue_key, expand="changelog")
```

---

## 6. Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Success |
| `201 Created` | Resource created |
| `204 No Content` | Success, no body |
| `400 Bad Request` | Invalid parameters |
| `401 Unauthorized` | Missing or invalid credentials |
| `403 Forbidden` | Authenticated but insufficient permissions |
| `404 Not Found` | Resource does not exist or user has no access |
| `429 Too Many Requests` | Rate limit exceeded |

**Error response body:**

```json
{
  "errorMessages": ["Issue does not exist or you do not have permission to see it."],
  "errors": {}
}
```

---

## 7. Special Request Headers

| Header | When Required |
|--------|--------------|
| `X-Atlassian-Token: no-check` | All `multipart/form-data` requests (file uploads) |
| `Content-Type: application/json` | All POST/PUT requests with a JSON body |
| `Accept: application/json` | Recommended on all GET requests |

---

## 8. Rate Limits & Pagination Notes

- Atlassian does not publish a fixed rate limit number; limits are enforced per-user and per-instance.
- Responses include `Retry-After` header when rate-limited (HTTP 429).
- Default page size for most list endpoints is 50; maximum is typically 100–1000 depending on the endpoint.
- Always check `total` and loop until `startAt + len(page) >= total`.

---

## 9. Additional v2 Endpoints Available (Not Yet Used)

These endpoints are available via v2 and may be useful for future extensions. See [crud-operations.md](crud-operations.md) for full CRUD details.

| Endpoint | Description |
|----------|-------------|
| `GET /rest/api/2/issue/{issueIdOrKey}` | Get a single issue |
| `POST /rest/api/2/issue` | Create an issue |
| `PUT /rest/api/2/issue/{issueIdOrKey}` | Update an issue |
| `DELETE /rest/api/2/issue/{issueIdOrKey}` | Delete an issue |
| `GET /rest/api/2/search` | Search issues with JQL |
| `GET /rest/api/2/project` | List all projects |
| `GET /rest/api/2/field` | List all fields (find custom field IDs) |
| `GET /rest/api/2/user` | Get user by account ID |
| `GET /rest/api/2/myself` | Get authenticated user info |
