# Confluence Skill

The Confluence skill (`confluence.py`) is a self-contained Python CLI script for Confluence content management, search, and space administration. It supports both Confluence Cloud and Data Center/Server deployments, with automatic Markdown ↔ native format conversion.

## Installation & Setup

```bash
# Install runtime dependencies
pip install --user requests keyring pyyaml

# Verify setup
python confluence.py check
```

The `check` command validates credentials, connectivity, and deployment type detection.

## Authentication Configuration

### Environment Variables (Recommended)

```bash
# Confluence Cloud
export CONFLUENCE_URL="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_EMAIL="you@example.com"
export CONFLUENCE_API_TOKEN="your-api-token"

# Confluence Data Center / Server (token auth)
export CONFLUENCE_URL="https://confluence.yourcompany.com"
export CONFLUENCE_API_TOKEN="your-personal-access-token"

# Confluence Data Center / Server (basic auth)
export CONFLUENCE_URL="https://confluence.yourcompany.com"
export CONFLUENCE_USERNAME="your-username"
export CONFLUENCE_PASSWORD="your-password"
```

**Note**: Both `CONFLUENCE_API_TOKEN` and `CONFLUENCE_TOKEN` are accepted.

### Config File

Create `~/.config/agent-skills/confluence.yaml`:

```yaml
url: https://yourcompany.atlassian.net/wiki
email: you@example.com
token: your-api-token

# Optional defaults
defaults:
  cql_scope: "space = DEMO"
  max_results: 25
  default_space: "DEMO"

# Optional space-specific defaults
spaces:
  DEMO:
    default_parent: "123456"
    default_labels: ["documentation", "internal"]
```

**Credential priority**: keyring > environment variables > config file. CLI arguments always override defaults.

## Deployment Auto-Detection

The skill automatically detects Cloud vs. Server and adapts:

- **Cloud** (`atlassian.net`): API base `/wiki/rest/api`, content in ADF (Atlas Doc Format) / editor format
- **DC/Server**: API base `/rest/api`, content in storage format (XHTML)

When creating/updating pages with Markdown, the skill converts to the appropriate format automatically.

## Capabilities

### Check — Validate Configuration

```python { .api }
python confluence.py check
```

Validates credentials, connectivity to Confluence, and deployment type (Cloud vs DC/Server).
Returns exit code 0 on success, 1 on failure.

### Search — Find Content with CQL

```python { .api }
python confluence.py search <cql> [--max-results N] [--type T] [--space S] [--json]
```

Parameters:
- `cql` (required): CQL (Confluence Query Language) query string
- `--max-results N`: Maximum results (default: 50, or configured default)
- `--type T`: Filter by content type: `page`, `blogpost`, `comment`
- `--space S`: Limit to specific space key
- `--json`: Output raw JSON list

If a configured `cql_scope` default exists, it is prepended: `({scope}) AND ({your_cql})`.
If a configured `default_space` exists, it is used when `--space` is not specified.

**Output**: Table with ID, Title, Type, Space columns. With `--json`: list of content objects.

```bash
python confluence.py search "type=page AND space=DEMO"
python confluence.py search "title~login" --space DEMO
python confluence.py search "text ~ API" --type page --max-results 10
python confluence.py search "type=page AND created >= now('-7d')" --json
python confluence.py search "label = important" --space DEMO --type page
```

### Page Get — Retrieve Page Content

```python { .api }
python confluence.py page get <page_identifier> \
  [--json] [--markdown] [--raw] [--no-body] [--expand <fields>]
```

Parameters:
- `page_identifier` (required): Numeric page ID or exact page title
- `--json`: Output full page object as JSON
- `--markdown`: Output body as Markdown (default behavior)
- `--raw`: Output body in original format (storage XHTML or ADF JSON)
- `--no-body`: Only show page metadata (no content)
- `--expand`: Comma-separated fields to expand (e.g., `body.storage,version,space,ancestors`)

When searching by title, uses CQL `title="<title>"` to find the page ID, then fetches full page.

**Output**: Page metadata (ID, Title, Type, Space, Status, Version) with body converted to Markdown.

```bash
python confluence.py page get "My Page Title"
python confluence.py page get 123456
python confluence.py page get "API Docs" --no-body
python confluence.py page get 123456 --json
python confluence.py page get "Design Doc" --raw
python confluence.py page get "Overview" --expand "body.storage,version,ancestors"
```

### Page Create — Create New Page

```python { .api }
python confluence.py page create \
  --space <space_key> \
  --title <title> \
  [--body <content>] \
  [--body-file <file_path>] \
  [--format <format>] \
  [--parent <parent_page_id>] \
  [--labels <label1,label2>] \
  [--json]
```

