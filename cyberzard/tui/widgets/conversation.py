"""Conversation widget for displaying chat messages.

This widget displays the conversation history with the AI agent,
showing user messages, AI responses, and tool execution results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from textual.widgets import RichLog


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"


@dataclass
class Message:
    """A single message in the conversation."""

    role: MessageRole
    content: str
    timestamp: datetime
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    success: Optional[bool] = None


class ConversationWidget(RichLog):
    """Widget for displaying conversation history with streaming support.

    This widget extends RichLog to provide a scrollable conversation
    display with formatted messages from the user, AI, and tools.
    Supports real-time streaming of assistant responses.
    """

    DEFAULT_CSS = """
    ConversationWidget {
        background: $surface;
        border: solid $primary;
        scrollbar-gutter: stable;
        overflow-y: auto;
        padding: 0 1;
    }
    
    ConversationWidget:focus {
        border: solid $accent;
    }
    """

    def __init__(
        self,
        *args,
        max_messages: int = 1000,
        **kwargs,
    ) -> None:
        super().__init__(*args, markup=True, highlight=True, wrap=True, **kwargs)
        self._messages: List[Message] = []
        self._max_messages = max_messages
        self._streaming_buffer: str = ""
        self._is_streaming: bool = False

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation.

        Args:
            content: Message content
        """
        message = Message(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now(),
        )
        self._add_message(message)
        self._render_message(message)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation.

        Args:
            content: Message content (supports markdown)
        """
        # End any active streaming
        if self._is_streaming:
            self._end_stream()
        
        message = Message(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
        )
        self._add_message(message)
        self._render_message(message)

    def add_tool_call(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> None:
        """Add a tool call indicator to the conversation.

        Shows that a tool is being called with optional arguments.

        Args:
            tool_name: Name of the tool being called
            args: Tool arguments (optional)
        """
        message = Message(
            role=MessageRole.TOOL_CALL,
            content=tool_name,
            timestamp=datetime.now(),
            tool_name=tool_name,
            tool_args=args,
        )
        self._add_message(message)
        self._render_message(message)

    def add_tool_result(
        self,
        tool_name: str,
        result: str,
        success: bool = True,
    ) -> None:
        """Add a tool execution result to the conversation.

        Args:
            tool_name: Name of the tool
            result: Tool execution result
            success: Whether the tool succeeded
        """
        message = Message(
            role=MessageRole.TOOL_RESULT,
            content=result,
            timestamp=datetime.now(),
            tool_name=tool_name,
            tool_result=result,
            success=success,
        )
        self._add_message(message)
        self._render_message(message)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation.

        Args:
            content: System message content
        """
        message = Message(
            role=MessageRole.SYSTEM,
            content=content,
            timestamp=datetime.now(),
        )
        self._add_message(message)
        self._render_message(message)

    def stream_text(self, chunk: str) -> None:
        """Stream text incrementally to the conversation.

        Use this for streaming assistant responses. Call with chunks
        as they arrive, and finish with add_assistant_message() or
        end_stream() when complete.

        Args:
            chunk: Text chunk to append
        """
        if not self._is_streaming:
            # Start new streaming session
            self._is_streaming = True
            self._streaming_buffer = ""
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.write(
                Text.from_markup(f"[dim]{timestamp}[/] [bold green]Cyberzard:[/]")
            )
        
        # Append to buffer and write chunk
        self._streaming_buffer += chunk
        # Write without newline for continuous streaming
        self.write(Text(chunk), expand=True, shrink=False)

    def _end_stream(self) -> None:
        """End the current streaming session."""
        if self._is_streaming:
            self._is_streaming = False
            # Store the complete message
            if self._streaming_buffer:
                message = Message(
                    role=MessageRole.ASSISTANT,
                    content=self._streaming_buffer,
                    timestamp=datetime.now(),
                )
                self._add_message(message)
            self._streaming_buffer = ""
            # Add spacing after stream
            self.write("")

    def _add_message(self, message: Message) -> None:
        """Add a message to the internal list."""
        self._messages.append(message)
        # Trim old messages if needed
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]

    def _render_message(self, message: Message) -> None:
        """Render a message to the log."""
        timestamp = message.timestamp.strftime("%H:%M:%S")

        if message.role == MessageRole.USER:
            # User messages in cyan
            self.write(
                Text.from_markup(
                    f"[dim]{timestamp}[/] [bold cyan]You:[/] {message.content}"
                )
            )
        elif message.role == MessageRole.ASSISTANT:
            # Assistant messages with markdown rendering
            self.write(
                Text.from_markup(f"[dim]{timestamp}[/] [bold green]Cyberzard:[/]")
            )
            try:
                self.write(Markdown(message.content))
            except Exception:
                self.write(Text(message.content))
        elif message.role == MessageRole.TOOL_CALL:
            # Tool call indicator with spinner
            args_str = ""
            if message.tool_args:
                # Format args nicely
                args_str = ", ".join(f"{k}={v!r}" for k, v in message.tool_args.items())
                if len(args_str) > 60:
                    args_str = args_str[:57] + "..."
                args_str = f"({args_str})"
            
            self.write(
                Text.from_markup(
                    f"[dim]{timestamp}[/] [bold yellow]⚙ Calling[/] "
                    f"[cyan]{message.tool_name}[/][dim]{args_str}[/] [yellow]...[/]"
                )
            )
        elif message.role == MessageRole.TOOL_RESULT:
            # Tool result with success/failure indicator
            icon = "✓" if message.success else "✗"
            color = "green" if message.success else "red"
            status = "succeeded" if message.success else "failed"
            
            self.write(
                Text.from_markup(
                    f"[dim]{timestamp}[/] [{color}]{icon}[/] "
                    f"[bold]{message.tool_name}[/] {status}"
                )
            )
            
            # Show result (truncated if too long)
            if message.tool_result:
                result_preview = message.tool_result
                if len(result_preview) > 200:
                    result_preview = result_preview[:197] + "..."
                self.write(
                    Text.from_markup(f"  [dim]└─ {result_preview}[/]")
                )
        elif message.role == MessageRole.SYSTEM:
            # System messages in magenta
            self.write(
                Text.from_markup(
                    f"[dim]{timestamp}[/] [bold magenta]System:[/] {message.content}"
                )
            )

        # Add spacing
        self.write("")

    def clear_conversation(self) -> None:
        """Clear all messages from the conversation."""
        self._messages.clear()
        self._streaming_buffer = ""
        self._is_streaming = False
        self.clear()

    # Alias for backward compatibility
    def clear(self) -> None:
        """Clear the log display."""
        super().clear()

    @property
    def messages(self) -> List[Message]:
        """Get all messages in the conversation."""
        return self._messages.copy()

    @property
    def message_count(self) -> int:
        """Get the number of messages."""
        return len(self._messages)

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._is_streaming
