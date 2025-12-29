from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
from rich.text import Text
from rich.prompt import Prompt, Confirm


_THEME = Theme(
    {
        "title": "bold cyan",
        "ok": "green",
        "warn": "yellow",
        "err": "red",
        "info": "dim",
        "highlight": "bold magenta",
        "key": "bold green",
    }
)


def _console() -> Console:
    return Console(theme=_THEME, soft_wrap=True)


def _summary_table(summary: Dict[str, Any]) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Key", style="info")
    table.add_column("Value")
    for k, v in summary.items():
        table.add_row(str(k), str(v))
    return table


def _actions_table(actions: List[Dict[str, Any]], limit: int = 10) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type", style="info")
    table.add_column("Target")
    table.add_column("Risk")
    table.add_column("Preview")
    for idx, a in enumerate(actions):
        if idx >= limit:
            break
        table.add_row(
            str(a.get("type", "")),
            str(a.get("target", ""))[:60],
            str(a.get("risk", "")),
            str(a.get("command_preview", ""))[:60],
        )
    return table


def render_scan_output(results: Dict[str, Any], plan: Dict[str, Any]) -> None:
    """Pretty print scan summary and remediation plan preview using Rich."""
    cons = _console()
    summary = results.get("summary", {})
    plan_obj = plan.get("plan", {}) if isinstance(plan, dict) else {}
    actions: List[Dict[str, Any]] = plan_obj.get("actions", []) if isinstance(plan_obj, dict) else []
    total = plan_obj.get("total_actions", len(actions))

    cons.print(Panel(Text("Cyberzard scan", style="title"), border_style="cyan"))
    cons.print(_summary_table(summary))

    cons.print()
    cons.print(
        Panel(
            Text(f"Remediation preview • {total} actions", style="title"),
            border_style="cyan",
        )
    )
    if actions:
        cons.print(_actions_table(actions, limit=12))
    else:
        cons.print(Text("No actions suggested.", style="info"))


def render_advice_output(advice: str, results: Dict[str, Any]) -> None:
    """Pretty print advice with a quick summary."""
    cons = _console()
    summary = results.get("summary", {}) if isinstance(results, dict) else {}
    cons.print(Panel(Text("Cyberzard advice", style="title"), border_style="cyan"))
    if summary:
        cons.print(_summary_table(summary))
        cons.print()
    cons.print(Panel(advice, title="Advice", border_style="green"))

def render_verified_output(results: Dict[str, Any], verification: Dict[str, Any]) -> None:
    cons = _console()
    summary = results.get("summary", {})
    cons.print(Panel(Text("Cyberzard scan (verified)", style="title"), border_style="cyan"))
    cons.print(_summary_table(summary))
    cons.print()
    verified = verification.get("verified_plan", {}) if isinstance(verification, dict) else {}
    dropped = verification.get("dropped", []) if isinstance(verification, dict) else []
    downgraded = verification.get("downgraded", []) if isinstance(verification, dict) else []
    total_kept = verified.get("total_actions", 0)
    cons.print(
        Panel(
            Text(
                f"Verified remediation • kept {total_kept} | dropped {len(dropped)} | downgraded {len(downgraded)}",
                style="title",
            ),
            border_style="cyan",
        )
    )
    actions = verified.get("actions", []) if isinstance(verified, dict) else []
    if actions:
        cons.print(_actions_table(actions, limit=12))
    else:
        cons.print(Text("No verified actions.", style="info"))
    if dropped:
        t = Table(show_header=True, header_style="bold red")
        t.add_column("Type", style="err"); t.add_column("Target"); t.add_column("Reason")
        for d in dropped[:10]:
            a = d.get("action", {})
            t.add_row(str(a.get("type", "")), str(a.get("target", ""))[:60], str(d.get("reason", ""))[:60])
        cons.print(Panel(t, title="Dropped", border_style="red"))
    if downgraded:
        t2 = Table(show_header=True, header_style="bold yellow")
        t2.add_column("Type", style="warn"); t2.add_column("Target"); t2.add_column("Reason")
        for d in downgraded[:10]:
            a = d.get("action", {})
            t2.add_row(str(a.get("type", "")), str(a.get("target", ""))[:60], str(d.get("reason", ""))[:60])
        cons.print(Panel(t2, title="Downgraded (manual review)", border_style="yellow"))


