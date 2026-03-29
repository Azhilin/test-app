# Confluence CRUD & Admin Operations Catalogue

This document catalogues Create, Read, Update, and Delete operations for every major Confluence entity, along with admin operations. Each entry shows the HTTP method + path, the `atlassian-python-api` equivalent where one exists, required permissions, and implementation status.

**Legend:**
- ✅ **Implemented** — already used in this project
- 🔲 **Available** — not yet used; ready to add via [extension-guide.md](extension-guide.md)

---

## 1. Spaces

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/space`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-space/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List all spaces | `GET /wiki/rest/api/space` | `confluence.get_all_spaces(start, limit, expand)` | Read space | 🔲 |
| Get space | `GET /wiki/rest/api/space/{key}` | `confluence.get_space(space_key, expand)` | Read space | 🔲 |
| Create space | `POST /wiki/rest/api/space` | *(use `_session.post`)* | Create space (admin) | 🔲 |
| Update space | `PUT /wiki/rest/api/space/{key}` | *(use `_session.put`)* | Administer space | 🔲 |
| Delete space | `DELETE /wiki/rest/api/space/{key}` | *(use `_session.delete`)* | Administer space | 🔲 |
| Archive space | `PUT /wiki/rest/api/space/{key}/state` | `confluence.archive_space(space_key)` | Administer space | 🔲 |
| Get space content | `GET /wiki/rest/api/space/{key}/content` | `confluence.get_space_content(space_key, ...)` | Read space | 🔲 |
| Get space export URL | `GET /wiki/rest/api/space/{key}/export` | `confluence.get_space_export(space_key, export_type)` | Read space | 🔲 |
| Get trashed content | `GET /wiki/rest/api/space/{key}/content?status=trashed` | `confluence.get_trashed_contents_by_space(space_key)` | Administer space | 🔲 |
| Purge trash | *(bulk delete)* | `confluence.remove_trashed_contents_by_space(space_key)` | Administer space | 🔲 |

**Create space request body:**

```json
{
  "key": "TEAM",
  "name": "Team Space",
  "description": {
    "plain": {
      "value": "Documentation for the AI Adoption team.",
      "representation": "plain"
    }
  }
}
```

---

## 2. Pages

**API:** Confluence REST API v1 (library) / v2 (raw)  
**Base path:** `/wiki/rest/api/content` (v1), `/wiki/api/v2/pages` (v2)  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List pages in space | `GET /wiki/rest/api/content?spaceKey={key}&type=page` | `confluence.get_all_pages_from_space(space, ...)` | Read space | 🔲 |
| Get page by ID | `GET /wiki/rest/api/content/{id}` | `confluence.get_page_by_id(page_id, expand)` | Read page | 🔲 |
| Get page by title | `GET /wiki/rest/api/content?title={title}&spaceKey={key}` | `confluence.get_page_by_title(space, title)` | Read page | 🔲 |
| Check page exists | `GET /wiki/rest/api/content` | `confluence.page_exists(space, title)` | Read space | 🔲 |
| Get page ID | `GET /wiki/rest/api/content` | `confluence.get_page_id(space, title)` | Read space | 🔲 |
| Create page | `POST /wiki/rest/api/content` | `confluence.create_page(space, title, body, parent_id)` | Create page | 🔲 |
| Update page | `PUT /wiki/rest/api/content/{id}` | `confluence.update_page(page_id, title, body)` | Edit page | 🔲 |
| Create or update page | `GET` then `POST` or `PUT` | `confluence.update_or_create(parent_id, title, body)` | Create/Edit page | 🔲 |
| Append to page | `GET` then `PUT` | `confluence.append_page(page_id, title, append_body)` | Edit page | 🔲 |
| Move page | `PUT /wiki/rest/api/content/{id}/move/{position}/{targetId}` | `confluence.move_page(space_key, page_id, target_title)` | Edit page | 🔲 |
| Delete page (to trash) | `DELETE /wiki/rest/api/content/{id}` | `confluence.remove_page(page_id, recursive=False)` | Delete page | 🔲 |
| Delete page recursively | `DELETE /wiki/rest/api/content/{id}` | `confluence.remove_page(page_id, recursive=True)` | Delete page | 🔲 |
| Restore from trash | `DELETE /wiki/rest/api/content/{id}?status=trashed` | `confluence.remove_page_from_trash(page_id)` | Administer space | 🔲 |
| Delete draft | `DELETE /wiki/rest/api/content/{id}?status=draft` | `confluence.remove_page_as_draft(page_id)` | Edit page | 🔲 |
| Get page history | `GET /wiki/rest/api/content/{id}/history` | `confluence.history(page_id)` | Read page | 🔲 |
| Get page version | `GET /wiki/rest/api/content/{id}/version/{n}` | `confluence.get_content_history_by_version_number(id, n)` | Read page | 🔲 |
| Delete page version | `DELETE /wiki/rest/api/content/{id}/version/{n}` | `confluence.remove_content_history(page_id, version_number)` | Administer space | 🔲 |
| Get page ancestors | `GET /wiki/rest/api/content/{id}?expand=ancestors` | `confluence.get_page_ancestors(page_id)` | Read page | 🔲 |
| Get child pages | `GET /wiki/rest/api/content/{id}/child/page` | `confluence.get_page_child_by_type(page_id, type='page')` | Read page | 🔲 |
| Export page as PDF | `GET /wiki/rest/api/content/{id}/export/pdf` | `confluence.export_page(page_id)` | Read page | 🔲 |

**Create page request body:**

```json
{
  "type": "page",
  "title": "AI Adoption Report — Sprint 42",
  "space": { "key": "TEAM" },
  "ancestors": [{ "id": "123456" }],
  "body": {
    "storage": {
      "value": "<h1>Sprint 42</h1><p>Velocity: 45 points.</p>",
      "representation": "storage"
    }
  }
}
```

---

## 3. Blog Posts

**API:** Confluence REST API v1 (library) / v2 (raw)  
**Base path:** `/wiki/rest/api/content` (v1, type=blogpost), `/wiki/api/v2/blogposts` (v2)  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List blog posts in space | `GET /wiki/rest/api/content?spaceKey={key}&type=blogpost` | `confluence.get_all_pages_from_space(space, content_type='blogpost')` | Read space | 🔲 |
| Get blog post by ID | `GET /wiki/rest/api/content/{id}` | `confluence.get_page_by_id(page_id, expand)` | Read blog post | 🔲 |
| Create blog post | `POST /wiki/rest/api/content` (type=blogpost) | `confluence.create_page(space, title, body, type='blogpost')` | Create blog post | 🔲 |
| Update blog post | `PUT /wiki/rest/api/content/{id}` | `confluence.update_page(page_id, title, body, type='blogpost')` | Edit blog post | 🔲 |
| Delete blog post | `DELETE /wiki/rest/api/content/{id}` | `confluence.remove_page(page_id)` | Delete blog post | 🔲 |

**Create blog post request body:**

```json
{
  "type": "blogpost",
  "title": "AI Adoption Update — Q1 2026",
  "space": { "key": "TEAM" },
  "body": {
    "storage": {
      "value": "<p>This quarter we achieved 65% AI-assisted story completion.</p>",
      "representation": "storage"
    }
  }
}
```

---

## 4. Attachments

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/content/{id}/child/attachment`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content---attachments/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List attachments | `GET /wiki/rest/api/content/{id}/child/attachment` | `confluence.get_attachments_from_content(page_id, ...)` | Read page | 🔲 |
| Upload attachment (file) | `POST /wiki/rest/api/content/{id}/child/attachment` | `confluence.attach_file(filename, page_id=page_id)` | Create attachment | 🔲 |
| Upload attachment (memory) | `POST /wiki/rest/api/content/{id}/child/attachment` | `confluence.attach_content(content, name, page_id=page_id)` | Create attachment | 🔲 |
| Download attachments | *(GET + write to disk)* | `confluence.download_attachments_from_page(page_id, path)` | Read page | 🔲 |
| Delete attachment | `DELETE /wiki/rest/api/content/{attachmentId}` | `confluence.delete_attachment(page_id, filename)` | Delete attachment | 🔲 |
| Delete attachment version | `DELETE /wiki/rest/api/content/{id}/version/{n}` | `confluence.delete_attachment_by_id(attachment_id, version)` | Delete attachment | 🔲 |
| Get attachment history | `GET /wiki/rest/api/content/{id}/history` | `confluence.get_attachment_history(attachment_id)` | Read page | 🔲 |

