"""Tools module for cyberzard.

This module provides unified tool management for Cyberzard, including:
- UnifiedToolRegistry: Central registry for all tools
- Pydantic schemas for type-safe tool I/O
- LangChain and MCP export capabilities
- Backward compatibility with legacy TOOL_REGISTRY
"""

from typing import Any, Dict

# Re-export from unified registry
from .unified import (
    TOOL_REGISTRY,
    PermissionLevel,
    RegisteredTool,
    ToolCategory,
    UnifiedToolRegistry,
    get_registry,
    register_tool,
)

# Re-export schemas
from .schemas import (
    CompleteShellCommandInput,
    CompleteShellCommandOutput,
    DebugShellCommandInput,
    DebugShellCommandOutput,
    ExecuteRemediationInput,
    ExecuteRemediationOutput,
    ListDirInput,
    ListDirOutput,
    PermissionLevel,
    ProposeEmailHardeningInput,
    ProposeEmailHardeningOutput,
    ProposeRemediationInput,
    ProposeRemediationOutput,
    ReadFileInput,
    ReadFileOutput,
    RunScanInput,
    RunScanOutput,
    RunShellCommandInput,
    RunShellCommandOutput,
    SandboxRunInput,
    SandboxRunOutput,
    ScanEmailSystemInput,
    ScanEmailSystemOutput,
    ScanServerInput,
    ScanServerOutput,
    ToolCategory,
    ToolDefinition,
)

# Re-export backward-compatible functions
from .registry import execute_tool, get_schema


def get_system_info() -> Dict[str, Any]:
    """Get basic system information."""
    return {
        "platform": "linux",
        "version": "1.0.0",
        "status": "active"
    }


__all__ = [
    # Core registry
    "UnifiedToolRegistry",
    "RegisteredTool",
    "get_registry",
    "register_tool",
    # Backward compatibility
    "TOOL_REGISTRY",
    "execute_tool",
    "get_schema",
    # Enums
    "ToolCategory",
    "PermissionLevel",
    # Schemas
    "ToolDefinition",
    "ReadFileInput",
    "ReadFileOutput",
    "ListDirInput",
    "ListDirOutput",
    "ScanServerInput",
    "ScanServerOutput",
    "RunScanInput",
    "RunScanOutput",
    "ProposeRemediationInput",
    "ProposeRemediationOutput",
    "ExecuteRemediationInput",
    "ExecuteRemediationOutput",
    "RunShellCommandInput",
    "RunShellCommandOutput",
    "DebugShellCommandInput",
    "DebugShellCommandOutput",
    "CompleteShellCommandInput",
    "CompleteShellCommandOutput",
    "SandboxRunInput",
    "SandboxRunOutput",
    "ScanEmailSystemInput",
    "ScanEmailSystemOutput",
    "ProposeEmailHardeningInput",
    "ProposeEmailHardeningOutput",
    # Utility
    "get_system_info",
]
