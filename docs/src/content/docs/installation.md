---
title: Installation
description: Install Cyberzard CLI and prerequisites
---

# Installation

## Prerequisites
- Python 3.10+ (3.11+ recommended)
- (Optional) LLM provider key: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

## Option 1: Install from PyPI (Recommended)

The easiest way to install Cyberzard:

```bash
pip install cyberzard
```

With AI extras (choose one):
```bash
pip install cyberzard[openai]    # OpenAI support
pip install cyberzard[anthropic] # Anthropic support
pip install cyberzard[all]       # All AI providers
```

### Using pipx (isolated environment)
```bash
pipx install cyberzard
pipx install cyberzard[openai]   # with OpenAI
```

### Using uv (fast installer)
```bash
uv pip install cyberzard
# or run directly without install:
uvx cyberzard scan
```

## Option 2: Linux Binary Installer

One-liner script for Linux servers:
```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

With AI extras:
```bash
CYBERZARD_EXTRAS=openai bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
# or
CYBERZARD_EXTRAS=anthropic bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

### Standalone Binary (no Python needed)
On each GitHub Release we attach Linux x86_64 binaries:

```bash
# Download latest binary
curl -fsSL -o cyberzard \
  https://github.com/elwizard33/Cyberzard/releases/download/$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[^"[:space:]]*\)".*/\1/p')/cyberzard-linux-x86_64 && \
chmod +x cyberzard
```

Verifying checksums:
```bash
curl -fsSL -O \
  https://github.com/elwizard33/Cyberzard/releases/download/$(curl -fsSL https://api.github.com/repos/elwizard33/Cyberzard/releases/latest | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\(v[^"[:space:]]*\)".*/\1/p')/checksums.txt
shasum -a 256 cyberzard | grep -F -f <(cut -d' ' -f1 checksums.txt) || echo 'Checksum mismatch!'
```

## Option 3: Install from Source

For development or latest changes:
```bash
git clone https://github.com/elwizard33/Cyberzard.git
cd Cyberzard
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -e .   # or .[openai] / .[anthropic]
```

## Verify Installation

Run a basic command:
```bash
cyberzard scan
```

If you have a model key:
```bash
export CYBERZARD_MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-... # or set via secret manager
cyberzard agent "Summarize current risks"
```

## Upgrade

### From PyPI
```bash
pip install --upgrade cyberzard
# or with pipx:
pipx upgrade cyberzard
```

### From git/installer-based install
```bash
cyberzard --upgrade   # or: cyberzard upgrade
cyberzard upgrade --channel stable   # use latest tagged release
```

### Manual (from source checkout)
```bash
git pull --rebase
pip install -e . --upgrade
```

See also: [Upgrade & Troubleshooting](./upgrade)

## Troubleshooting

Editable install fails with message like:

> build backend is missing the 'build_editable' hook

Fix:
```bash
python -m pip install -U pip setuptools wheel
pip install -e .    # or non-editable: pip install .
```
This commonly occurs on stock Ubuntu with older pip (22.x).

Docs build on CI fails with rollup optional deps error:

> Cannot find module @rollup/rollup-linux-x64-gnu

Workaround (already applied in CI): remove node_modules and lockfile, then reinstall:
```bash
rm -rf docs/node_modules docs/package-lock.json
cd docs && npm install --legacy-peer-deps && npm run build
```
