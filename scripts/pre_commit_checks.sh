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

# Prefer `uv run` so checks resolve dependencies exactly as CI does. Falls back
# to whatever is on PATH (e.g. an already-activated virtualenv) if uv is absent.
if command -v uv >/dev/null 2>&1; then
  run=(uv run --extra dev)
  have_uv=true
else
  run=()
  have_uv=false
fi

# --- Ruff lint and format ---
if [ "$skills_only" = false ]; then
  echo "=== Ruff lint ==="
  if ! "${run[@]}" ruff check --fix .; then
    status=1
  fi

  echo
  echo "=== Ruff format ==="
  if ! "${run[@]}" ruff format .; then
    status=1
  fi
  echo

  # --- Lockfile currency ---
  # Catches dependencies added to pyproject.toml without relocking, which is
  # what makes CI fail with ModuleNotFoundError while local runs pass.
  echo "=== uv lockfile current ==="
  if [ "$have_uv" = true ]; then
    if ! uv lock --check; then
      status=1
    fi
  else
    echo "SKIPPED: uv not installed (see CONTRIBUTING.md)"
    status=1
  fi
  echo
fi

# --- Skill validation ---
echo "=== Validate skill structure ==="
if ! "${run[@]}" python scripts/validate_skill.py skills/*; then
  status=1
fi
echo

# --- Skillsaw lint ---
# Not a Python dependency, so it may not be on PATH. pre-commit manages its own
# copy; fall back to that rather than failing on an environment gap.
echo "=== Skillsaw lint ==="
if command -v skillsaw >/dev/null 2>&1; then
  if ! skillsaw lint skills/; then
    status=1
  fi
elif "${run[@]}" pre-commit run skillsaw --all-files; then
  :
else
  status=1
fi
echo

# --- Test suite ---
# Runs in both modes: skill scripts are what the tests cover, so a skills-only
# change still needs them.
echo "=== Pytest (with coverage) ==="
if ! "${run[@]}" pytest tests/ -q \
  --cov=skills --cov=scripts --cov-report=term-missing --cov-fail-under=80; then
  status=1
fi
echo

# --- Skill execution smoke test ---
# Mirrors the `test-skills` CI job: every skill script must at least import and
# respond to --help. Catches import-time breakage the unit tests mock away.
echo "=== Skill execution smoke test ==="
for skill in skills/*/; do
  # Documentation-only skills (e.g. google, which wraps gogcli) have no
  # scripts/ dir. Guard the find so pipefail doesn't abort the whole run.
  skill_script=""
  if [ -d "${skill}scripts" ]; then
    skill_script=$(find "${skill}scripts" -name "*.py" -not -name "__init__.py" \
      2>/dev/null | head -1 || true)
  fi
  if [ -n "$skill_script" ]; then
    echo "Testing $skill_script"
    if ! "${run[@]}" python "$skill_script" --help >/dev/null; then
      status=1
    fi
    # `check` may fail when the skill isn't configured — CI tolerates that too.
    "${run[@]}" python "$skill_script" check >/dev/null 2>&1 || true
  fi
done
echo

if [ "$status" -eq 0 ]; then
  echo "All checks passed."
else
  echo "Some checks failed."
fi

exit $status
