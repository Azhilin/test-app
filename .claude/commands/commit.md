# /commit

Create a git commit following the project's commit message format.

## Format Rules (CLAUDE.md)

**Subject line:**
- Type + imperative summary: `<type>: <imperative>`
- Max 50 characters, no period
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

**Body (optional):**
- Only when changes span multiple unrelated areas
- Use 1–3 short bullets
- No paragraphs

## Examples

✓ **Single-area fix — no body needed:**
```
fix: handle missing story points field gracefully
```

✓ **Multi-area refactor — body required:**
```
refactor: extract schema detection into standalone module

- Move field ID lookup out of jira_client
- Add KNOWN_FIELD_SCHEMAS registry in schema.py
- Update metrics to accept schema-driven done_statuses
```

## Implementation

Before creating a commit:
1. Run `/test` to ensure all checks pass
2. Review staged changes: `git diff --cached`
3. Craft message following rules above
4. Commit: `git commit -m "..."`

Claude Code will:
- Stage only specified files (avoid `git add .`)
- Validate format before committing
- Add co-author trailer automatically

## Related

- `CLAUDE.md` — Commit message format rules and examples
- `docs/development/pipeline.md` — CI expectations for commit content
