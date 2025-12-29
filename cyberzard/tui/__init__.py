"""Cyberzard TUI (Text User Interface) package.

This package provides enhanced terminal UI components using the Textual framework,
including split-panel layouts for conversation and tool management.
"""

from .app import CyberzardApp, run_tui
from .widgets import ConversationWidget, ToolPanelWidget
from .legacy import ScanApp, run_scan_tui

__all__ = [
    # New chat TUI
    "CyberzardApp",
    "run_tui",
    "ConversationWidget",
    "ToolPanelWidget",
    # Legacy scan TUI
    "ScanApp",
    "run_scan_tui",
]
