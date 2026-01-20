# {{SKILL_NAME}}

{{DESCRIPTION}}

## Authentication

Configure authentication:

```bash
python scripts/setup_auth.py {{SERVICE_NAME}}
```

Required credentials:
- **URL**: Your {{SKILL_NAME}} instance URL
- **Token**: API token or personal access token

## Commands

### list

List resources.

```bash
python skills/{{SERVICE_NAME}}/scripts/list.py
python skills/{{SERVICE_NAME}}/scripts/list.py --limit 20
```

**Arguments:**
- `--limit`: Maximum number of results (default: 50)
- `--json`: Output as JSON

### get

Get a specific resource by ID.

```bash
python skills/{{SERVICE_NAME}}/scripts/get.py RESOURCE_ID
python skills/{{SERVICE_NAME}}/scripts/get.py RESOURCE_ID --json
```

**Arguments:**
- `resource_id`: The resource identifier (required)
- `--json`: Output as JSON

### create

Create a new resource.

```bash
python skills/{{SERVICE_NAME}}/scripts/create.py --name "New Resource"
```

**Arguments:**
- `--name`: Resource name (required)
- `--description`: Resource description
- `--json`: Output as JSON

## Examples

### List all resources

```bash
python skills/{{SERVICE_NAME}}/scripts/list.py
```

### Get resource details

```bash
python skills/{{SERVICE_NAME}}/scripts/get.py my-resource-id
```

### Create a new resource

```bash
python skills/{{SERVICE_NAME}}/scripts/create.py --name "My Resource" --description "A description"
```

## Troubleshooting

### Authentication failed

1. Verify your API token is correct
2. Ensure the URL is correct
3. Check token permissions

### Permission denied

You may not have access to the requested resource. Contact your administrator.
