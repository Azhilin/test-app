# Confluence REST API v2

This document covers the Confluence Cloud REST API v2 — the current recommended surface for new integrations. Use v2 endpoints via raw `_session` calls when the `atlassian-python-api` legacy `Confluence` class does not provide a wrapper.

**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/intro/>  
**OpenAPI spec:** <https://dac-static.atlassian.com/cloud/confluence/openapi-v2.v3.json>  
**Postman collection:** <https://developer.atlassian.com/cloud/confluence/confcloud.2.postman.json>

---

## 1. Base URL and Path

```
https://{your-domain}.atlassian.net/wiki/api/v2/
```

All v2 endpoints are relative to this base path. For example:

```
GET https://your-domain.atlassian.net/wiki/api/v2/pages
```

---

## 2. Authentication

Same HTTP Basic auth as v1 — see [authentication.md](authentication.md).

---

## 3. Key Differences from v1

| Feature | v1 | v2 |
|---------|----|----|
| Base path | `/wiki/rest/api/` | `/wiki/api/v2/` |
| Pagination | Offset-based (`start` + `limit`) | Cursor-based (`limit` + `cursor` from `Link` header) |
| Content IDs | Numeric strings | Numeric strings (same) |
| Space IDs | Space keys (e.g. `TEAM`) | Numeric space IDs (use `/spaces?keys=TEAM` to resolve) |
| Response envelope | `results`, `start`, `limit`, `size` | `results`, `_links.next` |
| Library support | Full (`atlassian-python-api` Confluence class) | Partial (use raw `_session` calls) |
| Coverage | Broad (all entity types) | Focused (pages, blog posts, spaces, labels, comments, attachments) |
| New entity types | — | Databases, Folders, Smart Links, Whiteboards, Classification Levels |

---

## 4. Cursor-Based Pagination

v2 uses **cursor-based pagination**. The `cursor` token is opaque — do not construct it manually.

**Request:**

```
GET /wiki/api/v2/pages?limit=25
```

**Response headers:**

```
Link: </wiki/api/v2/pages?limit=25&cursor=<token>>; rel="next"
```

**Response body:**

```json
{
  "results": [...],
  "_links": {
    "next": "/wiki/api/v2/pages?limit=25&cursor=<token>"
  }
}
```

**Pagination loop pattern:**

```python
from app import config

def get_all_pages_v2(confluence, space_id: str) -> list[dict]:
    results = []
    url = f"{config.JIRA_URL}/wiki/api/v2/pages"
    params = {"space-id": space_id, "limit": 250}
    while url:
        response = confluence._session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("results") or [])
        next_link = data.get("_links", {}).get("next")
        url = f"{config.JIRA_URL}{next_link}" if next_link else None
        params = {}  # cursor is embedded in the next URL
    return results
```

---

## 5. Pages

**Base path:** `/wiki/api/v2/pages`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List pages | `GET /wiki/api/v2/pages` | Returns pages; filter by `space-id`, `title`, `status` |
| Get page by ID | `GET /wiki/api/v2/pages/{id}` | Returns a single page; use `body-format` for content |
| Create page | `POST /wiki/api/v2/pages` | Create a new page |
| Update page | `PUT /wiki/api/v2/pages/{id}` | Update page title, body, or status |
| Delete page | `DELETE /wiki/api/v2/pages/{id}` | Move page to trash |
| Get page ancestors | `GET /wiki/api/v2/pages/{id}/ancestors` | Returns ancestor pages |
| Get page children | `GET /wiki/api/v2/pages/{id}/children` | Returns child pages |
| Get page versions | `GET /wiki/api/v2/pages/{id}/versions` | Returns version history |
| Get page version | `GET /wiki/api/v2/pages/{id}/versions/{versionNumber}` | Returns a specific version |

**`body-format` query parameter values:**

