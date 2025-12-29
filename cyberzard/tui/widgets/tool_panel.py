"""Tool panel widget for displaying available tools and execution status.

This widget shows a tree of available tool categories and a table
of recent tool executions with their status.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static, Tree
from textual.widgets.tree import TreeNode


class ToolStatus(str, Enum):
    """Status of a tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolExecution:
    """Record of a tool execution."""

    tool_name: str
    status: ToolStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


class ToolTreeWidget(Tree):
    """Tree widget showing available tools by category."""

    DEFAULT_CSS = """
    ToolTreeWidget {
        background: $surface;
        border: solid $primary;
        height: 1fr;
        scrollbar-gutter: stable;
    }
    
    ToolTreeWidget:focus {
        border: solid $accent;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__("🔧 Tools", *args, **kwargs)
        self._tools_by_category: Dict[str, List[str]] = {}

    def set_tools(self, tools_by_category: Dict[str, List[str]]) -> None:
        """Set the tools to display.

        Args:
            tools_by_category: Dict mapping category names to tool lists
        """
        self._tools_by_category = tools_by_category
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        """Rebuild the tree from the tools data."""
        self.clear()

        for category, tools in sorted(self._tools_by_category.items()):
            # Category node with folder emoji
            category_node = self.root.add(
                f"📁 {category} ({len(tools)})",
                expand=False,
            )
            # Add tools under category
            for tool in sorted(tools):
                category_node.add_leaf(f"🔨 {tool}")

    def add_category(self, category: str, tools: List[str]) -> None:
        """Add a category with tools.

        Args:
            category: Category name
            tools: List of tool names
        """
        self._tools_by_category[category] = tools
        self._rebuild_tree()

    def expand_category(self, category: str) -> None:
        """Expand a category node."""
        for node in self.root.children:
            if category.lower() in str(node.label).lower():
                node.expand()
                break


class ToolExecutionTable(DataTable):
    """Table showing recent tool executions."""

    DEFAULT_CSS = """
    ToolExecutionTable {
        background: $surface;
        border: solid $primary;
        height: 1fr;
        scrollbar-gutter: stable;
    }
    
    ToolExecutionTable:focus {
        border: solid $accent;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._executions: List[ToolExecution] = []
        self._max_rows = 50

    def on_mount(self) -> None:
        """Set up table columns on mount."""
        self.add_columns("Status", "Tool", "Duration", "Time")
        self.cursor_type = "row"

    def add_execution(self, execution: ToolExecution) -> None:
        """Add a tool execution to the table.

        Args:
            execution: Tool execution record
        """
        self._executions.append(execution)
        self._render_execution(execution)

        # Trim old rows
        while self.row_count > self._max_rows:
            self.remove_row(self.get_row_at(0))
            self._executions.pop(0)

    def update_execution(
        self,
        tool_name: str,
        status: ToolStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update an existing execution status.

        Args:
            tool_name: Name of the tool
            status: New status
            result: Execution result
            error: Error message if failed
        """
        # Find the execution
        for i, exec in enumerate(reversed(self._executions)):
            if exec.tool_name == tool_name and exec.status == ToolStatus.RUNNING:
                exec.status = status
                exec.completed_at = datetime.now()
                exec.result = result
                exec.error = error
                self._update_row(len(self._executions) - 1 - i, exec)
                break

    def _render_execution(self, execution: ToolExecution) -> None:
        """Render an execution to a table row."""
        status_text = self._format_status(execution.status)
        time_str = execution.started_at.strftime("%H:%M:%S")
        duration = self._format_duration(execution)

        self.add_row(status_text, execution.tool_name, duration, time_str)

    def _update_row(self, index: int, execution: ToolExecution) -> None:
        """Update an existing row."""
        status_text = self._format_status(execution.status)
        duration = self._format_duration(execution)
        time_str = execution.started_at.strftime("%H:%M:%S")

        # Get row key at index
        row_key = list(self.rows.keys())[index]
        self.update_cell(row_key, "Status", status_text)
        self.update_cell(row_key, "Duration", duration)

    def _format_status(self, status: ToolStatus) -> Text:
        """Format status with color."""
        if status == ToolStatus.PENDING:
            return Text("⏳", style="yellow")
        elif status == ToolStatus.RUNNING:
            return Text("🔄", style="cyan")
        elif status == ToolStatus.SUCCESS:
            return Text("✓", style="green")
        else:
            return Text("✗", style="red")

    def _format_duration(self, execution: ToolExecution) -> str:
        """Format execution duration."""
        if execution.completed_at is None:
            return "..."
        duration = (execution.completed_at - execution.started_at).total_seconds()
        if duration < 1:
            return f"{int(duration * 1000)}ms"
        return f"{duration:.1f}s"

    def clear_executions(self) -> None:
        """Clear all executions."""
        self._executions.clear()
        self.clear()


class ToolPanelWidget(Vertical):
    """Combined panel with tool tree and execution table."""

    DEFAULT_CSS = """
    ToolPanelWidget {
        width: 100%;
        height: 100%;
    }
    
    ToolPanelWidget > Static {
        height: 1;
        background: $primary-background;
        text-style: bold;
        text-align: center;
    }
    
    ToolPanelWidget > ToolTreeWidget {
        height: 1fr;
    }
    
    ToolPanelWidget > ToolExecutionTable {
        height: 1fr;
    }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the panel widgets."""
        yield Static("Available Tools", classes="section-header")
        yield ToolTreeWidget(id="tool-tree")
        yield Static("Recent Executions", classes="section-header")
        yield ToolExecutionTable(id="tool-executions")

    def set_tools(self, tools_by_category: Dict[str, List[str]]) -> None:
        """Set the available tools."""
        tree = self.query_one("#tool-tree", ToolTreeWidget)
        tree.set_tools(tools_by_category)

    def add_execution(self, tool_name: str) -> None:
        """Start tracking a tool execution."""
        execution = ToolExecution(
            tool_name=tool_name,
            status=ToolStatus.RUNNING,
            started_at=datetime.now(),
        )
        table = self.query_one("#tool-executions", ToolExecutionTable)
        table.add_execution(execution)

    def complete_execution(
        self,
        tool_name: str,
        success: bool = True,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Mark a tool execution as complete."""
        table = self.query_one("#tool-executions", ToolExecutionTable)
        status = ToolStatus.SUCCESS if success else ToolStatus.ERROR
        table.update_execution(tool_name, status, result, error)
