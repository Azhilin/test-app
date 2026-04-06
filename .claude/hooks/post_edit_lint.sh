#!/bin/bash

# Post-edit hook: auto-format Python files after editing
# Triggered after Edit or Write tool modifies a .py file
# Exit code 0 = success (formatting applied), non-zero = format error

if [[ ! "$1" =~ \.py$ ]]; then
    exit 0  # Not a Python file, skip
fi

FILE="$1"

# Check if file exists and is readable
if [[ ! -f "$FILE" ]]; then
    exit 0
fi

# Skip files in tests/ or non-source dirs
if [[ "$FILE" =~ ^tests/ ]] || [[ "$FILE" =~ __pycache__ ]]; then
    exit 0
fi

cd "$(dirname "$FILE")/.." || exit 1

# Run ruff format (auto-fix) on the edited file
if command -v ruff &>/dev/null; then
    ruff format "$FILE" 2>/dev/null
    exit $?
fi

# Fallback if ruff not available
exit 0