| Value | Description |
|-------|-------------|
| `storage` | Confluence storage format (XHTML) |
| `atlas_doc_format` | Atlassian Document Format (ADF, JSON) |
| `wiki` | Wiki markup |
| `anonymous_export_view` | HTML for anonymous export |

**Create page request body:**

```json
{
  "spaceId": "98304",
  "status": "current",
  "title": "Sprint Velocity Report",
  "parentId": "123456",
  "body": {
    "representation": "storage",
    "value": "<p>Sprint velocity data goes here.</p>"
  }
}
```

**Update page request body** (version number must be incremented):

```json
{
  "id": "789012",
  "status": "current",
  "title": "Updated Sprint Velocity Report",
  "version": { "number": 2, "message": "Updated with latest sprint data" },
  "body": {
    "representation": "storage",
    "value": "<p>Updated content.</p>"
  }
}
```

---

## 6. Blog Posts

**Base path:** `/wiki/api/v2/blogposts`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-blog-post/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List blog posts | `GET /wiki/api/v2/blogposts` | Returns blog posts; filter by `space-id`, `title` |
| Get blog post | `GET /wiki/api/v2/blogposts/{id}` | Returns a single blog post |
| Create blog post | `POST /wiki/api/v2/blogposts` | Create a new blog post |
| Update blog post | `PUT /wiki/api/v2/blogposts/{id}` | Update blog post content |
| Delete blog post | `DELETE /wiki/api/v2/blogposts/{id}` | Move blog post to trash |

**Create blog post request body:**

```json
{
  "spaceId": "98304",
  "status": "current",
  "title": "AI Adoption Update — Q1 2026",
  "body": {
    "representation": "storage",
    "value": "<p>This quarter's AI adoption metrics...</p>"
  }
}
```

---

## 7. Spaces

**Base path:** `/wiki/api/v2/spaces`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List spaces | `GET /wiki/api/v2/spaces` | Returns accessible spaces; filter by `keys`, `type`, `status` |
| Get space | `GET /wiki/api/v2/spaces/{id}` | Returns a single space by numeric ID |

> **Note:** v2 spaces use numeric IDs, not keys. Resolve a key to an ID:
> ```
> GET /wiki/api/v2/spaces?keys=TEAM
> ```

---

## 8. Attachments

**Base path:** `/wiki/api/v2/attachments`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-attachment/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List attachments | `GET /wiki/api/v2/attachments` | Returns attachments; filter by `mediaType`, `filename` |
| Get attachment | `GET /wiki/api/v2/attachments/{id}` | Returns a single attachment |
| Get attachment versions | `GET /wiki/api/v2/attachments/{id}/versions` | Returns version history |
| Get page attachments | `GET /wiki/api/v2/pages/{id}/attachments` | Returns attachments on a page |
| Get blog post attachments | `GET /wiki/api/v2/blogposts/{id}/attachments` | Returns attachments on a blog post |

---

## 9. Comments

**Base path:** `/wiki/api/v2/` (inline and footer comments)  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-comment/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get page footer comments | `GET /wiki/api/v2/pages/{id}/footer-comments` | Returns footer comments on a page |
| Get page inline comments | `GET /wiki/api/v2/pages/{id}/inline-comments` | Returns inline comments on a page |
| Get blog post footer comments | `GET /wiki/api/v2/blogposts/{id}/footer-comments` | Returns footer comments on a blog post |
| Create footer comment | `POST /wiki/api/v2/footer-comments` | Create a footer comment |
| Create inline comment | `POST /wiki/api/v2/inline-comments` | Create an inline comment |
| Update footer comment | `PUT /wiki/api/v2/footer-comments/{id}` | Update a footer comment |
| Update inline comment | `PUT /wiki/api/v2/inline-comments/{id}` | Update an inline comment |
| Delete footer comment | `DELETE /wiki/api/v2/footer-comments/{id}` | Delete a footer comment |
| Delete inline comment | `DELETE /wiki/api/v2/inline-comments/{id}` | Delete an inline comment |

