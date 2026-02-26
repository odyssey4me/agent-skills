#!/usr/bin/env bash
# Regenerate tile.json files via tessl skill import, then sync the version
# from each skill's SKILL.md frontmatter (tessl defaults it to 0.1.0).
set -euo pipefail

for skill in skills/*/; do
  [ -f "$skill/tile.json" ] || continue

  tessl skill import "$skill" --workspace odyssey4me --public --force 2>/dev/null

  version=$(sed -n 's/^  version: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/p' "$skill/SKILL.md" | head -1)
  [ -n "$version" ] || continue
  python3 -c "
import json
path = '${skill}tile.json'
with open(path) as f:
    data = json.load(f)
if data.get('version') != '$version':
    data['version'] = '$version'
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print('  updated ${skill}tile.json -> $version')
"
done