---

## 5. Comments

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/content` (type=comment)  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content---children-and-descendants/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List page comments | `GET /wiki/rest/api/content/{id}/child/comment` | `confluence.get_page_child_by_type(page_id, type='comment')` | Read page | 🔲 |
| Add footer comment | `POST /wiki/rest/api/content` (type=comment) | `confluence.add_comment(page_id, text)` | Add comment | 🔲 |
| Update comment | `PUT /wiki/rest/api/content/{commentId}` | *(use `_session.put`)* | Edit comment | 🔲 |
| Delete comment | `DELETE /wiki/rest/api/content/{commentId}` | `confluence.remove_content(content_id)` | Delete comment | 🔲 |

**Add comment request body (raw):**

```json
{
  "type": "comment",
  "container": { "id": "123456", "type": "page" },
  "body": {
    "storage": {
      "value": "<p>Auto-generated by AI Adoption Metrics tool.</p>",
      "representation": "storage"
    }
  }
}
```

---

## 6. Labels

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/content/{id}/label`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content-labels/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get labels | `GET /wiki/rest/api/content/{id}/label` | `confluence.get_page_labels(page_id, prefix, start, limit)` | Read page | 🔲 |
| Add label | `POST /wiki/rest/api/content/{id}/label` | `confluence.set_page_label(page_id, label)` | Edit page | 🔲 |
| Remove label | `DELETE /wiki/rest/api/content/{id}/label/{label}` | `confluence.remove_page_label(page_id, label)` | Edit page | 🔲 |
| Search by label | `GET /wiki/rest/api/content/search?cql=label=...` | `confluence.get_all_pages_by_label(label)` | Read space | 🔲 |