---

## 10. Labels

**Base path:** `/wiki/api/v2/` (labels on pages, blog posts, attachments)  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-label/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get page labels | `GET /wiki/api/v2/pages/{id}/labels` | Returns labels on a page |
| Add page labels | `POST /wiki/api/v2/pages/{id}/labels` | Add labels to a page |
| Delete page label | `DELETE /wiki/api/v2/pages/{id}/labels/{label}` | Remove a label from a page |
| Get blog post labels | `GET /wiki/api/v2/blogposts/{id}/labels` | Returns labels on a blog post |
| Add blog post labels | `POST /wiki/api/v2/blogposts/{id}/labels` | Add labels to a blog post |

---

## 11. Space Permissions

**Base path:** `/wiki/api/v2/spaces/{id}/permissions`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space-permissions/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get space permissions | `GET /wiki/api/v2/spaces/{id}/permissions` | Returns permissions for a space |
| Add space permission | `POST /wiki/api/v2/spaces/{id}/permissions` | Grant a permission |
| Delete space permission | `DELETE /wiki/api/v2/spaces/{id}/permissions/{permissionId}` | Revoke a permission |

---

## 12. Tasks

**Base path:** `/wiki/api/v2/tasks`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-task/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| List tasks | `GET /wiki/api/v2/tasks` | Returns tasks; filter by `space-id`, `page-id`, `assignee-id`, `status` |
| Get task | `GET /wiki/api/v2/tasks/{id}` | Returns a single task |
| Update task | `PUT /wiki/api/v2/tasks/{id}` | Update task status or assignee |

---

## 13. Whiteboards (Cloud Only)

**Base path:** `/wiki/api/v2/whiteboards`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-whiteboard/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Create whiteboard | `POST /wiki/api/v2/whiteboards` | Create a new whiteboard |
| Get whiteboard | `GET /wiki/api/v2/whiteboards/{id}` | Returns a whiteboard |
| Delete whiteboard | `DELETE /wiki/api/v2/whiteboards/{id}` | Delete a whiteboard |

---

## 14. Content Properties

**Base path:** `/wiki/api/v2/pages/{id}/properties`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-content-properties/>

| Operation | Method + Path | Description |
|-----------|--------------|-------------|
| Get page properties | `GET /wiki/api/v2/pages/{id}/properties` | Returns all properties on a page |
| Get page property | `GET /wiki/api/v2/pages/{id}/properties/{key}` | Returns a single property |
| Create page property | `POST /wiki/api/v2/pages/{id}/properties` | Create a key-value property |
| Update page property | `PUT /wiki/api/v2/pages/{id}/properties/{key}` | Update a property value |
| Delete page property | `DELETE /wiki/api/v2/pages/{id}/properties/{key}` | Delete a property |

---

## 15. Using v2 via Raw Session

Since `atlassian-python-api`'s legacy `Confluence` class does not wrap v2 endpoints, use the `_session` attribute directly:

```python
from atlassian import Confluence
from app import config

confluence = Confluence(
    url=config.JIRA_URL,
    username=config.JIRA_EMAIL,
    password=config.JIRA_API_TOKEN,
)

# GET example — list pages in a space
response = confluence._session.get(
    f"{config.JIRA_URL}/wiki/api/v2/pages",
    params={"space-id": "98304", "limit": 50},
)
response.raise_for_status()
data = response.json()
pages = data.get("results") or []

# POST example — create a page
response = confluence._session.post(
    f"{config.JIRA_URL}/wiki/api/v2/pages",
    json={
        "spaceId": "98304",
        "status": "current",
        "title": "New Report",
        "body": {"representation": "storage", "value": "<p>Content</p>"},
    },
)
response.raise_for_status()
created_page = response.json()
```

The session already carries `Authorization: Basic ...` from the `Confluence` constructor.
