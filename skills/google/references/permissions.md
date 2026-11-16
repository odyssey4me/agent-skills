# Permissions Reference

Read/write classification for the Google Workspace commands, against gogcli
`0.47.1` (the version pinned in `SKILL.md`). Read commands are safe for
autonomous use. Write commands change Google-side state and need the user's
approval for that specific change.

**The test.** `read` means the Google-side object is unchanged. Writing a local
file — an export, a download, an attachment — is `read`. Creating, updating,
deleting, moving, sharing, commenting, or changing a setting, label or
permission is `write`. Sharing splits the same way: `drive permissions` lists
(`read`), `drive share` changes (`write`).

## Use `--readonly` as the base for read-only work

Put the flag immediately after `gog`, before the service name, on every command
whose intent is read-only:

```bash
gog --readonly docs cat <docId>
gog --readonly gmail search "is:unread newer_than:7d"
gog --readonly drive ls --folder <folderId>
```

gogcli describes it as "Block mutating API requests at runtime". That is the
point: enforcement sits in the CLI, at the API boundary, rather than in an
agent's permission layer. An allow-list matches command text, so a mistyped
subcommand, an alias, or a mixed group reached one level too high slips past the
text match; `--readonly` refuses the mutation regardless of how the command was
spelled.

Use it as the default, not the exception:

- Read-only intent: always prefix it. A read pays no cost for the flag.
- A write the user asked for: drop the flag for that command only, so the
  approval and the mutation are the same action.
- A mixed group (below): `--readonly` makes its read children safe to call
  without deciding child by child.
- `gog auth add --readonly` requests read-only OAuth scopes, which shapes the
  consent screen rather than a single request.

The flag's blocking behaviour is quoted from its help text, not probed by this
document. To verify it on a given release, attempt a write against a scratch
document you own and confirm it is refused; never test it against shared
content.

## Calendar

| Command | Access | Description |
|---------|--------|-------------|
| `calendar calendars` | read | List calendars |
| `calendar acl` | read | List calendar ACL |
| `calendar events` | read | List events |
| `calendar event` | read | Get an event |
| `calendar raw` | read | Raw API response |
| `calendar freebusy` | read | Check availability |
| `calendar conflicts` | read | Find busy-time overlaps |
| `calendar changed` | read | Recently changed events |
| `calendar search` | read | Search events |
| `calendar colors` | read | Show calendar colors |
| `calendar time` | read | Server time |
| `calendar users` | read | List workspace users |
| `calendar team` | read | Events for a Workspace group |
| `calendar alias list` | read | List calendar aliases |
| `calendar propose-time` | read | Generate a propose-new-time URL |
| `calendar subscribe` | write | Add a calendar |
| `calendar unsubscribe` | write | Remove a calendar |
| `calendar create-calendar` | write | Create a secondary calendar |
| `calendar update-calendar` | write | Change calendar settings |
| `calendar delete-calendar` | write | Delete a secondary calendar |
| `calendar alias set` | write | Set a calendar alias |
| `calendar alias unset` | write | Remove a calendar alias |
| `calendar create` | write | Create an event |
| `calendar update` | write | Update an event |
| `calendar move` | write | Move an event |
| `calendar delete` | write | Delete an event |
| `calendar respond` | write | RSVP to an event |
| `calendar focus-time` | write | Create a focus-time block |
| `calendar out-of-office` | write | Create an out-of-office event |
| `calendar working-location` | write | Set working location |

## Docs

