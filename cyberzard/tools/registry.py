"""Tool registry for cyberzard.

This module provides backward compatibility with the original registry API
while delegating to the unified registry implementation.

For new code, prefer importing from cyberzard.tools.unified:
    from cyberzard.tools.unified import get_registry, register_tool, TOOL_REGISTRY
"""

from typing import Any, Callable, Dict, List, Optional

# Import from unified registry
from .unified import (
    TOOL_REGISTRY,
    PermissionLevel,
    RegisteredTool,
    ToolCategory,
    UnifiedToolRegistry,
    get_registry,
    register_tool,
)

__all__ = [
    "TOOL_REGISTRY",
    "register_tool",
    "execute_tool",
    "get_schema",
    "get_registry",
    "ToolCategory",
    "PermissionLevel",
]


def execute_tool(tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a registered tool.

    This function provides backward compatibility with the original API.
    It delegates to the unified registry.

    Args:
        tool_name: Name of the tool to execute
        params: Parameters to pass to the tool

    Returns:
        Tool execution result
    """
    registry = get_registry()
    result = registry.execute(tool_name, params)

    # Handle special cases for backward compatibility
    if tool_name in ["sandbox_run", "execute_remediation"]:
        if isinstance(result.get("result"), dict):
            inner = result["result"]
            if "error" in inner:
                return inner
            elif "status" in inner:
                response = inner.copy()
                if tool_name == "sandbox_run" and "returncode" in inner:
                    response["returncode"] = inner["returncode"]
                return response

    return result


def get_schema(tool_name: Optional[str] = None) -> Any:
    """Get schema for a tool or all tools.

    This function provides backward compatibility with the original API.
    The unified registry returns much more detailed schemas.

    Args:
        tool_name: Specific tool name, or None for all tools

    Returns:
        Schema dict or list of schemas
    """
    registry = get_registry()
    return registry.get_schema(tool_name)