Parameters:
- `--space` (required): Space key (e.g., `DEMO`)
- `--title` (required): Page title
- `--body`: Page content inline (Markdown by default)
- `--body-file`: Path to file containing page content
- `--format`: Input format: `markdown` (default), `storage` (XHTML), or `editor` (ADF JSON)
- `--parent`: Parent page ID for creating nested pages
- `--labels`: Comma-separated label names. If space has `default_labels` configured, they are applied automatically.
- `--json`: Output created page as JSON

**Output**: `Created page: <id>`, `Title: <title>`, `URL: <webui_url>`. With `--json`: full page object.

```bash
# From inline Markdown content
python confluence.py page create --space DEMO --title "New Page" --body "# Hello\n\nThis is content."

# From a Markdown file
python confluence.py page create --space DEMO --title "Documentation" --body-file README.md

# With parent page (for hierarchy)
python confluence.py page create --space DEMO --title "Sub-page" --body-file sub.md --parent 123456

# With labels
python confluence.py page create --space DEMO --title "Guide" --body-file guide.md --labels "doc,public"

# Using storage format (XHTML)
python confluence.py page create --space DEMO --title "XHTML Page" --body-file page.xml --format storage
```

### Page Update — Update Existing Page

```python { .api }
python confluence.py page update <page_id> \
  [--title <title>] \
  [--body <content>] \
  [--body-file <file_path>] \
  [--format <format>] \
  [--version <version_number>] \
  [--json]
```

Parameters:
- `page_id` (required): Numeric page ID
- `--title`: New page title (optional)
- `--body`: New content inline
- `--body-file`: Path to file with new content
- `--format`: Input format: `markdown` (default), `storage`, or `editor`
- `--version`: Current version number. If not provided, auto-detects current version.
- `--json`: Output updated page as JSON

Automatically increments version number (current + 1). Raises `APIError` on version conflict.

**Output**: `Updated page: <id>`, `New version: <version>`.

```bash
python confluence.py page update 123456 --body-file updated.md
python confluence.py page update 123456 --title "New Title" --body "Updated content"
python confluence.py page update 123456 --body-file page.md --version 5
```

### Space List — List Spaces

```python { .api }
python confluence.py space list [--type <space_type>] [--max-results N] [--json]
```

Parameters:
- `--type`: Filter by space type: `global` or `personal`
- `--max-results N`: Maximum results (default: 50)
- `--json`: Output raw JSON

**Output**: Table with Key, Name, Type columns.

```bash
python confluence.py space list
python confluence.py space list --type global --max-results 20
python confluence.py space list --json
```

### Space Get — Get Space Details

```python { .api }
python confluence.py space get <space_key> [--expand <fields>] [--json]
```

Parameters:
- `space_key` (required): Space key (e.g., `DEMO`)
- `--expand`: Comma-separated fields to expand
- `--json`: Output raw JSON

**Output**: Key, Name, Type, Description (if available).

```bash
python confluence.py space get DEMO
python confluence.py space get DEMO --json
```

### Space Create — Create New Space

```python { .api }
python confluence.py space create \
  --key <key> \
  --name <name> \
  [--description <description>] \
  [--type <space_type>] \
  [--json]
```

Parameters:
- `--key` (required): Short space key (e.g., `DEMO`)
- `--name` (required): Space display name
- `--description`: Space description
- `--type`: Space type: `global` (default) or `personal`
- `--json`: Output created space as JSON

May require admin permissions.

```bash
python confluence.py space create --key NEWSPACE --name "New Space" --description "Our new space"
python confluence.py space create --key PERSONAL --name "My Space" --type personal
```

### Config Show — Display Effective Configuration

```python { .api }
python confluence.py config show [--space <space_key>]
```

Parameters:
- `--space`: Show space-specific defaults for this space key

**Output**: Authentication (masked token), configured defaults (CQL scope, max results, default space), space-specific defaults.

```bash
python confluence.py config show
python confluence.py config show --space DEMO
```

## CQL Reference

Common CQL (Confluence Query Language) queries:

| Query | Description |
|-------|-------------|
| `type = page` | All pages |
| `type = blogpost` | All blog posts |
| `type = comment` | All comments |
| `space = DEMO` | Content in DEMO space |
| `title = "Exact Title"` | Exact title match |
| `title ~ "partial"` | Title contains "partial" |
| `text ~ "keyword"` | Body text contains keyword |
| `created >= now("-7d")` | Created in last 7 days |
| `lastmodified >= startOfDay()` | Modified today |
| `creator = currentUser()` | Created by current user |
| `contributor = "username"` | User contributed to |
| `label = "important"` | Has label "important" |
| `ancestor = 123456` | Descendants of page 123456 |
| `parent = 123456` | Direct children of page |

Combine with `AND`, `OR`, `NOT`, and `ORDER BY`:

