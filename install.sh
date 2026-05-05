#!/usr/bin/env bash
#
# Benoit OS installer
# Sets up skills, agents, slash commands, statusline, and MCP servers
# in your Claude Code + Claude Desktop environment.
#
# Usage: ./install.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
DESKTOP_CONFIG="${HOME}/Library/Application Support/Claude/claude_desktop_config.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; }

# 1. Skills — symlinks so edits in this repo flow back to Claude Code
echo "→ Installing skills"
mkdir -p "${CLAUDE_DIR}/skills"
for skill_dir in "${REPO_ROOT}"/skills/*/; do
  skill_name="$(basename "${skill_dir%/}")"
  target="${CLAUDE_DIR}/skills/${skill_name}"
  if [[ -L "${target}" || -d "${target}" ]]; then
    warn "skills/${skill_name} already exists, skipping"
  else
    ln -s "${skill_dir%/}" "${target}"
    info "skills/${skill_name} linked"
  fi
done

# 2. Agents — copies (Claude Code reads from ~/.claude/agents/)
echo "→ Installing agents"
mkdir -p "${CLAUDE_DIR}/agents"
for agent in "${REPO_ROOT}"/agents/*.md; do
  cp "${agent}" "${CLAUDE_DIR}/agents/"
  info "agents/$(basename "${agent}") copied"
done

# 3. Slash commands
echo "→ Installing slash commands"
mkdir -p "${CLAUDE_DIR}/commands"
for cmd in "${REPO_ROOT}"/commands/*.md; do
  cp "${cmd}" "${CLAUDE_DIR}/commands/"
  info "commands/$(basename "${cmd}") copied"
done

# 4. Statusline script
echo "→ Installing statusline"
mkdir -p "${CLAUDE_DIR}/scripts"
cp "${REPO_ROOT}/config/statusline.sh" "${CLAUDE_DIR}/scripts/status-line.sh"
chmod +x "${CLAUDE_DIR}/scripts/status-line.sh"
info "statusline installed"

# 5. Settings — never overwrite an existing one
echo "→ Settings"
if [[ -f "${CLAUDE_DIR}/settings.json" ]]; then
  warn "${CLAUDE_DIR}/settings.json exists — not overwritten"
  warn "  → see config/settings.example.json for reference"
else
  cp "${REPO_ROOT}/config/settings.example.json" "${CLAUDE_DIR}/settings.json"
  info "settings.json created from template"
fi

# 6. agent-vm — the sandbox foundation
echo "→ agent-vm (sandbox)"
if [[ ! -d "${HOME}/Dev/agent-vm" ]]; then
  git clone https://github.com/benoitvx/agent-vm "${HOME}/Dev/agent-vm"
  info "cloned agent-vm into ~/Dev/agent-vm"
  warn "  → run 'agent-vm setup' once to finish initialization"
else
  info "agent-vm already present"
fi

# 7. MCP — render configs from .env
echo "→ MCP servers"
if [[ ! -f "${REPO_ROOT}/.env" ]]; then
  warn ".env not found — copy .env.example to .env, fill secrets, then re-run"
  warn "  → MCP configs not rendered"
else
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a

  # Clone custom MCP servers if missing
  if [[ ! -d "${HOME}/Dev/mcp-docs" ]]; then
    git clone https://github.com/benoitvx/mcp-docs "${HOME}/Dev/mcp-docs"
    info "cloned mcp-docs into ~/Dev/mcp-docs"
  fi

  # Render Claude Desktop config (warns if exists)
  if [[ -f "${DESKTOP_CONFIG}" ]]; then
    warn "claude_desktop_config.json exists — not overwritten"
    warn "  → render manually with: envsubst < mcp/claude-desktop.example.json"
  else
    mkdir -p "$(dirname "${DESKTOP_CONFIG}")"
    envsubst < "${REPO_ROOT}/mcp/claude-desktop.example.json" > "${DESKTOP_CONFIG}"
    info "claude_desktop_config.json rendered"
  fi
fi

echo
info "Benoit OS installed."
echo "Next steps:"
echo "  • Restart Claude Code and Claude Desktop"
echo "  • Enable claude.ai connectors (Gmail, Drive, data.gouv, etc.) at https://claude.ai"
echo "  • See mcp/README.md for the full MCP setup"
