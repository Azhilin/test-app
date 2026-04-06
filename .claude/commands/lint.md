# /lint

Run code formatting, type checking, and security scanning without running tests.

## Usage

```bash
/lint           # check ruff + mypy + bandit
/lint --fix     # auto-fix ruff formatting issues
```

## Implementation

Individual checks:
```bash
.venv/Scripts/ruff check app/          # fast linting
.venv/Scripts/ruff format app/         # auto-fix with --fix
.venv/Scripts/mypy app/ --ignore-missing-imports --python-version 3.12
.venv/Scripts/bandit -r app/ -q        # security scanning
```

All three run in sequence. Exit on first failure.

## Related

- `/test` — Run lint + all tests
- POST-EDIT HOOK — Auto-fixes formatting after every file edit
