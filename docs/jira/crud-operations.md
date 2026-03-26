# Jira CRUD & Admin Operations Catalogue

This document catalogues Create, Read, Update, and Delete operations for every major Jira entity, along with admin operations. Each entry shows the HTTP method + path, required permissions, and the `atlassian-python-api` equivalent where one exists.

**Legend:**
- ✅ **Implemented** — already used in this project
- 🔲 **Available** — not yet used; ready to add via [extension-guide.md](extension-guide.md)

---

## 1. Boards

**API:** Jira Software Agile REST API 1.0  
**Base path:** `/rest/agile/1.0/board`  
**Official docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-board/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List all boards | `GET /rest/agile/1.0/board` | `jira.get_all_agile_boards(start, limit)` | Browse Projects | ✅ |
| Get board by ID | `GET /rest/agile/1.0/board/{boardId}` | `jira.get_agile_board(board_id)` | Browse Projects | 🔲 |
| Create board | `POST /rest/agile/1.0/board` | `jira.create_agile_board(name, type, filter_id)` | Administer Projects | 🔲 |
| Delete board | `DELETE /rest/agile/1.0/board/{boardId}` | `jira.delete_agile_board(board_id)` | Administer Projects | 🔲 |
| Get board configuration | `GET /rest/agile/1.0/board/{boardId}/configuration` | `jira.get_agile_board_configuration(board_id)` | Browse Projects | 🔲 |
| Get board backlog | `GET /rest/agile/1.0/board/{boardId}/backlog` | `jira.get_issues_for_board(board_id, ...)` | Browse Projects | 🔲 |

**Create board request body:**

```json
{
  "name": "Team Alpha Scrum Board",
  "type": "scrum",
  "filterId": 10040,
  "location": {
    "type": "project",
    "projectKeyOrId": "ALPHA"
  }
}
```

---

## 2. Sprints

**API:** Jira Software Agile REST API 1.0  
**Base path:** `/rest/agile/1.0/sprint`  
**Official docs:** <https://developer.atlassian.com/cloud/jira/software/rest/api-group-sprint/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List sprints for board | `GET /rest/agile/1.0/board/{boardId}/sprint` | `jira.get_all_sprints_from_board(board_id, state, start, limit)` | Browse Projects | ✅ |
| Get sprint by ID | `GET /rest/agile/1.0/sprint/{sprintId}` | *(use `_session.get`)* | Browse Projects | 🔲 |
| Create sprint | `POST /rest/agile/1.0/sprint` | `jira.create_sprint(name, board_id, start, end, goal)` | Administer Projects | 🔲 |
| Update sprint | `POST /rest/agile/1.0/sprint/{sprintId}` | `jira.rename_sprint(sprint_id, name, start, end)` | Administer Projects | 🔲 |
| Delete sprint | `DELETE /rest/agile/1.0/sprint/{sprintId}` | *(use `_session.delete`)* | Administer Projects | 🔲 |
| Move issues to sprint | `POST /rest/agile/1.0/sprint/{sprintId}/issue` | `jira.add_issues_to_sprint(sprint_id, issue_keys)` | Edit Issues | 🔲 |

**Create sprint request body:**

```json
{
  "name": "Sprint 15",
  "originBoardId": 84,
  "startDate": "2026-04-01T09:00:00.000Z",
  "endDate": "2026-04-14T18:00:00.000Z",
  "goal": "Complete authentication module"
}
```

**Update sprint request body (partial update supported):**

```json
{
  "name": "Sprint 15 (revised)",
  "state": "active",
  "startDate": "2026-04-01T09:00:00.000Z",
  "endDate": "2026-04-14T18:00:00.000Z"
}
```

---

## 3. Issues

