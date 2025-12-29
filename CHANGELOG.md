# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.1.20] - 2024-12-29
### Fixed
- **Chat agent**: Use correct `prompt` parameter for LangGraph `create_react_agent`
  - `state_modifier` is deprecated, now using `prompt` with `SystemMessage`

## [0.1.19] - 2024-12-29
### Fixed
- **Chat agent**: Use modern LangGraph `create_react_agent` instead of deprecated LangChain AgentExecutor
  - Works across all LangChain versions (0.2.x and 0.3.x)
  - Falls back to legacy AgentExecutor for older installations
- **Dependencies**: Added `langgraph>=0.2.0` as core dependency

## [0.1.18] - 2024-12-29
### Fixed
- **Chat agent**: Fixed `LangChain agent support not available` error
  - Properly import and use `AgentExecutor` wrapper for the tools agent
  - Chat now correctly invokes the agent with tool support
- **Deprecation warning**: Use `connection` instead of deprecated `connection_string` for SQLChatMessageHistory
- **Code cleanup**: Removed debug line markers from chat output

## [0.1.17] - 2024-12-29
### Fixed
- `cyberzard config`: Validate API key before saving
  - Format validation (checks key prefix for OpenAI/Anthropic)
  - Tests API key with actual API call before accepting
  - Better UX: note that input is hidden, retry up to 3 times
  - Prevents empty keys from being saved
  - Shows clear error messages for invalid/failed keys

## [0.1.16] - 2024-12-29
### Added
- **PyPI Publishing**: New GitHub Actions workflow for automated PyPI publishing with trusted publishing (OIDC)
- **Interactive AI Setup**: New `cyberzard config` command for guided AI provider configuration
  - Shows provider status (packages installed, API keys configured)
  - Prompts for API key with secure hidden input
  - Optionally saves to shell profile (`~/.zshrc`, `~/.bashrc`, etc.)
- **Pre-action AI Verification**: Commands that require AI (`agent`, `chat`) now check configuration and offer setup
- **Model Selector System**: New unified model selection with `ModelSelector` class
  - Supports OpenAI, Anthropic, and xAI (Grok) providers
  - Auto-detection of available providers
  - Provider validation with helpful error messages
- **MCP Server**: Model Context Protocol server for AI agent integration (`cyberzard mcp`)
- **Unified Tool System**: Refactored tool registry with schemas and unified interface
- **TUI Improvements**: Enhanced terminal UI with better provider status display

### Changed
- Installation docs now recommend PyPI as primary method (`pip install cyberzard`)
- README badges updated: added PyPI version/downloads, changed status to Beta
- `cyberzard advise` now shows warning when AI not configured but continues in limited mode
- `cyberzard providers` command now suggests `cyberzard config` for setup

### Fixed
- Agent module refactored for better modularity and testability

## [0.1.15] - 2024-09-18
### Fixed
- Switch back to ubuntu-22.04 with --strip flag for better runner availability
- Use PyInstaller --strip flag to create more portable binaries
- Resolves GitHub Actions runner availability issues with ubuntu-20.04

## [0.1.14] - 2024-09-18
### Fixed
- Use Ubuntu 20.04 for binary builds to improve GLIBC compatibility
- Resolves "GLIBC_2.38 not found" error on older Linux systems
- Binary now compatible with GLIBC 2.31+ instead of requiring 2.38+

## [0.1.13] - 2024-09-18
### Fixed
- ChatOpenAI model initialization is now lazy to avoid requiring API key at import time
- Prevents OpenAIError during binary smoke test when OPENAI_API_KEY is not set
- Chat functionality only initializes LangChain components when actually used

## [0.1.12] - 2024-09-18
### Fixed
- PyInstaller binary build now includes complete LangChain dependency chain
- Adds langchain-community and langchain-core to hidden imports and collections
- Resolves ModuleNotFoundError for langchain during binary execution

## [0.1.11] - 2024-09-18
### Fixed
- PyInstaller binary build now includes Textual dependencies and hidden imports
- Explicitly installs textual during build to ensure TUI functionality in binary

## [0.1.10] - 2024-09-18
### Fixed
- PyInstaller binary build now uses proper launcher script instead of relative imports
- Resolves ImportError during binary smoke test in release workflow

## [0.1.9] - 2024-09-18
### Added
- Optional Textual TUI via `cyberzard tui` command
- Global `--upgrade` flag now works with frozen binaries using built-in updater
- Lazy import for TUI to keep Textual as optional dependency

### Fixed
- Global `--upgrade` flag now prefers built-in updater for frozen binaries, falls back to git+pip for dev installs
- TUI compatibility with current Textual API (6.1.0+)

### Changed
- Updated documentation to clarify Linux-only binary releases
- Enhanced installation docs with both `--upgrade` flag and explicit `upgrade` command

