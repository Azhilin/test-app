# /implement

Full feature implementation workflow — from requirements to commit-ready code.

## Usage

```bash
/implement <requirement ID or feature description>
```

**Examples:**
- `/implement JDF-SP-001` — implement a specific requirement
- `/implement add support for custom story points field` — describe the feature

---

## Workflow: 7-Step Checklist

Follow these steps in order. Claude will mark each step complete and move to the next.

### Step 1: Read Requirements

1. Look up the feature area using `/requirements` and find the relevant requirement file(s)
2. Read each affected requirement row
3. Note the **current Status** of each row (✓ Met, ✗ Not met, ⬜ N/T)
4. Understand the **Acceptance Criterion** — this is the test you must pass

### Step 2: Implement Code

1. Follow the design principles in CLAUDE.md (Single Responsibility, Open/Closed, DRY, KISS, YAGNI)
2. Use existing patterns and utilities — check `docs/development/architecture.md` for module responsibilities
3. For new metrics: see `app/core/metrics.py` and `/extend`
4. For new config vars: see `app/core/config.py` and `/extend`
5. For new server endpoints: see `app/server/_base.py` and `/extend`
6. Keep changes minimal and focused on the requirement

### Step 3: Write or Update Tests

1. Write tests in the **narrowest layer** that proves the behavior (unit > component > integration > e2e)
2. Use test factories from `tests/conftest.py` — see `/test` for reference
3. Each test should assert one aspect of the requirement's acceptance criterion
4. If you updated existing code, update existing tests — don't add redundant tests

### Step 4: Run Full Test Suite

1. Run `/test` — all checks must pass (lint, type check, security, unit, component)
2. Fix any failures:
   - **Lint/type errors** — run `/lint --fix` to auto-correct
   - **Test failures** — read the failure, identify root cause, fix code (not the test)
   - **Security warnings** — address in code, not in test config
3. Re-run `/test` after each fix — confirm all pass

### Step 5: Update Test Coverage

1. Run `/coverage` to refresh `tests/coverage/test_coverage.md`
2. Verify the test count increased (if you added tests) or stayed same (if you only changed existing tests)

### Step 6: Update Requirement Status

1. Open the requirement file(s) from Step 1
2. For each row: set Status to `✓ Met` if the acceptance criterion is now satisfied
3. If the criterion is partially met or not yet tested, use `⬜ N/T` instead
4. Save the file

### Step 7: Update Documentation

Update docs **only if behavior changed** (not for internal refactors):

- **Module structure changed** → update `docs/development/architecture.md` (section 3: Project Layout, section 4: Architecture & Module Map)
- **New metric or metric output shape changed** → update `docs/product/metrics/`
- **UI or user-visible behavior changed** → update `docs/product/features/features.md`
- **Setup steps or CLI commands changed** → update `README.md`

---

## After Workflow Complete

1. Run `/test` one final time — all must pass
2. Run `/commit` with type `feat:` (new feature) or `fix:` (if this was a bug fix)
3. Optionally: run `/sync` to verify alignment across all 5 layers (requirements, code, tests, architecture.md, feature docs)

---

## Related

- `/requirements` — find and understand the requirement to implement
- `/test` — run full CI test suite
- `/coverage` — update test coverage stats
- `/commit` — commit with proper message format
- `/sync` — audit alignment across layers
- `CLAUDE.md` — Development Workflow (this command operationalizes that 6-step workflow)
- `/extend` — recipes for common patterns (new metric, new config var, new server handler)