| Command | Access | Description |
|---------|--------|-------------|
| `docs info` | read | Document metadata |
| `docs cat` | read | Read as plain text |
| `docs export` | read | Export to a local file |
| `docs structure` | read | Document structure |
| `docs raw` | read | Raw API response |
| `docs list-tabs` | read | List tabs |
| `docs tabs list` | read | List tabs |
| `docs headings list` | read | List headings |
| `docs paragraphs list` | read | List paragraphs |
| `docs tables list` | read | List native tables |
| `docs images list` | read | List images |
| `docs suggestions list` | read | List pending suggestions |
| `docs named-range list` | read | List named ranges |
| `docs header list` | read | List headers |
| `docs footer list` | read | List footers |
| `docs comments list` | read | List comments |
| `docs comments get` | read | Get a comment |
| `docs comments locate` | read | Map a comment quote to index ranges |
| `docs comments poll` | read | Poll new and modified comments |
| `docs find-range` | read | Find text and print index ranges |
| `docs create` | write | Create a document |
| `docs copy` | write | Copy a document |
| `docs write` | write | Write content |
| `docs insert` | write | Insert text at a position |
| `docs update` | write | Replace at an index or range |
| `docs edit` | write | Find and replace |
| `docs find-replace` | write | Find and replace |
| `docs sed` | write | Regex find and replace |
| `docs delete` | write | Delete a text range |
| `docs clear` | write | Clear all content |
| `docs format` | write | Apply formatting |
| `docs page-layout` | write | Set pageless or pages |
| `docs add-tab` | write | Add a tab |
| `docs rename-tab` | write | Rename a tab |
| `docs delete-tab` | write | Delete a tab |
| `docs tabs add` | write | Add a tab |
| `docs tabs rename` | write | Rename a tab |
| `docs tabs delete` | write | Delete a tab |
| `docs insert-table` | write | Insert a native table |
| `docs cell-update` | write | Replace a table cell |
| `docs cell-style` | write | Style a table cell |
| `docs table-row insert` | write | Insert a table row |
| `docs table-row delete` | write | Delete a table row |
| `docs table-row style` | write | Set row height and overflow |
| `docs table-row pin-header` | write | Pin or unpin header rows |
| `docs table-column insert` | write | Insert a table column |
| `docs table-column delete` | write | Delete a table column |
| `docs table-merge` | write | Merge table cells |
| `docs table-unmerge` | write | Unmerge table cells |
| `docs table-column-width` | write | Set or reset column widths |
| `docs insert-image` | write | Insert an image |
| `docs replace-image` | write | Replace an image |
| `docs insert-person` | write | Insert a person chip |
| `docs insert-file-chip` | write | Insert a Drive file chip |
| `docs insert-date-chip` | write | Insert a date chip |
| `docs insert-page-break` | write | Insert a page break |
| `docs insert-footnote` | write | Insert a footnote |
| `docs insert-section-break` | write | Insert a section break |
| `docs insert-horizontal-rule` | write | Insert a horizontal rule |
| `docs section-columns` | write | Set section column count |
| `docs named-range create` | write | Create a named range |
| `docs named-range replace` | write | Replace a named range with text |
| `docs named-range delete` | write | Delete a named range |
| `docs header create` | write | Create a header |
| `docs header delete` | write | Delete a header |
| `docs footer create` | write | Create a footer |
| `docs footer delete` | write | Delete a footer |
| `docs comments add` | write | Add a comment |
| `docs comments reply` | write | Reply to a comment |
| `docs comments resolve` | write | Resolve a comment |
| `docs comments reopen` | write | Reopen a comment |
| `docs comments delete` | write | Delete a comment |

## Drive

| Command | Access | Description |
|---------|--------|-------------|
| `drive ls` | read | List files |
| `drive search` | read | Full-text search |
| `drive tree` | read | Folder tree |
| `drive du` | read | Folder sizes |
| `drive inventory` | read | Export a read-only inventory |
| `drive get` | read | File metadata |
| `drive download` | read | Download to a local file |
| `drive url` | read | Print web URLs |
| `drive permissions` | read | List permissions |
| `drive audit sharing` | read | Find public or external permissions |
| `drive audit user` | read | Find permissions granted to a user |
| `drive drives` | read | List shared drives |
| `drive raw` | read | Raw API response |
| `drive comments list` | read | List comments |
| `drive comments get` | read | Get a comment |
| `drive revisions list` | read | List revisions |
| `drive revisions get` | read | Revision metadata |
| `drive changes start-token` | read | Get a changes page token |
| `drive changes list` | read | List changes since a token |
| `drive changes poll` | read | Poll changes with a local state file |
| `drive activity query` | read | Query Drive Activity events |
| `drive labels list` | read | List label schemas |
| `drive labels get` | read | Get a label schema |
| `drive labels file list` | read | List labels on a file |
| `drive comments create` | write | Add a comment |
| `drive comments update` | write | Update a comment |
| `drive comments reply` | write | Reply to a comment |
| `drive comments resolve` | write | Resolve a comment |
| `drive comments reopen` | write | Reopen a comment |
| `drive comments delete` | write | Delete a comment |
| `drive copy` | write | Copy a file |
| `drive upload` | write | Upload a file |
| `drive sync push` | write | Push a local directory |
| `drive mkdir` | write | Create a folder |
| `drive move` | write | Move a file |
| `drive rename` | write | Rename a file or folder |
| `drive delete` | write | Trash or permanently delete |
| `drive shortcut create` | write | Create a shortcut |
| `drive share` | write | Share a file or folder |
| `drive unshare` | write | Remove a permission |
| `drive bulk remove-public` | write | Remove public permissions in bulk |
| `drive bulk update-role` | write | Change roles in bulk |
| `drive changes watch` | write | Open a changes webhook channel |
| `drive changes stop` | write | Close a changes webhook channel |
| `drive changes serve` | write | Receive change notifications and run a local hook |
| `drive labels file apply` | write | Apply a label to files |
| `drive labels file remove` | write | Remove a label from files |