```bash
python confluence.py search "type=page AND space=DEMO AND created >= now('-30d') ORDER BY created DESC"
python confluence.py search "text ~ 'deployment' AND label = 'ops'" --space INFRA
```

## Python API (Programmatic Use)

The skill can be imported as a Python module:

```python { .api }
from skills.confluence.scripts.confluence import (
    # Credential management
    get_credential,             # get_credential(key: str) -> str | None
    set_credential,             # set_credential(key: str, value: str) -> None
    delete_credential,          # delete_credential(key: str) -> None
    get_credentials,            # get_credentials(service: str) -> Credentials
    load_config,                # load_config(service: str) -> dict | None
    save_config,                # save_config(service: str, config: dict) -> None
    get_confluence_defaults,    # get_confluence_defaults() -> ConfluenceDefaults
    get_space_defaults,         # get_space_defaults(space: str) -> SpaceDefaults
    merge_cql_with_scope,       # merge_cql_with_scope(user_cql: str, scope: str | None) -> str

    # Deployment detection
    detect_deployment_type,  # detect_deployment_type(force_refresh=False) -> str
    get_api_base,            # get_api_base() -> str
    api_path,                # api_path(endpoint: str) -> str
    is_cloud,                # is_cloud() -> bool
    clear_cache,             # clear_cache() -> None

    # Markdown/format conversion
    markdown_to_storage,    # markdown_to_storage(markdown: str) -> str
    storage_to_markdown,    # storage_to_markdown(storage: str) -> str
    markdown_to_adf,        # markdown_to_adf(markdown: str) -> dict
    adf_to_markdown,        # adf_to_markdown(adf: dict) -> str
    format_content,         # format_content(content, input_format, output_format) -> dict | str

    # HTTP
    make_request,  # make_request(service, method, endpoint, *, params, json_data, headers, timeout) -> dict | list
    get,           # get(service, endpoint, **kwargs) -> dict | list
    post,          # post(service, endpoint, data, **kwargs) -> dict | list
    put,           # put(service, endpoint, data, **kwargs) -> dict | list
    delete,        # delete(service, endpoint, **kwargs) -> dict | list

    # Output formatting
    format_json,         # format_json(data, *, indent=2) -> str
    format_table,        # format_table(rows, columns, *, headers: dict[str,str] | None, max_width) -> str
    format_page,         # format_page(page, *, include_body, as_markdown) -> str
    format_pages_list,   # format_pages_list(pages: list) -> str

    # Content search
    search_content,  # search_content(cql, max_results, content_type, space) -> list[dict]

    # Page operations
    get_page,     # get_page(page_identifier, *, expand) -> dict
    create_page,  # create_page(space, title, body, *, parent_id, body_format, labels) -> dict
    update_page,  # update_page(page_id, *, title, body, body_format, version) -> dict

    # Space operations
    list_spaces,   # list_spaces(*, space_type, max_results) -> list[dict]
    get_space,     # get_space(space_key, *, expand) -> dict
    create_space,  # create_space(key, name, *, description, space_type) -> dict

    # Data classes
    Credentials,
    ConfluenceDefaults,
    SpaceDefaults,

    # Exceptions
    APIError,
    ConfluenceDetectionError,
)
```

### Data Classes

```python { .api }
@dataclass
class Credentials:
    url: str | None = None
    email: str | None = None
    token: str | None = None
    username: str | None = None
    password: str | None = None

    def is_valid(self) -> bool:
        """Returns True if credentials are sufficient.
        Token-based: requires token + url.
        Basic auth: requires username + password + url.
        """

@dataclass
class ConfluenceDefaults:
    cql_scope: str | None = None
    max_results: int | None = None
    fields: list[str] | None = None
    default_space: str | None = None

    @staticmethod
    def from_config(config: dict) -> ConfluenceDefaults:
        """Load from config dict (reads config['defaults'])."""

@dataclass
class SpaceDefaults:
    default_parent: str | None = None
    default_labels: list[str] | None = None

    @staticmethod
    def from_config(config: dict, space: str) -> SpaceDefaults:
        """Load space defaults from config['spaces'][space]."""
```

### Exceptions

```python { .api }
class APIError(Exception):
    """Raised for API request failures."""
    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        ...
    status_code: int | None  # HTTP status code
    response: Any            # Response body text

class ConfluenceDetectionError(Exception):
    """Raised when Confluence deployment type detection fails."""
```

### Markdown Conversion API

