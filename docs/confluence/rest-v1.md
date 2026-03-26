# Confluence REST API v1

This document covers the Confluence Cloud REST API v1 — the primary API surface used by the `atlassian-python-api` `Confluence` class in this project.

**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/intro/>  
**OpenAPI spec:** <https://dac-static.atlassian.com/cloud/confluence/swagger.v3.json>  
**Postman collection:** <https://developer.atlassian.com/cloud/confluence/confcloud.1.postman.json>

---

## 1. Base URL and Path

```
https://{your-domain}.atlassian.net/wiki/rest/api/
```

All v1 endpoints are relative to this base path. For example:

```
GET https://your-domain.atlassian.net/wiki/rest/api/content/{id}
```

---

## 2. Authentication

HTTP Basic auth — see [authentication.md](authentication.md).  
Some mutating endpoints require `X-Atlassian-Token: no-check` header.

---

## 3. Pagination

v1 uses **offset-based pagination** with `start` and `limit` query parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `start` | Index of the first result (0-based) | `0` |
| `limit` | Maximum number of results per page | Varies by endpoint (max 100 for most) |

**Response envelope:**

```json
{
  "results": [...],
  "start": 0,
  "limit": 25,
  "size": 25,
  "_links": {
    "next": "/wiki/rest/api/content?start=25&limit=25",
    "self": "https://your-domain.atlassian.net/wiki/rest/api/content"
  }
}
```

Loop until `size < limit` or `_links.next` is absent.

---

## 4. Expansion

Many endpoints support the `expand` query parameter to include nested data. Use dot notation for nested expansion:

```
GET /wiki/rest/api/content/{id}?expand=space,body.storage,version,ancestors
```

Common expand values:

| Value | Description |
|-------|-------------|
| `space` | Space the content belongs to |
| `body.storage` | Content body in Confluence storage format (XHTML) |
| `body.view` | Content body rendered as HTML |
| `body.export_view` | Content body for export |
| `version` | Current version information |
| `ancestors` | Parent page hierarchy |
| `children.page` | Direct child pages |
| `children.attachment` | Attachments |
| `children.comment` | Inline and page comments |
| `history` | Full version history |
| `metadata.labels` | Labels attached to content |
| `restrictions.read.restrictions.user` | Read restrictions by user |
| `restrictions.update.restrictions.group` | Update restrictions by group |

---

## 5. Content Endpoints

**Base path:** `/wiki/rest/api/content`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List content | `GET /wiki/rest/api/content` | Returns pages, blog posts, or comments; filter by `spaceKey`, `title`, `type` |
| Get content by ID | `GET /wiki/rest/api/content/{id}` | Returns a single content item; use `expand` for body, version, etc. |
| Create content | `POST /wiki/rest/api/content` | Create a page, blog post, or comment |
| Update content | `PUT /wiki/rest/api/content/{id}` | Update title, body, or version; must increment `version.number` |
| Delete content | `DELETE /wiki/rest/api/content/{id}` | Moves to trash; use `?status=trashed` to permanently delete |
| Get content history | `GET /wiki/rest/api/content/{id}/history` | Returns version history |
| Get content version | `GET /wiki/rest/api/content/{id}/version/{versionNumber}` | Returns a specific version |
| Restore content version | `POST /wiki/rest/api/content/{id}/version` | Restores content to a previous version |
| Delete content version | `DELETE /wiki/rest/api/content/{id}/version/{versionNumber}` | Permanently removes a version |
| Search content (CQL) | `GET /wiki/rest/api/content/search?cql=...` | CQL-based content search |

**Create page request body:**

```json
{
  "type": "page",
  "title": "My New Page",
  "space": { "key": "TEAM" },
  "body": {
    "storage": {
      "value": "<p>Page content in storage format.</p>",
      "representation": "storage"
    }
  },
  "ancestors": [{ "id": "123456" }]
}
```

**Update page request body** (version number must be incremented):