## Gmail

| Command | Access | Description |
|---------|--------|-------------|
| `gmail search` | read | Search threads |
| `gmail get` | read | Get a message |
| `gmail raw` | read | Raw API response |
| `gmail attachment` | read | Download an attachment to a local file |
| `gmail url` | read | Print web URLs for threads |
| `gmail history` | read | Gmail history |
| `gmail messages search` | read | Search messages |
| `gmail thread get` | read | Get a thread |
| `gmail thread attachments` | read | List a thread's attachments |
| `gmail labels list` | read | List labels |
| `gmail labels get` | read | Label details and counts |
| `gmail drafts list` | read | List drafts |
| `gmail drafts get` | read | Draft details |
| `gmail settings filters list` | read | List filters |
| `gmail settings filters get` | read | Get a filter |
| `gmail settings filters export` | read | Export filters to local XML |
| `gmail settings delegates list` | read | List delegates |
| `gmail settings delegates get` | read | Get a delegate |
| `gmail settings forwarding list` | read | List forwarding addresses |
| `gmail settings forwarding get` | read | Get a forwarding address |
| `gmail settings autoforward get` | read | Get auto-forwarding settings |
| `gmail settings sendas list` | read | List send-as aliases |
| `gmail settings sendas get` | read | Get a send-as alias |
| `gmail settings vacation get` | read | Get vacation responder settings |
| `gmail settings watch status` | read | Show stored watch state |
| `gmail track opens` | read | Query recorded email opens |
| `gmail track status` | read | Show tracking configuration |
| `gmail archive` | write | Archive messages |
| `gmail mark-read` | write | Mark messages read |
| `gmail unread` | write | Mark messages unread |
| `gmail trash` | write | Trash messages |
| `gmail batch` | write | Batch operations, including permanent delete |
| `gmail messages modify` | write | Change a message's labels |
| `gmail thread modify` | write | Change a thread's labels |
| `gmail labels create` | write | Create a label |
| `gmail labels rename` | write | Rename a label |
| `gmail labels style` | write | Change label colour or visibility |
| `gmail labels modify` | write | Apply labels to threads |
| `gmail labels delete` | write | Delete a label |
| `gmail send` | write | Send email |
| `gmail import` | write | Import an RFC822 message |
| `gmail reply` | write | Reply |
| `gmail reply-all` | write | Reply to all |
| `gmail forward` | write | Forward |
| `gmail autoreply` | write | Reply once to matching messages |
| `gmail drafts create` | write | Create a draft |
| `gmail drafts update` | write | Update a draft |
| `gmail drafts delete` | write | Delete a draft permanently |
| `gmail drafts send` | write | Send a draft |
| `gmail drafts reply` | write | Save a reply as a draft |
| `gmail drafts reply-all` | write | Save a reply-all as a draft |
| `gmail drafts forward` | write | Save a forward as a draft |
| `gmail settings filters create` | write | Create a filter |
| `gmail settings filters delete` | write | Delete a filter |
| `gmail settings delegates add` | write | Add a delegate |
| `gmail settings delegates remove` | write | Remove a delegate |
| `gmail settings forwarding create` | write | Add a forwarding address |
| `gmail settings forwarding delete` | write | Delete a forwarding address |
| `gmail settings autoforward update` | write | Update auto-forwarding |
| `gmail settings sendas create` | write | Create a send-as alias |
| `gmail settings sendas update` | write | Update a send-as alias |
| `gmail settings sendas verify` | write | Resend alias verification |
| `gmail settings sendas delete` | write | Delete a send-as alias |
| `gmail settings vacation update` | write | Update vacation responder |
| `gmail settings watch start` | write | Start a Gmail watch |
| `gmail settings watch renew` | write | Renew a Gmail watch |
| `gmail settings watch stop` | write | Stop a Gmail watch |
| `gmail settings watch serve` | write | Run a Pub/Sub push handler |
| `gmail settings watch pull` | write | Run a Pub/Sub pull consumer |
| `gmail track setup` | write | Deploy the tracking worker |
| `gmail track key` | write | Manage tracking encryption keys |

## Sheets

