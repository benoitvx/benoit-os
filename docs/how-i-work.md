# How I work with agents

A short field note on the operating system above the operating system.

## Premise

In 2026, *using* AI tools is not a differentiator. *Owning* a small agentic infrastructure tuned to your work is. This repo is the materialization of that idea for one operator.

## The four primitives

I think of my Claude Code setup as four composable layers.

**1. Skills** — auto-loaded knowledge bundles tied to triggers. They bring expertise into the session without me asking. `rgaa` brings 106 accessibility criteria with code patterns. `securite-anssi` brings ANSSI hardening rules. `react-dsfr` brings the French State design system. The skill fires when the situation calls for it; I never have to re-prime the agent.

**2. Agents** — sub-personas the main agent can hand off to. `cadrer` runs a 30-minute product framing dialog. `runtime` walks through repo + hosting setup. `obsidian-vault-manager` reorganizes thousands of notes. Each one encapsulates a workflow that recurs.

**3. MCPs** — the agent's senses and hands. Gmail and Drive for work surface. data.gouv, Parlement, Leximpact, Pappers for the public-data layer I navigate daily. Context7 and Chrome DevTools for code. Custom MCP servers (`mcp-docs`, `dvf-mcp-app`) where no off-the-shelf tool exists.

**4. Slash commands and statusline** — the muscle memory layer. `/pause-session` ports my context to a new machine. `/save-article` is a one-token reflex when something interesting passes through.

## How they compose

A typical Tuesday morning:

1. I `/save-article` three pieces from my reading list — they land structured in my Obsidian vault.
2. I open Claude Code in a project, ask for a UI tweak. `react-dsfr` and `rgaa` skills trigger automatically; the agent ships a DSFR-conformant, accessible component without me asking.
3. I hand off to `cadrer` to think through a new POC. Output: a `SPEC.md` ready for `runtime` to scaffold.
4. The Docs MCP publishes the resulting one-pager directly to La Suite. The Gmail MCP drafts the announcement.

No glue code. The primitives compose. Each one is small, replaceable, and documented in this repo.

## Why dotfiles for AI matter

Dotfiles for shells codified a generation of developer taste — what aliases, which prompt, which keybindings. Dotfiles for AI codify *agentic* taste — what skills, which agents, which MCPs, what they're for. The codification is the point: the moment you can ship your agent stack to a new machine in one command, the stack stops being friction and starts being leverage.

This repo is mine. Fork it, gut it, replace half of it.
