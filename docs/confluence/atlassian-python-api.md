# atlassian-python-api — Confluence Module

This document covers the `Confluence` class from `atlassian-python-api>=3.41.0` — the library already used in this project for Jira. All methods listed here are available without additional dependencies.

**Official docs:** <https://atlassian-python-api.readthedocs.io/confluence.html>  
**PyPI:** <https://pypi.org/project/atlassian-python-api/>  
**Source:** <https://github.com/atlassian-api/atlassian-python-api/blob/master/atlassian/confluence.py>

---

## 1. Constructor

```python
from atlassian import Confluence
from app import config

confluence = Confluence(
    url=config.JIRA_URL,        # e.g. https://your-domain.atlassian.net
    username=config.JIRA_EMAIL,
    password=config.JIRA_API_TOKEN,
)
```

The constructor accepts the same `url`, `username`, `password` parameters as the `Jira` class already used in `app/jira_client.py`. No additional setup is required.

**Optional parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `cloud` | `bool` | Set `True` for Confluence Cloud (default behaviour with Basic auth) |
| `timeout` | `int` | Request timeout in seconds |
| `verify_ssl` | `bool` | SSL certificate verification (default `True`) |
| `session` | `requests.Session` | Inject a custom session |

---

## 2. Page Methods

All methods map to Confluence REST API v1 (`/wiki/rest/api/`).

### 2.1 Reading Pages

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `page_exists` | `(space, title, type=None)` | `GET /wiki/rest/api/content` | Check if a page exists by title |
| `get_page_id` | `(space, title)` | `GET /wiki/rest/api/content` | Get page ID from space + title |
| `get_page_by_title` | `(space, title, start=None, limit=None)` | `GET /wiki/rest/api/content` | Get page object by title |
| `get_page_by_id` | `(page_id, expand=None, status=None, version=None)` | `GET /wiki/rest/api/content/{id}` | Get full page by ID |
| `get_page_space` | `(page_id)` | `GET /wiki/rest/api/content/{id}` | Get space key for a page |
| `get_page_ancestors` | `(page_id)` | `GET /wiki/rest/api/content/{id}?expand=ancestors` | Get ancestor pages |
| `get_page_child_by_type` | `(page_id, type='page', start=None, limit=None, expand=None)` | `GET /wiki/rest/api/content/{id}/child/{type}` | Get child content by type |
| `get_all_pages_from_space` | `(space, start=0, limit=100, status=None, expand=None, content_type='page')` | `GET /wiki/rest/api/content` | List all pages in a space |
| `get_all_pages_from_space_as_generator` | `(space, start=0, limit=100, ...)` | `GET /wiki/rest/api/content` | Generator version of above |
| `get_all_pages_by_label` | `(label, start=0, limit=50, expand=None)` | `GET /wiki/rest/api/content/search` | Get pages with a specific label |
| `get_draft_page_by_id` | `(page_id, status='draft')` | `GET /wiki/rest/api/content/{id}?status=draft` | Get a draft page |
| `get_all_draft_pages_from_space` | `(space, start=0, limit=500, status='draft')` | `GET /wiki/rest/api/content` | List draft pages in a space |
| `get_all_pages_from_space_trash` | `(space, start=0, limit=500, status='trashed', content_type='page')` | `GET /wiki/rest/api/content` | List trashed pages |
| `history` | `(page_id)` | `GET /wiki/rest/api/content/{id}/history` | Get page version history |
| `get_content_history_by_version_number` | `(content_id, version_number)` | `GET /wiki/rest/api/content/{id}/version/{n}` | Get content at a specific version |

**Usage examples:**

```python
# Check if a page exists
exists = confluence.page_exists("TEAM", "Sprint Velocity Report")

# Get page ID
page_id = confluence.get_page_id("TEAM", "Sprint Velocity Report")

# Get full page with body
page = confluence.get_page_by_id(page_id, expand="body.storage,version,space")
body = page["body"]["storage"]["value"]  # XHTML content

# List all pages in a space (paginated)
pages = confluence.get_all_pages_from_space("TEAM", start=0, limit=100)
```

