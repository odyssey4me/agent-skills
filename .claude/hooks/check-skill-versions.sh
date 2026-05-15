#!/usr/bin/env bash
# Claude Code hook: check for unbumped skill versions before committing.
# Runs scripts/check_versions.sh and blocks the commit if any changed
# skills haven't had their version bumped.

set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}"

# Check if any skills have staged changes
staged_skills=$(git diff --cached --name-only -- 'skills/' 2>/dev/null | grep -v 'tile\.json' || true)
if [ -z "$staged_skills" ]; then
  exit 0
fi

output=$(scripts/check_versions.sh 2>&1) || {
  echo "$output" >&2
  echo "" >&2
  echo "Bump the version in SKILL.md before committing." >&2
  exit 2
}
