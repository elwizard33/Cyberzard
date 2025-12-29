from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import os
import sys


# --- LangChain/LangGraph agent integration ---
import subprocess

# Try importing from langchain core first (newer versions)
try:
    from langchain.agents import create_openai_tools_agent as create_agent
except ImportError:
    try:
        from langchain_core.agents import create_openai_tools_agent as create_agent
    except ImportError:
        # Fallback: define a no-op if agent not available
        def create_agent(*args, **kwargs):
            raise ImportError("LangChain agent support not available. Install langchain.")

try:
    from langchain.tools import tool
except ImportError:
    from langchain_core.tools import tool

try:
    from langchain_community.chat_message_histories import SQLChatMessageHistory
except ImportError:
    # Fallback: disable SQL history if not available
    SQLChatMessageHistory = None

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import sqlite3

# Tool: run shell command
@tool
def run_shell_command(command: str) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {e}"

# Tool: debug shell command
@tool
def debug_shell_command(command: str) -> str:
    """Debug a shell command and suggest a fix."""
    # Simple heuristic: check for common errors
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return "Command executed successfully."
        err = result.stderr
        if "not found" in err:
            return f"Error: Command not found. Did you mean to install it?"
        if "permission denied" in err.lower():
            return "Error: Permission denied. Try running with sudo or check file permissions."
        return f"Error: {err}"
    except Exception as e:
        return f"Exception: {e}"

# Tool: complete shell command
@tool
def complete_shell_command(partial: str) -> str:
    """Suggest a completion for a partial shell command."""
    # Simple completion: suggest 'ls', 'cat', 'echo', etc.
    common_cmds = ["ls", "cat", "echo", "grep", "find", "pwd", "cd", "touch", "rm", "cp", "mv"]
    for cmd in common_cmds:
        if cmd.startswith(partial):
            return f"Did you mean: {cmd} ...?"
    return "No suggestion."

# SQLite database path for chat history persistence
DB_PATH = "cyberzard_agent.sqlite"

def _list_sessions() -> list[str]:
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # SQLChatMessageHistory default table is 'message_store' with columns including 'session_id'
        cur.execute("SELECT DISTINCT session_id FROM message_store ORDER BY session_id")
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows if r and r[0]]
    except Exception:
        return []

# Lazy initialization - only create when needed
_model = None
_agent = None
_active_provider: str | None = None

def get_model():
    """Get the LLM model, auto-detecting the best available provider."""
    global _model, _active_provider
    if _model is None:
        from .models.selector import ModelSelector
        selector = ModelSelector()
        provider = selector.get_default_provider()
        if not provider:
            raise RuntimeError(
                "No AI provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or XAI_API_KEY."
            )
        _model = selector.create_model(
            provider=provider,
            model=None,  # Use provider's default model
            temperature=0,
            streaming=False
        )
        _active_provider = provider
    return _model

def get_active_provider() -> str | None:
    """Return the active provider name, or None if model not yet initialized."""
    return _active_provider

def get_agent():
    global _agent
    if _agent is None:
        model = get_model()
        system_prompt = "You are a helpful CLI agent that can run, debug, and complete shell commands. Use tools to assist the user."
        
        # Build a proper chat prompt template for the tools agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("messages"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        
        _agent = create_agent(model, tools=[run_shell_command, debug_shell_command, complete_shell_command], prompt=prompt)
    return _agent

def run_chat(verify: bool = True, auto_approve: bool = False, max_probes: int = 5, session_id: str = "default") -> None:
    # Initialize model early to detect provider
    try:
        get_model()
        provider_info = f"provider: {get_active_provider()}"
    except RuntimeError as e:
        print(f"Error: {e}")
        return
    
    print(f"Cyberzard AI Chat (LangChain agent) [{provider_info}] [session: {session_id}]. Type 'quit' to exit. Commands: /clear, /history [n], /sessions, /switch <id>")
    # Create a chat history instance for this session
    chat_history = SQLChatMessageHistory(session_id=session_id, connection_string=f"sqlite:///{DB_PATH}")
    while True:
        try:
            user = input("You: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye. - chat.py:97")
            break
        if not user.strip():
            continue
        if user.strip().lower() in {"quit", "exit", ":q", "/q"}:
            print("Exiting chat. - chat.py:102")
            break
        # Built-in commands
        if user.strip().startswith("/clear"):
            try:
                # Best effort clear
                chat_history.clear()
                print("History cleared. - chat.py:109")
            except Exception:
                # Fallback: re-init local history
                try:
                    chat_history = SQLChatMessageHistory(session_id=session_id, connection_string=f"sqlite:///{DB_PATH}")
                    print("History reset. - chat.py:114")
                except Exception:
                    print("Unable to clear history. - chat.py:116")
            continue
        if user.strip().startswith("/history"):
            parts = user.strip().split()
            try:
                n = int(parts[1]) if len(parts) > 1 else 10
            except Exception:
                n = 10
            msgs: list[BaseMessage] = chat_history.messages or []
            for m in msgs[-n:]:
                role = "assistant" if m.type == "ai" else ("user" if m.type == "human" else m.type)
                content = getattr(m, "content", "")
                print(f"{role}> {content} - chat.py:128")
            continue
        if user.strip().startswith("/sessions"):
            sessions = _list_sessions()
            if not sessions:
                print("No sessions found. - chat.py:133")
            else:
                print("Sessions: - chat.py:135")
                for s in sessions:
                    marker = "*" if s == session_id else " "
                    print(f"{marker} {s} - chat.py:138")
            continue
        if user.strip().startswith("/switch"):
            parts = user.strip().split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                print("Usage: /switch <session_id> - chat.py:143")
                continue
            new_id = parts[1].strip()
            try:
                chat_history = SQLChatMessageHistory(session_id=new_id, connection_string=f"sqlite:///{DB_PATH}")
                session_id = new_id
                print(f"Switched to session: {session_id} - chat.py:149")
            except Exception as e:
                print(f"Unable to switch session: {e} - chat.py:151")
            continue
        # Agent invocation
        # Load history (list[BaseMessage]) and append the current user message
        history_messages: list[BaseMessage] = chat_history.messages or []
        input_messages = history_messages + [HumanMessage(content=user)]
        agent = get_agent()
        response = agent.invoke({"messages": input_messages})

        # Extract assistant text from various possible return shapes
        answer: str
        if hasattr(response, "content"):
            # AIMessage or similar
            answer = getattr(response, "content") or ""
        elif isinstance(response, dict):
            answer = (
                response.get("final")
                or response.get("output")
                or response.get("answer")
                or ""
            )
            if not answer and isinstance(response.get("messages"), list) and response["messages"]:
                last = response["messages"][-1]
                answer = getattr(last, "content", str(last))
        else:
            answer = str(response)

        # Persist turn to history
        try:
            chat_history.add_user_message(user)
            chat_history.add_ai_message(answer)
        except Exception:
            pass

        print("Agent: - chat.py:184", answer)
