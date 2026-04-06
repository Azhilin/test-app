# /coverage

Regenerate the test coverage report in `tests/coverage/test_coverage.md`.

## Usage

```bash
/coverage            # regenerate coverage report
/coverage --dry-run  # preview changes without writing
```

## When to Use

Run this command **after adding, removing, or renaming test functions** to keep the coverage index up-to-date.

The coverage report is auto-generated from the test suite — never hand-edit `tests/coverage/test_coverage.md`.

## Implementation

Runs `python tests/tools/test_coverage.py` which:
- Scans all test files under `tests/`
- Counts test functions per module
- Calculates pass rate per layer (unit, component, integration, e2e)
- Outputs markdown table to `tests/coverage/test_coverage.md`

## Fixing Invalid Tests

An "invalid test" is one that asserts behavior that was intentionally changed (requirement updated) or tests an internal implementation detail that no longer exists.

### Decision Tree

**Is the requirement the test covers still `✓ Met` in a requirements file?**
- **Yes, with different implementation** → **FIX** the test to match new behavior (assertion values, mocks, setup change, but test purpose stays same)
- **Yes, requirement unchanged** → test should pass; if it fails, it's a code bug, not a test issue (use `/fix`)
- **No, requirement dropped or marked `⬜ N/T`** → **REMOVE** the test (it's orphaned; no requirement to test)

**Does the test assert an internal implementation detail?**
- **Yes** (e.g., testing private function `_parse_iso()`, testing internal dict structure that changed) → **REMOVE** if the public behavior it implies is tested elsewhere; otherwise **FIX** to test public API
- **No** → keep the test

### Workflow

1. Identify which test is invalid (usually via `/fix` when test fails or `/implement` when requirement changes)
2. Decide: FIX or REMOVE (use decision tree above)
3. **If FIX:** update test assertion, mocks, or setup to match new behavior — keep test purpose same
4. **If REMOVE:** delete the entire test function and file (if empty)
5. Run `/coverage` to refresh stats (must run whenever test functions are added/removed/renamed)

### Example: Fix vs. Remove

**Scenario: Requirement JDF-SP-001 changed from "compute velocity from customfield_10016" to "compute velocity from dynamically-detected story points field"**

Old test:
```python
def test_compute_velocity_uses_customfield_10016():
    issue = make_issue(key="X-1", points=5.0, story_points_field="customfield_10016")
    sprints = [make_sprint(id=1)]
    result = compute_velocity([sprints[0]], {1: [issue]})
    assert result[0]["velocity"] == 5.0
```

Decision: **FIX** — requirement is still Met, just the field source changed.

New test:
```python
def test_compute_velocity_uses_detected_story_points_field():
    issue = make_issue(key="X-1", points=5.0, story_points_field="customfield_99999")  # dynamic
    sprints = [make_sprint(id=1)]
    result = compute_velocity([sprints[0]], {1: [issue]})
    assert result[0]["velocity"] == 5.0
```

---

## Related

- `CLAUDE.md` — Development Workflow step 5: "Maintain test coverage"
- `/fix` — bug-fix loop includes decision criteria for fixing vs. removing tests
- `/implement` — step 5 in workflow is to run `/coverage` after adding/removing tests
- `tests/conftest.py` — Test factories and fixtures