### 2.2 Creating and Updating Pages

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `create_page` | `(space, title, body, parent_id=None, type='page', representation='storage', editor='v2', full_width=False)` | `POST /wiki/rest/api/content` | Create a new page |
| `update_page` | `(page_id, title, body, parent_id=None, type='page', representation='storage', minor_edit=False, full_width=False)` | `PUT /wiki/rest/api/content/{id}` | Update an existing page |
| `update_or_create` | `(parent_id, title, body, representation='storage', full_width=False)` | `GET` then `POST` or `PUT` | Create or update by title |
| `append_page` | `(page_id, title, append_body, parent_id=None, type='page', representation='storage', minor_edit=False)` | `GET` then `PUT` | Append content to an existing page |
| `move_page` | `(space_key, page_id, target_title, position="append")` | `PUT /wiki/rest/api/content/{id}/move/{position}/{targetId}` | Move page under a different parent |

**Usage examples:**

```python
# Create a new page
new_page = confluence.create_page(
    space="TEAM",
    title="AI Adoption Report — Sprint 42",
    body="<p>Velocity: 45 points. AI-assisted: 60%.</p>",
    parent_id="123456",
)
page_id = new_page["id"]

# Update an existing page
confluence.update_page(
    page_id=page_id,
    title="AI Adoption Report — Sprint 42 (Updated)",
    body="<p>Updated content.</p>",
)

# Create or update by title (idempotent)
confluence.update_or_create(
    parent_id="123456",
    title="AI Adoption Report — Sprint 42",
    body="<p>Latest data.</p>",
)
```

### 2.3 Deleting Pages

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `remove_page` | `(page_id, status=None, recursive=False)` | `DELETE /wiki/rest/api/content/{id}` | Move to trash; `recursive=True` deletes children too |
| `remove_content` | `(content_id)` | `DELETE /wiki/rest/api/content/{id}` | Remove any content type |
| `remove_page_from_trash` | `(page_id)` | `DELETE /wiki/rest/api/content/{id}?status=trashed` | Permanently delete from trash |
| `remove_page_as_draft` | `(page_id)` | `DELETE /wiki/rest/api/content/{id}?status=draft` | Delete a draft page |
| `remove_content_history` | `(page_id, version_number)` | `DELETE /wiki/rest/api/content/{id}/version/{n}` | Remove a specific version |

---

## 3. Page Properties

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `get_page_properties` | `(page_id)` | `GET /wiki/rest/api/content/{id}/property` | Get all properties |
| `get_page_property` | `(page_id, page_property_key)` | `GET /wiki/rest/api/content/{id}/property/{key}` | Get a single property |
| `set_page_property` | `(page_id, data)` | `POST /wiki/rest/api/content/{id}/property` | Create or update a property |
| `delete_page_property` | `(page_id, page_property)` | `DELETE /wiki/rest/api/content/{id}/property/{key}` | Delete a property |

**Usage example:**

```python
# Store report metadata as a page property
confluence.set_page_property(page_id, {
    "key": "report-metadata",
    "value": {"generated_at": "2026-03-26T10:00:00Z", "sprint_count": 10},
})

# Read it back
prop = confluence.get_page_property(page_id, "report-metadata")
```

---

## 4. Attachments

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `attach_file` | `(filename, name=None, content_type=None, page_id=None, title=None, space=None, comment=None)` | `POST /wiki/rest/api/content/{id}/child/attachment` | Upload a file from disk |
| `attach_content` | `(content, name=None, content_type=None, page_id=None, title=None, space=None, comment=None)` | `POST /wiki/rest/api/content/{id}/child/attachment` | Upload in-memory content |
| `get_attachments_from_content` | `(page_id, start=0, limit=50, expand=None, filename=None, media_type=None)` | `GET /wiki/rest/api/content/{id}/child/attachment` | List attachments |
| `download_attachments_from_page` | `(page_id, path=None)` | `GET` + download | Download all attachments to disk |
| `delete_attachment` | `(page_id, filename, version=None)` | `DELETE /wiki/rest/api/content/{id}` | Delete attachment or specific version |
| `delete_attachment_by_id` | `(attachment_id, version)` | `DELETE /wiki/rest/api/content/{id}/version/{n}` | Delete attachment version by ID |
| `get_attachment_history` | `(attachment_id, limit=200, start=0)` | `GET /wiki/rest/api/content/{id}/history` | Get attachment version history |
| `has_unknown_attachment_error` | `(page_id)` | `GET /wiki/rest/api/content/{id}/child/attachment` | Check for broken attachments |

**Usage examples:**