```python { .api }
def markdown_to_storage(markdown: str) -> str:
    """
    Convert Markdown to Confluence storage format (XHTML).
    Used for Data Center/Server API.

    Supports: headers (#-######), bold (**), italic (*/_),
    unordered lists (-/*), ordered lists (1.), code blocks (```),
    inline code (`), links ([text](url)).

    Args:
        markdown: Markdown string.

    Returns:
        XHTML string suitable for storage format API field.
    """

def storage_to_markdown(storage: str) -> str:
    """
    Convert Confluence storage format (XHTML) to Markdown.
    Best-effort conversion.

    Args:
        storage: XHTML string from storage format API.

    Returns:
        Markdown string.
    """

def markdown_to_adf(markdown: str) -> dict:
    """
    Convert Markdown to ADF (Atlassian Document Format).
    Used for Confluence Cloud API (editor format).

    Args:
        markdown: Markdown string.

    Returns:
        ADF dict: {"version": 1, "type": "doc", "content": [...]}
    """

def adf_to_markdown(adf: dict) -> str:
    """
    Convert ADF (Atlassian Document Format) to Markdown.

    Args:
        adf: ADF dict with "type": "doc" structure.

    Returns:
        Markdown string.
    """

def format_content(content: str, input_format: str = "markdown", output_format: str = "auto") -> dict | str:
    """
    Convert content between formats for API submission.

    Args:
        content: Content string.
        input_format: "markdown", "storage", or "editor".
        output_format: "auto", "storage", or "editor".
                      "auto" uses "editor" for Cloud, "storage" for Server.

    Returns:
        Formatted content: dict (ADF) for editor/Cloud, str (XHTML) for storage/Server.
    """
```

### Programmatic Usage Examples

```python
from skills.confluence.scripts.confluence import (
    search_content, get_page, create_page, update_page,
    list_spaces, get_space, APIError
)

# Search for pages
pages = search_content("type=page AND space=DEMO", max_results=10)
for page in pages:
    print(page["id"], page["title"])

# Search with filters
pages = search_content(
    cql="title ~ 'API'",
    max_results=5,
    content_type="page",
    space="DEMO"
)

# Get a page by title (returns full page with body)
page = get_page("My Page Title", expand=["body.storage", "version", "space"])
print(f"Page ID: {page['id']}")
print(f"Version: {page['version']['number']}")

# Get a page by ID
page = get_page("123456", expand=["body.storage"])
body = page.get("body", {}).get("storage", {}).get("value", "")

# Create a page from Markdown
new_page = create_page(
    space="DEMO",
    title="New Documentation",
    body="# Introduction\n\nThis is the content.",
    parent_id="456789",
    labels=["documentation", "public"]
)
print(f"Created: {new_page['id']}")
print(f"URL: {new_page['_links']['webui']}")

# Update a page
updated = update_page(
    page_id="123456",
    title="Updated Title",
    body="# Updated Content\n\nNew content here.",
)
print(f"New version: {updated['version']['number']}")

# List spaces
spaces = list_spaces(space_type="global", max_results=20)
for space in spaces:
    print(space["key"], space["name"])

# Get space details
space = get_space("DEMO")
print(space["name"])

# Error handling
try:
    page = get_page("Nonexistent Page Title")
except APIError as e:
    print(f"Error {e.status_code}: {e}")
```

### Deployment Detection API

```python { .api }
def detect_deployment_type(force_refresh: bool = False) -> str:
    """
    Detect Confluence deployment type.
    Uses URL pattern (atlassian.net = Cloud) verified by API probe.
    Results cached per URL.

    Args:
        force_refresh: Bypass cache and re-detect.

    Returns:
        "Cloud" or "Server"

    Raises:
        ConfluenceDetectionError: If detection fails.
    """

def get_api_base() -> str:
    """
    Returns:
        "/wiki/rest/api" for Cloud, "/rest/api" for Server/DataCenter.
    """

def api_path(endpoint: str) -> str:
    """
    Constructs full API path with correct base.

    Args:
        endpoint: Path without base (e.g., "content/search", "space/DEMO").

    Returns:
        "/wiki/rest/api/content/search" or "/rest/api/content/search"
    """
```

### HTTP Helpers (Low-Level)

```python
from skills.confluence.scripts.confluence import get, post, put, delete, api_path

# Make raw API calls
response = get("confluence", api_path("content/search"), params={"cql": "type=page", "limit": 5})
results = response.get("results", [])

# Create via raw API
new_page = post("confluence", api_path("content"), {
    "type": "page",
    "title": "Raw API Page",
    "space": {"key": "DEMO"},
    "body": {
        "storage": {
            "value": "<p>Content</p>",
            "representation": "storage"
        }
    }
})

# Update via raw API
put("confluence", api_path("content/123456"), {
    "version": {"number": 2},
    "type": "page",
    "title": "Updated",
    "body": {"storage": {"value": "<p>New content</p>", "representation": "storage"}}
})

# Delete
delete("confluence", api_path("content/123456"))
```