**API:** Jira Platform REST API v2  
**Base path:** `/rest/api/2/issue`  
**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get issues for sprint | `GET /rest/agile/1.0/board/{boardId}/sprint/{sprintId}/issue` | `jira.get_all_issues_for_sprint_in_board(board_id, sprint_id, jql, start, limit)` | Browse Projects | ✅ |
| Get issue with changelog | `GET /rest/api/2/issue/{key}?expand=changelog` | `jira.get_issue(key, expand="changelog")` | Browse Projects | ✅ |
| Get issue | `GET /rest/api/2/issue/{key}` | `jira.issue(key)` | Browse Projects | 🔲 |
| Create issue | `POST /rest/api/2/issue` | `jira.issue_create(fields)` | Create Issues | 🔲 |
| Update issue | `PUT /rest/api/2/issue/{key}` | `jira.issue_update(key, fields)` | Edit Issues | 🔲 |
| Delete issue | `DELETE /rest/api/2/issue/{key}` | *(use `_session.delete`)* | Delete Issues | 🔲 |
| Transition issue | `POST /rest/api/2/issue/{key}/transitions` | `jira.set_issue_status(key, status_name)` | Transition Issues | 🔲 |
| Search issues (JQL) | `GET /rest/api/2/search?jql=...` | `jira.jql(query)` | Browse Projects | 🔲 |
| Assign issue | `PUT /rest/api/2/issue/{key}/assignee` | `jira.assign_issue(key, account_id)` | Assign Issues | 🔲 |
| Add comment | `POST /rest/api/2/issue/{key}/comment` | `jira.issue_add_comment(key, body)` | Add Comments | 🔲 |
| Add attachment | `POST /rest/api/2/issue/{key}/attachments` | `jira.add_attachment(key, filename)` | Create Attachments | 🔲 |
| Get changelog | `GET /rest/api/2/issue/{key}/changelog` | `jira.get_issue_changelog(key)` | Browse Projects | 🔲 |

**Create issue request body:**

```json
{
  "fields": {
    "project": { "key": "ALPHA" },
    "summary": "Implement OAuth login",
    "issuetype": { "name": "Story" },
    "description": "As a user, I want to log in with OAuth.",
    "priority": { "name": "High" },
    "assignee": { "accountId": "5b10a2844c20165700ede21g" },
    "customfield_10016": 5
  }
}
```

**Update issue request body (only changed fields needed):**

```json
{
  "fields": {
    "summary": "Updated summary",
    "priority": { "name": "Medium" }
  }
}
```

**Transition issue request body:**

```json
{
  "transition": { "id": "31" }
}
```

Get available transition IDs first: `GET /rest/api/2/issue/{key}/transitions`

---

## 4. Filters

**API:** Jira Platform REST API v2  
**Base path:** `/rest/api/2/filter`  
**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-filters/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get filter by ID | `GET /rest/api/2/filter/{id}` | `jira.get_filter(filter_id)` | View filter | ✅ |
| Get filter name (raw) | `GET /rest/api/2/filter/{id}` | `jira._session.get(url).json()` | View filter | ✅ |
| List my filters | `GET /rest/api/2/filter/my` | *(use `_session.get`)* | Authenticated | 🔲 |
| Search filters | `GET /rest/api/2/filter/search` | *(use `_session.get`)* | Authenticated | 🔲 |
| Create filter | `POST /rest/api/2/filter` | *(use `_session.post`)* | Create Shared Objects | 🔲 |
| Update filter | `PUT /rest/api/2/filter/{id}` | *(use `_session.put`)* | Edit filter | 🔲 |
| Delete filter | `DELETE /rest/api/2/filter/{id}` | *(use `_session.delete`)* | Edit filter | 🔲 |

**Create filter request body:**

```json
{
  "name": "Alpha Team Active Issues",
  "description": "All open issues for team Alpha",
  "jql": "project = ALPHA AND status != Done",
  "favourite": false
}
```

---

## 5. Users

**API:** Jira Platform REST API v2  
**Base path:** `/rest/api/2/user`  
**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-users/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get current user | `GET /rest/api/3/myself` | `jira.myself()` | Authenticated | ✅ (via `server.py`) |
| Get user by account ID | `GET /rest/api/2/user?accountId={id}` | `jira.user(account_id)` | Browse Users | 🔲 |
| Search users | `GET /rest/api/2/user/search?query=...` | `jira.user_find_by_user_string(query)` | Browse Users | 🔲 |
| Create user | `POST /rest/api/2/user` | *(use `_session.post`)* | Administer Jira | 🔲 |
| Update user | `PUT /rest/api/2/user?accountId={id}` | *(use `_session.put`)* | Administer Jira | 🔲 |
| Deactivate user | *(Jira Cloud: managed via Atlassian Admin)* | `jira.user_deactivate(username)` | Administer Jira | 🔲 |
| Get user groups | `GET /rest/api/2/user/groups?accountId={id}` | `jira.get_user_groups(account_id)` | Browse Users | 🔲 |

---

## 6. Projects

