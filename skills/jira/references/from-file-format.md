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
parent: "EPIC-123"       # parent issue key for hierarchy (epic→story, feature→epic, etc.)
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

Link keys can be the type name, outward label, or inward label (e.g.
`blocks`, `is blocked by`, `Relates`). The new issue takes the role named
by the key: `blocks: DEMO-456` makes the new issue block DEMO-456, while
`is blocked by: DEMO-456` makes it blocked by DEMO-456. The type name
behaves like the outward label. Direction comes from the configured labels,
so it also covers types such as `Depend`, where the blocked side is the
outward end.
```