---

## 7. Content Restrictions

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/content/{id}/restriction`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content-restrictions/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get restrictions | `GET /wiki/rest/api/content/{id}/restriction` | `confluence.get_all_restrictions_for_content(content_id)` | Read page | 🔲 |
| Add restrictions | `POST /wiki/rest/api/content/{id}/restriction` | *(use `_session.post`)* | Administer page | 🔲 |
| Update restrictions | `PUT /wiki/rest/api/content/{id}/restriction` | *(use `_session.put`)* | Administer page | 🔲 |
| Delete restriction | `DELETE /wiki/rest/api/content/{id}/restriction/byOperation/{op}` | *(use `_session.delete`)* | Administer page | 🔲 |

---

## 8. Content Properties

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/content/{id}/property`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get all properties | `GET /wiki/rest/api/content/{id}/property` | `confluence.get_page_properties(page_id)` | Read page | 🔲 |
| Get property | `GET /wiki/rest/api/content/{id}/property/{key}` | `confluence.get_page_property(page_id, key)` | Read page | 🔲 |
| Set property | `POST /wiki/rest/api/content/{id}/property` | `confluence.set_page_property(page_id, data)` | Edit page | 🔲 |
| Delete property | `DELETE /wiki/rest/api/content/{id}/property/{key}` | `confluence.delete_page_property(page_id, key)` | Edit page | 🔲 |

---

## 9. Users and Groups (Admin)

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/user`, `/wiki/rest/api/group`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-users/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get current user | `GET /wiki/rest/api/user/current` | `confluence.get_user_details_by_username(email)` | Authenticated | 🔲 |
| Get user by account ID | `GET /wiki/rest/api/user?accountId={id}` | *(use `_session.get`)* | Browse users | 🔲 |
| Get user by username | `GET /wiki/rest/api/user?username={name}` | `confluence.get_user_details_by_username(username)` | Browse users | 🔲 |
| Get user by key | `GET /wiki/rest/api/user?key={key}` | `confluence.get_user_details_by_userkey(userkey)` | Browse users | 🔲 |
| List all groups | `GET /wiki/rest/api/group` | `confluence.get_all_groups(start, limit)` | Browse users | 🔲 |
| Get group members | `GET /wiki/rest/api/group/{name}/member` | *(use `_session.get`)* | Browse users | 🔲 |
| Add user to group | `POST /wiki/rest/api/group/{name}/member` | `confluence.add_user_to_group(username, group_name)` | Administer Confluence | 🔲 |
| Remove user from group | `DELETE /wiki/rest/api/group/{name}/member?accountId={id}` | `confluence.remove_user_from_group(username, group_name)` | Administer Confluence | 🔲 |
| Change user password | `PUT /wiki/rest/api/user/password` | `confluence.change_user_password(username, password)` | Administer Confluence | 🔲 |

---

## 10. Space Permissions (Admin)

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/space/{key}/permission`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-space-permissions/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get all space permissions | JSON-RPC | `confluence.get_all_space_permissions(space_key)` | Administer space | 🔲 |
| Grant permission to user | `POST /wiki/rest/api/space/{key}/permission` | `confluence.set_permissions_to_user_for_space(space_key, user_key, ops)` | Administer space | 🔲 |
| Revoke permission from user | `DELETE /wiki/rest/api/space/{key}/permission/{id}` | `confluence.remove_permissions_from_user_for_space(space_key, user_key)` | Administer space | 🔲 |
| Grant permission to group | `POST /wiki/rest/api/space/{key}/permission` | `confluence.set_permissions_to_group_for_space(space_key, group, ops)` | Administer space | 🔲 |
| Revoke permission from group | `DELETE /wiki/rest/api/space/{key}/permission/{id}` | `confluence.remove_permissions_from_group_for_space(space_key, group)` | Administer space | 🔲 |
| Grant anonymous permissions | `POST /wiki/rest/api/space/{key}/permission/anonymous` | `confluence.set_permissions_to_anonymous_for_space(space_key, ops)` | Administer space | 🔲 |
| Revoke anonymous permissions | `DELETE /wiki/rest/api/space/{key}/permission/anonymous` | `confluence.remove_permissions_granted_to_anonymous_for_space(space_key)` | Administer space | 🔲 |

