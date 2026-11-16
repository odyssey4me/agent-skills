# Permissions Reference

gogcli enforces read-only mode itself: `--readonly` blocks mutating API requests
inside the CLI. This skill leans on that flag instead of on a list of command
names, because the command tree moves with every release while the flag does
not.

## The rule

Prefix every read-only command with `gog --readonly`. Treat every other gog
invocation as a write: it needs the user's approval for that specific change.

```bash
gog --readonly docs cat <docId>
gog --readonly gmail search "is:unread newer_than:7d"
gog --readonly drive ls --folder <folderId>
```

- Read-only intent: always prefix it. A read pays no cost for the flag.
- A write the user asked for: drop the flag for that command only, so the
  approval and the mutation are the same action.
- Unsure whether a command mutates: run it under `--readonly`. If the CLI
  refuses it, it was a mutation.

## Why not enumerate the commands

- The flag is enforced at the API boundary, so it does not depend on how a
  command was spelled. An allow-list matches command text, and a mistyped
  subcommand, an alias, or a group reached one level too high slips past it.
- The surface moves. Each release adds, renames and regroups commands, and a
  hand-maintained list of several hundred paths is stale the moment it is
  written. The flag's guarantee survives that churn; a list does not.
- Commands that need gating are gated. Batch submission is the clearest case:
  the CLI reports `submission_allowed: false` for every batch service when
  `--readonly` is on, and `true` when it is off.

## What the flag alone does not cover

`--readonly` stops Google-side mutations. Three things still need care, and none
of them are made safe by the flag.

- **Local state.** The CLI still writes locally: state files behind
  `drive changes poll` and `drive changes serve`, the tracking store behind
  `gmail track`, staged batches behind `gog batch begin`, and credentials or
  configuration behind `auth` and `config`.
- **Local execution.** `drive changes serve --on-change` runs a shell command for
  each change batch, and `gmail settings watch serve|pull` runs a Pub/Sub
  consumer. Approval has to cover what that local code does, not just the API
  call that triggered it.
- **Grant scope.** `gog auth add --readonly` requests read-only OAuth scopes for
  the whole grant. That shapes the consent screen for every later command, so it
  is a credential decision rather than a per-request one.

## For allow-lists

When a permission layer matches command text, match the flag rather than command
names: allowing `gog --readonly *` covers read-only work without naming a
command that a later release can rename or split, and the CLI still refuses
mutations. Keep the local-state and local-execution cases above behind approval,
because no flag makes those safe.

Never allow-list a bare parent group. Children split across read and write in
`docs comments`, `docs tabs`, `gmail settings`, `gmail drafts`, `drive changes`,
`drive comments`, `drive labels`, `sheets table`, `sheets datasource`,
`sheets chart`, `slides element` and `slides table`, among others.

## Commands this skill does not cover

This skill covers Calendar, Docs, Drive, Gmail, Sheets and Slides. gog also ships
other groups — `chat`, `contacts`, `tasks`, `keep`, `forms`, `meet`, `groups`,
`admin`, `backup`, `batch`, `api`, `maps`, `youtube`, `photos`, `zoom` and more.
They are absent because the skill does not cover them, not because they are safe:
treat an unlisted command as unclassified and run it under `--readonly` when the
intent is read-only.

The blocking behaviour described here comes from the CLI's own help text and
`schema` output. To confirm it on a release you care about, attempt a write
against a scratch document you own and check that it is refused; never test it
against shared content.
