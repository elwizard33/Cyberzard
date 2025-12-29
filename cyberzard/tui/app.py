"""Enhanced Textual TUI application for Cyberzard.

This module provides a split-panel interface with conversation
on the left and tools/execution status on the right.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Static

from .widgets import ConversationWidget, ToolPanelWidget
from .widgets.tool_output import ToolOutputWidget

if TYPE_CHECKING:
    from ..tools.unified import UnifiedToolRegistry
    from ..agent.orchestrator import AgentOrchestrator, LocalFallbackOrchestrator


class InputBar(Horizontal):
    """Input bar at the bottom of the screen."""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $primary;
    }
    
    InputBar > Static {
        width: 4;
        height: 3;
        content-align: left middle;
    }
    
    InputBar > Input {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("❯ ")
        yield Input(placeholder="Type your message...", id="message-input")


class CyberzardApp(App):
    """Main Cyberzard TUI application with split panel layout."""

    TITLE = "Cyberzard AI Assistant"
    SUB_TITLE = "CyberPanel Security Scanner"

    CSS = """
    Screen {
        background: $background;
    }
    
    #main-container {
        width: 100%;
        height: 1fr;
    }
    
    #conversation-panel {
        width: 2fr;
        height: 100%;
        border-right: solid $primary;
    }
    
    #tool-panel {
        width: 1fr;
        height: 100%;
        min-width: 30;
    }
    
    .panel-header {
        height: 1;
        background: $primary-background;
        text-style: bold;
        text-align: center;
        padding: 0 1;
    }
    
    .status-bar {
        height: 1;
        background: $primary-darken-2;
        text-align: center;
        padding: 0 1;
    }
    
    #conversation-container {
        height: 1fr;
        padding: 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("escape", "clear_input", "Clear"),
        Binding("ctrl+l", "clear_conversation", "Clear Chat"),
        Binding("ctrl+t", "toggle_tools", "Toggle Tools"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(
        self,
        on_message: Optional[Callable[[str], Any]] = None,
        tool_registry: Optional["UnifiedToolRegistry"] = None,
        provider: str = "auto",
        *args,
        **kwargs,
    ) -> None:
        """Initialize the app.

        Args:
            on_message: Callback when user sends a message (overrides orchestrator)
            tool_registry: Registry to populate tool panel
            provider: LLM provider ('openai', 'anthropic', 'local', 'auto')
        """
        super().__init__(*args, **kwargs)
        self._on_message = on_message
        self._tool_registry = tool_registry
        self._tools_visible = True
        self._provider = provider
        self._orchestrator: Optional[Union["AgentOrchestrator", "LocalFallbackOrchestrator"]] = None
        self._tool_exec_ids: Dict[str, str] = {}  # tool_name -> exec_id mapping
        self._chat_history: List[Any] = []

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="conversation-panel"):
                yield Static("💬 Conversation", classes="panel-header")
                with Container(id="conversation-container"):
                    yield ConversationWidget(id="conversation")
            with Vertical(id="tool-panel"):
                yield ToolPanelWidget(id="tools")
        yield InputBar()
        yield Footer()

    def on_mount(self) -> None:
        """Initialize on mount."""
        # Focus the input
        self.query_one("#message-input", Input).focus()

        # Populate tools if registry provided
        if self._tool_registry is not None:
            self._populate_tools()

        # Initialize orchestrator if no custom handler
        if self._on_message is None:
            self._init_orchestrator()

        # Welcome message
        conversation = self.query_one("#conversation", ConversationWidget)
        conversation.add_system_message(
            "Welcome to Cyberzard! I'm your AI assistant for CyberPanel security."
        )
        
        if self._orchestrator is not None:
            if self._orchestrator.is_available:
                conversation.add_system_message(
                    "Type a message below to get started. Use Ctrl+L to clear the chat."
                )
            else:
                conversation.add_system_message(
                    f"⚠️ {self._orchestrator.error_message or 'Agent not available'}"
                )
                conversation.add_system_message(
                    "Running in limited local mode. Set OPENAI_API_KEY for full AI features."
                )
        else:
            conversation.add_system_message(
                "Type a message below to get started. Use Ctrl+L to clear the chat."
            )

    def _init_orchestrator(self) -> None:
        """Initialize the agent orchestrator."""
        try:
            from ..agent.orchestrator import create_orchestrator, AgentEvent
            
            self._orchestrator = create_orchestrator(
                callback=self._handle_agent_event,
                provider=self._provider,
            )
        except ImportError:
            self._orchestrator = None

    def _handle_agent_event(self, event) -> None:
        """Handle events from the agent orchestrator."""
        from ..agent.orchestrator import AgentEvent
        
        conversation = self.query_one("#conversation", ConversationWidget)
        tool_panel = self.query_one("#tools", ToolPanelWidget)

        if event.event == AgentEvent.THINKING:
            conversation.add_system_message("🤔 Thinking...")
        
        elif event.event == AgentEvent.ASSISTANT_CHUNK:
            # Stream text chunk
            conversation.stream_text(event.data)
        
        elif event.event == AgentEvent.ASSISTANT_MESSAGE:
            # Final message (if not streamed)
            if not conversation.is_streaming:
                conversation.add_assistant_message(event.data)
        
        elif event.event == AgentEvent.TOOL_START:
            # Tool call starting
            conversation.add_tool_call(event.tool_name, event.tool_args)
            tool_panel.add_execution(event.tool_name)
            self._tool_exec_ids[event.tool_name] = event.tool_name
        
        elif event.event == AgentEvent.TOOL_END:
            # Tool completed successfully
            result_str = str(event.tool_result)[:200] if event.tool_result else "Success"
            conversation.add_tool_result(event.tool_name, result_str, success=True)
            tool_panel.complete_execution(event.tool_name, success=True, result=result_str)
        
        elif event.event == AgentEvent.TOOL_ERROR:
            # Tool failed
            conversation.add_tool_result(event.tool_name, event.error or "Error", success=False)
            tool_panel.complete_execution(event.tool_name, success=False, error=event.error)
        
        elif event.event == AgentEvent.ERROR:
            conversation.add_system_message(f"❌ Error: {event.error}")
        
        elif event.event == AgentEvent.DONE:
            pass  # Could show completion indicator

    def _populate_tools(self) -> None:
        """Populate the tool panel from registry."""
        if self._tool_registry is None:
            return

        tools = self._tool_registry.list_tools()
        
        # Group by category (extract from tool names)
        categories: Dict[str, List[str]] = {
            "Scanner": [],
            "File Operations": [],
            "CyberPanel": [],
            "Network": [],
            "MCP": [],
            "Other": [],
        }

        for tool in tools:
            name = tool.get("name", "")
            # Categorize based on name patterns
            if "scan" in name.lower():
                categories["Scanner"].append(name)
            elif "file" in name.lower() or "read" in name.lower() or "write" in name.lower():
                categories["File Operations"].append(name)
            elif "cyberpanel" in name.lower() or any(
                x in name.lower()
                for x in ["website", "database", "email", "dns", "ssl", "backup", "firewall"]
            ):
                categories["CyberPanel"].append(name)
            elif "network" in name.lower() or "port" in name.lower():
                categories["Network"].append(name)
            elif "mcp" in name.lower() or "external:" in name.lower():
                categories["MCP"].append(name)
            else:
                categories["Other"].append(name)

        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}

        tool_panel = self.query_one("#tools", ToolPanelWidget)
        tool_panel.set_tools(categories)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message submission."""
        if event.input.id != "message-input":
            return

        message = event.value.strip()
        if not message:
            return

        # Clear input
        event.input.value = ""

        conversation = self.query_one("#conversation", ConversationWidget)

        # Use custom handler if provided
        if self._on_message is not None:
            conversation.add_user_message(message)
            conversation.add_system_message("Thinking...")
            
            try:
                if asyncio.iscoroutinefunction(self._on_message):
                    response = await self._on_message(message)
                else:
                    response = self._on_message(message)
                
                if response:
                    conversation.add_assistant_message(str(response))
            except Exception as e:
                conversation.add_system_message(f"Error: {e}")
            return

        # Use orchestrator
        if self._orchestrator is not None:
            try:
                # Run in background to not block UI
                self.run_worker(self._run_orchestrator(message), exclusive=True)
            except Exception as e:
                conversation.add_system_message(f"Error: {e}")
        else:
            conversation.add_user_message(message)
            conversation.add_system_message(
                "No AI provider configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
            )

    async def _run_orchestrator(self, message: str) -> None:
        """Run the orchestrator in background."""
        if self._orchestrator is None:
            return
        
        try:
            response = await self._orchestrator.run(message, self._chat_history)
            
            # Update chat history
            try:
                from langchain_core.messages import HumanMessage, AIMessage
                self._chat_history.append(HumanMessage(content=message))
                if response:
                    self._chat_history.append(AIMessage(content=response))
                # Keep history manageable
                if len(self._chat_history) > 20:
                    self._chat_history = self._chat_history[-20:]
            except ImportError:
                pass
        except Exception as e:
            conversation = self.query_one("#conversation", ConversationWidget)
            conversation.add_system_message(f"Error: {e}")

    def action_clear_input(self) -> None:
        """Clear the input field."""
        self.query_one("#message-input", Input).value = ""

    def action_clear_conversation(self) -> None:
        """Clear the conversation."""
        conversation = self.query_one("#conversation", ConversationWidget)
        conversation.clear()
        conversation.add_system_message("Conversation cleared.")

    def action_toggle_tools(self) -> None:
        """Toggle tool panel visibility."""
        tool_panel = self.query_one("#tool-panel")
        self._tools_visible = not self._tools_visible
        tool_panel.display = self._tools_visible

    def action_help(self) -> None:
        """Show help message."""
        conversation = self.query_one("#conversation", ConversationWidget)
        conversation.add_system_message(
            "**Keyboard Shortcuts:**\n"
            "• `Enter` - Send message\n"
            "• `Ctrl+L` - Clear conversation\n"
            "• `Ctrl+T` - Toggle tool panel\n"
            "• `Escape` - Clear input\n"
            "• `q` - Quit"
        )

    # Public API for external control

    def add_user_message(self, message: str) -> None:
        """Add a user message to the conversation."""
        conversation = self.query_one("#conversation", ConversationWidget)
        conversation.add_user_message(message)

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the conversation."""
        conversation = self.query_one("#conversation", ConversationWidget)
        conversation.add_assistant_message(message)

    def add_tool_result(self, tool_name: str, result: str) -> None:
        """Add a tool result to the conversation."""
        conversation = self.query_one("#conversation", ConversationWidget)
        conversation.add_tool_result(tool_name, result)

    def start_tool_execution(self, tool_name: str) -> None:
        """Track start of tool execution."""
        tool_panel = self.query_one("#tools", ToolPanelWidget)
        tool_panel.add_execution(tool_name)

    def complete_tool_execution(
        self,
        tool_name: str,
        success: bool = True,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Track completion of tool execution."""
        tool_panel = self.query_one("#tools", ToolPanelWidget)
        tool_panel.complete_execution(tool_name, success, result, error)


def run_tui(
    on_message: Optional[Callable[[str], Any]] = None,
    tool_registry: Optional["UnifiedToolRegistry"] = None,
    provider: str = "auto",
) -> None:
    """Run the Cyberzard TUI.

    Args:
        on_message: Callback when user sends a message (overrides AI agent)
        tool_registry: Registry to populate tool panel
        provider: LLM provider ('openai', 'anthropic', 'local', 'auto')
    """
    app = CyberzardApp(
        on_message=on_message,
        tool_registry=tool_registry,
        provider=provider,
    )
    app.run()
