# How I work with agents

A short field note on the operating system above the operating system.

## Premise

In 2026, *using* AI tools is not a differentiator. *Owning* a small agentic infrastructure tuned to your work is. This repo is the materialization of that idea for one operator.

## Where I spend my time

Across the Anthropic surface, my usage roughly splits as:

- **Claude Code — 80%.** Where the actual work happens: shipping POCs, MCP servers, content, decks. The agentic primitives below are tuned for it.
- **claude.ai — 10%.** For one-shot research with the connectors (Gmail, Drive, data.gouv, Parlement, Pappers). When the question is read-only and lives on the open web or my mailbox, it's faster than firing up Claude Code.
- **Claude Cowork — 10%.** Long-running scheduled jobs, my weekly tech-watch pipeline, async agent runs that don't need me supervising.

The 80% is why this repo exists — Claude Code is where the leverage compounds.

## My second brain

I run Obsidian as my second brain — meeting notes, research, drafts, decisions, an Index of weekly tech-watch syntheses. It's the source-of-truth that survives any tool, any laptop. That's why two of the skills in this repo touch Obsidian directly (`save-article` for ingest, `obsidian-vault-manager` / `obsidian-vault-organizer` agents for upkeep): the agentic stack and the second brain are the same surface.

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

## A real-world example: my weekly tech-watch pipeline

The clearest illustration of how the four primitives compose is a workflow I run for the IAE department of DINUM, every Monday morning, on autopilot.

**Stage 1 — collection (GitHub Actions, Monday 7h UTC).** A Python script reads a YAML list of 8 RSS/Atom sources (Latent Space, Pragmatic Engineer, MCP Blog, IBM Technology, etc.), filters by the past week's date range, fetches the full article text, and commits a structured JSON snapshot to the repo.

**Stage 2 — synthesis (Claude Cowork, Monday ~10h).** A scheduled Cowork task reads that JSON, applies a 5-axis thematic synthesis prompt, writes a clean markdown digest, and updates the index.

**Stage 3 — distribution (Docs MCP, on demand).** When I'm ready, `/publier-veille-docs` pushes the synthesis straight into La Suite Docs at the right node in the documentation tree.

The team gets a curated weekly read for ~5 minutes of upkeep. No manual collection, no copy-paste, no "I'll catch up next week." That's an operator multiplier.

The pattern is templated and reusable in [`veille/`](../veille/) — strip the DINUM-specific 8 sources, point it at your own feeds, edit the prompt, ship it.

## Why dotfiles for AI matter

Dotfiles for shells codified a generation of developer taste — what aliases, which prompt, which keybindings. Dotfiles for AI codify *agentic* taste — what skills, which agents, which MCPs, what they're for. The codification is the point: the moment you can ship your agent stack to a new machine in one command, the stack stops being friction and starts being leverage.

This repo is mine. Fork it, gut it, replace half of it.
