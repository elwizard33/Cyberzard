---
title: Chat mode
description: Interactive, permission-aware chat for CyberPanel anomaly hunting
---

# Chat mode

Cyberzard’s chat mode gives you an interactive, on-mission assistant focused on CyberPanel anomaly detection. It uses a safe, permission-gated set of tools, persisted conversation memory (SQLite), and a readable TTY UI.

## What it does

- Stays focused on CyberPanel security tasks
- Runs safe, read-only checks with your explicit approval
- Summarizes results and shows a remediation preview
- Optionally verifies suggested actions with bounded, consented probes
- Persists conversations locally (SQLite) so you can resume where you left off

## Start chat

```bash
cyberzard chat
```

Helpful flags:

- `--verify/--no-verify`: enable AI/heuristic verification of actions (default: verify)
- `--auto-approve`: auto-consent to safe, read-only probes (no prompts)
- `--max-probes N`: cap total verification probes (default: 5)
- `--session ID`: name the conversation session (history is stored per session)

Examples:

```bash
cyberzard chat --no-verify
cyberzard chat --auto-approve --max-probes 8
cyberzard chat --session ops
```

## In-chat commands

Core navigation and memory:
- `/history [n]` — show the last n messages in the current session (default: 10)
- `/clear` — clear the conversation history for the current session
- `/sessions` — list available session IDs (from local SQLite store)
- `/switch <id>` — switch to another session (created on first use)

Examples:
```text
/sessions
/switch ops
/history 5
```

Notes:
- Session data is stored locally in `cyberzard_agent.sqlite` next to the CLI.
- If you want separate contexts (e.g., prod vs. staging), use different sessions.

## Permissions & safety

When chat needs to use a tool (e.g., scan, read file, limited probes), it asks for permission. You can allow once or “remember” the choice for the session.

- Tools are read-only; there’s no raw shell access
- Verification probes are grouped by category (e.g., `file`, `systemd`, `ps`)
- Probes are bounded by `--max-probes` and require consent
- Non-interactive terminals or `NO_COLOR=1` skip the Rich UI and default to deny

## Providers (optional)

Chat works offline. If you set a provider, advice summaries may be AI‑enriched.

```bash
export CYBERZARD_PROVIDER=openai
export OPENAI_API_KEY=sk-...
cyberzard chat
```

Or with xAI (Grok):
```bash
export CYBERZARD_PROVIDER=xai
export XAI_API_KEY=xai-...
cyberzard chat
```

Supported: `none` (default), `openai`, `anthropic`, `xai`.

Use `cyberzard providers` to check which providers are available on your system.

## Troubleshooting

- “Chat mode is best used in an interactive terminal (TTY).” — Run in a real TTY; don’t pipe/redirect output.
- No prompts? You used `--auto-approve` or your terminal isn’t interactive.
- Minimal UI? `NO_COLOR=1` disables Rich styling.