Supported `operationKey` + `targetType` pairs for permissions:

| operationKey | targetType |
|-------------|------------|
| `read` | `space` |
| `administer` | `space` |
| `export` | `space` |
| `restrict` | `space` |
| `create` | `page`, `blogpost`, `comment`, `attachment` |
| `delete` | `page`, `blogpost`, `comment`, `attachment` |

---

## 11. Search (CQL)

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/search`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Search content | `GET /wiki/rest/api/search?cql=...` | `confluence.cql(cql, start, limit, expand)` | Read space | 🔲 |
| Search users | `GET /wiki/rest/api/search/user?cql=...` | *(use `_session.get`)* | Browse users | 🔲 |

**CQL examples:**

```
# Pages in a space modified recently
type = page AND space = "TEAM" AND lastModified >= now("-7d")

# Pages with a specific label
type = page AND label = "sprint-report"

# Blog posts by a specific user
type = blogpost AND creator = "user@example.com"

# Pages containing specific text
type = page AND text ~ "AI adoption"
```

---

## 12. Templates (Admin)

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/template`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-template/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List global templates | `GET /wiki/rest/api/template/page` | `confluence.get_content_templates()` | Read space | 🔲 |
| List space templates | `GET /wiki/rest/api/template/page?spaceKey={key}` | `confluence.get_content_templates(space)` | Read space | 🔲 |
| Get template | `GET /wiki/rest/api/template/{id}` | `confluence.get_content_template(template_id)` | Read space | 🔲 |
| Create template | `POST /wiki/rest/api/template` | `confluence.create_or_update_template(name, body, ...)` | Administer space | 🔲 |
| Update template | `PUT /wiki/rest/api/template` | `confluence.create_or_update_template(name, body, template_id=id, ...)` | Administer space | 🔲 |
| Delete template | `DELETE /wiki/rest/api/template/{id}` | `confluence.remove_template(template_id)` | Administer space | 🔲 |

---

## 13. Whiteboards (Cloud Only)

**API:** Confluence REST API v2  
**Base path:** `/wiki/api/v2/whiteboards`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-whiteboard/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Create whiteboard | `POST /wiki/api/v2/whiteboards` | `confluence.create_whiteboard(spaceId, title, parentId)` | Create in space | 🔲 |
| Get whiteboard | `GET /wiki/api/v2/whiteboards/{id}` | `confluence.get_whiteboard(whiteboard_id)` | Read space | 🔲 |
| Delete whiteboard | `DELETE /wiki/api/v2/whiteboards/{id}` | `confluence.delete_whiteboard(whiteboard_id)` | Delete in space | 🔲 |

---

## 14. Audit Log (Admin)

**API:** Confluence REST API v1  
**Base path:** `/wiki/rest/api/audit`  
**Official docs:** <https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-audit/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get audit records | `GET /wiki/rest/api/audit` | *(use `_session.get`)* | Administer Confluence | 🔲 |
| Export audit log | `GET /wiki/rest/api/audit/export` | *(use `_session.get`)* | Administer Confluence | 🔲 |
| Get audit retention | `GET /wiki/rest/api/audit/retention` | *(use `_session.get`)* | Administer Confluence | 🔲 |
| Set audit retention | `PUT /wiki/rest/api/audit/retention` | *(use `_session.put`)* | Administer Confluence | 🔲 |
