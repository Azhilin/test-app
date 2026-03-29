---
applyTo: "**"
---

# Development workflow and interaction style

Apply these rules to every non-trivial code change (new feature, behavioral fix, refactor). Trivial one-liners (typos, formatting) only require steps 2–4.

## Development workflow

Follow these steps in order:

### 1. Maintain requirements

Before and after implementing, check `docs/product/requirements/`. See `docs/product/requirements/README.md` for a quick-lookup index of all files and their ID prefixes.

- Identify which file(s) are relevant to the change.
- Update the `Status` column only — use exactly these values: `✓ Met`, `✗ Not met`, `⬜ N/T`.
- Do not add new rows or create new requirement files.
- Requirement IDs follow a topic prefix pattern (e.g. `LOG-01`, `DAU-F-001`). Do not reassign or reuse IDs.

### 2. Maintain application functionality

Implement the feature, fix, or refactor in the smallest necessary file set. Reuse existing helpers, factories, and file conventions before introducing new abstractions.

### 3. Maintain tests

Write or update tests in the narrowest test layer that proves the changed behavior:

- `tests/unit/` — pure logic, no I/O
- `tests/component/` — filesystem or HTTP behavior
- `tests/integration/` — module integration
- `tests/e2e/` — end-to-end flows

Use factories from `tests/conftest.py` directly (`make_sprint`, `make_issue`, `make_issue_with_changelog`, `make_issue_with_labels`). Config tests: `monkeypatch` + `importlib.reload(config)`.

### 4. Complete testing and verification

Run the test suite and fix all failures before declaring the task done:

```bash
.venv/Scripts/pytest tests/ -v --tb=short
```

For a targeted run: `.venv/Scripts/pytest tests/ -v -k "<test_name>"`.

### 5. Maintain test coverage

After adding, removing, or renaming test functions, regenerate coverage stats:

```bash
python tests/tools/test_coverage.py
```

Never hand-edit `tests/coverage/test_coverage.md` (Test Pyramid block or Count column).

### 6. Maintain project documentation

Update the relevant doc(s) when behavior changes:

- `docs/product/metrics/<name>.md` — when a metric's behavior, output shape, or required fields change
- `docs/development/architecture.md` — when modules are added, removed, or restructured
- `README.md` — when setup steps, CLI commands, or project purpose changes
- `docs/product/features/features.md` — when UI elements or user-visible behavior changes

## Interaction style

### Provide recommendations proactively

- **While working:** flag related issues or improvement opportunities — describe them concisely, don't implement them unless asked.
- **Before implementing:** when multiple valid approaches exist, propose design alternatives with trade-off explanations before starting.
- **After finishing:** suggest logical follow-up tasks the user may not have considered (e.g. "the metric doc may also need updating", "a new requirement row may be worth adding").

### Ask clarifying questions before acting when

- The task scope, edge cases, or expected behavior are ambiguous — ask before writing code.
- A change touches multiple areas (core + reporters + tests + docs) — ask about priorities or constraints upfront.
- A change might break existing metrics contracts, API response shapes, or test expectations — ask for confirmation.
