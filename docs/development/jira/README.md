# Jira API Documentation

This folder contains self-contained reference documentation for every Jira API surface used by — or available for extension of — this project.

## Project Overview

**AI Adoption Metrics Report** is a Python 3.12+ tool that reads sprint and issue data from Jira Cloud and generates HTML + Markdown velocity/cycle-time reports. All Jira communication is handled by `app/jira_client.py` via the `atlassian-python-api` library.

---

## API Versions Used in This Project

| API | Version | Base Path | Used For |
|-----|---------|-----------|----------|
| Jira Platform REST API | **v2** | `/rest/api/2/` | Fetch saved filter metadata (`GET /rest/api/2/filter/{id}`) |
| Jira Platform REST API | **v3** | `/rest/api/3/` | Validate credentials (`GET /rest/api/3/myself`) |
| Jira Software Agile REST API | **1.0** | `/rest/agile/1.0/` | Boards, sprints, sprint issues (via `atlassian-python-api`) |

> **Why both v2 and v3?**  
> `atlassian-python-api` defaults to v2 for its internal calls. The `server.py` connection test explicitly calls v3 (`/myself`) because v3 is the current recommended version for new integrations. Both versions expose the same operations; v3 adds [Atlassian Document Format (ADF)](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/) support for rich text fields.

---

## Documentation Index

| File | Contents |
|------|----------|
| [authentication.md](authentication.md) | API token creation, Basic auth header construction, credential flow through the codebase |
| [api-v2.md](api-v2.md) | Jira Platform REST API v2 — endpoints used by this project, request/response shapes, pagination, error codes |
| [api-v3.md](api-v3.md) | Jira Platform REST API v3 — `/myself` endpoint, differences from v2, ADF |
| [agile-api.md](agile-api.md) | Jira Software Agile REST API 1.0 — boards, sprints, sprint issues, changelogs |
| [atlassian-python-api.md](atlassian-python-api.md) | `atlassian-python-api` library wrapper — every method called in `jira_client.py` with signatures and underlying REST endpoints |
| [crud-operations.md](crud-operations.md) | Full CRUD + admin operation catalogue for all Jira entities (boards, sprints, issues, filters, users, projects, permissions) |
| [extension-guide.md](extension-guide.md) | Step-by-step guide for adding new Jira API calls to this project |

---

## Official Atlassian Sources

- Jira Platform REST API v2: <https://developer.atlassian.com/cloud/jira/platform/rest/v2/intro/>
- Jira Platform REST API v3: <https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/>
- Jira Software Agile REST API 1.0: <https://developer.atlassian.com/cloud/jira/software/rest/intro/>
- Basic auth for REST APIs: <https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/>
- atlassian-python-api Jira module: <https://atlassian-python-api.readthedocs.io/jira.html>
- OAuth 2.0 (3LO) apps: <https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/>
- API token management: <https://confluence.atlassian.com/x/Vo71Nw>

---

## Key Project Files

| File | Role |
|------|------|
| `app/jira_client.py` | All Jira API calls; wraps `atlassian-python-api` |
| `app/config.py` | Loads `JIRA_*` env vars from `.env` |
| `main.py` | Orchestration; raw `GET /rest/api/2/filter/{id}` |
| `server.py` | Dev server; `POST /api/test-connection` → `GET /rest/api/3/myself` |
| `requirements.txt` | `atlassian-python-api>=3.41.0` |
| `.env.example` | Template for all required and optional config vars |
