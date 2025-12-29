"""Cyberzard MCP module.

This module provides MCP (Model Context Protocol) server and client capabilities:
- Server: Allow external AI agents to use Cyberzard's security tools
- Client: Connect to external MCP servers and use their tools
"""

from .server import (
    create_mcp_server,
    run_mcp_server,
    get_mcp_server,
)

from .client import (
    MCPClientManager,
    MCPServerConfig,
    ServerInfo,
    get_mcp_client_manager,
    connect_mcp_server,
    disconnect_mcp_server,
    call_mcp_tool,
)

__all__ = [
    # Server
    "create_mcp_server",
    "run_mcp_server",
    "get_mcp_server",
    # Client
    "MCPClientManager",
    "MCPServerConfig",
    "ServerInfo",
    "get_mcp_client_manager",
    "connect_mcp_server",
    "disconnect_mcp_server",
    "call_mcp_tool",
]

