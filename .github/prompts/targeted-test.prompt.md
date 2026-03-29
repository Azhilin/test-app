---
name: targeted-test
description: Add or update tests in the smallest appropriate layer for this repository.
argument-hint: Describe the behavior to test and the file under change.
---

Create or update tests for this repository with minimal scope.

Behavior under test: ${input:behavior:Describe the behavior to verify}
Changed file: ${input:file:Name the primary changed file}
Preferred layer: ${input:layer:unit, component, integration, or e2e}

Requirements:

- Choose the smallest test layer that proves the behavior.
- Reuse factories and fixtures from `tests/conftest.py`.
- Keep assertions focused on the changed behavior.
- If test functions are added, removed, or renamed, remind me to run `python tests/tools/test_coverage.py`.
