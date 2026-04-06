# /fix

Bug-fix loop — identify failing tests, fix code, verify, and update requirements.

## Usage

```bash
/fix                              # run tests to find failures
/fix <test name or bug description>  # jump to a specific failing test
```

**Examples:**
- `/fix` — run `/test` and identify failures
- `/fix test_compute_velocity` — fix the failing test by name
- `/fix schema detection returns None for custom fields` — describe the bug

---

## Workflow: 7-Step Checklist

### Step 1: Run Full Test Suite

1. Run `/test` (or invoke this if you already have test failures)
2. Capture the failing test name(s) and error message(s)
3. Note: do not fix the test itself yet — fix the code

### Step 2: Read the Failing Test

1. Open the test file and locate the failing test function
2. Read the test assertion — this is the **expected behavior**
3. Trace the test inputs and setup — understand what it's testing
4. This test is your source of truth for the bug fix

### Step 3: Find Root Cause in Application Code

1. **Do not modify the test** — the test reflects the correct behavior
2. Read the code path that the test is exercising
3. Identify where the actual output diverges from expected
4. Check logs, error traces, or intermediate values
5. Root cause is in application code, not the test

### Step 4: Fix Code Minimally

1. Make the smallest change needed to make the test pass
2. Follow CLAUDE.md design principles (Single Responsibility, DRY, KISS)
3. Do not refactor unrelated code
4. Do not add new features while fixing a bug
5. Test one fix at a time

### Step 5: Verify Fix + No Regressions

1. Run `/test` again
2. Confirm the failing test now passes
3. Confirm no other tests broke (if a test broke, it's a regression — fix it)
4. Re-run `/test` after each fix — don't batch multiple fixes

### Step 6: Update Requirement Status (if applicable)

1. If this bug fix resolves a requirement:
   - Look up the requirement using `/requirements`
   - Open the requirement file
   - Find the row that describes the bug (acceptance criterion)
   - Set Status to `✓ Met`
2. If the bug is not explicitly in a requirement, skip this step

### Step 7: Commit the Fix

1. Run `/commit` with type `fix:`
2. Message format: `fix: <imperative description of what was fixed>`
3. Examples:
   - `fix: handle missing story points field gracefully`
   - `fix: return correct cycle time when changelog is empty`

---

## Decision: Fix Test vs. Remove Test

**When to FIX the test:**
- The test reflects **valid product behavior** that should still work
- The requirement the test covers is still `✓ Met`
- The implementation changed, but the behavior it asserts is correct
- → Update the test to match the new implementation

**When to REMOVE the test:**
- The test asserts behavior for a requirement that was **dropped** (Status `⬜ N/T`)
- The test is testing an **internal implementation detail** that no longer exists (private function moved, refactored internal structure)
- The test was **never finished** and is still a skeleton
- → Delete the test and run `/coverage` to refresh the stats

**Example of fixing vs. removing:**
- Requirement: "Compute cycle time from In Progress to Done status"
- Old test: asserts cycle time includes transition times: `[5.0, 10.2, 8.1]`
- New implementation: we now compute business-hours cycle time instead
- Decision: **FIX** — the requirement is still valid, just the assertion values change
- vs.
- Requirement: "Support legacy Jira 7 issue format" → Status set to `⬜ N/T` (no longer supporting)
- Old test: tests parsing of Jira 7 custom field IDs
- Decision: **REMOVE** — the requirement was dropped, test is now orphaned

---

## Related

- `/test` — run full CI test suite to find failures
- `/requirements` — look up the requirement the bug fix resolves
- `/commit` — commit with type `fix:`
- `CLAUDE.md` — Development Workflow steps 3–4 (tests, verification)
