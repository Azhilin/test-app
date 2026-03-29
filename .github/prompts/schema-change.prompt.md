---
name: schema-change
description: Make a Jira schema or config change while keeping schema JSON, Python helpers, and tests aligned.
agent: jira-schema-curator
argument-hint: Describe the field, status mapping, or config behavior you want to change.
---

Apply a Jira schema or configuration change in this repository.

Requested change: ${input:change:Describe the schema, field, or config change}
Known files: ${input:files:Optional specific files such as app/core/schema.py or config/jira_schema.json}
Constraints: ${input:constraints:Optional constraints or compatibility requirements}

Requirements:

- Keep `config/jira_schema.json` and Python schema helpers aligned.
- Prefer schema-driven mappings instead of hard-coded values.
- Update only the smallest affected set of tests.
- Call out any new Jira-specific assumptions.
