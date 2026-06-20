#!/usr/bin/env bash
# Run all pre-commit checks that Claude should execute before committing.
#
# Usage:
#   scripts/pre_commit_checks.sh           # run all checks
#   scripts/pre_commit_checks.sh --skills  # only run skill-related checks
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed

set -euo pipefail

skills_only=false
if [ "${1:-}" = "--skills" ]; then
  skills_only=true
fi

status=0

# --- Ruff lint and format ---
if [ "$skills_only" = false ]; then
  echo "=== Ruff lint ==="
  if ! ruff check --fix .; then
    status=1
  fi

  echo
  echo "=== Ruff format ==="
  if ! ruff format .; then
    status=1
  fi
  echo
fi

# --- Skill validation ---
echo "=== Validate skill structure ==="
if ! python scripts/validate_skill.py skills/*; then
  status=1
fi
echo

# --- Skillsaw lint ---
echo "=== Skillsaw lint ==="
if ! skillsaw lint skills/; then
  status=1
fi
echo

if [ "$status" -eq 0 ]; then
  echo "All checks passed."
else
  echo "Some checks failed."
fi

exit $status
