---
title: Configuration
description: Configure Cyberzard settings
---

# Configuration

Set environment variables or a future `config.toml` (planned). Precedence: CLI flags > environment.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CYBERZARD_PROVIDER` | Provider selection: `openai`, `anthropic`, `xai`, `none` | `none` |
| `CYBERZARD_MODEL` | Override default model per provider | Provider default |
| `CYBERZARD_MAX_CONTEXT_BYTES` | Upper bound for model context payload | 20000 |
| `CYBERZARD_NO_HISTORY` | Disable transcript retention | unset |
| `OPENAI_API_KEY` | API key for OpenAI provider | — |
| `ANTHROPIC_API_KEY` | API key for Anthropic provider | — |
| `XAI_API_KEY` | API key for xAI (Grok) provider | — |

> **Note:** `CYBERZARD_MODEL_PROVIDER` is supported for backward compatibility but `CYBERZARD_PROVIDER` is preferred.

## Provider Setup

### OpenAI
```bash
export CYBERZARD_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

### Anthropic
```bash
export CYBERZARD_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

### xAI (Grok)
```bash
export CYBERZARD_PROVIDER=xai
export XAI_API_KEY=xai-...
```

Or per-invocation without changing your shell environment:
```bash
cyberzard --provider anthropic advise
cyberzard --provider xai advise
```

## Check Available Providers

Use the `providers` command to see which providers are available:

```bash
cyberzard providers
```

This shows a table with:
- Provider name and default model
- Package installation status
- API key configuration status
- Whether auto-detection would select it

## Data storage

- Chat history is persisted to `cyberzard_agent.sqlite` in the project directory.
- Use `cyberzard chat --session <id>` to segment conversations (each session has its own history).
- Clear the current session during chat with `/clear`.

