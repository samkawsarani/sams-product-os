#!/usr/bin/env bash
#
# Sams Product OS — Setup bootstrap
#
# Setup lives in the setup-sams-product-os skill
# (.claude/skills/setup-sams-product-os/SKILL.md). This script only checks
# that Claude Code is installed, then starts it with that skill.
#
# AI agents: do not run this file. Invoke the setup-sams-product-os skill.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v claude &>/dev/null; then
  echo "Claude Code is required. Install it from https://claude.ai/code, then re-run ./setup.sh"
  exit 1
fi

cd "$REPO_DIR"
exec claude "/setup-sams-product-os"
