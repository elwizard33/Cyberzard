<div align="center">

# 🛡️ Cyberzard & CyberPanel Cleanup

[![PyPI version](https://img.shields.io/pypi/v/cyberzard?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/cyberzard/)
[![PyPI downloads](https://img.shields.io/pypi/dm/cyberzard?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/cyberzard/)
[![Docs](https://img.shields.io/badge/docs-Starlight%20Site-0b7285?logo=astro)](https://elwizard33.github.io/Cyberzard/)
[![Build Docs](https://github.com/elwizard33/Cyberzard/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/elwizard33/Cyberzard/actions/workflows/deploy-docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)
![Status](https://img.shields.io/badge/Status-Beta-yellow)
![AI Optional](https://img.shields.io/badge/AI-Optional-7c3aed)
![Offline‑first](https://img.shields.io/badge/Mode-Offline--first-495057)

</div>

Modern incident triage for CyberPanel:
- 🧰 Legacy bash cleanup scripts (basic & advanced)
- 🤖 Cyberzard — an AI‑assisted, safety‑constrained CLI for scanning, explaining, and planning remediation

---

## 🔗 Quick Links

- 📚 Docs: https://elwizard33.github.io/Cyberzard/
- 🧪 Try Cyberzard: see “Install & Use” below
- 🗺️ Roadmap: [ROADMAP.md](./ROADMAP.md)
- 🐞 Issues Guide: [ISSUE_GUIDE.md](./ISSUE_GUIDE.md)
- 📜 License: [MIT](./LICENSE)

---

<details>
<summary><strong>📖 Table of Contents</strong></summary>

- [Cyberzard — AI Security CLI](#-cyberzard--ai-security-cli)
  - [Features](#features)
  - [Install & Use](#install--use)
  - [Environment](#environment)
  - [Safety Model](#safety-model)
- [🧰 Legacy Cleanup Scripts](#-legacy-cleanup-scripts)
  - [Overview](#overview)
  - [Quick Start](#quick-start)
  - [Advanced vs Basic](#advanced-vs-basic)
  - [Decrypt Helpers](#decrypt-helpers)
- [🤝 Contributing](#-contributing)
- [⚠️ Disclaimer](#️-disclaimer)

</details>

---

## 🤖 Cyberzard — AI Security CLI

> Experimental preview. Interfaces may change until v0.1.

### Features

| Area | What you get |
|---|---|
| Multi‑source scanning | Files, processes, cron, services, users, SSH keys, encrypted files |
| Severity scoring | Critical/High/Medium/Low with rationale |
| Evidence preservation | Optional hashing/archiving prior to actions |
| Dry‑run planning | Generate remediation plan JSON first |
| AI reasoning (optional) | Summaries, prioritization, advice (OpenAI/Anthropic/xAI/none) |
| ReAct loop | Safe tool schema, sandboxed helpers |
| Output | Pretty tables + JSON |
| Chat mode | Interactive, permission‑aware assistant | Focused on CyberPanel |
| TUI (optional) | Simple terminal UI for scan results | `cyberzard tui` (requires textual) |
| Email stack hardening | scan + AI summary + guided execution | `email-security`, `email-fix` |

### Install & Use

#### Option 1: Install from PyPI (Recommended) 🐍

```bash
# Basic install
pip install cyberzard

# With AI provider extras
pip install cyberzard[openai]      # OpenAI support
pip install cyberzard[anthropic]   # Anthropic Claude support
pip install cyberzard[xai]         # xAI Grok support
pip install cyberzard[providers]   # All AI providers
pip install cyberzard[all]         # Everything (AI + TUI + MCP)
```

**With pipx** (recommended for CLI tools - isolated environment):
```bash
pipx install cyberzard
pipx install 'cyberzard[openai]'
```

**With uv** (fast modern package manager):
```bash
uv tool install cyberzard
# Or run without installing:
uvx cyberzard scan
```

#### Option 2: One-liner installer (Linux binary)

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

Upgrade later:

```bash
# PyPI upgrade
pip install --upgrade cyberzard

# Binary upgrade
cyberzard --upgrade                    # quick upgrade using global flag
cyberzard upgrade --channel stable     # explicit upgrade command
```

#### Option 3: Install from source (development)

```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e .[openai]   # or .[anthropic] or .[dev]
```

Notes:
- **PyPI**: Available at https://pypi.org/project/cyberzard/
- **Linux binaries**: Pre-built binaries available on [GitHub Releases](https://github.com/elwizard33/Cyberzard/releases)
- **macOS/Windows**: Use PyPI install (`pip install cyberzard`)

Optional TUI (terminal UI):

```bash
pip install 'textual>=0.60'
cyberzard tui
```

Common commands:

```bash
# Scan and pretty print
cyberzard scan

# JSON findings
cyberzard scan --json > findings.json

# Advice (static + optional AI enrichment)
CYBERZARD_MODEL_PROVIDER=openai OPENAI_API_KEY=sk-... cyberzard advise

# Explain findings (AI)
OPENAI_API_KEY=sk-... cyberzard explain --provider openai

# Bounded reasoning loop (ReAct)
OPENAI_API_KEY=sk-... cyberzard agent "Top suspicious processes and rationale" --steps 4

# Interactive chat (permission‑aware)
cyberzard chat
cyberzard chat --auto-approve --max-probes 8

# Remediation (requires explicit flags)
cyberzard remediate --delete --kill --preserve

# n8n deployment assistant (generate + optional apply)
# Native (OpenLiteSpeed reverse-proxy):
cyberzard n8n-setup --domain example.com --subdomain n8n --mode native --basic-auth --out-dir ./out

# Cloudflare Tunnel (docker compose + cloudflared):
cyberzard n8n-setup --domain example.com --subdomain n8n --mode tunnel --out-dir ./out

# Write-only JSON summary (no apply):
cyberzard n8n-setup --domain example.com --mode native --write-only --out-dir ./out --overwrite

# Email security (scan + hardening preview)
cyberzard email-security --dry-run

# Execute guided (still dry-run by default until --no-dry-run)
cyberzard email-security --run --dry-run --max-risk medium

# Full remediation guide + optional execution
cyberzard email-fix --run --dry-run --max-risk low

# JSON output (no rich)
cyberzard email-security --json --run --dry-run
```

Troubleshooting
- Editable install error (missing build_editable hook): upgrade pip/setuptools/wheel in a venv, or use non‑editable install:
  - `python -m pip install -U pip setuptools wheel`
  - `pip install .[openai]` (or `.[anthropic]` or just `.`)


### Environment

| Var | Purpose | Default |
|---|---|---|
| CYBERZARD_PROVIDER | `openai`, `anthropic`, `xai`, `none` | `none` |
| OPENAI_API_KEY | API key when provider=openai | — |
| ANTHROPIC_API_KEY | API key when provider=anthropic | — |
| XAI_API_KEY | API key when provider=xai | — |
| CYBERZARD_EVIDENCE_DIR | Evidence dir | `/var/lib/cyberzard/evidence` |
| CYBERZARD_DRY_RUN | Global dry‑run | `true` |

Check available providers:
```bash
cyberzard providers
```

### Safety Model

- No raw shell; curated, allow‑listed tools only
- Dry‑run by default; explicit flags to delete/kill
- Reasoning step cap; sandboxed helpers
- AI optional; offline works fine

### MCP Server (Model Context Protocol)

Cyberzard can act as an MCP server, exposing all its security tools to AI agents like Claude:

```bash
# Start MCP server (stdio transport for Claude Desktop)
cyberzard mcp

# Start with SSE transport for web clients
cyberzard mcp --transport sse --port 8080

# Start with streamable HTTP transport
cyberzard mcp --transport streamable-http --port 8080
```

Configure in Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cyberzard": {
      "command": "cyberzard",
      "args": ["mcp"],
      "env": {}
    }
  }
}
```

Available tools via MCP:
- `scan_server` - Full security scan
- `read_file` - Safe file reading
- `propose_remediation` - Generate remediation plans
- CyberPanel management (websites, databases, email, DNS, SSL, backups, firewall)

### CyberPanel Integration

Cyberzard integrates with CyberPanel's REST API for server management:

```bash
# Set CyberPanel credentials
export CYBERPANEL_HOST=https://your-server:8090
export CYBERPANEL_USER=admin
export CYBERPANEL_PASS=your-password

# Use via chat mode
cyberzard chat
> List all websites on this server
> Create a new database called myapp_db

# Or programmatically in Python
from cyberzard.cyberpanel import CyberPanelClient
client = CyberPanelClient()
websites = await client.list_websites()
```

Supported operations:
- **Websites**: List, create, delete, suspend/unsuspend
- **Databases**: List, create, delete MySQL/MariaDB databases
- **Email**: Accounts, forwarders, DKIM
- **DNS**: Records management
- **SSL**: Issue/renew certificates
- **Firewall**: CSF rules, block/unblock IPs
- **Backups**: Create, restore, schedule

### Enhanced TUI (Terminal UI)

The enhanced TUI provides a split-panel chat interface:

```bash
# Install TUI dependencies
pip install 'cyberzard[tui]'

# Run chat TUI
cyberzard chat --tui

# Or legacy scan TUI
cyberzard tui
```

Features:
- **Split layout**: Conversation on left, tools on right
- **Real-time tool tracking**: See tool calls as they execute
- **Streaming responses**: Watch AI responses as they generate
- **Keyboard shortcuts**: Ctrl+L (clear), Ctrl+T (toggle tools), q (quit)

---

## 🧰 Legacy Cleanup Scripts

### Overview

Basic and Advanced bash scripts to triage and clean common artifacts from the November CyberPanel attacks.

| Capability | Basic | Advanced |
|---|---|---|
| Diagnostics (files, processes, encrypted files) | ✅ | ✅ |
| Cleanup of artifacts | ✅ | ✅ |
| User + SSH key audit | — | ✅ |
| Interactive confirmations | — | ✅ |
| Extra post‑hardening tips | — | ✅ |

### Quick Start

Basic:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/wizard_cleanup.sh)"
```

Advanced:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/advanced_wizard_cleanup.sh)"
```

### Decrypt Helpers

- `.psaux` files: [1-decrypt.sh](https://gist.github.com/gboddin/d78823245b518edd54bfc2301c5f8882/raw/d947f181e3a1297506668e347cf0dec24b7e92d1/1-decrypt.sh)
- `.encryp` files: [encryp_dec.out](https://github.com/v0idxyz/babukencrypdecrytor/raw/c71b409cf35469bb3ee0ad593ad48c9465890959/encryp_dec.out)

---

## 🤝 Contributing

Please read the [Issue Guide](ISSUE_GUIDE.md) before filing.

- Small, focused PRs with tests/docs updates are welcome
- Clearly document environment and reproduction steps

## ⚠️ Disclaimer

These tools are provided as‑is, without warranty. Validate outputs before acting in production. Maintain backups and snapshots.

---

### Useful References

- [ManagingWP CyberPanel RCE Auth Bypass](https://github.com/managingwp/cyberpanel-rce-auth-bypass)
- [ArrayIterator's Cleanup Gist](https://gist.github.com/ArrayIterator/ebd67a0b4862e6bfb5d021c9f9d8dcd3)
- [Yoyosan's Cleanup Gist](https://gist.github.com/yoyosan/5f88c1a023f006f952d7378bdc7bcf01)
- [NothingCtrl's First Cleanup Gist](https://gist.github.com/NothingCtrl/710a12db2acb01baf66e3b4572919743)
- [NothingCtrl's Second Cleanup Gist](https://gist.github.com/NothingCtrl/78a7a8f0b2c35ada80bf6d52ac4cfef0)
- [Crosstyan's Cleanup Gist](https://gist.github.com/crosstyan/93966e4ab9c85b038e85308df1c8b420)

