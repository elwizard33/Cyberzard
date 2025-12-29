"""MCP Client Manager for connecting to external MCP servers.

This module provides a client manager that can connect to external MCP servers,
discover their tools, and proxy calls through the unified registry.

Example usage:
    manager = MCPClientManager()
    
    # Connect to an external server
    await manager.connect(
        name="filesystem",
        command="uvx",
        args=["mcp-server-filesystem", "/path/to/dir"]
    )
    
    # Tools are now available in the unified registry as "external:filesystem:*"
    
    # Call a tool directly
    result = await manager.call_tool("filesystem", "read_file", {"path": "/etc/hosts"})
    
    # Disconnect
    await manager.disconnect("filesystem")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    transport: str = "stdio"  # stdio, http, sse
    url: Optional[str] = None  # For HTTP/SSE transport
    auto_connect: bool = False


class MCPServersConfig(BaseModel):
    """Configuration file for MCP servers."""

    servers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


# ============================================================================
# External Tool Schemas
# ============================================================================


class ExternalToolInput(BaseModel):
    """Input schema for external tool calls."""

    server: str = Field(..., description="MCP server name")
    tool: str = Field(..., description="Tool name on the server")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ExternalToolOutput(BaseModel):
    """Output schema for external tool calls."""

    success: bool = Field(..., description="Whether the call succeeded")
    server: str = Field(..., description="Server that handled the call")
    tool: str = Field(..., description="Tool that was called")
    result: Optional[Any] = Field(None, description="Tool result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class ServerInfo(BaseModel):
    """Information about a connected MCP server."""

    name: str = Field(..., description="Server name")
    connected: bool = Field(..., description="Whether currently connected")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    command: Optional[str] = Field(None, description="Command used to start server")
    transport: str = Field("stdio", description="Transport type")


# ============================================================================
# MCP Client Manager
# ============================================================================


class MCPClientManager:
    """Manager for connecting to external MCP servers.

    This class handles:
    - Connecting to MCP servers via stdio or HTTP transport
    - Tool discovery and registration in the unified registry
    - Proxying tool calls to external servers
    - Managing server lifecycle and configurations

    External tools are registered with the naming convention:
        external:{server_name}:{tool_name}
    """

    _instance: Optional["MCPClientManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "MCPClientManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._sessions: Dict[str, Any] = {}  # ClientSession instances
        self._transports: Dict[str, Any] = {}  # Transport context managers
        self._tools: Dict[str, Dict[str, Any]] = {}  # Server -> tool definitions
        self._configs: Dict[str, MCPServerConfig] = {}
        self._initialized = True
        self._load_config()

    @property
    def config_path(self) -> Path:
        """Get the path to the MCP servers config file."""
        return Path.home() / ".cyberzard" / "mcp_servers.json"

    def _load_config(self) -> None:
        """Load server configurations from file."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            for name, config in data.get("servers", {}).items():
                self._configs[name] = MCPServerConfig(
                    name=name,
                    command=config.get("command", ""),
                    args=config.get("args", []),
                    env=config.get("env"),
                    transport=config.get("transport", "stdio"),
                    url=config.get("url"),
                    auto_connect=config.get("auto_connect", False),
                )
                logger.debug(f"Loaded MCP server config: {name}")
        except Exception as e:
            logger.warning(f"Failed to load MCP server configs: {e}")

    def _save_config(self) -> None:
        """Save server configurations to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "servers": {
                    name: {
                        "command": config.command,
                        "args": config.args,
                        "env": config.env,
                        "transport": config.transport,
                        "url": config.url,
                        "auto_connect": config.auto_connect,
                    }
                    for name, config in self._configs.items()
                }
            }

            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved MCP server configs to {self.config_path}")
        except Exception as e:
            logger.warning(f"Failed to save MCP server configs: {e}")

    def add_server_config(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        transport: str = "stdio",
        url: Optional[str] = None,
        auto_connect: bool = False,
    ) -> None:
        """Add or update a server configuration.

        Args:
            name: Unique server name
            command: Command to start the server
            args: Command arguments
            env: Environment variables
            transport: Transport type (stdio, http, sse)
            url: Server URL for HTTP/SSE transport
            auto_connect: Whether to auto-connect on startup
        """
        self._configs[name] = MCPServerConfig(
            name=name,
            command=command,
            args=args or [],
            env=env,
            transport=transport,
            url=url,
            auto_connect=auto_connect,
        )
        self._save_config()
        logger.info(f"Added MCP server config: {name}")

    def remove_server_config(self, name: str) -> bool:
        """Remove a server configuration.

        Args:
            name: Server name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._configs:
            del self._configs[name]
            self._save_config()
            logger.info(f"Removed MCP server config: {name}")
            return True
        return False

    async def connect(
        self,
        name: str,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        transport: str = "stdio",
        url: Optional[str] = None,
    ) -> bool:
        """Connect to an MCP server.

        Args:
            name: Unique name for this server connection
            command: Command to start the server (for stdio)
            args: Command arguments
            env: Environment variables
            transport: Transport type (stdio, http)
            url: Server URL (for HTTP transport)

        Returns:
            True if connected successfully
        """
        if name in self._sessions:
            logger.warning(f"Server '{name}' is already connected")
            return True

        # Check for saved config if no command provided
        if command is None and name in self._configs:
            config = self._configs[name]
            command = config.command
            args = args or config.args
            env = env or config.env
            transport = config.transport
            url = url or config.url

        if transport == "stdio" and not command:
            logger.error(f"No command provided for stdio transport: {name}")
            return False

        try:
            if transport == "stdio":
                return await self._connect_stdio(name, command, args or [], env)
            elif transport in ("http", "streamable-http"):
                return await self._connect_http(name, url or "")
            else:
                logger.error(f"Unknown transport: {transport}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{name}': {e}")
            return False

    async def _connect_stdio(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Connect via stdio transport."""
        try:
            from mcp import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError:
            logger.error("MCP SDK not installed. Install with: pip install 'mcp[cli]'")
            return False

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env or {},
            )

            # Create transport context manager
            transport_cm = stdio_client(server_params)
            read, write = await transport_cm.__aenter__()
            self._transports[name] = transport_cm

            # Create session
            session = ClientSession(read, write)
            await session.__aenter__()
            self._sessions[name] = session

            # Initialize connection
            await session.initialize()

            # Discover and register tools
            await self._discover_tools(name, session)

            # Save config if not already saved
            if name not in self._configs:
                self.add_server_config(name, command, args, env, "stdio")

            logger.info(f"Connected to MCP server '{name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to connect via stdio to '{name}': {e}")
            # Cleanup on failure
            await self._cleanup_connection(name)
            return False

    async def _connect_http(self, name: str, url: str) -> bool:
        """Connect via HTTP transport."""
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client
        except ImportError:
            logger.error("MCP SDK not installed. Install with: pip install 'mcp[cli]'")
            return False

        if not url:
            logger.error(f"No URL provided for HTTP transport: {name}")
            return False

        try:
            # Create transport context manager
            transport_cm = streamable_http_client(url)
            read, write, _ = await transport_cm.__aenter__()
            self._transports[name] = transport_cm

            # Create session
            session = ClientSession(read, write)
            await session.__aenter__()
            self._sessions[name] = session

            # Initialize connection
            await session.initialize()

            # Discover and register tools
            await self._discover_tools(name, session)

            # Save config if not already saved
            if name not in self._configs:
                self.add_server_config(name, "", [], None, "http", url)

            logger.info(f"Connected to MCP server '{name}' via HTTP")
            return True

        except Exception as e:
            logger.error(f"Failed to connect via HTTP to '{name}': {e}")
            await self._cleanup_connection(name)
            return False

    async def _discover_tools(self, name: str, session: Any) -> None:
        """Discover tools from a connected server and register them."""
        try:
            tools_result = await session.list_tools()
            self._tools[name] = {}

            for tool in tools_result.tools:
                tool_name = tool.name
                self._tools[name][tool_name] = {
                    "name": tool_name,
                    "description": tool.description or f"External tool from {name}",
                    "input_schema": getattr(tool, "inputSchema", {}),
                }

                # Register in unified registry as external tool
                self._register_external_tool(name, tool_name, tool)

            logger.info(f"Discovered {len(self._tools[name])} tools from '{name}'")

        except Exception as e:
            logger.error(f"Failed to discover tools from '{name}': {e}")

    def _register_external_tool(self, server: str, tool_name: str, tool: Any) -> None:
        """Register an external tool in the unified registry."""
        from ..tools.schemas import PermissionLevel, ToolCategory
        from ..tools.unified import UnifiedToolRegistry

        registry = UnifiedToolRegistry()
        full_name = f"external:{server}:{tool_name}"

        # Create a wrapper function for this tool
        async def external_tool_handler(**kwargs) -> Dict[str, Any]:
            return await self.call_tool(server, tool_name, kwargs)

        # Synchronous wrapper
        def sync_handler(**kwargs) -> Dict[str, Any]:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None:
                # Can't run async in existing loop, return pending indicator
                return {"success": False, "error": "Cannot call external tool synchronously in async context"}
            else:
                return asyncio.run(external_tool_handler(**kwargs))

        # Create dynamic Pydantic model for input
        input_schema = getattr(tool, "inputSchema", {})
        properties = input_schema.get("properties", {})

        # Use a generic input schema for external tools
        class DynamicInput(BaseModel):
            """Dynamic input for external tool."""

            class Config:
                extra = "allow"

        try:
            registry.register(
                name=full_name,
                description=tool.description or f"External tool '{tool_name}' from server '{server}'",
                category=ToolCategory.EXTERNAL,
                handler=sync_handler,
                input_schema=DynamicInput,
                output_schema=ExternalToolOutput,
                permission_level=PermissionLevel.EXECUTE,
                tags=["external", server, tool_name],
            )
            logger.debug(f"Registered external tool: {full_name}")
        except Exception as e:
            logger.warning(f"Failed to register external tool {full_name}: {e}")

    async def _cleanup_connection(self, name: str) -> None:
        """Clean up a failed or closing connection."""
        # Clean up session
        if name in self._sessions:
            try:
                await self._sessions[name].__aexit__(None, None, None)
            except Exception:
                pass
            del self._sessions[name]

        # Clean up transport
        if name in self._transports:
            try:
                await self._transports[name].__aexit__(None, None, None)
            except Exception:
                pass
            del self._transports[name]

        # Clean up tool registrations
        if name in self._tools:
            self._unregister_external_tools(name)
            del self._tools[name]

    def _unregister_external_tools(self, server: str) -> None:
        """Unregister all tools from a server."""
        from ..tools.unified import UnifiedToolRegistry

        registry = UnifiedToolRegistry()

        if server in self._tools:
            for tool_name in self._tools[server]:
                full_name = f"external:{server}:{tool_name}"
                registry.unregister(full_name)
                logger.debug(f"Unregistered external tool: {full_name}")

    async def disconnect(self, name: str) -> bool:
        """Disconnect from an MCP server.

        Args:
            name: Server name to disconnect

        Returns:
            True if disconnected, False if not connected
        """
        if name not in self._sessions:
            logger.warning(f"Server '{name}' is not connected")
            return False

        await self._cleanup_connection(name)
        logger.info(f"Disconnected from MCP server '{name}'")
        return True

    async def disconnect_all(self) -> None:
        """Disconnect from all connected servers."""
        names = list(self._sessions.keys())
        for name in names:
            await self.disconnect(name)

    async def call_tool(
        self,
        server: str,
        tool: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a tool on an external MCP server.

        Args:
            server: Server name
            tool: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if server not in self._sessions:
            return {
                "success": False,
                "server": server,
                "tool": tool,
                "result": None,
                "error": f"Server '{server}' is not connected",
            }

        try:
            session = self._sessions[server]
            result = await session.call_tool(tool, arguments or {})

            # Extract result content
            content = []
            for item in result.content:
                if hasattr(item, "text"):
                    content.append(item.text)
                elif hasattr(item, "data"):
                    content.append(f"[Binary data: {len(item.data)} bytes]")
                else:
                    content.append(str(item))

            return {
                "success": not result.isError if hasattr(result, "isError") else True,
                "server": server,
                "tool": tool,
                "result": content[0] if len(content) == 1 else content,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "server": server,
                "tool": tool,
                "result": None,
                "error": str(e),
            }

    def list_servers(self) -> List[ServerInfo]:
        """List all configured and connected servers.

        Returns:
            List of server information
        """
        servers = []

        # Add connected servers
        for name in self._sessions:
            tools = list(self._tools.get(name, {}).keys())
            config = self._configs.get(name)
            servers.append(
                ServerInfo(
                    name=name,
                    connected=True,
                    tools=tools,
                    command=config.command if config else None,
                    transport=config.transport if config else "stdio",
                )
            )

        # Add configured but not connected servers
        for name, config in self._configs.items():
            if name not in self._sessions:
                servers.append(
                    ServerInfo(
                        name=name,
                        connected=False,
                        tools=[],
                        command=config.command,
                        transport=config.transport,
                    )
                )

        return servers

    def is_connected(self, name: str) -> bool:
        """Check if a server is connected.

        Args:
            name: Server name

        Returns:
            True if connected
        """
        return name in self._sessions

    def get_tools(self, server: str) -> List[str]:
        """Get list of tools from a connected server.

        Args:
            server: Server name

        Returns:
            List of tool names
        """
        return list(self._tools.get(server, {}).keys())

    async def auto_connect(self) -> int:
        """Connect to all servers configured with auto_connect=True.

        Returns:
            Number of servers connected
        """
        connected = 0
        for name, config in self._configs.items():
            if config.auto_connect and name not in self._sessions:
                if await self.connect(name):
                    connected += 1
        return connected


# ============================================================================
# Module-level functions
# ============================================================================


def get_mcp_client_manager() -> MCPClientManager:
    """Get the singleton MCP client manager instance.

    Returns:
        MCPClientManager singleton
    """
    return MCPClientManager()


async def connect_mcp_server(
    name: str,
    command: str,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> bool:
    """Convenience function to connect to an MCP server.

    Args:
        name: Unique server name
        command: Command to start the server
        args: Command arguments
        env: Environment variables

    Returns:
        True if connected
    """
    manager = get_mcp_client_manager()
    return await manager.connect(name, command, args, env)


async def disconnect_mcp_server(name: str) -> bool:
    """Convenience function to disconnect from an MCP server.

    Args:
        name: Server name

    Returns:
        True if disconnected
    """
    manager = get_mcp_client_manager()
    return await manager.disconnect(name)


async def call_mcp_tool(
    server: str,
    tool: str,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience function to call an MCP tool.

    Args:
        server: Server name
        tool: Tool name
        arguments: Tool arguments

    Returns:
        Tool execution result
    """
    manager = get_mcp_client_manager()
    return await manager.call_tool(server, tool, arguments)


__all__ = [
    # Classes
    "MCPClientManager",
    "MCPServerConfig",
    "MCPServersConfig",
    "ServerInfo",
    "ExternalToolInput",
    "ExternalToolOutput",
    # Functions
    "get_mcp_client_manager",
    "connect_mcp_server",
    "disconnect_mcp_server",
    "call_mcp_tool",
]