```json
{
  "type": "page",
  "title": "Updated Title",
  "version": { "number": 2 },
  "body": {
    "storage": {
      "value": "<p>Updated content.</p>",
      "representation": "storage"
    }
  }
}
```

---

## 6. Content Attachments

**Base path:** `/wiki/rest/api/content/{id}/child/attachment`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content---attachments/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get attachments | `GET /wiki/rest/api/content/{id}/child/attachment` | List attachments on a page |
| Upload attachment | `POST /wiki/rest/api/content/{id}/child/attachment` | Upload new file; requires `X-Atlassian-Token: no-check` |
| Update attachment data | `PUT /wiki/rest/api/content/{id}/child/attachment/{attachmentId}/data` | Upload new version of existing attachment |
| Delete attachment | `DELETE /wiki/rest/api/content/{attachmentId}` | Remove attachment |
| Download attachment | `GET /wiki/rest/api/content/{attachmentId}/download` | Download file content |

**Upload attachment** uses `multipart/form-data`:

```python
import requests
from app import config

with open("report.pdf", "rb") as f:
    response = requests.post(
        f"{config.JIRA_URL}/wiki/rest/api/content/{page_id}/child/attachment",
        auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN),
        headers={"X-Atlassian-Token": "no-check"},
        files={"file": ("report.pdf", f, "application/pdf")},
    )
```

---

## 7. Content Labels

**Base path:** `/wiki/rest/api/content/{id}/label`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content-labels/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get labels | `GET /wiki/rest/api/content/{id}/label` | List labels on content |
| Add labels | `POST /wiki/rest/api/content/{id}/label` | Add one or more labels |
| Delete label | `DELETE /wiki/rest/api/content/{id}/label/{label}` | Remove a label |

**Add labels request body:**

```json
[
  { "prefix": "global", "name": "ai-adoption" },
  { "prefix": "global", "name": "sprint-report" }
]
```

---

## 8. Content Comments

**Base path:** `/wiki/rest/api/content/{id}/child/comment`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content---children-and-descendants/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get comments | `GET /wiki/rest/api/content/{id}/child/comment` | List page comments |
| Add comment | `POST /wiki/rest/api/content` (type=comment) | Create a comment on a page |
| Update comment | `PUT /wiki/rest/api/content/{commentId}` | Update comment body |
| Delete comment | `DELETE /wiki/rest/api/content/{commentId}` | Delete a comment |

**Add comment request body:**

```json
{
  "type": "comment",
  "container": { "id": "123456", "type": "page" },
  "body": {
    "storage": {
      "value": "<p>This is a comment.</p>",
      "representation": "storage"
    }
  }
}
```

---

## 9. Content Restrictions

**Base path:** `/wiki/rest/api/content/{id}/restriction`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content-restrictions/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get restrictions | `GET /wiki/rest/api/content/{id}/restriction` | List all restrictions |
| Add restrictions | `POST /wiki/rest/api/content/{id}/restriction` | Add read/update restrictions |
| Update restrictions | `PUT /wiki/rest/api/content/{id}/restriction` | Replace all restrictions |
| Delete restriction | `DELETE /wiki/rest/api/content/{id}/restriction/byOperation/{operation}` | Remove restrictions for an operation |

---

## 10. Space Endpoints

**Base path:** `/wiki/rest/api/space`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-space/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List spaces | `GET /wiki/rest/api/space` | Returns all accessible spaces; filter by `type` (global, personal) |
| Get space | `GET /wiki/rest/api/space/{spaceKey}` | Returns a single space; use `expand` for description, homepage |
| Create space | `POST /wiki/rest/api/space` | Create a new global or personal space |
| Update space | `PUT /wiki/rest/api/space/{spaceKey}` | Update space name or description |
| Delete space | `DELETE /wiki/rest/api/space/{spaceKey}` | Delete a space (long-running task) |
| Get space content | `GET /wiki/rest/api/space/{spaceKey}/content` | List content in a space |

