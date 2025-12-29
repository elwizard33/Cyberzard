"""Legacy TUI module - provides scan-focused interface.

For the enhanced chat-based TUI, use:
    from cyberzard.tui import CyberzardApp, run_tui

This module maintains the original ScanApp for backward compatibility.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable
from textual.reactive import reactive

from ..agent_engine.tools import scan_server, propose_remediation


class ScanApp(App):
    """Original scan-focused TUI application."""

    CSS = """
    Screen { background: $surface; }
    #title { content-align: center middle; height: 3; color: $accent; text-style: bold; }
    #summary { padding: 1; }
    #plan { padding: 1; }
    """

    running = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Cyberzard Scan", id="title")
        yield Static("Loading...", id="summary")
        yield DataTable(id="findings")
        yield Static("No plan yet", id="plan")
        yield Footer()

    def on_mount(self) -> None:
        # Schedule scan without blocking UI
        self.call_later(self._run_scan)

    async def _run_scan(self) -> None:
        if self.running:
            return
        self.running = True
        # Fire-and-forget worker; no await on run_worker
        self.run_worker(self._do_scan(), exclusive=True)

    async def _do_scan(self) -> None:
        results = scan_server(include_encrypted=False)
        plan = propose_remediation(results)
        self._render_summary(results)
        self._render_findings(results)
        self._render_plan(plan)

    def _render_summary(self, results) -> None:
        s = results.get("summary", {})
        items = [f"{k}: {v}" for k, v in s.items()]
        self.query_one('#summary', Static).update("\n".join(items))

    def _render_findings(self, results) -> None:
        table = self.query_one('#findings', DataTable)
        table.clear(columns=True)
        table.add_columns("Category", "Count")
        s = results.get("summary", {})
        for k, v in s.items():
            table.add_row(k, str(v))

    def _render_plan(self, plan) -> None:
        self.query_one('#plan', Static).update("Previews: " + str(plan.get('plan', {}).get('total_actions', 0)))


def run_scan_tui() -> None:
    """Run the scan-focused TUI."""
    ScanApp().run()
