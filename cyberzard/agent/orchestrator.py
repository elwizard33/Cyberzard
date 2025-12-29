"""Agent orchestrator for connecting LangChain agents to the TUI.

This module provides the AgentOrchestrator class that handles:
- LangChain agent creation with unified tools
- Streaming callbacks for real-time TUI updates
- Tool execution with progress reporting
- Graceful fallback when API keys are missing
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# Try importing LangChain components
try:
    from langchain.agents import create_openai_tools_agent, AgentExecutor
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_core.agents import create_openai_tools_agent
        from langchain.agents import AgentExecutor
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        create_openai_tools_agent = None
        AgentExecutor = None

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    ChatPromptTemplate = None
    MessagesPlaceholder = None
    BaseCallbackHandler = None

# Import unified registry
try:
    from ..tools.unified import UnifiedToolRegistry
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False
    UnifiedToolRegistry = None

# Import model selector
try:
    from ..models import ModelSelector
    MODEL_SELECTOR_AVAILABLE = True
except ImportError:
    MODEL_SELECTOR_AVAILABLE = False
    ModelSelector = None


class AgentEvent(str, Enum):
    """Events emitted by the agent orchestrator."""

    USER_MESSAGE = "user_message"
    ASSISTANT_CHUNK = "assistant_chunk"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    TOOL_ERROR = "tool_error"
    ERROR = "error"
    THINKING = "thinking"
    DONE = "done"


@dataclass
class AgentCallback:
    """Callback data for agent events."""

    event: AgentEvent
    data: Any = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    error: Optional[str] = None
    exec_id: Optional[str] = None


# Callback handler for LangChain streaming
if BaseCallbackHandler is not None:
    class TUICallbackHandler(BaseCallbackHandler):
        """LangChain callback handler that forwards events to TUI."""

        def __init__(self, callback: Callable[[AgentCallback], None]) -> None:
            super().__init__()
            self.callback = callback
            self._current_tool: Optional[str] = None

        def on_llm_start(self, *args, **kwargs) -> None:
            self.callback(AgentCallback(event=AgentEvent.THINKING))

        def on_llm_new_token(self, token: str, **kwargs) -> None:
            self.callback(AgentCallback(
                event=AgentEvent.ASSISTANT_CHUNK,
                data=token,
            ))

        def on_llm_end(self, *args, **kwargs) -> None:
            pass  # We'll get the full message from agent output

        def on_tool_start(
            self,
            serialized: Dict[str, Any],
            input_str: str,
            **kwargs,
        ) -> None:
            tool_name = serialized.get("name", "unknown")
            self._current_tool = tool_name
            # Try to parse args from input_str
            try:
                import json
                tool_args = json.loads(input_str) if input_str.startswith("{") else {"input": input_str}
            except Exception:
                tool_args = {"input": input_str}
            
            self.callback(AgentCallback(
                event=AgentEvent.TOOL_START,
                tool_name=tool_name,
                tool_args=tool_args,
            ))

        def on_tool_end(self, output: str, **kwargs) -> None:
            self.callback(AgentCallback(
                event=AgentEvent.TOOL_END,
                tool_name=self._current_tool,
                tool_result=output,
            ))
            self._current_tool = None

        def on_tool_error(self, error: BaseException, **kwargs) -> None:
            self.callback(AgentCallback(
                event=AgentEvent.TOOL_ERROR,
                tool_name=self._current_tool,
                error=str(error),
            ))
            self._current_tool = None
else:
    TUICallbackHandler = None  # type: ignore


class AgentOrchestrator:
    """Orchestrator that connects LangChain agents to the TUI.

    Handles agent creation, tool registration, and streaming callbacks
    for real-time UI updates.
    """

    SYSTEM_PROMPT = """You are Cyberzard, an AI-powered CyberPanel security assistant.

You help system administrators:
- Scan servers for malware, miners, and security threats
- Analyze suspicious files and processes
- Manage CyberPanel websites, databases, and email
- Execute remediation plans with user approval
- Monitor system security status

Always be helpful, accurate, and security-conscious. When executing commands
or making changes, explain what you're doing and ask for confirmation when
appropriate.