| Command | Access | Description |
|---------|--------|-------------|
| `sheets get` | read | Read a range |
| `sheets read-format` | read | Read cell formatting |
| `sheets notes` | read | Read cell notes |
| `sheets metadata` | read | Spreadsheet metadata |
| `sheets raw` | read | Raw API response |
| `sheets export` | read | Export to a local file |
| `sheets conditional-format list` | read | List conditional formatting |
| `sheets validation get` | read | Get data validation |
| `sheets banding list` | read | List banded ranges |
| `sheets links get` | read | Get cell hyperlinks |
| `sheets named-ranges list` | read | List named ranges |
| `sheets named-ranges get` | read | Get a named range |
| `sheets table list` | read | List tables |
| `sheets table get` | read | Get a table |
| `sheets datasource list` | read | List data sources |
| `sheets datasource describe` | read | Describe a data source |
| `sheets datasource table list` | read | List data-source tables |
| `sheets datasource table describe` | read | Describe a data-source table |
| `sheets datasource table read` | read | Read data-source table values |
| `sheets chart list` | read | List charts |
| `sheets chart get` | read | Get a chart definition |
| `sheets update` | write | Update values |
| `sheets batch-update` | write | Update multiple ranges |
| `sheets batch-request` | write | Submit a structural request batch |
| `sheets append` | write | Append values |
| `sheets insert` | write | Insert rows or columns |
| `sheets delete-dimension` | write | Delete rows or columns |
| `sheets clear` | write | Clear values |
| `sheets format` | write | Apply formatting |
| `sheets number-format` | write | Apply number format |
| `sheets merge` | write | Merge cells |
| `sheets unmerge` | write | Unmerge cells |
| `sheets copy-paste` | write | Copy values or formatting |
| `sheets freeze` | write | Freeze rows and columns |
| `sheets resize-columns` | write | Resize columns |
| `sheets resize-rows` | write | Resize rows |
| `sheets update-note` | write | Set or clear a cell note |
| `sheets find-replace` | write | Find and replace |
| `sheets conditional-format add` | write | Add a conditional formatting rule |
| `sheets conditional-format clear` | write | Remove conditional formatting |
| `sheets validation set` | write | Set data validation |
| `sheets validation clear` | write | Clear data validation |
| `sheets banding set` | write | Apply banded colours |
| `sheets banding clear` | write | Remove banding |
| `sheets filter set` | write | Set a basic filter |
| `sheets links set` | write | Set cell hyperlinks |
| `sheets named-ranges add` | write | Add a named range |
| `sheets named-ranges update` | write | Update a named range |
| `sheets named-ranges delete` | write | Delete a named range |
| `sheets table create` | write | Create a table |
| `sheets table append` | write | Append rows to a table |
| `sheets table clear` | write | Clear table rows |
| `sheets table delete` | write | Delete a table |
| `sheets datasource add` | write | Add a data source |
| `sheets datasource update` | write | Update a data source |
| `sheets datasource refresh` | write | Refresh a data source |
| `sheets datasource delete` | write | Delete a data source |
| `sheets chart create` | write | Create a chart |
| `sheets chart update` | write | Update a chart |
| `sheets chart delete` | write | Delete a chart |
| `sheets create` | write | Create a spreadsheet |
| `sheets copy` | write | Copy a spreadsheet |
| `sheets add-tab` | write | Add a tab |
| `sheets duplicate-tab` | write | Duplicate a tab |
| `sheets rename-tab` | write | Rename a tab |
| `sheets delete-tab` | write | Delete a tab |
| `sheets reorder-tab` | write | Reorder tabs |

## Slides

| Command | Access | Description |
|---------|--------|-------------|
| `slides info` | read | Presentation metadata |
| `slides list-slides` | read | List slides |
| `slides read-slide` | read | Read slide content |
| `slides locate` | read | Locate text elements |
| `slides thumbnail` | read | Get or download a thumbnail |
| `slides raw` | read | Raw API response |
| `slides export` | read | Export to a local file |
| `slides create` | write | Create a presentation |
| `slides create-from-markdown` | write | Create from markdown |
| `slides create-from-template` | write | Create from a template |
| `slides copy` | write | Copy a presentation |
| `slides add-slide` | write | Add an image slide |
| `slides new-slide` | write | Create a themed slide |
| `slides duplicate-slide` | write | Duplicate a slide |
| `slides move-slide` | write | Move a slide |
| `slides skip-slide` | write | Skip a slide when presenting |
| `slides unskip-slide` | write | Un-skip a slide |
| `slides delete-slide` | write | Delete a slide |
| `slides update-notes` | write | Update speaker notes |
| `slides replace-slide` | write | Replace a slide image |
| `slides insert-image` | write | Insert an image |
| `slides insert-text` | write | Insert text into an element |
| `slides replace-text` | write | Find and replace text |
| `slides style-text` | write | Style a text range |
| `slides paragraph-style` | write | Set paragraph style |
| `slides link` | write | Apply a hyperlink |
| `slides bullets` | write | Toggle paragraph bullets |
| `slides table create` | write | Create a table |
| `slides table merge` | write | Merge table cells |
| `slides table unmerge` | write | Unmerge table cells |
| `slides table row insert` | write | Insert table rows |
| `slides table row delete` | write | Delete table rows |
| `slides table row size` | write | Set row height |
| `slides table column insert` | write | Insert table columns |
| `slides table column delete` | write | Delete table columns |
| `slides table column size` | write | Set column width |
| `slides table cell style` | write | Style a table cell |
| `slides table border style` | write | Style table borders |
| `slides element create-shape` | write | Create a shape |
| `slides element create-line` | write | Create a line |
| `slides element transform` | write | Move, resize, or rotate |
| `slides element style` | write | Style a fill, outline, or line |
| `slides element z-order` | write | Change stacking order |
| `slides element group` | write | Group elements |
| `slides element ungroup` | write | Ungroup elements |
| `slides element alt-text` | write | Set or clear alt text |
| `slides element delete` | write | Delete elements |

