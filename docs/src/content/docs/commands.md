---
title: Commands
description: CLI command reference
---

# Commands

Global flags:
- `--provider none|openai|anthropic|xai` select AI provider for this run
- `--upgrade` self-update from git checkout (see Upgrade section)

## Config

Interactive AI provider configuration. Guides you through setting up an API key and optionally saves it to your shell profile.

```bash
cyberzard config
```

This command:
- Shows current provider status (installed packages, API keys)
- Prompts you to select and configure a provider
- Optionally saves the API key to `~/.zshrc`, `~/.bashrc`, etc.

Use this when you first install Cyberzard or need to change your AI provider.

## Providers

Show available AI providers with their configuration status.

```bash
cyberzard providers
```

Output shows a table with:
- Provider name and default model
- Package status (✓ installed / ✗ not installed)
- API key status (✓ configured / ✗ missing)
- Auto-detection status (shows which provider would be used if none specified)

This is useful for troubleshooting provider setup and verifying your configuration.

## Scan

Run a deterministic system scan.

Flags:
- `--json` output full JSON including remediation preview
- `--include-encrypted/--no-include-encrypted` include heuristic search for encrypted-looking files
- `--verify/--no-verify` run AI/heuristic verification to reduce false positives (default: verify)
- `--auto-approve` auto-consent to safe, read-only probes (no prompts in TTY when set)
- `--max-probes N` limit total verification probes (default: 5)

Examples:

```bash
cyberzard scan
cyberzard scan --json --include-encrypted
cyberzard scan --no-verify
cyberzard scan --auto-approve --max-probes 8
cyberzard --provider openai scan --include-encrypted
```

JSON output shape (abridged):

```jsonc
{
	"scan": { /* scan results */ },
	"remediation": { /* proposed plan (preview only) */ },
	"verification": { // present when --verify
		"success": true,
		"verified_plan": { "total_actions": 2, "actions": [/* kept actions */] },
		"dropped": [ { "action": { /* ... */ }, "reason": "..." } ],
		"downgraded": [ { "action": { /* ... */ }, "reason": "..." } ],
		"meta": { "probe_count": 3, "probes_skipped": 0, "consent_log": [/* categories + approvals */] }
	}
}
```

## Advise

Run a scan and print concise advice. Uses `CYBERZARD_MODEL_PROVIDER` (none|openai|anthropic); defaults to static advice.

```bash
CYBERZARD_MODEL_PROVIDER=none cyberzard advise
CYBERZARD_MODEL_PROVIDER=openai OPENAI_API_KEY=... cyberzard advise --include-encrypted
cyberzard --provider anthropic advise
```

## Agent

Ask the minimal local agent to perform actions with tools. **Requires AI to be configured.**

```bash
cyberzard agent "scan the server"
cyberzard agent --steps 5 "read /etc/passwd"
```

If AI is not configured, you'll be prompted to set it up interactively.

Run `cyberzard --help` for full list.

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `config` | Interactive AI provider setup | — |
| `scan` | Run all scanners, list findings | `--json`, `--verify/--no-verify`, `--auto-approve`, `--max-probes` |
| `advise` | Generate concise advice from scan | `--json`, `--include-encrypted` |
| `agent` | Minimal ReAct loop over safe tools | `--steps N`, `--show-plan` |
| `chat` | Interactive chat with permission-gated tools & SQLite history | `--verify/--no-verify`, `--auto-approve`, `--max-probes`, `--session` |
| `providers` | Show AI provider status | — |
| `show-prompt` | Print the agent system prompt | — |
| `version` | Show version | — |
| `upgrade` | Self-update from git checkout | — |
| `email-security` | Email stack scan + hardening preview / guided exec | `--json`, `--run`, `--dry-run/--no-dry-run`, `--max-risk` |
| `email-fix` | Full email remediation guide + optional execution | `--json`, `--run`, `--dry-run/--no-dry-run`, `--max-risk` |

## Chat

A beautiful, permission-aware chat loop. Cyberzard stays focused on CyberPanel anomaly detection.

Flags:
- `--verify/--no-verify` AI/heuristic verification of suggested actions (default: verify)
- `--auto-approve` auto-consent to safe read-only probes
- `--max-probes N` limit total probes during verification
 - `--session ID` conversation session id for persisted history

Examples:

```bash
cyberzard chat
cyberzard chat --no-verify
cyberzard chat --auto-approve --max-probes 8
cyberzard chat --session ops
```

In-chat commands:

- `/history [n]` — show last n messages (default: 10)
- `/clear` — clear current session history
- `/sessions` — list available sessions
- `/switch <id>` — switch active session


## Logs and Memory

Cyberzard’s n8n setup and email troubleshooting flows now integrate with the AI agent for safer, permission‑gated execution and provide persistent logs + memory records:

- n8n (`cyberzard n8n-setup`)
	- Flags: `--interactive/--no-interactive`, `--auto-approve`, `--json-out`
	- Execution logs: placed next to the applied script (e.g., `n8n_setup_native.sh.log`)
	- Memory: recorded under chat session `n8n` with applied/aborted status, mode, and paths

- Email (`email-security`, `email-fix`)
	- Flags: `--log-dir <path>` (JSON log per run), plus existing `--run`, `--dry-run/--no-dry-run`, `--max-risk`, `--auto-approve`, `--ai-refine/--no-ai-refine`
	- Logs: a JSON file saved in the chosen directory (e.g., `./logs/email_exec_1694971234.json`)
	- Memory: recorded under chat session `email-troubleshooting` with summary counters and `log_path`

In chat, you can list sessions with `/sessions`, switch with `/switch n8n` or `/switch email-troubleshooting`, and view history with `/history`.