Available tools allow you to scan systems, read files, manage CyberPanel
resources, and execute security operations."""

    def __init__(
        self,
        callback: Callable[[AgentCallback], None],
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            callback: Callback function for TUI events
            provider: LLM provider ('openai' or 'anthropic')
            model: Model name (defaults to provider's default)
            temperature: Model temperature
        """
        self.callback = callback
        self.provider = provider
        self.model_name = model
        self.temperature = temperature
        
        self._agent = None
        self._agent_executor = None
        self._tools = []
        self._available = False
        self._error_message: Optional[str] = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize the agent with tools."""
        # Check if LangChain is available
        if not LANGCHAIN_AVAILABLE:
            self._error_message = "LangChain not installed. Install with: pip install langchain langchain-openai"
            return

        if not REGISTRY_AVAILABLE:
            self._error_message = "Tool registry not available"
            return

        if not MODEL_SELECTOR_AVAILABLE:
            self._error_message = "Model selector not available"
            return

        try:
            # Use ModelSelector for provider validation and model creation
            selector = ModelSelector()

            # Validate provider
            valid, error = selector.validate_provider(self.provider)
            if not valid:
                self._error_message = error
                return

            # Get tools from unified registry
            registry = UnifiedToolRegistry()
            self._tools = registry.get_for_langchain()

            # Create LLM using ModelSelector
            llm = selector.create_model(
                provider=self.provider,
                model=self.model_name,
                temperature=self.temperature,
                streaming=True,
            )

            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ])

            # Create agent
            self._agent = create_openai_tools_agent(llm, self._tools, prompt)
            self._agent_executor = AgentExecutor(
                agent=self._agent,
                tools=self._tools,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=10,
            )
            self._available = True

        except Exception as e:
            self._error_message = f"Failed to initialize agent: {e}"

    @property
    def is_available(self) -> bool:
        """Check if the agent is available."""
        return self._available

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if agent is not available."""
        return self._error_message

    async def run(
        self,
        user_input: str,
        chat_history: Optional[List[BaseMessage]] = None,
    ) -> Optional[str]:
        """Run the agent with user input.

        Args:
            user_input: User's message
            chat_history: Previous chat messages

        Returns:
            Agent's final response or None if error
        """
        if not self._available:
            self.callback(AgentCallback(
                event=AgentEvent.ERROR,
                error=self._error_message or "Agent not available",
            ))
            return None

        # Notify user message
        self.callback(AgentCallback(
            event=AgentEvent.USER_MESSAGE,
            data=user_input,
        ))

        try:
            # Create callback handler
            handler = TUICallbackHandler(self.callback) if TUICallbackHandler else None
            callbacks = [handler] if handler else []

            # Run agent
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._agent_executor.invoke(
                    {
                        "input": user_input,
                        "chat_history": chat_history or [],
                    },
                    config={"callbacks": callbacks},
                )
            )

            # Extract output
            output = result.get("output", "")

            # Notify completion
            self.callback(AgentCallback(
                event=AgentEvent.ASSISTANT_MESSAGE,
                data=output,
            ))

            self.callback(AgentCallback(event=AgentEvent.DONE))

            return output

        except Exception as e:
            self.callback(AgentCallback(
                event=AgentEvent.ERROR,
                error=str(e),
            ))
            return None

    def run_sync(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
    ) -> Optional[str]:
        """Run the agent synchronously.

        Args:
            user_input: User's message
            chat_history: Previous chat messages

        Returns:
            Agent's final response or None if error
        """
        if not self._available:
            self.callback(AgentCallback(
                event=AgentEvent.ERROR,
                error=self._error_message or "Agent not available",
            ))
            return None

        # Notify user message
        self.callback(AgentCallback(
            event=AgentEvent.USER_MESSAGE,
            data=user_input,
        ))

        try:
            # Create callback handler
            handler = TUICallbackHandler(self.callback) if TUICallbackHandler else None
            callbacks = [handler] if handler else []

            # Run agent
            result = self._agent_executor.invoke(
                {
                    "input": user_input,
                    "chat_history": chat_history or [],
                },
                config={"callbacks": callbacks},
            )

            # Extract output
            output = result.get("output", "")

            # Notify completion
            self.callback(AgentCallback(
                event=AgentEvent.ASSISTANT_MESSAGE,
                data=output,
            ))

            self.callback(AgentCallback(event=AgentEvent.DONE))

            return output

        except Exception as e:
            self.callback(AgentCallback(
                event=AgentEvent.ERROR,
                error=str(e),
            ))
            return None