## Shorthand aliases

`gog` maps a few top-level words onto service commands. They classify the same
way as their targets.

| Command | Access | Description |
|---------|--------|-------------|
| `gog ls` | read | Alias for `drive ls` |
| `gog search` | read | Alias for `drive search` |
| `gog download` | read | Alias for `drive download` |
| `gog open` | read | Print a web URL, offline |
| `gog me` | read | Alias for `people me` |
| `gog status` | read | Alias for `auth status` |
| `gog send` | write | Alias for `gmail send` |
| `gog upload` | write | Alias for `drive upload` |
| `gog login` | write | Alias for `auth add` |
| `gog logout` | write | Alias for `auth remove` |

## Groups that mix read and write

Never allow-list a parent group whose children split across the two classes.
Call the child, or run the child under `--readonly`.

| Group | Reads | Writes |
|-------|-------|--------|
| `docs comments` | `list`, `get`, `locate`, `poll` | `add`, `reply`, `resolve`, `reopen`, `delete` |
| `docs tabs`, `docs named-range`, `docs header`, `docs footer` | `list` | `add`/`create`, `rename`, `delete`, `replace` |
| `docs table-row`, `docs table-column` | none | all children |
| `gmail messages`, `gmail thread`, `gmail labels` | `search`, `get`, `list`, `attachments` | `modify`, `create`, `rename`, `style`, `delete` |
| `gmail drafts` | `list`, `get` | the rest |
| `gmail settings filters` | `list`, `get`, `export` | `create`, `delete` |
| `gmail settings delegates`, `forwarding`, `sendas` | `list`, `get` | `add`/`create`, `update`, `verify`, `remove`/`delete` |
| `gmail settings autoforward`, `vacation` | `get` | `update` |
| `gmail settings watch` | `status` | `start`, `renew`, `stop`, `serve`, `pull` |
| `gmail track` | `opens`, `status` | `setup`, `key` |
| `drive audit` | all children | none |
| `drive comments`, `drive labels` | `list`, `get`, `file list` | `create`, `update`, `reply`, `resolve`, `reopen`, `delete`, `file apply`, `file remove` |
| `drive revisions` | all children | none |
| `drive changes` | `start-token`, `list`, `poll` | `watch`, `serve`, `stop` |
| `drive bulk`, `drive sync`, `drive shortcut` | none | all children |
| `sheets conditional-format`, `banding` | `list` | `add`/`set`, `clear` |
| `sheets validation`, `links` | `get` | `set`, `clear` |
| `sheets named-ranges`, `table`, `chart` | `list`, `get` | `add`/`create`, `update`, `delete`, `append`, `clear` |
| `sheets datasource` | `list`, `describe` | `add`, `update`, `refresh`, `delete` |
| `sheets datasource table` | all children | none |
| `sheets filter` | none | `set` |
| `slides table`, `slides element` | none | all children |

## Not classified here

gogcli `0.47.1` also ships top-level groups this skill does not document:
`chat`, `contacts`, `tasks`, `people`, `keep`, `forms`, `sites`, `meet`,
`groups`, `admin`, `backup`, `batch`, `api`, `maps`, `classroom`, `zoom`,
`appscript`, `analytics`, `searchconsole`, `adsense`, `youtube`, `photos`,
`time`, `config`, `schema`, `mcp` and `update`. They are not in this reference
because the skill does not cover them, not because they are safe. Treat an
unlisted command as unclassified: run it under `--readonly` when the intent is
read-only, and confirm with `gog <group> --help` before treating anything as a
read.