## [0.1.0] - 2025-09-07
### Added
- Core scanner suite (files, processes, services, cron, users, SSH keys, encrypted files, composite correlation)
- Severity classification and rationale model
- Rich TTY + JSON reporting
- Hardening advice (static + AI enrichment when provider configured)
- AI providers abstraction (OpenAI / Anthropic) with graceful degradation
- ReAct agent loop with secure tool schema (file read/list/search, scan bridge, sandboxed exec)
- Sandboxed execution environment (AST validation + resource limits)
- Remediation planning & execution (remove / kill) with evidence preservation hook
- Configuration system via environment variables
- Minimal test suite (scanners orchestration, remediation dry run)
- Packaging metadata, dev extras, LICENSE

### Security
- Path allowlist enforcement for destructive operations
- Dry-run default safety

## [Unreleased]
### Planned
- Extended composite heuristics
- Delta scan caching
- YARA integration (optional)

## [0.1.5] - 2025-09-13
### Added
- Email stack scanner (`scan_email_system`) capturing services, queue backlog, SASL auth failures, DNS mismatch, RainLoop config, Fail2Ban, TLS posture, rate limits, Dovecot hardening, firewall, log tail
- Hardening planner (`propose_email_hardening`) with conditional actions (service restart, rate limiting, Fail2Ban, TLS, Dovecot, firewall, monitoring)
- AI email provider (`summarize_email_security`, `generate_email_fix_guide`, `justify_email_action`, `refine_email_action`) with OpenAI / Anthropic + deterministic fallback
- Guided execution engine (`run_guided`) with safety whitelist, dry-run, refinement, structured results
- CLI commands: `email-security` (scan + plan + optional guided exec) and `email-fix` (full remediation guide + optional exec)
### UI
- Rich render helpers: email security summary, execution progress, markdown guide
### Docs
- README feature row & usage examples for new email commands
- New docs pages: `email-security` reference and removal of stray duplicate `email_commands.md`
### Safety
- Command allowlist & heuristics (reject dangerous paths, pipeline downloads, excessive heredocs)
### Misc
- Top-level exports for email scan/plan

## [0.1.4] - 2025-09-12
### Added
- New `n8n-setup` command to guide n8n deployment on CyberPanel
	- Generates native (OpenLiteSpeed reverse-proxy) or tunnel (docker compose + cloudflared) scripts
	- Optional apply step with idempotent execution and Rich-styled feedback
	- Safe handling of secrets (redacted in JSON output)
### Docs
- New "n8n Setup" page with quick start, options, and troubleshooting
- Sidebar TOC updated to include n8n Setup
- Introduction updated to reflect long-term goal: beyond security toward a general-purpose CyberPanel assistant

## [0.1.6] - 2025-09-17
### Added
- LangChain tools agent powering `cyberzard chat` with safe tool calls (run, debug, and complete shell commands via constrained tools)
- SQLite-backed conversation history with per-session isolation (`--session <id>`)
- In-chat commands: `/history [n]`, `/clear`, `/sessions`, `/switch <id>`
- TUI scaffolding command (`tui`) wiring ready for future UI (experimental)
### Docs
- Chat guide updated with session support and in-chat commands
- Commands reference updated (`--session` flag, in-chat commands)
- Introduction now includes a Chat quick start
- Security and Configuration pages note local data storage in `cyberzard_agent.sqlite`
### Developer
- VS Code settings to align interpreter with Anaconda for consistent imports

## [0.1.7] - 2025-09-17
### Added
	- n8n: script-side `.log` capturing method, script, combined output, and explicit exit code marker
	- email: `--log-dir` flag writes structured JSON execution logs per run
	- n8n: chat history session `n8n` records applied/aborted state, mode, and paths
	- email: chat history session `email-troubleshooting` records summary counters and log path
### CLI
### Docs
## v0.1.8 - 2025-09-18
### Changed
- Release workflow trimmed to Linux x86_64 binary only; macOS artifacts removed.
- Installation and Upgrade docs updated to reflect Linux-only binary support and how to use from macOS/Windows via SSH or source install.

### Fixed
- GitHub Actions workflow no longer references secrets in job-level conditions; step now skips cleanly if signing secrets are absent.


## v0.1.9 - 2025-09-18
### Added
- Minimal Textual TUI (`cyberzard tui`) to visualize scan summary, findings table, and plan preview. Optional dependency: `textual>=0.60`.

### Changed
- README updated to reflect Linux-only installer, upgrade instructions, and optional TUI usage.
- Global `--upgrade` flag now prefers the built-in updater when running a frozen/binary build, falling back to git+pip self-update for source checkouts.

### Notes
- macOS users should install from source for now (see README). Binary releases remain Linux-only.