def render_email_security(scan: Dict[str, Any], plan: Dict[str, Any], summary_text: str | None = None) -> None:
    """Render email security scan + plan preview.

    Fallback: if Rich import failed earlier (unlikely), do naive prints.
    """
    try:
        cons = _console()
    except Exception:  # pragma: no cover
        s = (scan or {}).get("summary", {})
        print("Email Security Scan")
        print(f"Queue size: {s.get('queue_size')} backlog={s.get('queue_backlog')}")
        print(f"SASL failures: {s.get('sasl_failures')}")
        return
    s = (scan or {}).get("summary", {})
    cons.print(Panel(Text("Email security scan", style="title"), border_style="cyan"))
    cons.print(_summary_table({
        "failed_services": s.get("failed_services_count"),
        "queue_size": s.get("queue_size"),
        "queue_backlog": s.get("queue_backlog"),
        "sasl_failures": s.get("sasl_failures"),
        "dns_mismatch": s.get("dns_mismatch"),
        "fail2ban_active": s.get("fail2ban_active"),
        "tls_hardened": s.get("tls_hardened"),
        "rate_limited": s.get("rate_limited"),
    }))
    if summary_text:
        cons.print(Panel(summary_text, title="AI Summary", border_style="green"))
    plan_obj = plan.get("plan", {}) if isinstance(plan, dict) else {}
    actions = plan_obj.get("actions", [])
    total = plan_obj.get("total_actions", len(actions))
    cons.print(Panel(Text(f"Hardening preview • {total} actions", style="title"), border_style="cyan"))
    if actions:
        cons.print(_actions_table(actions, limit=12))
    else:
        cons.print(Text("No suggested actions", style="info"))


