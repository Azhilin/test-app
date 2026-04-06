# Claude Code Improvements — April 6, 2026

This document summarizes all improvements made to the `.claude` folder to optimize Claude Code's workflow for this project.

---

## 1. Documentation Fixes

### Fixed Incorrect File Paths
- **CLAUDE.md:232** — Changed `app/server.py` → `app/server/_base.py` in extension pattern
- **docs/development/architecture.md:517** — Same fix for consistency

**Why:** The server module is a package, not a single file. This prevents Claude from creating files in the wrong location on future server extension tasks.

---

## 2. Memory System

Created two new memory entries in `~/.claude/projects/.../memory/`:

### `feedback_test_runner.md`
Canonical test runner invocation: always use `python tests/runners/run_all_checks.py`, never direct venv paths or pytest.

### `project_server_layout.md`
Server module structure: `app/server/` is a package with `_base.py` (routing) and handler files by category.

**Impact:** Future sessions will not need to rediscover test runner paths or server structure.

---

## 3. Settings Consolidation

### Project Settings (`.claude/settings.local.json`)
- **Before:** 61 lines of specific Bash command patterns (fragmented, error-prone)
- **After:** 30 lines of broad but safe patterns (e.g., `.venv/Scripts/pytest:*`, `.venv/Scripts/python:*`)
- **Added:** `"autoCompact": true` for automatic context management

**Benefit:** Reduces noise, prevents "permission denied" on minor command variations, auto-compacts context.

---

## 4. Slash Commands

Five new user-invocable commands in `.claude/commands/`:

| Command | Purpose | Usage |
|---------|---------|-------|
| **`/test`** | Run full CI suite (lint + type + security + tests) | `/test --all` |
| **`/lint`** | Format + type check + security scan only | `/lint --fix` |
| **`/commit`** | Document commit message format rules | Reference for format |
| **`/coverage`** | Regenerate test coverage report | `/coverage --dry-run` |
| **`/server`** | Start dev server | `/server 9000` |

**Benefit:** Discoverable, documented commands replace fragmented venv path memory.

---

## 5. Hooks (Safety & Automation)

### Post-Edit Lint Hook (`.claude/hooks/post_edit_lint.sh`)
Auto-runs `ruff format` on every Python file edited. Keeps code lint-clean without manual intervention.

### Pre-Bash Safety Hook (`.claude/hooks/pre_bash_safety.sh`)
Blocks destructive commands:
- `git push --force` (to main/master)
- `git reset --hard`
- `rm -rf`
- `git clean -f`

**Benefit:** Safety net that surfaces risky operations before execution rather than relying on Claude's judgment.

---

## 6. Optional: MCP Server Configuration

Created `.claude/mcp-servers-template.json` documenting how to set up Jira MCP server for direct board/sprint/issue queries.

**Note:** Requires Node.js + external MCP packages. Not auto-enabled; use as reference if needed.

---

## Immediate Impact

✓ **Correct file paths** — No more incorrect `app/server.py` references  
✓ **Faster decision-making** — Memory entries + documented commands  
✓ **Cleaner permissions** — Settings reduced from 61 to 30 lines  
✓ **Automatic safety** — Hooks catch dangerous operations  
✓ **Auto-formatting** — Every edit is lint-clean  

---

## Using the Improvements

### In This Session
```bash
/test --all              # Run everything
/lint --fix              # Auto-format
/server                  # Start dev server
/coverage                # Update coverage stats
```

### In Future Sessions
- Commands appear in autocomplete: type `/` to see options
- Memory auto-loads: test runner path and server layout always available
- Settings auto-apply: autoCompact prevents context truncation
- Hooks auto-run: lint hook runs after edits, safety hook blocks risky commands

---

## Summary Table

| Area | Improvement | Lines Changed | User Benefit |
|------|-------------|----------------|--------------|
| Docs | Fix file paths (CLAUDE.md + architecture.md) | 2 files, 1 line each | Prevents future mistakes |
| Memory | Add test runner + server layout entries | 2 new files | Future sessions remember canonical paths |
| Settings | Consolidate bash patterns + add autoCompact | 30 lines (was 61) | Cleaner, auto-context management |
| Commands | Add 5 slash commands with docs | 5 files | Discoverability + guidance |
| Hooks | Post-edit lint + pre-bash safety | 2 files | Automation + safety |
| Optional | MCP server template | 1 reference file | Future extensibility |

---

## Next Steps (Optional)

1. **Enable MCP servers** — Follow `.claude/mcp-servers-template.json` if Jira API queries become frequent
2. **Customize hooks** — Modify `.claude/hooks/pre_bash_safety.sh` to block/allow additional patterns
3. **Add more commands** — Create additional `.claude/commands/*.md` files as workflow evolves
4. **Monitor task tracker** — Use `TaskCreate` / `TaskUpdate` for multi-step work (already configured in settings)

---

## Files Modified or Created

```
✓ CLAUDE.md                              — Fixed app/server.py → app/server/_base.py
✓ docs/development/architecture.md       — Fixed app/server.py → app/server/_base.py
✓ memory/feedback_test_runner.md         — NEW: test runner canonical path
✓ memory/project_server_layout.md        — NEW: server package structure
✓ memory/MEMORY.md                       — Updated index
✓ .claude/settings.local.json            — Consolidated + added autoCompact
✓ .claude/commands/test.md               — NEW: /test command
✓ .claude/commands/lint.md               — NEW: /lint command
✓ .claude/commands/commit.md             — NEW: /commit command
✓ .claude/commands/coverage.md           — NEW: /coverage command
✓ .claude/commands/server.md             — NEW: /server command
✓ .claude/hooks/post_edit_lint.sh        — NEW: auto-format after edits
✓ .claude/hooks/pre_bash_safety.sh       — NEW: block destructive commands
✓ .claude/mcp-servers-template.json      — NEW: optional MCP config
```

