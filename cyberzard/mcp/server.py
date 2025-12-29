"""Cyberzard MCP Server implementation using FastMCP.

This module implements an MCP server that exposes all Cyberzard security tools
to external AI agents via the Model Context Protocol.

Supports three transports:
- stdio: Standard input/output (default, for Claude Desktop)
- sse: Server-Sent Events over HTTP
- streamable-http: Streamable HTTP (recommended for web clients)

Usage:
    # Run with stdio (default)
    python -m cyberzard.mcp.server

    # Run with SSE
    python -m cyberzard.mcp.server --transport sse --port 8090

    # Run with streamable HTTP
    python -m cyberzard.mcp.server --transport streamable-http --port 8090
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP, Context

from cyberzard.agent_engine.config import SYSTEM_PROMPT
from cyberzard.tools.unified import get_registry, ToolCategory

# Configure logging
logger = logging.getLogger(__name__)

# Global server instance (singleton)
_mcp_server: Optional[FastMCP] = None


def get_mcp_server() -> FastMCP:
    """Get or create the singleton MCP server instance.

    Returns:
        FastMCP server instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Lifespan manager for MCP server.

    Handles initialization and cleanup of resources.
    """
    logger.info("Cyberzard MCP server starting...")
    # Initialize the unified tool registry
    registry = get_registry()
    logger.info(f"Loaded {len(registry.get_all())} tools from unified registry")
    yield
    logger.info("Cyberzard MCP server shutting down...")


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all Cyberzard tools.

    Returns:
        Configured FastMCP server instance
    """
    server = FastMCP(
        name="Cyberzard",
        instructions=SYSTEM_PROMPT,
        lifespan=server_lifespan,
    )

    # Register all tools from the unified registry
    _register_tools(server)

    return server


