# Ecosystem map

Benoit OS sits at the center of a small constellation of repos. This file is the map.

## The dotfiles (this repo)

**[benoit-os](https://github.com/benoitvx/benoit-os)** — skills, agents, MCP configs, slash commands, statusline. The "how I work with Claude" repo.

## MCP servers I built

- **[mcp-docs](https://github.com/benoitvx/mcp-docs)** — Python · MCP wrapping La Suite Numérique's Docs API · 25 tools, used in production at DINUM.
- **[dvf-mcp-app](https://github.com/benoitvx/dvf-mcp-app)** — TypeScript · MCP App (server + sandboxed iframe UI) for Paris real-estate prices over the data.gouv DVF dataset.

## Skills I built (with their own audience)

- **[data-gouv-skill](https://github.com/benoitvx/data-gouv-skill)** — Python · skill + lib to query the French open-data catalog. ★22.
- **[claude-skill-save-webpage-to-obsidian](https://github.com/benoitvx/claude-skill-save-webpage-to-obsidian)** — Markdown · save web articles as Obsidian notes. ★7. *Synced with `skills/save-article/` in this repo.*

## Bundles built on top

- **[eig-vibe](https://github.com/benoitvx/eig-vibe)** — Agents `cadrer` + `runtime` for non-technical PMs at beta.gouv to ship POCs via Claude Code. The two agents in `agents/` come from here.

## Adjacent infrastructure

- **[agent-vm](https://github.com/benoitvx/agent-vm)** — Run AI coding agents inside sandboxed Lima VMs scoped to a folder.
- **[albert-proxy](https://github.com/benoitvx/albert-proxy)** — OpenAI-format compatibility proxy for the French sovereign LLM API (Albert / OpenGateLLM).
- **[albert-code](https://github.com/benoitvx/albert-code)** — One-shot installer for a fully local AI coding stack on macOS (Ollama + Qwen + OpenCode).

## Examples / proofs of concept

- **[veille-IAE](https://github.com/benoitvx/veille-IAE)** — Weekly automated tech-watch pipeline (private).
- **[sources-ia-numerique](https://github.com/benoitvx/sources-ia-numerique)** — National catalog of AI-exploitable public datasets.
- **[observatoire-spdr](https://github.com/benoitvx/observatoire-spdr)** — Dashboard for the 9 reference datasets defined by the French Digital Republic Act.
- **[POC-MCP-datagouv-MediaTech-AlbertAPI-AssistantIA](https://github.com/benoitvx/POC-MCP-datagouv-MediaTech-AlbertAPI-AssistantIA)** — End-to-end POC: vector catalog of 99k datasets + datagouv-mcp + Albert.

## Templates

- **[dsfr-slides-template](https://github.com/benoitvx/dsfr-slides-template)** — Markdown-driven slides framework using the French State design system. ★6.
