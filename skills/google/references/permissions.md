# Permissions Reference

Read/write classification for Google Workspace commands. Read commands are safe for autonomous agent use. Write commands modify data and should require user approval.

## Gmail

| Command | Access | Description |
|---------|--------|-------------|
| `gmail search` | read | Search messages |
| `gmail get` | read | Get a message |
| `gmail raw` | read | Raw API response |
| `gmail attachment` | read | Download attachment |
| `gmail url` | read | Print web URLs |
| `gmail history` | read | View history |
| `gmail thread get` | read | Get a thread |
| `gmail labels list` | read | List labels |
| `gmail drafts list` | read | List drafts |
| `gmail mark-read` | write | Mark as read |
| `gmail unread` | write | Mark as unread |
| `gmail archive` | write | Archive messages |
| `gmail trash` | write | Trash messages |
| `gmail batch delete` | write | Permanently delete |
| `gmail send` | write | Send email |
| `gmail reply` | write | Reply to message |
| `gmail reply-all` | write | Reply to all |
| `gmail forward` | write | Forward message |
| `gmail drafts create` | write | Create draft |
| `gmail drafts send` | write | Send draft |
| `gmail labels create` | write | Create label |
| `gmail labels delete` | write | Delete label |
| `gmail thread modify` | write | Modify thread labels |

## Calendar

| Command | Access | Description |
|---------|--------|-------------|
| `calendar calendars` | read | List calendars |
| `calendar acl` | read | List calendar ACL |
| `calendar events` | read | List events |
| `calendar event` | read | Get an event |
| `calendar freebusy` | read | Check availability |
| `calendar conflicts` | read | Find overlaps |
| `calendar search` | read | Search events |
| `calendar colors` | read | Show colors |
| `calendar time` | read | Server time |
| `calendar users` | read | List users |
| `calendar create` | write | Create event |
| `calendar update` | write | Update event |
| `calendar delete` | write | Delete event |
| `calendar move` | write | Move event |
| `calendar respond` | write | RSVP to event |
| `calendar subscribe` | write | Add calendar |
| `calendar unsubscribe` | write | Remove calendar |
| `calendar create-calendar` | write | Create calendar |
| `calendar delete-calendar` | write | Delete calendar |
| `calendar focus-time` | write | Create focus time |
| `calendar out-of-office` | write | Create OOO event |
| `calendar working-location` | write | Set working location |

## Drive

| Command | Access | Description |
|---------|--------|-------------|
| `drive ls` | read | List files |
| `drive search` | read | Search files |
| `drive tree` | read | Folder tree |
| `drive du` | read | Folder sizes |
| `drive inventory` | read | Drive inventory |
| `drive get` | read | File metadata |
| `drive download` | read | Download file |
| `drive url` | read | Print web URLs |
| `drive permissions` | read | List permissions |
| `drive audit` | read | Audit sharing |
| `drive drives` | read | List shared drives |
| `drive revisions` | read | File revisions |
| `drive changes` | read | Track changes |
| `drive activity` | read | Activity audit |
| `drive raw` | read | Raw API response |
| `drive comments list` | read | List comments |
| `drive upload` | write | Upload file |
| `drive copy` | write | Copy file |
| `drive move` | write | Move file |
| `drive rename` | write | Rename file |
| `drive mkdir` | write | Create folder |
| `drive delete` | write | Delete/trash file |
| `drive share` | write | Share file |
| `drive unshare` | write | Remove permission |
| `drive bulk` | write | Bulk operations |
| `drive comments create` | write | Add comment |
| `drive comments reply` | write | Reply to comment |
| `drive comments resolve` | write | Resolve comment |
| `drive comments delete` | write | Delete comment |

## Docs

| Command | Access | Description |
|---------|--------|-------------|
| `docs info` | read | Document metadata |
| `docs cat` | read | Read as text |
| `docs export` | read | Export document |
| `docs structure` | read | Document structure |
| `docs headings list` | read | List headings |
| `docs paragraphs list` | read | List paragraphs |
| `docs tables list` | read | List tables |
| `docs images list` | read | List images |
| `docs find-range` | read | Find text ranges |
| `docs list-tabs` | read | List tabs |
| `docs raw` | read | Raw API response |
| `docs create` | write | Create document |
| `docs copy` | write | Copy document |
| `docs write` | write | Write content |
| `docs insert` | write | Insert text |
| `docs delete` | write | Delete text range |
| `docs clear` | write | Clear all content |
| `docs update` | write | Insert/replace at index |
| `docs edit` | write | Find and replace |
| `docs find-replace` | write | Find and replace |
| `docs sed` | write | Regex find/replace |
| `docs format` | write | Apply formatting |
| `docs insert-table` | write | Insert table |
| `docs cell-update` | write | Update table cell |
| `docs cell-style` | write | Style table cell |
| `docs insert-image` | write | Insert image |
| `docs replace-image` | write | Replace image |
| `docs page-layout` | write | Set page layout |

## Sheets

| Command | Access | Description |
|---------|--------|-------------|
| `sheets metadata` | read | Spreadsheet metadata |
| `sheets get` | read | Read values |
| `sheets read-format` | read | Read formatting |
| `sheets notes` | read | Read cell notes |
| `sheets raw` | read | Raw API response |
| `sheets create` | write | Create spreadsheet |
| `sheets copy` | write | Copy spreadsheet |
| `sheets export` | write | Export spreadsheet |
| `sheets update` | write | Update values |
| `sheets batch-update` | write | Batch update |
| `sheets append` | write | Append values |
| `sheets clear` | write | Clear values |
| `sheets insert` | write | Insert rows/columns |
| `sheets delete-dimension` | write | Delete rows/columns |
| `sheets format` | write | Apply formatting |
| `sheets merge` | write | Merge cells |
| `sheets unmerge` | write | Unmerge cells |
| `sheets add-tab` | write | Add tab |
| `sheets delete-tab` | write | Delete tab |
| `sheets rename-tab` | write | Rename tab |
| `sheets reorder-tab` | write | Reorder tabs |
| `sheets find-replace` | write | Find and replace |
| `sheets update-note` | write | Set cell note |

## Slides

| Command | Access | Description |
|---------|--------|-------------|
| `slides info` | read | Presentation metadata |
| `slides list-slides` | read | List slides |
| `slides read-slide` | read | Read slide content |
| `slides locate` | read | Find text elements |
| `slides thumbnail` | read | Get slide thumbnail |
| `slides raw` | read | Raw API response |
| `slides create` | write | Create presentation |
| `slides create-from-markdown` | write | Create from markdown |
| `slides create-from-template` | write | Create from template |
| `slides copy` | write | Copy presentation |
| `slides export` | write | Export presentation |
| `slides new-slide` | write | Create slide |
| `slides add-slide` | write | Add image slide |
| `slides duplicate-slide` | write | Duplicate slide |
| `slides move-slide` | write | Move slide |
| `slides delete-slide` | write | Delete slide |
| `slides insert-text` | write | Insert text |
| `slides replace-text` | write | Find and replace |
| `slides insert-image` | write | Insert image |
| `slides style-text` | write | Apply text styling |
| `slides update-notes` | write | Update speaker notes |
