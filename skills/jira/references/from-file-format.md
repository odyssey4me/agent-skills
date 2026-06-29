# Markdown File Format for `--from-file`

The `issue create --from-file` and `issue update --from-file` commands read issue fields from a markdown file. YAML frontmatter (between `---` delimiters) defines issue fields; the markdown body becomes the description. CLI arguments override frontmatter values.

```yaml
---
summary: "Issue title"
project: "DEMO"          # create only; ignored on update
type: "Task"             # create only; ignored on update
priority: "High"
labels:
  - label1
  - label2
assignee: "account-id"
fields:                  # custom fields, same names as --set-field
  story_points: 5
  assigned_team: "Platform"
links:                   # issue links (additive with --link CLI args)
  - blocks: DEMO-456
  - relates to: DEMO-789
  - is cloned by: DEMO-100
---

Markdown body becomes the issue description.
Supports headings, bold, links, lists, and tables.

Link type names can be the type name, outward label, or inward label
(e.g. `blocks`, `is blocked by`, `Relates`). The direction is resolved
automatically based on which label matches.
```
