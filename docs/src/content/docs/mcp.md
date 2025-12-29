---
title: MCP Server Integration
description: Using Cyberzard as an MCP server for AI agents
---

# MCP Server Integration

Cyberzard implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to expose its security tools to AI agents like Claude, GPT, and other MCP-compatible clients.

## Quick Start

Start the MCP server:

```bash
# Default stdio transport (for Claude Desktop)
cyberzard mcp

# SSE transport for web clients
cyberzard mcp --transport sse --port 8080

# Streamable HTTP transport
cyberzard mcp --transport streamable-http --port 8080
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cyberzard": {
      "command": "cyberzard",
      "args": ["mcp"],
      "env": {
        "CYBERPANEL_HOST": "https://your-server:8090",
        "CYBERPANEL_USER": "admin",
        "CYBERPANEL_PASS": "your-password"
      }
    }
  }
}
```

## Available Tools

### Security Scanner Tools

| Tool | Description |
|------|-------------|
| `scan_server` | Full security scan for malware, miners, suspicious files |
| `read_file` | Safely read file contents with size limits |
| `propose_remediation` | Generate remediation plans from scan results |
| `execute_remediation` | Execute approved remediation actions |

### CyberPanel Tools

| Tool | Description |
|------|-------------|
| `cyberpanel_list_websites` | List all websites |
| `cyberpanel_create_website` | Create a new website |
| `cyberpanel_create_database` | Create MySQL/MariaDB database |
| `cyberpanel_list_email_accounts` | List email accounts |
| `cyberpanel_issue_ssl` | Issue/renew SSL certificate |
| `cyberpanel_firewall_add_rule` | Add firewall rule |

## Transport Options

### stdio (default)

Best for local integrations like Claude Desktop:

```bash
cyberzard mcp --transport stdio
```

### SSE (Server-Sent Events)

For web-based clients:

```bash
cyberzard mcp --transport sse --host 0.0.0.0 --port 8080
```

### Streamable HTTP

For modern HTTP clients:

```bash
cyberzard mcp --transport streamable-http --host 0.0.0.0 --port 8080
```

## Connecting to External MCP Servers

Cyberzard can also connect to external MCP servers and use their tools:

```python
from cyberzard.mcp.client import MCPClientManager

manager = MCPClientManager()

# Connect via stdio
await manager.connect_stdio("filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/path"])

# Connect via HTTP
await manager.connect_http("remote-server", "http://localhost:8080/sse")

# List available tools
tools = manager.list_all_tools()

# Call a tool
result = await manager.call_tool("filesystem", "read_file", {"path": "/etc/passwd"})
```

## Security Considerations

- MCP exposes powerful system tools - use appropriate access controls
- Set `CYBERPANEL_*` environment variables securely
- Consider using a firewall for network transports
- Review tool permissions before exposing to untrusted clients
