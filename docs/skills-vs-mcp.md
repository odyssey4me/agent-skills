# Skills vs MCP Servers

This document explains why this repository uses skills instead of MCP (Model Context Protocol) servers for agent integrations.

## What Are Skills?

Skills are a combination of:
1. **Markdown instructions** (`SKILL.md`) - Human and agent-readable documentation
2. **Python scripts** - Executable helpers for API interactions
3. **Shared utilities** - Common authentication and HTTP handling

## What Are MCP Servers?

MCP servers are standalone processes that:
1. Communicate via JSON-RPC over stdio or HTTP
2. Expose "tools" that agents can invoke
3. Run continuously as background processes

## Key Advantages of Skills

### 1. Portability

Skills work across multiple agent tools without modification:

| Agent | Skills Support | MCP Support |
|-------|---------------|-------------|
| Claude Code | Native | Native |
| Gemini CLI | `@` import syntax | Not supported |
| Cursor | Rules files | Native |
| Continue.dev | Rules + config | Native |
| GitHub Copilot | Instructions file | Not supported |

MCP servers are protocol-specific and require each agent to implement the protocol.

### 2. Simplicity

**Skills:**
- Markdown files + Python scripts
- No server process to manage
- No transport configuration
- Works with standard Python tooling

**MCP Servers:**
- Require a running server process
- Need transport configuration (stdio, SSE, HTTP)
- Require MCP client implementation
- Often need TypeScript/Node.js runtime

### 3. Transparency

Skills are readable markdown that users can inspect:

```markdown
# Jira Skill

## Commands

### search
Search for issues using JQL.
Uses: skills/jira/scripts/search.py
```

Users understand exactly what the agent will do. MCP tools are opaque function signatures.

### 4. Context-Aware Loading

Skills load progressively:
1. Skill metadata (always available)
2. Instructions (when relevant)
3. Scripts (only when executed)

MCP servers expose all tools immediately, regardless of relevance.

### 5. Offline Capable

Skills work with just the local Python scripts. No server process needs to be running.

MCP servers require:
- Server process running
- Port availability (for HTTP transport)
- Process management (restart on failure)

### 6. Composability

Skills naturally compose:

```python
# In skills/jira/scripts/issue.py
from shared.auth import get_credentials
from shared.http import make_request
from shared.output import format_issue
```

MCP servers are isolated processes that can't easily share code.

### 7. Version Control Friendly

Skills are files in a repository:
- Easy to review changes
- Simple branching and merging
- No deployment pipeline needed

MCP servers require:
- Separate deployment
- Version compatibility management
- Server infrastructure

## When MCP Still Makes Sense

MCP servers are better suited for:

### Real-Time Bidirectional Communication
When the integration needs to push updates to the agent (e.g., file watchers, live notifications).

### Stateful Long-Running Operations
When maintaining complex state across multiple invocations (e.g., database connections, session management).

### Non-Python Ecosystems
When the integration is primarily in another language (TypeScript, Go, Rust) and Python bindings aren't practical.

### Official MCP-Only Integrations
When a vendor only provides an MCP server and doesn't expose a REST API.

## Comparison Table

| Aspect | Skills | MCP Servers |
|--------|--------|-------------|
| Multi-agent support | Excellent | Limited |
| Setup complexity | Low | Medium-High |
| Runtime requirements | Python only | Server process |
| Code sharing | Natural | Difficult |
| User transparency | High | Low |
| Offline capability | Yes | No |
| Version control | Simple | Complex |
| Real-time updates | No | Yes |
| Stateful operations | Limited | Yes |

## Conclusion

For most API integrations (REST APIs, OAuth services), skills provide a simpler, more portable, and more transparent approach than MCP servers. This repository uses skills as the primary integration method, with MCP servers reserved for cases where their unique capabilities (real-time, stateful) are specifically needed.
