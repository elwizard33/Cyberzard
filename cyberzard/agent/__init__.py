"""Agent package for Cyberzard.

This package provides the AI agent orchestration layer that connects
LangChain/LangGraph agents to the TUI interface.
"""

from .orchestrator import AgentOrchestrator, AgentCallback, AgentEvent, create_orchestrator

# Re-export run_agent from the legacy module for backward compatibility
try:
    from ..legacy_agent import run_agent, MiniReasoner, TOOL_REGISTRY
except ImportError:
    run_agent = None
    MiniReasoner = None
    TOOL_REGISTRY = {}

# Re-export SYSTEM_PROMPT from agent_engine.config
try:
    from ..agent_engine.config import SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = ""

__all__ = [
    "AgentOrchestrator",
    "AgentCallback",
    "AgentEvent",
    "create_orchestrator",
    # Legacy exports
    "run_agent",
    "MiniReasoner",
    "TOOL_REGISTRY",
    "SYSTEM_PROMPT",
]