class LocalFallbackOrchestrator:
    """Fallback orchestrator when no API key is available.

    Uses the local MiniReasoner from the original agent.py for basic
    functionality without requiring an API key.
    """

    def __init__(self, callback: Callable[[AgentCallback], None]) -> None:
        """Initialize the fallback orchestrator."""
        self.callback = callback
        
        # Import MiniReasoner
        try:
            from ..agent import MiniReasoner
            self._reasoner = MiniReasoner(max_steps=5)
            self._available = True
        except ImportError:
            self._reasoner = None
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> Optional[str]:
        if not self._available:
            return "Local reasoner not available"
        return None

    def run_sync(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
    ) -> Optional[str]:
        """Run the local reasoner synchronously."""
        if not self._available:
            self.callback(AgentCallback(
                event=AgentEvent.ERROR,
                error="Local reasoner not available",
            ))
            return None

        self.callback(AgentCallback(
            event=AgentEvent.USER_MESSAGE,
            data=user_input,
        ))

        try:
            # Run local reasoning
            result = self._reasoner.run(user_input)

            # Report tool calls
            for output in result.get("tool_outputs", []):
                tool_name = output.get("tool", "unknown")
                self.callback(AgentCallback(
                    event=AgentEvent.TOOL_START,
                    tool_name=tool_name,
                ))
                
                if "error" in output:
                    self.callback(AgentCallback(
                        event=AgentEvent.TOOL_ERROR,
                        tool_name=tool_name,
                        error=output["error"],
                    ))
                else:
                    self.callback(AgentCallback(
                        event=AgentEvent.TOOL_END,
                        tool_name=tool_name,
                        tool_result=output.get("result"),
                    ))

            # Format response
            response_parts = ["Local analysis complete."]
            for output in result.get("tool_outputs", []):
                if output.get("result", {}).get("success"):
                    response_parts.append(f"• {output['tool']}: Success")
                elif "error" in output:
                    response_parts.append(f"• {output['tool']}: Error - {output['error']}")

            response = "\n".join(response_parts)

            self.callback(AgentCallback(
                event=AgentEvent.ASSISTANT_MESSAGE,
                data=response,
            ))

            self.callback(AgentCallback(event=AgentEvent.DONE))

            return response

        except Exception as e:
            self.callback(AgentCallback(
                event=AgentEvent.ERROR,
                error=str(e),
            ))
            return None

    async def run(
        self,
        user_input: str,
        chat_history: Optional[List] = None,
    ) -> Optional[str]:
        """Run the local reasoner asynchronously."""
        return self.run_sync(user_input, chat_history)


def create_orchestrator(
    callback: Callable[[AgentCallback], None],
    provider: str = "auto",
    **kwargs,
) -> Union[AgentOrchestrator, LocalFallbackOrchestrator]:
    """Create the best available orchestrator.

    Tries to create a full LangChain orchestrator, falls back to
    local reasoning if API keys are not available.

    Args:
        callback: Callback function for events
        provider: 'openai', 'anthropic', 'xai', 'local', or 'auto'

    Returns:
        Available orchestrator instance
    """
    if provider == "local":
        return LocalFallbackOrchestrator(callback)

    if provider == "auto":
        # Use ModelSelector to find available provider
        if MODEL_SELECTOR_AVAILABLE:
            selector = ModelSelector()
            default_provider = selector.get_default_provider()
            if default_provider:
                provider = default_provider
            else:
                return LocalFallbackOrchestrator(callback)
        else:
            # Legacy fallback if ModelSelector not available
            if os.environ.get("OPENAI_API_KEY"):
                provider = "openai"
            elif os.environ.get("ANTHROPIC_API_KEY"):
                provider = "anthropic"
            elif os.environ.get("XAI_API_KEY"):
                provider = "xai"
            else:
                return LocalFallbackOrchestrator(callback)

    orchestrator = AgentOrchestrator(callback, provider=provider, **kwargs)
    if orchestrator.is_available:
        return orchestrator

    # Fall back to local
    return LocalFallbackOrchestrator(callback)
