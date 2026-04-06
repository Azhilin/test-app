#!/bin/bash

# Pre-bash safety hook: block destructive operations that are too risky to run
# Triggered before Bash tool executes
# Exit code 0 = safe to execute, non-zero = blocked

COMMAND="$1"

# Dangerous patterns to block
BLOCKED_PATTERNS=(
    "git push --force"
    "git reset --hard"
    "git checkout --"
    "rm -rf"
    "git clean -f"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if [[ "$COMMAND" =~ $pattern ]]; then
        echo "ERROR: Blocked destructive operation: $pattern"
        echo "This operation requires explicit user confirmation."
        exit 1
    fi
done

# Allow git reset to main/master without --hard (safe)
# Block force push to main/master
if [[ "$COMMAND" =~ git\ push.*--force.*(main|master) ]]; then
    echo "ERROR: Blocked force push to main/master branch"
    echo "This would overwrite remote history. Requires explicit user approval."
    exit 1
fi

# Allow everything else
exit 0
