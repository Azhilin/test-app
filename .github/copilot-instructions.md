# Project Instructions

## Generated and temporary files

Place temporary, scratch, diagnostic, or AI-generated working files under
`generated/`, not in the repository root or next to source files.

Use these locations by default:

- `generated/tmp/` for one-off temporary files
- `generated/debug/` for diagnostic output
- `generated/reports/` for report artifacts

Delete disposable files before finishing a task when they are no longer needed.
Do not move real source files into `generated/`; this applies only to generated
or temporary artifacts.

## Test Coverage Stats — never hand-edit

`tests/test_coverage.md` contains auto-generated statistics (test counts, percentages,
pyramid totals). **Do not edit the Test Pyramid block or the Count column by hand.**

Whenever you add, remove, or rename test functions — or whenever the user asks you to
update test coverage stats — run the coverage script instead:

```bash
# Update tests/test_coverage.md in-place
python tests/tools/test_coverage.py

# Preview without writing (dry-run)
python tests/tools/test_coverage.py --dry-run
```

The script (`tests/tools/test_coverage.py`) uses AST analysis to count test cases
(including `@pytest.mark.parametrize` expansions), computes per-layer percentages,
and rewrites both the pyramid block and the Count column automatically.

**Trigger this script when:**
- A test function is added or deleted in `tests/unit/`, `tests/component/`,
  `tests/integration/`, or `tests/e2e/`
- The user asks to "update test coverage", "refresh coverage stats",
  or "update test_coverage.md"
- You add a new test file to any of the layer folders above