**API:** Jira Platform REST API v2  
**Base path:** `/rest/api/2/project`  
**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-projects/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| List all projects | `GET /rest/api/2/project` | `jira.get_all_projects()` | Browse Projects | 🔲 |
| Get project | `GET /rest/api/2/project/{key}` | `jira.project(key)` | Browse Projects | 🔲 |
| Create project | `POST /rest/api/2/project` | *(use `_session.post`)* | Administer Jira | 🔲 |
| Update project | `PUT /rest/api/2/project/{key}` | `jira.update_project(key, data)` | Administer Projects | 🔲 |
| Delete project | `DELETE /rest/api/2/project/{key}` | `jira.delete_project(key)` | Administer Jira | 🔲 |
| Archive project | `POST /rest/api/2/project/{key}/archive` | `jira.archive_project(key)` | Administer Jira | 🔲 |
| Get project components | `GET /rest/api/2/project/{key}/components` | `jira.get_project_components(key)` | Browse Projects | 🔲 |
| Get project versions | `GET /rest/api/2/project/{key}/versions` | `jira.get_project_versions(key)` | Browse Projects | 🔲 |

**Create project request body:**

```json
{
  "key": "ALPHA",
  "name": "Alpha Project",
  "projectTypeKey": "software",
  "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-scrum-template",
  "description": "AI Adoption tracking project",
  "leadAccountId": "5b10a2844c20165700ede21g",
  "assigneeType": "PROJECT_LEAD"
}
```

---

## 7. Permissions & Admin Operations

**API:** Jira Platform REST API v2  
**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-permissions/>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get my permissions | `GET /rest/api/2/mypermissions` | `jira.permissions(permissions)` | Authenticated | 🔲 |
| Get all permissions | `GET /rest/api/2/permissions` | `jira.get_all_permissions()` | Administer Jira | 🔲 |
| Get permission schemes | `GET /rest/api/2/permissionscheme` | *(use `_session.get`)* | Administer Jira | 🔲 |
| Get project permission scheme | `GET /rest/api/2/project/{key}/permissionscheme` | `jira.get_project_permission_scheme(key)` | Administer Projects | 🔲 |
| Get groups | `GET /rest/api/2/group/member` | `jira.get_all_users_from_group(group)` | Browse Users | 🔲 |
| Create group | `POST /rest/api/2/group` | `jira.create_group(name)` | Administer Jira | 🔲 |
| Delete group | `DELETE /rest/api/2/group?groupname={name}` | `jira.remove_group(name)` | Administer Jira | 🔲 |
| Add user to group | `POST /rest/api/2/group/user` | `jira.add_user_to_group(account_id, group_name)` | Administer Jira | 🔲 |
| Remove user from group | `DELETE /rest/api/2/group/user` | `jira.remove_user_from_group(account_id, group_name)` | Administer Jira | 🔲 |

---

## 8. Changelogs

**API:** Jira Platform REST API v2  
**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issues/#api-rest-api-2-issue-issueidorkey-changelog-get>

| Operation | Method + Path | Library Method | Permission | Status |
|-----------|--------------|----------------|------------|--------|
| Get changelog (via expand) | `GET /rest/api/2/issue/{key}?expand=changelog` | `jira.get_issue(key, expand="changelog")` | Browse Projects | ✅ |
| Get changelog (paginated) | `GET /rest/api/2/issue/{key}/changelog` | `jira.get_issue_changelog(key)` | Browse Projects | 🔲 |

The `expand=changelog` approach (used by this project) returns all changelog entries in the issue response. For issues with very long histories, use the paginated `/changelog` endpoint instead.

---

## 9. Fields & Custom Fields

| Operation | Method + Path | Library Method | Status |
|-----------|--------------|----------------|--------|
| List all fields | `GET /rest/api/2/field` | *(use `_session.get`)* | 🔲 |
| Get custom fields | `GET /rest/api/2/field` (filter custom) | `jira.get_custom_fields(search)` | 🔲 |
| Get custom field option | `GET /rest/api/2/customFieldOption/{id}` | `jira.get_custom_field_option(option_id)` | 🔲 |

Use `GET /rest/api/2/field` to discover the correct `customfield_XXXXX` ID for story points on your Jira instance if the default `customfield_10016` does not match.

---

## 10. Webhooks (Admin)

**Official docs:** <https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-webhooks/>

| Operation | Method + Path | Status |
|-----------|--------------|--------|
| List webhooks | `GET /rest/api/2/webhook` | 🔲 |
| Register webhook | `POST /rest/api/2/webhook` | 🔲 |
| Delete webhook | `DELETE /rest/api/2/webhook?webhookId={id}` | 🔲 |
| Extend webhook life | `PUT /rest/api/2/webhook/refresh` | 🔲 |

Webhooks allow Jira to push events (issue created, sprint started, etc.) to your server instead of polling. Useful if you want to trigger report generation automatically.