```python
# Upload a generated HTML report
confluence.attach_file(
    filename="generated/reports/2026-03-26/report.html",
    name="sprint-report.html",
    content_type="text/html",
    page_id=page_id,
    comment="Auto-generated sprint report",
)

# Upload in-memory content (e.g. a Markdown string)
confluence.attach_content(
    content=report_markdown.encode("utf-8"),
    name="sprint-report.md",
    content_type="text/markdown",
    page_id=page_id,
)
```

---

## 5. Labels

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `get_page_labels` | `(page_id, prefix=None, start=None, limit=None)` | `GET /wiki/rest/api/content/{id}/label` | List labels on a page |
| `set_page_label` | `(page_id, label)` | `POST /wiki/rest/api/content/{id}/label` | Add a label |
| `remove_page_label` | `(page_id, label)` | `DELETE /wiki/rest/api/content/{id}/label/{label}` | Remove a label |

**Usage example:**

```python
confluence.set_page_label(page_id, "ai-adoption")
confluence.set_page_label(page_id, "sprint-report")
labels = confluence.get_page_labels(page_id)
```

---

## 6. Comments

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `add_comment` | `(page_id, text)` | `POST /wiki/rest/api/content` (type=comment) | Add a footer comment |
| `get_page_child_by_type` | `(page_id, type='comment', ...)` | `GET /wiki/rest/api/content/{id}/child/comment` | List page comments |

**Usage example:**

```python
confluence.add_comment(page_id, "Report auto-generated by AI Adoption Metrics tool.")
```

---

## 7. Spaces

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `get_all_spaces` | `(start=0, limit=500, expand=None)` | `GET /wiki/rest/api/space` | List all accessible spaces |
| `get_space` | `(space_key, expand='description.plain,homepage')` | `GET /wiki/rest/api/space/{key}` | Get a single space |
| `get_space_content` | `(space_key, depth="all", start=0, limit=500, content_type=None, expand="body.storage")` | `GET /wiki/rest/api/space/{key}/content` | List content in a space |
| `get_space_permissions` | `(space_key)` | JSON-RPC call | Get space permissions (legacy JSON-RPC) |
| `get_space_export` | `(space_key, export_type)` | `GET /wiki/rest/api/space/{key}/export` | Get export download URL |
| `archive_space` | `(space_key)` | `PUT /wiki/rest/api/space/{key}/state` | Archive a space |
| `get_trashed_contents_by_space` | `(space_key, cursor=None, expand=None, limit=100)` | `GET /wiki/rest/api/space/{key}/content?status=trashed` | List trashed content |
| `remove_trashed_contents_by_space` | `(space_key)` | `DELETE` (bulk) | Permanently delete all trash in a space |

**Usage example:**

```python
# Get all spaces
spaces = confluence.get_all_spaces(limit=50)
for space in spaces["results"]:
    print(space["key"], space["name"])

# Get a specific space with homepage
space = confluence.get_space("TEAM", expand="description.plain,homepage")
homepage_id = space["homepage"]["id"]
```

---

## 8. Space Permissions

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `get_all_space_permissions` | `(space_key)` | JSON-RPC | List all permissions in a space |
| `set_permissions_to_multiple_items_for_space` | `(space_key, user_key=None, group_name=None, operations=None)` | `POST /wiki/rest/api/space/{key}/permission` | Grant permissions to users/groups |
| `get_permissions_granted_to_anonymous_for_space` | `(space_key)` | `GET /wiki/rest/api/space/{key}/permission/anonymous` | Get anonymous permissions |
| `set_permissions_to_anonymous_for_space` | `(space_key, operations=None)` | `POST /wiki/rest/api/space/{key}/permission/anonymous` | Grant anonymous permissions |
| `remove_permissions_granted_to_anonymous_for_space` | `(space_key)` | `DELETE /wiki/rest/api/space/{key}/permission/anonymous` | Revoke anonymous permissions |
| `get_permissions_granted_to_group_for_space` | `(space_key, user_key)` | `GET /wiki/rest/api/space/{key}/permission/group/{name}` | Get group permissions |
| `set_permissions_to_group_for_space` | `(space_key, user_key, operations=None)` | `POST /wiki/rest/api/space/{key}/permission/group/{name}` | Grant group permissions |
| `remove_permissions_from_group_for_space` | `(space_key, group_name)` | `DELETE /wiki/rest/api/space/{key}/permission/group/{name}` | Revoke group permissions |
| `get_permissions_granted_to_user_for_space` | `(space_key, user_key)` | `GET /wiki/rest/api/space/{key}/permission/user` | Get user permissions |
| `set_permissions_to_user_for_space` | `(space_key, user_key, operations=None)` | `POST /wiki/rest/api/space/{key}/permission/user` | Grant user permissions |
| `remove_permissions_from_user_for_space` | `(space_key, user_key)` | `DELETE /wiki/rest/api/space/{key}/permission/user` | Revoke user permissions |
| `add_space_permissions` | `(space_key, user_key, group_name, operations)` | `POST /wiki/rest/api/space/{key}/permission` | Add permissions (bulk) |
| `remove_space_permissions` | `(space_key, user_key, group_name, permission)` | `DELETE /wiki/rest/api/space/{key}/permission/{id}` | Remove a permission |

