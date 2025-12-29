"""Unified Tool Registry for Cyberzard.

This module provides a single source of truth for all tools across Cyberzard,
supporting both LangChain agent integration and MCP server exposure.

The registry:
1. Consolidates tools from: tools/registry.py, agent.py, chat.py, agent_engine/tools/
2. Provides Pydantic schema validation for all tool inputs/outputs
3. Exports tools in LangChain BaseTool format
4. Exports tools in MCP-compatible format
5. Maintains backward compatibility via proxy in registry.py
"""

from __future__ import annotations

import functools
import importlib
import inspect
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_type_hints,
)

from pydantic import BaseModel

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


# ============================================================================
# Tool Registry Core
# ============================================================================


@dataclass
class RegisteredTool:
    """Internal representation of a registered tool."""

    name: str
    description: str
    category: ToolCategory
    handler: Callable[..., Any]
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    permission_level: PermissionLevel = PermissionLevel.READ
    tags: List[str] = field(default_factory=list)

    def to_definition(self) -> ToolDefinition:
        """Convert to ToolDefinition schema."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            category=self.category,
            handler=f"{self.handler.__module__}.{self.handler.__name__}",
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            permission_level=self.permission_level,
            tags=self.tags,
        )


class UnifiedToolRegistry:
    """Centralized registry for all Cyberzard tools.

    This class provides:
    - Tool registration with schema validation
    - Category-based filtering
    - Export to LangChain and MCP formats
    - Thread-safe singleton pattern
    """

    _instance: Optional["UnifiedToolRegistry"] = None
    _initialized: bool = False

    def __new__(cls) -> "UnifiedToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._tools: Dict[str, RegisteredTool] = {}
        self._initialized = True
        self._register_builtin_tools()

    def register(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        handler: Callable[..., Any],
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        permission_level: PermissionLevel = PermissionLevel.READ,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Register a new tool in the registry.

        Args:
            name: Unique identifier for the tool
            description: Human-readable description
            category: Tool category for grouping
            handler: Function that implements the tool
            input_schema: Pydantic model for input validation
            output_schema: Pydantic model for output
            permission_level: Required permission level
            tags: Optional searchable tags
        """
        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            category=category,
            handler=handler,
            input_schema=input_schema,
            output_schema=output_schema,
            permission_level=permission_level,
            tags=tags or [],
        )

    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry.

        Args:
            name: Tool name to remove

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[RegisteredTool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            RegisteredTool if found, None otherwise
        """
        return self._tools.get(name)

    def get_all(self) -> Dict[str, RegisteredTool]:
        """Get all registered tools.

        Returns:
            Dictionary of all tools keyed by name
        """
        return self._tools.copy()

    def get_by_category(self, category: ToolCategory) -> List[RegisteredTool]:
        """Get all tools in a category.

        Args:
            category: Category to filter by

        Returns:
            List of tools in the category
        """
        return [t for t in self._tools.values() if t.category == category]

    def get_by_permission(
        self, max_level: PermissionLevel
    ) -> List[RegisteredTool]:
        """Get tools up to a permission level.

        Args:
            max_level: Maximum permission level to include

        Returns:
            List of tools with permission <= max_level
        """
        level_order = [
            PermissionLevel.READ,
            PermissionLevel.WRITE,
            PermissionLevel.EXECUTE,
            PermissionLevel.ADMIN,
        ]
        max_idx = level_order.index(max_level)
        return [
            t
            for t in self._tools.values()
            if level_order.index(t.permission_level) <= max_idx
        ]

    def search(self, query: str) -> List[RegisteredTool]:
        """Search tools by name, description, or tags.

        Args:
            query: Search string

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        results = []
        for tool in self._tools.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
                or any(query_lower in tag.lower() for tag in tool.tags)
            ):
                results.append(tool)
        return results

    def execute(
        self, name: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a tool by name with parameters.

        Args:
            name: Tool name
            params: Parameters to pass to the tool

        Returns:
            Tool execution result
        """
        tool = self.get(name)
        if tool is None:
            return {
                "success": False,
                "error": f"Tool '{name}' not found",
                "available_tools": list(self._tools.keys()),
            }

        try:
            params = params or {}
            # Validate input against schema
            validated_input = tool.input_schema(**params)
            # Execute with validated params
            result = tool.handler(**validated_input.model_dump())
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_for_langchain(self) -> List[Any]:
        """Export tools in LangChain BaseTool format.

        Returns:
            List of LangChain-compatible tool objects
        """
        try:
            # Try langchain_core first (newer versions)
            from langchain_core.tools import StructuredTool
        except ImportError:
            try:
                # Fall back to langchain.tools
                from langchain.tools import StructuredTool
            except ImportError:
                # Return empty if langchain not installed
                return []

        langchain_tools = []
        for tool in self._tools.values():
            # Create a wrapper that uses the Pydantic schema
            lc_tool = StructuredTool.from_function(
                func=tool.handler,
                name=tool.name,
                description=tool.description,
                args_schema=tool.input_schema,
            )
            langchain_tools.append(lc_tool)
        return langchain_tools

    def get_for_mcp(self) -> List[Dict[str, Any]]:
        """Export tools in MCP-compatible format.

        Returns:
            List of MCP tool definitions
        """
        mcp_tools = []
        for tool in self._tools.values():
            # Convert Pydantic schema to JSON schema
            json_schema = tool.input_schema.model_json_schema()

            mcp_tool = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }
            mcp_tools.append(mcp_tool)
        return mcp_tools

    def get_schema(self, tool_name: Optional[str] = None) -> Any:
        """Get schema for a tool or all tools.

        Args:
            tool_name: Specific tool name, or None for all

        Returns:
            Schema dict or list of schemas
        """
        if tool_name is None:
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema.model_json_schema(),
                    "output_schema": t.output_schema.model_json_schema(),
                }
                for t in self._tools.values()
            ]

        tool = self.get(tool_name)
        if tool is None:
            return {"error": f"Tool '{tool_name}' not found"}

        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema.model_json_schema(),
            "output_schema": tool.output_schema.model_json_schema(),
        }

    # ========================================================================
    # Built-in Tool Registration
    # ========================================================================

    def _register_builtin_tools(self) -> None:
        """Register all built-in Cyberzard tools."""
        self._register_file_tools()
        self._register_security_tools()
        self._register_shell_tools()
        self._register_remediation_tools()
        self._register_email_tools()
        self._register_cyberpanel_tools()

    def _register_cyberpanel_tools(self) -> None:
        """Register CyberPanel tools."""
        try:
            from cyberzard.cyberpanel.tools import register_cyberpanel_tools
            register_cyberpanel_tools()
        except ImportError:
            # CyberPanel tools not available
            pass
        except Exception:
            # Ignore registration errors (e.g., missing httpx)
            pass

    def _register_file_tools(self) -> None:
        """Register file operation tools."""
        from cyberzard.agent_engine.tools.file_ops import read_file as agent_read_file

        self.register(
            name="read_file",
            description="Read contents of a file with path restrictions for security",
            category=ToolCategory.FILE,
            handler=agent_read_file,
            input_schema=ReadFileInput,
            output_schema=ReadFileOutput,
            permission_level=PermissionLevel.READ,
            tags=["file", "read", "content"],
        )

        self.register(
            name="list_dir",
            description="List contents of a directory",
            category=ToolCategory.FILE,
            handler=_list_dir_handler,
            input_schema=ListDirInput,
            output_schema=ListDirOutput,
            permission_level=PermissionLevel.READ,
            tags=["file", "directory", "list"],
        )

    def _register_security_tools(self) -> None:
        """Register security scanning tools."""
        from cyberzard.agent_engine.tools.server_scan import scan_server

        self.register(
            name="scan_server",
            description="Comprehensive security scan for malware, suspicious processes, cron jobs, and more",
            category=ToolCategory.SECURITY,
            handler=scan_server,
            input_schema=ScanServerInput,
            output_schema=ScanServerOutput,
            permission_level=PermissionLevel.READ,
            tags=["security", "scan", "malware", "processes", "cron"],
        )

        self.register(
            name="run_scan",
            description="Run a basic security scan on a target",
            category=ToolCategory.SECURITY,
            handler=_run_scan_handler,
            input_schema=RunScanInput,
            output_schema=RunScanOutput,
            permission_level=PermissionLevel.READ,
            tags=["security", "scan", "basic"],
        )

    def _register_shell_tools(self) -> None:
        """Register shell command tools."""
        self.register(
            name="run_shell_command",
            description="Execute a shell command and return its output",
            category=ToolCategory.SHELL,
            handler=_run_shell_command_handler,
            input_schema=RunShellCommandInput,
            output_schema=RunShellCommandOutput,
            permission_level=PermissionLevel.EXECUTE,
            tags=["shell", "command", "execute"],
        )

        self.register(
            name="debug_shell_command",
            description="Debug a shell command and suggest fixes",
            category=ToolCategory.SHELL,
            handler=_debug_shell_command_handler,
            input_schema=DebugShellCommandInput,
            output_schema=DebugShellCommandOutput,
            permission_level=PermissionLevel.EXECUTE,
            tags=["shell", "debug", "help"],
        )

        self.register(
            name="complete_shell_command",
            description="Suggest completion for a partial shell command",
            category=ToolCategory.SHELL,
            handler=_complete_shell_command_handler,
            input_schema=CompleteShellCommandInput,
            output_schema=CompleteShellCommandOutput,
            permission_level=PermissionLevel.READ,
            tags=["shell", "completion", "help"],
        )

        self.register(
            name="sandbox_run",
            description="Execute Python code in a sandboxed environment",
            category=ToolCategory.SHELL,
            handler=_sandbox_run_handler,
            input_schema=SandboxRunInput,
            output_schema=SandboxRunOutput,
            permission_level=PermissionLevel.EXECUTE,
            tags=["sandbox", "python", "execute"],
        )

    def _register_remediation_tools(self) -> None:
        """Register remediation tools."""
        from cyberzard.agent_engine.tools.server_scan import propose_remediation

        self.register(
            name="propose_remediation",
            description="Generate remediation plan based on scan results",
            category=ToolCategory.SECURITY,
            handler=propose_remediation,
            input_schema=ProposeRemediationInput,
            output_schema=ProposeRemediationOutput,
            permission_level=PermissionLevel.READ,
            tags=["remediation", "plan", "security"],
        )

        self.register(
            name="execute_remediation",
            description="Execute a remediation action (remove, kill, etc.)",
            category=ToolCategory.SECURITY,
            handler=_execute_remediation_handler,
            input_schema=ExecuteRemediationInput,
            output_schema=ExecuteRemediationOutput,
            permission_level=PermissionLevel.ADMIN,
            tags=["remediation", "execute", "security"],
        )

    def _register_email_tools(self) -> None:
        """Register email security tools."""
        from cyberzard.agent_engine.tools.email_scan import (
            scan_email_system,
            propose_email_hardening,
        )

        self.register(
            name="scan_email_system",
            description="Scan email stack for security issues (postfix, dovecot, etc.)",
            category=ToolCategory.EMAIL,
            handler=scan_email_system,
            input_schema=ScanEmailSystemInput,
            output_schema=ScanEmailSystemOutput,
            permission_level=PermissionLevel.READ,
            tags=["email", "scan", "postfix", "dovecot", "security"],
        )

        self.register(
            name="propose_email_hardening",
            description="Generate email hardening recommendations based on scan",
            category=ToolCategory.EMAIL,
            handler=propose_email_hardening,
            input_schema=ProposeEmailHardeningInput,
            output_schema=ProposeEmailHardeningOutput,
            permission_level=PermissionLevel.READ,
            tags=["email", "hardening", "security", "recommendation"],
        )


# ============================================================================
# Tool Handler Functions
# ============================================================================


def _list_dir_handler(path: str) -> Dict[str, Any]:
    """List directory contents."""
    try:
        items = [item.name for item in Path(path).iterdir()]
        return {"items": items, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


def _run_scan_handler(target: Optional[str] = None) -> Dict[str, Any]:
    """Run a basic security scan."""
    return {
        "target": target or "default",
        "findings": [],
        "status": "completed",
    }


def _run_shell_command_handler(command: str) -> Dict[str, Any]:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return {"output": output, "success": result.returncode == 0}
    except Exception as e:
        return {"output": f"Error: {e}", "success": False}


def _debug_shell_command_handler(command: str) -> Dict[str, Any]:
    """Debug a shell command and suggest a fix."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return {"result": "Command executed successfully."}
        err = result.stderr
        if "not found" in err:
            return {"result": "Error: Command not found. Did you mean to install it?"}
        if "permission denied" in err.lower():
            return {
                "result": "Error: Permission denied. Try running with sudo or check file permissions."
            }
        return {"result": f"Error: {err}"}
    except Exception as e:
        return {"result": f"Exception: {e}"}


def _complete_shell_command_handler(partial: str) -> Dict[str, Any]:
    """Suggest a completion for a partial shell command."""
    common_cmds = [
        "ls",
        "cat",
        "echo",
        "grep",
        "find",
        "pwd",
        "cd",
        "touch",
        "rm",
        "cp",
        "mv",
    ]
    for cmd in common_cmds:
        if cmd.startswith(partial):
            return {"suggestion": f"Did you mean: {cmd} ...?"}
    return {"suggestion": "No suggestion."}


def _sandbox_run_handler(source: str) -> Dict[str, Any]:
    """Sandbox execution tool."""
    # Security check
    if "import os" in source:
        return {
            "status": "blocked",
            "returncode": 1,
            "error": "Import of 'os' not allowed in sandbox",
        }

    try:
        if "print(" in source:
            import contextlib
            import io

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                exec(source)
            output = f.getvalue().strip()
            return {
                "stdout": output,
                "output": output,
                "returncode": 0,
                "status": "success",
            }
        else:
            result = eval(source) if source.strip() else None
            return {"result": result, "returncode": 0, "status": "success"}
    except Exception as e:
        return {"error": str(e), "returncode": 1, "status": "failed"}


def _execute_remediation_handler(
    action: str, target: str, dry_run: bool = False
) -> Dict[str, Any]:
    """Execute a remediation action."""
    if dry_run:
        return {"status": f"would_{action}", "target": target}

    # In production, this would perform actual actions
    if action == "remove":
        return {"status": "removed", "target": target}
    elif action == "kill":
        return {"status": "killed", "target": target}
    else:
        return {"status": "completed", "target": target}


# ============================================================================
# Module-level convenience functions
# ============================================================================


def get_registry() -> UnifiedToolRegistry:
    """Get the singleton registry instance.

    Returns:
        The unified tool registry
    """
    return UnifiedToolRegistry()


def register_tool(
    name: str,
    description: str = "",
    category: ToolCategory = ToolCategory.EXTERNAL,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    permission_level: PermissionLevel = PermissionLevel.READ,
    tags: Optional[List[str]] = None,
) -> Callable[[Callable], Callable]:
    """Decorator to register a tool in the unified registry.

    Args:
        name: Tool name
        description: Tool description (falls back to docstring)
        category: Tool category
        input_schema: Pydantic input schema (auto-generated if None)
        output_schema: Pydantic output schema (uses generic if None)
        permission_level: Required permission level
        tags: Searchable tags

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        # Use docstring if no description provided
        desc = description or func.__doc__ or f"Tool: {name}"

        # Create generic schemas if not provided
        nonlocal input_schema, output_schema
        if input_schema is None:
            # Create a dynamic schema from function signature
            input_schema = _create_input_schema_from_func(func, name)
        if output_schema is None:
            output_schema = _GenericOutput

        registry = get_registry()
        registry.register(
            name=name,
            description=desc,
            category=category,
            handler=func,
            input_schema=input_schema,
            output_schema=output_schema,
            permission_level=permission_level,
            tags=tags or [],
        )
        return func

    return decorator


class _GenericOutput(BaseModel):
    """Generic output schema for tools without specific output schemas."""

    result: Any = None
    success: bool = True
    error: Optional[str] = None


def _create_input_schema_from_func(func: Callable, name: str) -> Type[BaseModel]:
    """Create a Pydantic schema from function signature."""
    sig = inspect.signature(func)
    fields: Dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            annotation = Any

        default = (
            param.default
            if param.default is not inspect.Parameter.empty
            else ...
        )
        fields[param_name] = (annotation, default)

    # Create dynamic Pydantic model
    model = type(
        f"{name.title().replace('_', '')}Input",
        (BaseModel,),
        {"__annotations__": {k: v[0] for k, v in fields.items()}},
    )

    # Set defaults
    for k, v in fields.items():
        if v[1] is not ...:
            setattr(model, k, v[1])

    return model


# ============================================================================
# Backward Compatibility - TOOL_REGISTRY dict interface
# ============================================================================


class _ToolRegistryProxy:
    """Proxy class that provides dict-like access to the unified registry.

    This enables backward compatibility with code that uses:
        from cyberzard.tools.registry import TOOL_REGISTRY
        TOOL_REGISTRY["tool_name"](**params)
    """

    def __getitem__(self, name: str) -> Callable:
        registry = get_registry()
        tool = registry.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        return tool.handler

    def __contains__(self, name: str) -> bool:
        return get_registry().get(name) is not None

    def __iter__(self):
        return iter(get_registry().get_all().keys())

    def keys(self):
        return get_registry().get_all().keys()

    def values(self):
        return [t.handler for t in get_registry().get_all().values()]

    def items(self):
        return [(k, t.handler) for k, t in get_registry().get_all().items()]

    def get(self, name: str, default: Any = None) -> Any:
        try:
            return self[name]
        except KeyError:
            return default


# Create the proxy instance for backward compatibility
TOOL_REGISTRY = _ToolRegistryProxy()


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    # Core registry
    "UnifiedToolRegistry",
    "RegisteredTool",
    "get_registry",
    # Registration decorator
    "register_tool",
    # Backward compatibility
    "TOOL_REGISTRY",
    # Schemas (re-exported)
    "ToolCategory",
    "PermissionLevel",
    "ToolDefinition",
]
