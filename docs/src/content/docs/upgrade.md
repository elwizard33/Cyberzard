---
title: Upgrade & Troubleshooting
description: How to upgrade Cyberzard and resolve common install/upgrade issues
---

# Upgrade & Troubleshooting

This page covers how upgrades work for different install types, what the `edge` vs `stable` channels mean, how to avoid GitHub API rate limits, and how to resolve macOS Gatekeeper issues.

## Upgrade methods

Cyberzard can be installed in several ways:

- **PyPI install** (recommended): `pip install cyberzard`
- **pipx install**: `pipx install cyberzard`
- **Git/source install** (developer mode): cloned repo + `pip install -e .`
- **Binary install** (Linux x86_64, PyInstaller) via our installer script or GitHub Releases

### PyPI / pipx Upgrade

The simplest upgrade path:

```bash
# Standard pip
pip install --upgrade cyberzard

# With pipx
pipx upgrade cyberzard

# With uv
uv pip install --upgrade cyberzard
```

### CLI Upgrade Command

The CLI `upgrade` command handles git/source and binary installs:

- Git/source: runs `git pull` (or checks out latest tag for `--channel stable`) and reinstalls with pip
- Binary (Linux): downloads a new binary from GitHub Releases and atomically replaces the current one (verifies SHA-256 against `checksums.txt`)

To upgrade:

- Run: `cyberzard upgrade --channel stable` to get the latest release
- Or: `cyberzard upgrade --channel edge` to get the newest non-draft release (may be a prerelease)
- For a dry run with binaries: `cyberzard upgrade --dry-run`

If you installed from source and prefer manual control, you can always run `git pull --rebase` and `pip install -e . --upgrade`.

## Channels: stable vs edge

- stable: the latest non-prerelease GitHub Release (the same endpoint used by GitHub’s “Latest” badge)
- edge: the first (most recent) non-draft release returned by `/releases` (prereleases allowed)

If `edge` yields no items (rare), we fall back to `stable`.

## Avoiding GitHub API rate limits

Unauthenticated GitHub API calls are limited and can be throttled on busy networks. The self-updater will use a token automatically if present in either of these environment variables:

- `CYBERZARD_GH_TOKEN`
- `GITHUB_TOKEN`

If you hit rate limits, set one of the variables above to a personal access token (PAT) with public repo read access.

## macOS and Windows

Cyberzard targets Linux servers (CyberPanel). If you’re on macOS or Windows, run Cyberzard on the Linux server directly (SSH in and use the binary), or clone the repo locally for development and tests.

## Manual fallback (reinstall)

If `cyberzard upgrade` fails and you’re not in a git checkout, you can re-run the installer script to replace the current binary:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberzard/main/scripts/install.sh)"
```

On Linux/macOS you can also download a specific release asset and replace the binary manually. Always verify checksums against the published `checksums.txt`.

## Common errors

- Rate limited / API errors during upgrade:
  - Set `CYBERZARD_GH_TOKEN` or `GITHUB_TOKEN` to a valid GitHub token
  - Retry later; the updater has retries/backoff but may still hit global throttles

- Checksum mismatch:
  - Delete the partial download and retry
  - Ensure you downloaded the correct asset for your platform (`macos-arm64`, `macos-x86_64`, `linux-x86_64`)

- Gatekeeper blocked:
  - Prefer signed releases (when available) or remove quarantine for the file you downloaded

- Editable install errors (pip):
  - Ensure `pip`, `setuptools`, and `wheel` are up-to-date; see the note in the Installation page