---

## 9. Users and Groups

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `get_all_groups` | `(start=0, limit=1000)` | `GET /wiki/rest/api/group` | List all groups |
| `get_user_details_by_username` | `(username, expand=None)` | `GET /wiki/rest/api/user?username={name}` | Get user by username |
| `get_user_details_by_userkey` | `(userkey, expand=None)` | `GET /wiki/rest/api/user?key={key}` | Get user by user key |
| `add_user_to_group` | `(username, group_name)` | `POST /wiki/rest/api/group/{name}/member` | Add user to group |
| `remove_user_from_group` | `(username, group_name)` | `DELETE /wiki/rest/api/group/{name}/member` | Remove user from group |
| `change_user_password` | `(username, password)` | `PUT /wiki/rest/api/user/password` | Change a user's password |
| `change_my_password` | `(oldpass, newpass)` | `PUT /wiki/rest/api/user/password/current` | Change the calling user's password |

---

## 10. Search (CQL)

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `cql` | `(cql, start=0, limit=None, expand=None, include_archived_spaces=None, excerpt=None)` | `GET /wiki/rest/api/search` | Execute a CQL search |

**Usage example:**

```python
# Find all pages with a specific label in a space
results = confluence.cql(
    'type = page AND space = "TEAM" AND label = "sprint-report"',
    limit=50,
)
for item in results.get("results") or []:
    print(item["content"]["id"], item["title"])
```

---

## 11. Templates

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `get_content_templates` | `(space=None)` | `GET /wiki/rest/api/template/page` | List page templates (global or space) |
| `get_blueprint_templates` | `(space=None)` | `GET /wiki/rest/api/template/blueprint` | List blueprint templates |
| `get_content_template` | `(template_id)` | `GET /wiki/rest/api/template/{id}` | Get a single template |
| `create_or_update_template` | `(name, body, template_type, template_id=None, description=None, labels=None, space=None)` | `POST` or `PUT /wiki/rest/api/template` | Create or update a template |
| `remove_template` | `(template_id)` | `DELETE /wiki/rest/api/template/{id}` | Delete a template |

---

## 12. Whiteboards (Cloud Only)

| Method | Signature | REST Endpoint | Description |
|--------|-----------|---------------|-------------|
| `create_whiteboard` | `(spaceId, title=None, parentId=None)` | `POST /wiki/api/v2/whiteboards` | Create a whiteboard |
| `get_whiteboard` | `(whiteboard_id)` | `GET /wiki/api/v2/whiteboards/{id}` | Get a whiteboard |
| `delete_whiteboard` | `(whiteboard_id)` | `DELETE /wiki/api/v2/whiteboards/{id}` | Delete a whiteboard |

---

## 13. Utility Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `convert_wiki_to_storage` | `(wiki)` | Convert wiki markup to Confluence storage format (XHTML) |
| `is_page_content_is_already_updated` | `(page_id, body)` | Compare body with current; returns `True` if already up to date |
| `get_tables_from_page` | `(page_id)` | Extract HTML tables from a page |
| `scrap_regex_from_page` | `(page_id, regex)` | Find regex matches in page content |
| `export_page` | `(page_id)` | Export page as PDF |
| `clean_all_caches` | `()` | Clear all Confluence caches (admin only) |
| `set_inline_tasks_checkbox` | `(page_id, task_id, status)` | Update an inline task checkbox |

---

## 14. Accessing Raw Session

For endpoints not covered by the library, use the underlying `requests.Session`:

```python
# The session has Authorization: Basic ... already set
response = confluence._session.get(
    f"{config.JIRA_URL}/wiki/api/v2/pages",
    params={"space-id": "98304", "limit": 50},
)
response.raise_for_status()
data = response.json()
```

See [rest-v2.md](rest-v2.md) for all v2 endpoints accessible this way.
