# Model Context Protocol (MCP) Setup

## Overview

This document explains the MCP (Model Context Protocol) setup for the Subscription Tracker project. MCPs enhance Claude Code's capabilities by providing specialized tools and context.

## Recommended MCPs for This Project

### 1. **File System MCP** (Built-in)
Provides file operations and code search.

**Already Available** - No setup needed with Claude Code.

### 2. **Database MCP** (Recommended)
Direct database inspection and querying.

**Setup**:
```bash
# Install SQLite MCP
npm install -g @modelcontextprotocol/server-sqlite

# Or for PostgreSQL
npm install -g @modelcontextprotocol/server-postgres
```

**Configuration** (`~/.config/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "/Users/yurii_jupus/Documents/Personal/subscription-tracker/subscriptions.db"
      ]
    },
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://subscriptions:localdev@localhost:5433/subscriptions"
      ]
    }
  }
}
```

**Benefits**:
- Query subscriptions directly
- Inspect schema
- Debug data issues
- Generate test data

### 3. **Git MCP** (Recommended)
Enhanced git operations and history analysis.

**Setup**:
```bash
npm install -g @modelcontextprotocol/server-git
```

**Configuration**:
```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-git",
        "/Users/yurii_jupus/Documents/Personal/subscription-tracker"
      ]
    }
  }
}
```

**Benefits**:
- Analyze git history
- Find code changes
- Understand evolution
- Generate changelogs

### 4. **Brave Search MCP** (Optional)
Web search for latest docs and packages.

**Setup**:
```bash
npm install -g @modelcontextprotocol/server-brave-search
```

**Configuration**:
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key"
      }
    }
  }
}
```

**Benefits**:
- Find latest Python packages
- Check TypeScript/React docs
- Research best practices

### 5. **Ruff MCP** (Custom - To Build)
Python linting and formatting directly from Claude.

**Concept**:
```typescript
// .claude/mcp/ruff-server.ts
import { Server } from "@modelcontextprotocol/sdk/server";

const server = new Server({
  name: "ruff",
  version: "1.0.0",
});

server.setRequestHandler("lint", async (request) => {
  const { filePath } = request.params;
  // Run ruff check
  const result = execSync(`ruff check ${filePath}`);
  return { diagnostics: result.toString() };
});

server.setRequestHandler("format", async (request) => {
  const { filePath } = request.params;
  execSync(`ruff format ${filePath}`);
  return { success: true };
});
```

### 6. **Docker MCP** (Custom - To Build)
Docker container management from Claude.

**Benefits**:
- Check container status
- View logs
- Restart services
- Inspect networks

## Complete MCP Configuration

**File**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://subscriptions:localdev@localhost:5433/subscriptions"
      ]
    },
    "git": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-git",
        "/Users/yurii_jupus/Documents/Personal/subscription-tracker"
      ]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key-here"
      }
    }
  },
  "globalShortcut": "Cmd+Shift+Space"
}
```

## Using MCPs in Development

### Database Queries

```
Ask Claude Code:
"Using the database MCP, show me all subscriptions created in the last week"
"Query the database to find subscriptions over £50 per month"
"Check the schema of the subscriptions table"
```

### Git Operations

```
Ask Claude Code:
"Using git MCP, show me all changes to the parser.py file"
"Find when the currency conversion feature was added"
"Generate a changelog for the last 10 commits"
```

### Web Search

```
Ask Claude Code:
"Search for the latest FastAPI async best practices"
"Find TypeScript utility types documentation"
"Look up Claude Haiku 4.5 model specifications"
```

## Project-Specific MCP Ideas

### 1. Anthropic API MCP
Direct access to test Claude prompts:

```typescript
server.setRequestHandler("test-prompt", async (request) => {
  const { prompt } = request.params;
  const response = await anthropic.messages.create({
    model: "claude-haiku-4.5-20250929",
    messages: [{ role: "user", content: prompt }]
  });
  return response;
});
```

### 2. Subscription Analytics MCP
Complex analytics queries:

```typescript
server.setRequestHandler("analyze-spending", async (request) => {
  // Run complex SQL analytics
  // Generate spending trends
  // Predict future costs
});
```

### 3. Currency Rate MCP
Real-time currency conversion:

```typescript
server.setRequestHandler("get-rates", async (request) => {
  // Fetch live rates
  // Return conversions
});
```

## Security Considerations

1. **Never commit MCP config with API keys**
2. **Use environment variables for secrets**
3. **Limit MCP database access to read-only when possible**
4. **Review MCP logs regularly**

## Testing MCPs

```bash
# Test PostgreSQL MCP
npx @modelcontextprotocol/server-postgres postgresql://subscriptions:localdev@localhost:5433/subscriptions

# Test Git MCP
npx @modelcontextprotocol/server-git /path/to/subscription-tracker
```

## Troubleshooting

### MCP Not Working

1. **Check Claude Code MCP Settings**
   - Open Claude Code settings
   - Verify MCP servers are listed
   - Check for error messages

2. **Verify MCP Server**
   ```bash
   # Test the server manually
   npx @modelcontextprotocol/server-postgres --help
   ```

3. **Check Logs**
   - MacOS: `~/Library/Logs/Claude/`
   - Linux: `~/.config/Claude/logs/`

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql postgresql://subscriptions:localdev@localhost:5433/subscriptions

# Check if container is running
docker ps | grep subscription-db
```

## Benefits Summary

| MCP | Benefit | Setup Time |
|-----|---------|-----------|
| Database | Direct DB access | 5 min |
| Git | Code history | 2 min |
| Brave Search | Latest docs | 5 min |
| Custom Ruff | Inline linting | 30 min |
| Custom Docker | Container mgmt | 30 min |

## Next Steps

1. Install recommended MCPs (Database, Git)
2. Configure Claude desktop config
3. Test each MCP
4. Consider building custom MCPs
5. Document MCP usage in team guide

---

**Last Updated**: 2025-11-28
**Status**: PostgreSQL and Git MCPs recommended for immediate setup
