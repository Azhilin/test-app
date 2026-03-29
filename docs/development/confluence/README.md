# Confluence API Documentation

This folder contains self-contained reference documentation for every Confluence API surface used by — or available for extension of — this project.

## Project Overview

**AI Adoption Metrics Report** is a Python 3.12+ tool that reads sprint and issue data from Jira Cloud and generates HTML + Markdown velocity/cycle-time reports. The same Atlassian Cloud account and credentials used for Jira also provide access to Confluence Cloud. All Confluence communication is handled via the `atlassian-python-api` library's `Confluence` class, which mirrors the `Jira` class already used in `app/jira_client.py`.

---

## API Versions Used in This Project

| API | Version | Base Path | Used For |
|-----|---------|-----------|----------|
| Confluence REST API | **v1** (legacy) | `/wiki/rest/api/` | Primary surface for `atlassian-python-api` legacy `Confluence` class; all current library methods map here |
| Confluence REST API | **v2** (current) | `/wiki/api/v2/` | Newer endpoints (pages, blog posts, spaces, labels) with cursor-based pagination; use for raw calls not yet in the library |

> **Why both v1 and v2?**  
> `atlassian-python-api`'s legacy `Confluence` class (the one used in this project) maps to the **v1** REST surface at `/wiki/rest/api/`. The newer `ConfluenceCloud` class targets **v2** at `/wiki/api/v2/`. Since this project already uses the legacy `Confluence` class pattern (matching the `Jira` class), v1 is the primary surface. v2 is documented for raw `_session` calls where v1 lacks coverage (e.g. cursor-based pagination, classification levels, smart links).

---

## Documentation Index

| File | Contents |
|------|----------|
| [authentication.md](authentication.md) | Reuse of existing `JIRA_*` credentials for Confluence; Basic auth header construction; new optional env vars |
| [rest-v1.md](rest-v1.md) | Confluence REST API v1 — endpoint groups, request/response shapes, pagination, expansion, error codes |
| [rest-v2.md](rest-v2.md) | Confluence REST API v2 — endpoint groups, cursor-based pagination, differences from v1 |
| [atlassian-python-api.md](atlassian-python-api.md) | `atlassian-python-api` `Confluence` class — every method grouped by entity with signatures and underlying REST endpoints |
| [crud-operations.md](crud-operations.md) | Full CRUD + admin operation catalogue for all Confluence entities (spaces, pages, blog posts, attachments, comments, labels, users, groups, permissions) |
| [extension-guide.md](extension-guide.md) | Step-by-step guide for adding new Confluence API calls to this project |

---

## Official Atlassian Sources

- Confluence REST API v1: <https://developer.atlassian.com/cloud/confluence/rest/v1/intro/>
- Confluence REST API v2: <https://developer.atlassian.com/cloud/confluence/rest/v2/intro/>
- Basic auth for Confluence REST APIs: <https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/>
- Confluence Cloud scopes: <https://developer.atlassian.com/cloud/confluence/scopes/>
- Advanced searching using CQL: <https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/>
- Content properties in the REST API: <https://developer.atlassian.com/cloud/confluence/content-properties/>
- Webhooks: <https://developer.atlassian.com/cloud/confluence/modules/webhook/>
- Security overview: <https://developer.atlassian.com/cloud/confluence/security-overview/>
- atlassian-python-api Confluence module: <https://atlassian-python-api.readthedocs.io/confluence.html>
- API token management: <https://id.atlassian.com/manage-profile/security/api-tokens>

---

## Key Project Files

| File | Role |
|------|------|
| `app/config.py` | Loads `JIRA_*` env vars from `.env`; Confluence client reuses `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` |
| `app/jira_client.py` | Pattern reference for building `app/confluence_client.py` |
| `requirements.txt` | `atlassian-python-api>=3.41.0` — includes `Confluence` class |
| `.env.example` | Template for all required and optional config vars |
