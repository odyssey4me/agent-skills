#!/usr/bin/env python3
"""GitHub skill - uses gh CLI exclusively.

This skill is documentation-only and leverages the official GitHub CLI (gh).
All GitHub operations should be performed using gh commands directly.

For usage instructions, see skills/github/SKILL.md

Quick reference:
  gh issue list               # List issues
  gh pr create                # Create pull request
  gh workflow run "CI"        # Trigger workflow
  gh repo view OWNER/REPO     # View repository

Full documentation: https://cli.github.com/manual/
"""

import sys


def main() -> int:
    """Main entry point."""
    print("This GitHub skill uses the gh CLI exclusively.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Please use gh commands directly:", file=sys.stderr)
    print("  gh issue list               # List issues", file=sys.stderr)
    print("  gh pr create                # Create pull request", file=sys.stderr)
    print('  gh workflow run "CI"        # Trigger workflow', file=sys.stderr)
    print("  gh repo view OWNER/REPO     # View repository", file=sys.stderr)
    print("", file=sys.stderr)
    print("See skills/github/SKILL.md for full documentation.", file=sys.stderr)
    print("See https://cli.github.com/manual/ for gh CLI reference.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
