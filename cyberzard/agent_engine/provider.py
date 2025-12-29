from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

# Valid provider names for this module
SUPPORTED_PROVIDERS = {"openai", "anthropic", "xai"}


def _get_provider_and_client() -> Tuple[Optional[str], Any]:
    """Get current provider and appropriate client using ModelSelector for validation.
    
    Returns (provider_name, client) or (None, None) if not configured.
    """
    from ..models.selector import ModelSelector
    
    provider = os.getenv("CYBERZARD_PROVIDER") or os.getenv("CYBERZARD_MODEL_PROVIDER") or "none"
    provider = provider.lower().strip()
    
    if provider not in SUPPORTED_PROVIDERS:
        return None, None
    
    selector = ModelSelector()
    valid, _ = selector.validate_provider(provider)
    if not valid:
        return None, None
    
    # Return provider name; client will be created lazily by caller
    return provider, selector


def _static_summary(scan_results: Dict[str, Any]) -> str:
    s = scan_results.get("summary", {})
    lines = []
    lines.append("Cyberzard Advice (static)")
    lines.append(f"- Malicious files: {s.get('malicious_file_count', 0)}")
    lines.append(f"- Suspicious process groups: {s.get('suspicious_process_groups', 0)}")
    lines.append(f"- Encrypted-like files: {s.get('encrypted_file_count', 0)}")
    lines.append(f"- Suspicious cron entries: {s.get('cron_suspicious_count', 0)}")
    lines.append(f"- Suspicious systemd units: {s.get('systemd_units_count', 0)}")
    lines.append(f"- Users: {s.get('users_count', 0)}; keys files: {s.get('ssh_keys_files', 0)}")
    lines.append(f"- ld.so.preload present: {bool(s.get('ld_preload_exists', False))}")
    lines.append(f"- CyberPanel key files present: {s.get('cyberpanel_files_present', 0)}")
    return "\n".join(lines[:8])


def summarize(scan_results: Dict[str, Any]) -> str:
    provider, selector = _get_provider_and_client()
    if not provider:
        return _static_summary(scan_results)

    # Build a compact prompt payload
    s = scan_results.get("summary", {})
    compact = {
        "malicious": s.get("malicious_file_count", 0),
        "proc_groups": s.get("suspicious_process_groups", 0),
        "encrypted": s.get("encrypted_file_count", 0),
        "cron": s.get("cron_suspicious_count", 0),
        "systemd": s.get("systemd_units_count", 0),
        "users": s.get("users_count", 0),
        "keys_files": s.get("ssh_keys_files", 0),
        "ld_preload": bool(s.get("ld_preload_exists", False)),
        "cyberpanel_present": s.get("cyberpanel_files_present", 0),
    }
    instruction = (
        "Provide concise CyberPanel-focused incident triage advice (6-8 lines). "
        "Use deterministic actions, no remote downloads/executions."
    )
    prompt = f"{instruction}\nSummary: {compact}\nRespond briefly."

    try:
        if provider == "openai":
            try:
                from openai import OpenAI  # type: ignore
            except Exception:
                return _static_summary(scan_results)
            client = OpenAI()
            try:
                resp = client.chat.completions.create(
                    model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=200,
                )
                text = resp.choices[0].message.content  # type: ignore[attr-defined]
                return text or _static_summary(scan_results)
            except Exception:
                return _static_summary(scan_results)
        elif provider == "anthropic":
            try:
                import anthropic  # type: ignore
            except Exception:
                return _static_summary(scan_results)
            client = anthropic.Anthropic()
            try:
                msg = client.messages.create(
                    model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                    max_tokens=200,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                parts = getattr(msg, "content", [])
                text = " ".join(getattr(p, "text", "") for p in parts)
                return text.strip() or _static_summary(scan_results)
            except Exception:
                return _static_summary(scan_results)
        elif provider == "xai":
            # Use LangChain's init_chat_model for xAI (Grok)
            try:
                model = selector.create_model(
                    provider="xai",
                    model=os.getenv("CYBERZARD_MODEL", "grok-2"),
                    temperature=0.2,
                    streaming=False
                )
                response = model.invoke(prompt)
                text = getattr(response, "content", "") or ""
                return text.strip() or _static_summary(scan_results)
            except Exception:
                return _static_summary(scan_results)
    except Exception:
        return _static_summary(scan_results)
    
    return _static_summary(scan_results)


__all__ = ["summarize", "justify_actions"]


def justify_actions(actions, scan_results):
    """Optionally produce brief justifications per action using configured provider.

    Returns a list of strings with the same length as actions, or None when provider
    is not configured/available. Any failure results in None (graceful degrade).
    """
    try:
        provider, selector = _get_provider_and_client()
        if not provider:
            return None
        # Build compact context once
        s = scan_results.get("summary", {}) if isinstance(scan_results, dict) else {}
        compact = {
            "malicious": s.get("malicious_file_count", 0),
            "proc_groups": s.get("suspicious_process_groups", 0),
            "encrypted": s.get("encrypted_file_count", 0),
            "cron": s.get("cron_suspicious_count", 0),
            "systemd": s.get("systemd_units_count", 0),
            "users": s.get("users_count", 0),
            "keys_files": s.get("ssh_keys_files", 0),
            "ld_preload": bool(s.get("ld_preload_exists", False)),
            "cyberpanel_present": s.get("cyberpanel_files_present", 0),
        }
        
        def _make_prompt(action):
            t = action.get("type")
            tgt = action.get("target")
            return (
                "One-line justification (max 25 words) for verifying this remediation action in a CyberPanel context. "
                "Be specific and cautious.\n"
                f"Action: type={t} target={tgt}\nSummary: {compact}"
            )
        
        if provider == "openai":
            try:
                from openai import OpenAI  # type: ignore
            except Exception:
                return None
            client = OpenAI()
            out: list[str] = []
            for a in actions or []:
                prompt = _make_prompt(a)
                try:
                    resp = client.chat.completions.create(
                        model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=60,
                    )
                    text = resp.choices[0].message.content  # type: ignore[attr-defined]
                    out.append((text or "").strip())
                except Exception:
                    out.append("")
            return out
        if provider == "anthropic":
            try:
                import anthropic  # type: ignore
            except Exception:
                return None
            client = anthropic.Anthropic()
            out: list[str] = []
            for a in actions or []:
                prompt = _make_prompt(a)
                try:
                    msg = client.messages.create(
                        model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                        max_tokens=60,
                        temperature=0.2,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    parts = getattr(msg, "content", [])
                    text = " ".join(getattr(p, "text", "") for p in parts).strip()
                    out.append(text)
                except Exception:
                    out.append("")
            return out
        if provider == "xai":
            # Use LangChain's init_chat_model for xAI (Grok)
            try:
                model = selector.create_model(
                    provider="xai",
                    model=os.getenv("CYBERZARD_MODEL", "grok-2"),
                    temperature=0.2,
                    streaming=False
                )
                out: list[str] = []
                for a in actions or []:
                    prompt = _make_prompt(a)
                    try:
                        response = model.invoke(prompt)
                        text = getattr(response, "content", "") or ""
                        out.append(text.strip())
                    except Exception:
                        out.append("")
                return out
            except Exception:
                return None
        return None
    except Exception:
        return None