**Create space request body:**

```json
{
  "key": "TEAM",
  "name": "Team Space",
  "description": {
    "plain": {
      "value": "Space for team documentation.",
      "representation": "plain"
    }
  }
}
```

---

## 11. Space Permissions

**Base path:** `/wiki/rest/api/space/{spaceKey}/permission`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-space-permissions/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Add permission | `POST /wiki/rest/api/space/{spaceKey}/permission` | Grant a permission to a user or group |
| Remove permission | `DELETE /wiki/rest/api/space/{spaceKey}/permission/{id}` | Revoke a permission |

Supported `operationKey` + `targetType` pairs:

| operationKey | targetType |
|-------------|------------|
| `read` | `space` |
| `administer` | `space` |
| `export` | `space` |
| `restrict` | `space` |
| `create` | `page`, `blogpost`, `comment`, `attachment` |
| `delete` | `page`, `blogpost`, `comment`, `attachment` |

---

## 12. Search (CQL)

**Base path:** `/wiki/rest/api/search`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/>  
**CQL reference:** <https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Search content | `GET /wiki/rest/api/search?cql=...` | Full-text and structured CQL search |
| Search users | `GET /wiki/rest/api/search/user?cql=...` | Search for users |

**CQL examples:**

```
# Pages in a space modified in the last 7 days
type = page AND space = "TEAM" AND lastModified >= now("-7d")

# Blog posts with a specific label
type = blogpost AND label = "ai-adoption"

# Pages containing specific text
type = page AND text ~ "sprint velocity"

# Pages created by a specific user
type = page AND creator = "user@example.com"
```

---

## 13. Users and Groups

**Base path:** `/wiki/rest/api/user`, `/wiki/rest/api/group`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-users/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get current user | `GET /wiki/rest/api/user/current` | Returns the authenticated user |
| Get user by account ID | `GET /wiki/rest/api/user?accountId={id}` | Returns a user by Atlassian account ID |
| Get user by key | `GET /wiki/rest/api/user?key={key}` | Returns a user by user key (legacy) |
| List groups | `GET /wiki/rest/api/group` | Returns all groups |
| Get group members | `GET /wiki/rest/api/group/{groupName}/member` | Returns members of a group |
| Add user to group | `POST /wiki/rest/api/group/{groupName}/member` | Adds a user to a group |
| Remove user from group | `DELETE /wiki/rest/api/group/{groupName}/member?accountId={id}` | Removes a user from a group |

---

## 14. Templates

**Base path:** `/wiki/rest/api/template`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-template/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List global templates | `GET /wiki/rest/api/template/page` | Returns global page templates |
| List space templates | `GET /wiki/rest/api/template/page?spaceKey={key}` | Returns space-specific templates |
| Get template | `GET /wiki/rest/api/template/{templateId}` | Returns a single template |
| Create template | `POST /wiki/rest/api/template` | Creates a new template |
| Update template | `PUT /wiki/rest/api/template` | Updates an existing template |
| Delete template | `DELETE /wiki/rest/api/template/{templateId}` | Deletes a template |

---

## 15. Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created |
| `204 No Content` | Delete succeeded |
| `400 Bad Request` | Invalid request body or parameters |
| `401 Unauthorized` | Missing or invalid credentials |
| `403 Forbidden` | Authenticated but insufficient permissions |
| `404 Not Found` | Resource does not exist or is not accessible |
| `409 Conflict` | Version conflict on update (increment `version.number`) |
| `429 Too Many Requests` | Rate limit exceeded; back off and retry |
| `500 Internal Server Error` | Atlassian-side error |

---

## 16. Long-Running Tasks

Some operations (e.g. delete space) return a task reference instead of completing immediately:

```json
{
  "id": "task-id",
  "links": {
    "status": "/wiki/rest/api/longtask/task-id"
  }
}
```

Poll `GET /wiki/rest/api/longtask/{taskId}` until `finished: true`.

**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-long-running-task/>