def render_email_execution_progress(executions: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    """Render progress/results of guided execution."""
    try:
        cons = _console()
    except Exception:  # pragma: no cover
        print("Email Execution Summary:", summary)
        return
    cons.print(Panel(Text("Email remediation execution", style="title"), border_style="cyan"))
    cons.print(_summary_table(summary))
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type")
    table.add_column("Risk")
    table.add_column("Status")
    table.add_column("Refined")
    table.add_column("Unsafe/Skip")
    for ex in executions[:30]:
        status = "dry-run" if ex.get("dry_run") else ("ok" if ex.get("success") else ("fail" if ex.get("success") is False else "?"))
        row = [
            str(ex.get("type")),
            str(ex.get("risk")),
            status,
            "yes" if ex.get("refinement_success") else ("attempt" if ex.get("refinement_attempted") else ""),
            "unsafe" if ex.get("unsafe") else ("skipped" if ex.get("skipped") else ""),
        ]
        table.add_row(*row)
    cons.print(table)


def render_email_fix(guide_markdown: str) -> None:
    """Render email fix guide (markdown simplified)."""
    try:
        from rich.markdown import Markdown  # local import to avoid heavy cost if unused
        cons = _console()
        cons.print(Markdown(guide_markdown[:8000]))
    except Exception:  # pragma: no cover
        print(guide_markdown[:8000])


def check_ai_configured() -> Tuple[bool, Optional[str], Optional[str]]:
    """Check if an AI provider is configured and ready.

    Returns:
        Tuple of (is_configured, provider_key, error_message)
        - is_configured: True if a provider is fully configured
        - provider_key: The active provider key if configured, None otherwise
        - error_message: Human-readable error if not configured, None otherwise
    """
    from .models import ModelSelector, get_provider

    selector = ModelSelector()
    available = selector.detect_available_providers()

    # Check for any fully configured provider
    for provider_key, installed, has_key in available:
        if installed and has_key:
            return True, provider_key, None

    # Determine what's missing
    has_any_installed = any(installed for _, installed, _ in available)
    has_any_key = any(has_key for _, _, has_key in available)

    if not has_any_installed:
        return False, None, "No AI provider packages installed. Install with: pip install cyberzard[openai]"

    if not has_any_key:
        # Find which providers are installed but missing keys
        missing_keys = [
            get_provider(pk).api_key_env
            for pk, installed, has_key in available
            if installed and not has_key
        ]
        return False, None, f"API key not set. Set one of: {', '.join(missing_keys)}"

    return False, None, "No AI provider fully configured"


def prompt_ai_setup(skip_if_configured: bool = True) -> Tuple[bool, Optional[str]]:
    """Interactive prompt to set up AI provider.

    Args:
        skip_if_configured: If True, returns immediately if already configured

    Returns:
        Tuple of (success, provider_key)
        - success: True if AI is now configured (or was already)
        - provider_key: The active provider key, or None if setup failed/cancelled
    """
    from .models import ModelSelector, get_provider, list_providers

    cons = _console()
    selector = ModelSelector()

    # Check current status
    is_configured, active_provider, _ = check_ai_configured()
    if is_configured and skip_if_configured:
        return True, active_provider

    available = selector.detect_available_providers()

    # Show current status
    cons.print()
    cons.print(Panel(
        Text("🤖 AI Provider Setup", style="title"),
        border_style="cyan",
        subtitle="Configure your AI model provider"
    ))
    cons.print()

    # Build status table
    table = Table(border_style="cyan", show_header=True)
    table.add_column("Provider", style="cyan bold")
    table.add_column("Package", style="dim")
    table.add_column("Installed", justify="center")
    table.add_column("API Key", justify="center")

    installed_providers = []
    for provider_key, installed, has_key in available:
        info = get_provider(provider_key)
        if not info:
            continue

        installed_icon = Text("✓", style="ok") if installed else Text("✗", style="err")
        key_icon = Text("✓", style="ok") if has_key else Text("✗", style="warn")

        table.add_row(
            info.name,
            info.package,
            installed_icon,
            key_icon,
        )

        if installed:
            installed_providers.append((provider_key, info, has_key))

    cons.print(table)
    cons.print()

    # If nothing installed, guide to install
    if not installed_providers:
        cons.print("[warn]No AI provider packages installed.[/warn]")
        cons.print()
        cons.print("Install a provider package:")
        cons.print("  [cyan]pip install cyberzard[openai][/cyan]     # OpenAI (GPT)")
        cons.print("  [cyan]pip install cyberzard[anthropic][/cyan]  # Anthropic (Claude)")
        cons.print("  [cyan]pip install cyberzard[all][/cyan]        # All providers")
        cons.print()
        return False, None

    # Find providers that need API keys
    needs_key = [(pk, info) for pk, info, has_key in installed_providers if not has_key]

    if not needs_key:
        # All installed providers have keys - we're good!
        default = selector.get_default_provider()
        cons.print(f"[ok]✓ AI is configured![/ok] Active provider: [cyan]{default}[/cyan]")
        return True, default

    # Offer to set up an API key
    cons.print("[warn]API key needed.[/warn] Choose a provider to configure:")
    cons.print()

    for i, (pk, info) in enumerate(needs_key, 1):
        cons.print(f"  [{i}] {info.name} ({info.api_key_env})")

    cons.print(f"  [0] Skip for now")
    cons.print()

    # Get user choice
    try:
        choice = Prompt.ask(
            "Select provider",
            choices=[str(i) for i in range(len(needs_key) + 1)],
            default="1" if len(needs_key) == 1 else None,
        )
    except (KeyboardInterrupt, EOFError):
        cons.print("\n[info]Setup cancelled.[/info]")
        return False, None

    if choice == "0":
        cons.print("[info]Skipped AI setup. Some features will be limited.[/info]")
        return False, None

    # Get API key for selected provider
    idx = int(choice) - 1
    selected_key, selected_info = needs_key[idx]

    cons.print()
    cons.print(f"[title]Setting up {selected_info.name}[/title]")
    cons.print()
    cons.print(f"Get your API key from:")

    # Provider-specific URLs
    urls = {
        "openai": "https://platform.openai.com/api-keys",
        "anthropic": "https://console.anthropic.com/settings/keys",
        "xai": "https://console.x.ai/",
    }
    url = urls.get(selected_key, "your provider's website")
    cons.print(f"  [cyan]{url}[/cyan]")
    cons.print()
    cons.print("[info]Note: Input is hidden for security. Paste your key and press Enter.[/info]")
    cons.print()

    # Try up to 3 times to get a valid key
    max_attempts = 3
    api_key = None

    for attempt in range(max_attempts):
        try:
            entered_key = Prompt.ask(
                f"Enter your {selected_info.api_key_env}",
                password=True,  # Hide input
            )
        except (KeyboardInterrupt, EOFError):
            cons.print("\n[info]Setup cancelled.[/info]")
            return False, None

        if not entered_key or not entered_key.strip():
            cons.print("[warn]No key entered.[/warn] Please paste your API key and press Enter.")
            if attempt < max_attempts - 1:
                cons.print(f"[info]Attempts remaining: {max_attempts - attempt - 1}[/info]")
            continue

        entered_key = entered_key.strip()

        # Basic format validation
        key_valid, key_error = _validate_api_key_format(selected_key, entered_key)
        if not key_valid:
            cons.print(f"[warn]{key_error}[/warn]")
            if attempt < max_attempts - 1:
                cons.print(f"[info]Attempts remaining: {max_attempts - attempt - 1}[/info]")
            continue

        # Test the API key with a simple request
        cons.print("[info]Testing API key...[/info]")
        test_ok, test_error = _test_api_key(selected_key, entered_key)

        if test_ok:
            cons.print("[ok]✓ API key is valid![/ok]")
            api_key = entered_key
            break
        else:
            cons.print(f"[err]✗ API key test failed: {test_error}[/err]")
            if attempt < max_attempts - 1:
                cons.print(f"[info]Attempts remaining: {max_attempts - attempt - 1}[/info]")
                retry = Confirm.ask("Try again?", default=True)
                if not retry:
                    cons.print("[info]Setup cancelled.[/info]")
                    return False, None

    if not api_key:
        cons.print("[err]Failed to configure API key after multiple attempts.[/err]")
        cons.print("Please verify your API key is correct and try again.")
        return False, None

    # Set the environment variable for this session
    os.environ[selected_info.api_key_env] = api_key

    # Offer to save to shell profile
    cons.print()
    cons.print("[ok]✓ API key set for this session![/ok]")
    cons.print()

    save_permanent = Confirm.ask(
        "Save to shell profile for future sessions?",
        default=True,
    )

    if save_permanent:
        saved_path = _save_to_shell_profile(selected_info.api_key_env, api_key)
        if saved_path:
            cons.print(f"[ok]✓ Saved to {saved_path}[/ok]")
            cons.print(f"[info]Run [cyan]source {saved_path}[/cyan] or restart your terminal to apply.[/info]")
        else:
            cons.print("[warn]Could not auto-save. Add manually to your shell profile:[/warn]")
            cons.print(f'  [cyan]export {selected_info.api_key_env}="{api_key[:8]}..."[/cyan]')

    cons.print()
    cons.print(f"[ok]✓ {selected_info.name} is now configured![/ok]")

    return True, selected_key


def _validate_api_key_format(provider: str, key: str) -> Tuple[bool, str]:
    """Validate API key format before testing.

    Args:
        provider: Provider key (openai, anthropic, xai)
        key: The API key to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not key:
        return False, "API key is empty"

    if len(key) < 10:
        return False, "API key is too short"

    # Provider-specific format checks
    if provider == "openai":
        if not (key.startswith("sk-") or key.startswith("sk-proj-")):
            return False, "OpenAI keys typically start with 'sk-' or 'sk-proj-'"
    elif provider == "anthropic":
        if not key.startswith("sk-ant-"):
            return False, "Anthropic keys typically start with 'sk-ant-'"
    # xAI doesn't have a standard prefix

    return True, ""


def _test_api_key(provider: str, key: str) -> Tuple[bool, str]:
    """Test if an API key is valid by making a simple API call.

    Args:
        provider: Provider key (openai, anthropic, xai)
        key: The API key to test

    Returns:
        Tuple of (is_valid, error_message)
    """
    import httpx

    try:
        if provider == "openai":
            # Test with models endpoint (lightweight)
            response = httpx.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return True, ""
            elif response.status_code == 401:
                return False, "Invalid API key"
            elif response.status_code == 429:
                return True, ""  # Rate limited but key is valid
            else:
                return False, f"API error: {response.status_code}"

        elif provider == "anthropic":
            # Test with a minimal completion request
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "Hi"}],
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                return True, ""
            elif response.status_code == 401:
                return False, "Invalid API key"
            elif response.status_code == 429:
                return True, ""  # Rate limited but key is valid
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", str(response.status_code))
                    return False, f"API error: {error_msg}"
                except Exception:
                    return False, f"API error: {response.status_code}"

        elif provider == "xai":
            # xAI uses OpenAI-compatible API
            response = httpx.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                return True, ""
            elif response.status_code == 401:
                return False, "Invalid API key"
            elif response.status_code == 429:
                return True, ""  # Rate limited but key is valid
            else:
                return False, f"API error: {response.status_code}"

        else:
            # Unknown provider, skip validation
            return True, ""

    except httpx.TimeoutException:
        return False, "Connection timed out. Check your internet connection."
    except httpx.ConnectError:
        return False, "Could not connect to API. Check your internet connection."
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def _save_to_shell_profile(env_var: str, value: str) -> Optional[str]:
    """Save an environment variable to the user's shell profile.

    Args:
        env_var: Environment variable name
        value: Value to set

    Returns:
        Path to the file that was modified, or None if failed
    """
    from pathlib import Path

    home = Path.home()

    # Determine which shell profile to use
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        profile_candidates = [home / ".zshrc", home / ".zprofile"]
    elif "bash" in shell:
        profile_candidates = [home / ".bashrc", home / ".bash_profile", home / ".profile"]
    else:
        profile_candidates = [home / ".profile", home / ".bashrc"]

    # Find existing profile or create .profile
    target = None
    for candidate in profile_candidates:
        if candidate.exists():
            target = candidate
            break

    if target is None:
        target = profile_candidates[0]  # Create the first candidate

    try:
        # Check if already exists in file
        export_line = f'export {env_var}="{value}"'

        if target.exists():
            content = target.read_text()
            # Check if this env var is already set (to avoid duplicates)
            if f"export {env_var}=" in content:
                # Replace existing line
                lines = content.splitlines()
                new_lines = []
                for line in lines:
                    if line.strip().startswith(f"export {env_var}="):
                        new_lines.append(export_line)
                    else:
                        new_lines.append(line)
                target.write_text("\n".join(new_lines) + "\n")
                return str(target)

        # Append new export
        with target.open("a") as f:
            f.write(f"\n# Cyberzard AI provider key\n{export_line}\n")

        return str(target)

    except Exception:
        return None


def ensure_ai_configured(
    require: bool = False,
    prompt_setup: bool = True,
    command_name: str = "this command",
) -> Tuple[bool, Optional[str]]:
    """Ensure AI is configured, optionally prompting for setup.

    This is the main entry point for commands that need AI.

    Args:
        require: If True, exit with error if AI not configured after prompt
        prompt_setup: If True, offer interactive setup when not configured
        command_name: Name of the command (for error messages)

    Returns:
        Tuple of (is_configured, provider_key)
    """
    is_configured, provider, error = check_ai_configured()

    if is_configured:
        return True, provider

    cons = _console()

    # Check if we're in interactive mode
    interactive = sys.stdout.isatty() and sys.stdin.isatty()

    if interactive and prompt_setup:
        cons.print()
        cons.print(f"[warn]⚠ AI provider not configured.[/warn] {command_name} works best with AI.")
        cons.print()

        setup_now = Confirm.ask("Set up an AI provider now?", default=True)
        if setup_now:
            success, provider = prompt_ai_setup(skip_if_configured=False)
            if success:
                return True, provider

    # Not configured and either non-interactive or user declined
    if require:
        cons.print()
        cons.print(f"[err]✗ AI provider required for {command_name}.[/err]")
        cons.print()
        cons.print("Configure with one of:")
        cons.print("  [cyan]cyberzard config[/cyan]     # Interactive setup")
        cons.print("  [cyan]export OPENAI_API_KEY=sk-...[/cyan]")
        cons.print("  [cyan]export ANTHROPIC_API_KEY=sk-ant-...[/cyan]")
        cons.print()
        raise SystemExit(1)

    return False, None


__all__ = [
    "render_scan_output",
    "render_advice_output",
    "render_verified_output",
    "render_email_security",
    "render_email_execution_progress",
    "render_email_fix",
    "check_ai_configured",
    "prompt_ai_setup",
    "ensure_ai_configured",
    "_THEME",
]
