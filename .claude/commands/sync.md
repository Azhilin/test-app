# /sync

Alignment audit — verify requirements, code, tests, and documentation are consistent across all 5 layers.

## Usage

```bash
/sync                      # full audit across all 5 layers
/sync requirements         # audit requirement Status accuracy only
/sync code                 # audit code-to-test alignment
/sync docs                 # audit documentation accuracy
```

---

## Full Audit: 5-Layer Checklist

Run these checks in order. Each layer builds on the previous one.

### Layer 1: Requirements Status

**Goal:** Verify that each requirement Status (`✓ Met`, `✗ Not met`, `⬜ N/T`) accurately reflects implementation.

1. Open `docs/product/requirements/README.md` for the file map
2. For each requirement file (start with one area at a time):
   - Scan all rows with Status `✓ Met` (supposedly satisfied)
   - For each such row, identify the test(s) that verify it — check `tests/unit/test_*.py` or `tests/component/test_*.py`
   - If no test found → flag as **gap**: "Requirement X marked Met but no test coverage"
   - Run `/test` — if a related test fails → flag as **gap**: "Requirement X marked Met but test fails"
   - Scan all rows with Status `✗ Not met`
   - If code exists that implements this requirement → flag as **gap**: "Requirement X marked Not Met but code exists"
3. Report all gaps found (do NOT auto-fix — report and wait for direction)

### Layer 2: Code ↔ Tests Alignment

**Goal:** Verify application code matches test expectations (baseline sanity check).

1. Run `/test` — all unit + component tests must pass
2. If any test fails:
   - Read the failure message
   - Identify whether it's a code bug (test is correct, code is wrong) or a test bug (test is wrong)
   - Flag as **gap**: "<test name>: <failure summary>"
3. No code changes yet — just report gaps

### Layer 3: Architecture Documentation

**Goal:** Verify `docs/development/architecture.md` reflects current module structure and patterns.

1. Check section 3 (Project Layout):
   - Do all directories listed in the tree still exist? (`app/core/`, `app/reporters/`, `app/server/`, etc.)
   - Any new directories added since last update? → flag as **gap**: "New directory <path> not in architecture.md"
2. Check section 4 (Architecture & Module Map):
   - Each module description — is it still accurate?
   - `app/server/` package split (check our memory: `app/server/_base.py`, handler modules) — is this documented?
   - Any new modules added (e.g., new `metrics_<name>.py`) → flag as **gap**: "New module not documented"
3. Check data structures (Issue dict, Sprint dict, metrics_dict shapes):
   - Do they match the current code in `app/core/metrics.py`, `app/core/jira_client.py`?
   - Any new fields added to metrics_dict? → flag as **gap**: "metrics_dict has new fields not documented"
4. Report gaps found

### Layer 4: Feature Documentation

**Goal:** Verify user-facing behavior is documented in `docs/product/features/features.md`.

1. Review `docs/product/features/features.md` (if it exists):
   - Does it describe the main UI features?
   - Does it match what's in `ui/index.html` and `templates/report.html.j2`?
   - Any new UI features added (new tabs, new controls, new report sections) not documented? → flag as **gap**: "Feature <X> added but not documented"
2. If no such file exists, report: "**gap**: `docs/product/features/features.md` missing"

### Layer 5: Metric Documentation

**Goal:** Verify `docs/product/metrics/` accurately describes all computed metrics and their output shapes.

1. Open `docs/product/metrics/`:
   - List all `.md` files in this directory
2. For each metric:
   - Read its documentation
   - Compare to `app/core/metrics.py` — does the metric's computation and output shape match the doc?
   - Check `metrics_dict` output — are all metric fields documented? (velocity, cycle_time, ai_assistance_trend, ai_usage_details, etc.)
   - Any new metric added since last doc update? → flag as **gap**: "Metric <name> not documented in metrics/ dir"
3. Report gaps found

---

## Summary Output

After running the audit, provide a report:

```
ALIGNMENT AUDIT SUMMARY
======================

Layer 1 (Requirements):
  ✓ All Met rows have test coverage
  ⚠ GAP: JDF-SP-001 marked Met but test_compute_velocity fails
  
Layer 2 (Code ↔ Tests):
  ✓ All unit + component tests pass
  
Layer 3 (Architecture Docs):
  ⚠ GAP: New module app/reporters/report_json.py not documented
  
Layer 4 (Feature Docs):
  ⚠ GAP: DAU survey UI feature added but docs/product/features/features.md not updated
  
Layer 5 (Metric Docs):
  ✓ All metrics documented in docs/product/metrics/

TOTAL GAPS FOUND: 3
ACTION REQUIRED: See gaps above. User to decide which to address and in what priority.
```

---

## After Audit

Do NOT auto-fix gaps. Instead:

1. Present the gap report to the user
2. Ask which gaps should be fixed (e.g., "Should we update architecture.md to document the new metric?")
3. For each gap user approves: use `/implement`, `/fix`, or direct code changes to address
4. After fixes: re-run `/sync <layer>` to verify the gap is closed

---

## Typical Use Cases

**After a feature is implemented:**
- Run `/sync` (full audit) to find any documentation that wasn't updated

**After a major refactor:**
- Run `/sync docs` to verify architecture.md reflects the new structure
- Run `/sync requirements` to verify all requirement statuses still accurate

**Periodic maintenance (weekly or monthly):**
- Run `/sync` to keep everything aligned
- Address gaps before they accumulate

**Before a release:**
- Run `/sync` (full audit) to ensure nothing slipped through

---

## Related

- `/requirements` — understand requirement Status values and update rules
- `/implement` — implements features (step 7 updates docs to keep them aligned)
- `/test` — runs full test suite (Layer 2 baseline)
- `docs/development/architecture.md` — the authoritative architecture reference
