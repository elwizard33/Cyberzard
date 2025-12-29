"""Tool execution display widget for real-time tool tracking.

This widget shows a DataTable-based display of tool executions
with real-time status updates, durations, and result previews.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static


class ExecutionStatus(str, Enum):
    """Status of a tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class ToolExecutionRecord:
    """Record of a single tool execution."""

    exec_id: str
    tool_name: str
    args: Dict[str, Any]
    status: ExecutionStatus = ExecutionStatus.RUNNING
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: Optional[float] = None


class ToolOutputWidget(DataTable):
    """DataTable-based widget showing real-time tool execution status.

    Displays tool executions with columns for Tool name, Status,
    Duration, and a truncated preview of arguments/results.
    Supports real-time updates as tools execute.
    """

    DEFAULT_CSS = """
    ToolOutputWidget {
        background: $surface;
        border: solid $primary;
        height: 100%;
        scrollbar-gutter: stable;
    }
    
    ToolOutputWidget:focus {
        border: solid $accent;
    }
    
    ToolOutputWidget > .datatable--header {
        background: $primary-background;
    }
    
    ToolOutputWidget > .datatable--cursor {
        background: $primary-lighten-2;
    }
    """

    def __init__(
        self,
        *args,
        max_history: int = 50,
        **kwargs,
    ) -> None:
        """Initialize the tool output widget.

        Args:
            max_history: Maximum number of executions to keep
        """
        super().__init__(*args, **kwargs)
        self._executions: Dict[str, ToolExecutionRecord] = {}
        self._row_keys: Dict[str, Any] = {}  # exec_id -> row_key
        self._max_history = max_history
        self._execution_order: List[str] = []  # Track order for trimming

    def on_mount(self) -> None:
        """Set up table columns on mount."""
        self.add_columns("Tool", "Status", "Duration", "Preview")
        self.cursor_type = "row"
        self.zebra_stripes = True

    def start_execution(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start tracking a new tool execution.

        Args:
            tool_name: Name of the tool
            args: Tool arguments

        Returns:
            Execution ID for later updates
        """
        exec_id = str(uuid.uuid4())[:8]  # Short ID
        args = args or {}

        record = ToolExecutionRecord(
            exec_id=exec_id,
            tool_name=tool_name,
            args=args,
            status=ExecutionStatus.RUNNING,
        )
        self._executions[exec_id] = record
        self._execution_order.append(exec_id)

        # Format the args preview
        args_preview = self._format_preview(args)

        # Add row to table
        row_key = self.add_row(
            tool_name,
            self._format_status(ExecutionStatus.RUNNING),
            "-",
            args_preview,
            key=exec_id,
        )
        self._row_keys[exec_id] = row_key

        # Scroll to bottom
        self.scroll_end()

        # Trim old executions if needed
        self._trim_history()

        return exec_id

    def complete_execution(
        self,
        exec_id: str,
        result: Any = None,
        duration: Optional[float] = None,
    ) -> None:
        """Mark an execution as successfully completed.

        Args:
            exec_id: Execution ID from start_execution
            result: Tool result
            duration: Execution duration in seconds (auto-calculated if None)
        """
        if exec_id not in self._executions:
            return

        record = self._executions[exec_id]
        record.status = ExecutionStatus.SUCCESS
        record.completed_at = datetime.now()
        record.result = result

        if duration is not None:
            record.duration = duration
        else:
            record.duration = (
                record.completed_at - record.started_at
            ).total_seconds()

        # Update table row
        self._update_row(exec_id)

    def fail_execution(
        self,
        exec_id: str,
        error: str,
        duration: Optional[float] = None,
    ) -> None:
        """Mark an execution as failed.

        Args:
            exec_id: Execution ID from start_execution
            error: Error message
            duration: Execution duration in seconds (auto-calculated if None)
        """
        if exec_id not in self._executions:
            return

        record = self._executions[exec_id]
        record.status = ExecutionStatus.FAILED
        record.completed_at = datetime.now()
        record.error = error

        if duration is not None:
            record.duration = duration
        else:
            record.duration = (
                record.completed_at - record.started_at
            ).total_seconds()

        # Update table row
        self._update_row(exec_id)

    def _update_row(self, exec_id: str) -> None:
        """Update a row with current execution data."""
        record = self._executions[exec_id]
        row_key = self._row_keys.get(exec_id)
        if row_key is None:
            return

        # Update status cell
        self.update_cell(row_key, "Status", self._format_status(record.status))

        # Update duration cell
        if record.duration is not None:
            duration_str = self._format_duration(record.duration)
            self.update_cell(row_key, "Duration", duration_str)

        # Update preview cell with result or error
        if record.status == ExecutionStatus.SUCCESS and record.result:
            preview = self._format_preview(record.result)
            self.update_cell(row_key, "Preview", preview)
        elif record.status == ExecutionStatus.FAILED and record.error:
            preview = Text(f"❌ {record.error[:40]}...", style="red")
            self.update_cell(row_key, "Preview", preview)

    def _format_status(self, status: ExecutionStatus) -> Text:
        """Format status with appropriate styling."""
        if status == ExecutionStatus.PENDING:
            return Text("⏸ Pending", style="dim")
        elif status == ExecutionStatus.RUNNING:
            return Text("⏳ Running", style="yellow bold")
        elif status == ExecutionStatus.SUCCESS:
            return Text("✓ Done", style="green bold")
        else:  # FAILED
            return Text("✗ Failed", style="red bold")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 0.1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"

    def _format_preview(self, data: Any) -> str:
        """Format data as a truncated preview."""
        if data is None:
            return "-"
        
        if isinstance(data, dict):
            # Format dict as key=value pairs
            parts = [f"{k}={v!r}" for k, v in list(data.items())[:3]]
            preview = ", ".join(parts)
        elif isinstance(data, (list, tuple)):
            preview = str(data[:3]) + ("..." if len(data) > 3 else "")
        else:
            preview = str(data)

        # Truncate to 50 chars
        if len(preview) > 50:
            preview = preview[:47] + "..."
        return preview

    def _trim_history(self) -> None:
        """Remove old executions to stay under max_history."""
        while len(self._execution_order) > self._max_history:
            old_id = self._execution_order.pop(0)
            
            # Remove from table
            row_key = self._row_keys.pop(old_id, None)
            if row_key is not None:
                try:
                    self.remove_row(row_key)
                except Exception:
                    pass  # Row may already be gone
            
            # Remove from records
            self._executions.pop(old_id, None)

    def clear_history(self) -> None:
        """Clear all execution history."""
        self._executions.clear()
        self._row_keys.clear()
        self._execution_order.clear()
        self.clear()
        # Re-add columns after clear
        self.add_columns("Tool", "Status", "Duration", "Preview")

    def get_execution(self, exec_id: str) -> Optional[ToolExecutionRecord]:
        """Get an execution record by ID.

        Args:
            exec_id: Execution ID

        Returns:
            Execution record or None if not found
        """
        return self._executions.get(exec_id)

    @property
    def running_count(self) -> int:
        """Get count of currently running executions."""
        return sum(
            1 for e in self._executions.values()
            if e.status == ExecutionStatus.RUNNING
        )

    @property
    def total_count(self) -> int:
        """Get total execution count."""
        return len(self._executions)


class ToolOutputPanel(Vertical):
    """Panel combining header and tool output widget."""

    DEFAULT_CSS = """
    ToolOutputPanel {
        width: 100%;
        height: 100%;
    }
    
    ToolOutputPanel > Static {
        height: 1;
        background: $primary-background;
        text-style: bold;
        text-align: center;
    }
    
    ToolOutputPanel > ToolOutputWidget {
        height: 1fr;
    }
    """

    def __init__(self, *args, title: str = "Tool Executions", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._title = title

    def compose(self) -> ComposeResult:
        yield Static(f"🔧 {self._title}")
        yield ToolOutputWidget(id="tool-output")

    def start_execution(
        self,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start tracking a tool execution."""
        widget = self.query_one("#tool-output", ToolOutputWidget)
        return widget.start_execution(tool_name, args)

    def complete_execution(
        self,
        exec_id: str,
        result: Any = None,
        duration: Optional[float] = None,
    ) -> None:
        """Mark execution as complete."""
        widget = self.query_one("#tool-output", ToolOutputWidget)
        widget.complete_execution(exec_id, result, duration)

    def fail_execution(
        self,
        exec_id: str,
        error: str,
        duration: Optional[float] = None,
    ) -> None:
        """Mark execution as failed."""
        widget = self.query_one("#tool-output", ToolOutputWidget)
        widget.fail_execution(exec_id, error, duration)

    def clear_history(self) -> None:
        """Clear all history."""
        widget = self.query_one("#tool-output", ToolOutputWidget)
        widget.clear_history()
