#!/bin/bash
# Run code quality checks. Exit non-zero if any check fails.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=true

echo "=== black (format check) ==="
if uv run black --check backend/ main.py; then
    echo "black: OK"
else
    echo "black: FAIL — run 'uv run black backend/ main.py' to fix"
    PASS=false
fi

if [ "$PASS" = true ]; then
    echo ""
    echo "All checks passed."
else
    echo ""
    echo "Some checks failed. Fix the issues above and re-run."
    exit 1
fi