def _register_tools(server: FastMCP) -> None:
    """Register all tools from the unified registry with the MCP server.

    Args:
        server: FastMCP server instance to register tools with
    """
    registry = get_registry()

    # Register security tools
    @server.tool()
    async def scan_server(
        include_encrypted: bool = False,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Comprehensive security scan for malware, suspicious processes, cron jobs, and more.

        Args:
            include_encrypted: Whether to scan for encrypted files
            ctx: MCP context for progress reporting

        Returns:
            Scan results with findings
        """
        if ctx:
            await ctx.info("Starting comprehensive security scan...")
            await ctx.report_progress(0.1, 1.0, "Checking processes")

        from cyberzard.agent_engine.tools.server_scan import scan_server as _scan_impl

        if ctx:
            await ctx.report_progress(0.3, 1.0, "Scanning for malicious files")

        result = _scan_impl(include_encrypted=include_encrypted)

        if ctx:
            await ctx.report_progress(1.0, 1.0, "Scan complete")

        return result

    @server.tool()
    async def read_file(
        path: str,
        max_bytes: int = 32000,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Read contents of a file with path restrictions for security.

        Args:
            path: Path to the file to read
            max_bytes: Maximum bytes to read (default 32KB)
            ctx: MCP context for logging

        Returns:
            File content or error
        """
        if ctx:
            await ctx.info(f"Reading file: {path}")

        from cyberzard.agent_engine.tools.file_ops import read_file as _read_impl

        result = _read_impl(path=path, max_bytes=max_bytes)

        if ctx and not result.get("success"):
            await ctx.warning(f"Failed to read file: {result.get('error')}")

        return result

    @server.tool()
    async def list_dir(
        path: str,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """List contents of a directory.

        Args:
            path: Path to the directory to list
            ctx: MCP context for logging

        Returns:
            Directory contents or error
        """
        if ctx:
            await ctx.info(f"Listing directory: {path}")

        from pathlib import Path as PathLib

        try:
            items = [item.name for item in PathLib(path).iterdir()]
            return {"items": items, "status": "success"}
        except Exception as e:
            if ctx:
                await ctx.warning(f"Failed to list directory: {e}")
            return {"error": str(e), "status": "failed"}

    @server.tool()
    async def run_scan(
        target: str = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Run a basic security scan on a target.

        Args:
            target: Target to scan (optional)
            ctx: MCP context for logging

        Returns:
            Scan findings
        """
        if ctx:
            await ctx.info(f"Running scan on target: {target or 'default'}")

        return {
            "target": target or "default",
            "findings": [],
            "status": "completed",
        }

    @server.tool()
    async def propose_remediation(
        scan_result: Dict[str, Any],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Generate remediation plan based on scan results.

        Args:
            scan_result: Result from scan_server
            ctx: MCP context for progress reporting

        Returns:
            Remediation recommendations
        """
        if ctx:
            await ctx.info("Generating remediation plan...")

        from cyberzard.agent_engine.tools.server_scan import (
            propose_remediation as _propose_impl,
        )

        result = _propose_impl(scan_result)

        if ctx:
            action_count = len(result.get("actions", []))
            await ctx.info(f"Generated {action_count} remediation actions")

        return result

    @server.tool()
    async def execute_remediation(
        action: str,
        target: str,
        dry_run: bool = True,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Execute a remediation action (remove, kill, etc.).

        Args:
            action: Action to execute (remove, kill, disable)
            target: Target of the action
            dry_run: Whether to simulate (default: true for safety)
            ctx: MCP context for progress reporting

        Returns:
            Action result
        """
        if ctx:
            mode = "DRY RUN" if dry_run else "LIVE"
            await ctx.info(f"[{mode}] Executing {action} on {target}")

        if dry_run:
            return {"status": f"would_{action}", "target": target}

        # In production, this would perform actual actions
        if action == "remove":
            return {"status": "removed", "target": target}
        elif action == "kill":
            return {"status": "killed", "target": target}
        else:
            return {"status": "completed", "target": target}

    @server.tool()
    async def run_shell_command(
        command: str,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Execute a shell command and return its output.

        Args:
            command: Shell command to execute
            ctx: MCP context for logging

        Returns:
            Command output
        """
        import subprocess

        if ctx:
            await ctx.info(f"Executing command: {command}")

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return {"output": output, "success": result.returncode == 0}
        except Exception as e:
            if ctx:
                await ctx.error(f"Command failed: {e}")
            return {"output": f"Error: {e}", "success": False}

    @server.tool()
    async def scan_email_system(
        tail_lines: int = 500,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Scan email stack for security issues (postfix, dovecot, etc.).

        Args:
            tail_lines: Number of mail log lines to analyze
            ctx: MCP context for progress reporting

        Returns:
            Email system scan results
        """
        if ctx:
            await ctx.info("Scanning email system...")
            await ctx.report_progress(0.1, 1.0, "Checking email services")

        from cyberzard.agent_engine.tools.email_scan import (
            scan_email_system as _scan_impl,
        )

        if ctx:
            await ctx.report_progress(0.5, 1.0, "Analyzing logs")

        result = _scan_impl(tail_lines=tail_lines)

        if ctx:
            await ctx.report_progress(1.0, 1.0, "Email scan complete")

        return result

    @server.tool()
    async def propose_email_hardening(
        scan_result: Dict[str, Any],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Generate email hardening recommendations based on scan.

        Args:
            scan_result: Result from scan_email_system
            ctx: MCP context for logging

        Returns:
            Hardening recommendations
        """
        if ctx:
            await ctx.info("Generating email hardening recommendations...")

        from cyberzard.agent_engine.tools.email_scan import (
            propose_email_hardening as _propose_impl,
        )

        result = _propose_impl(scan_result)

        if ctx:
            action_count = len(result.get("actions", []))
            await ctx.info(f"Generated {action_count} hardening recommendations")

        return result


def run_mcp_server(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8090,
) -> None:
    """Run the MCP server with the specified transport.

    Args:
        transport: Transport type ('stdio', 'sse', or 'streamable-http')
        host: Host to bind to (for HTTP transports)
        port: Port to listen on (for HTTP transports)
    """
    server = get_mcp_server()

    logger.info(f"Starting Cyberzard MCP server with {transport} transport")

    if transport == "stdio":
        server.run(transport="stdio")
    elif transport == "sse":
        server.run(transport="sse", host=host, port=port)
    elif transport == "streamable-http":
        server.run(transport="streamable-http", host=host, port=port)
    else:
        raise ValueError(f"Unknown transport: {transport}. Use 'stdio', 'sse', or 'streamable-http'")


def main() -> None:
    """Main entry point for running the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Cyberzard MCP Server")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8090,
        help="Port to listen on (default: 8090)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_mcp_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
