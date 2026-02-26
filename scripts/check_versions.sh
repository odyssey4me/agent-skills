#!/usr/bin/env bash
# Check skill versions against the last published release tag.
#
# Usage:
#   scripts/check_versions.sh            # compare against latest tag
#   scripts/check_versions.sh 0.3.0      # compare against a specific tag
#
# Exit codes:
#   0 — all changed skills have been version-bumped
#   1 — one or more changed skills still need a bump

set -euo pipefail

TAG="${1:-$(git tag --sort=-v:refname | head -1)}"

if [ -z "$TAG" ]; then
  echo "ERROR: No release tags found and no tag specified." >&2
  exit 1
fi

extract_version() {
  sed -n 's/^  version: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' "$1" | head -1
}

needs_bump=0

printf "%-22s %-10s %-10s %s\n" "SKILL" "RELEASED" "CURRENT" "STATUS"
printf "%-22s %-10s %-10s %s\n" "-----" "--------" "-------" "------"

for skill in skills/*/; do
  skill_name=$(basename "$skill")
  current=$(extract_version "${skill}SKILL.md")
  released=$(git show "${TAG}:${skill}SKILL.md" 2>/dev/null \
    | sed -n 's/^  version: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' | head -1)
  changed_files=$(git diff "$TAG" -- "$skill" --stat 2>/dev/null | grep -c '|' || true)

  if [ "$changed_files" -eq 0 ]; then
    status="no changes"
  elif [ -z "$released" ]; then
    status="new skill (v${current})"
  elif [ "$released" = "$current" ]; then
    status="NEEDS BUMP (${changed_files} files changed)"
    needs_bump=1
  else
    status="bumped (${released} -> ${current})"
  fi

  printf "%-22s %-10s %-10s %s\n" "$skill_name" "${released:-N/A}" "$current" "$status"
done

echo
echo "Compared against tag: ${TAG}"

if [ "$needs_bump" -eq 1 ]; then
  echo "Some skills have unreleased changes without a version bump."
  exit 1
else
  echo "All changed skills have been version-bumped."
  exit 0
fi
