# Benoit OS

> My personal agent OS — skills, agents, MCP servers, slash commands, statusline and configs that compound across every project I touch.

This is the dotfiles I'd reach for if I had to set up a new Mac and be productive on day one with Claude Code, Claude Desktop, and the MCP ecosystem I use daily.

## What's inside

```
benoit-os/
├── skills/              # Claude Code skills (auto-loaded by trigger)
├── agents/              # Claude Code sub-agents
├── commands/            # Slash commands
├── mcp/                 # MCP server configs (templates, no secrets)
├── config/              # settings.json template + statusline script
├── plugins/             # Local plugins
├── docs/                # Ecosystem map + how I work with agents
└── install.sh           # One-shot installer
```

## Where I run this — `agent-vm`

Most of my agent work happens **inside [agent-vm](https://github.com/benoitvx/agent-vm)** — sandboxed Lima VMs scoped to a local folder, pre-configured with Chrome DevTools MCP, Docker, and dev tools. It solves the "give the agent autonomy without exposing the host" problem and is the foundation everything else in this repo plugs into.

The skills, agents and MCPs of Benoit OS are designed to flow inside an agent-vm session — that's the safety + leverage combo I default to.

## Skills (6)

| Skill | Trigger | What it does |
|---|---|---|
| `pause-session` | `/pause-session` | Save Claude Code session state to resume later via `claude --resume` |
| `save-article` | `/save-article <url>` | Save a web article as clean markdown to an Obsidian vault |
| `react-dsfr` † | mention DSFR / react-dsfr | Build React UIs that conform to the French State design system |
| `rgaa` † | mention RGAA / a11y FR | Audit and apply French web accessibility standard (RGAA 4.1.2) |
| `securite-anssi` † | mention ANSSI / hardening | Apply ANSSI security rules for State-grade web apps |
| `design-principles` | `/design-principles` | Enforce a precise, minimal design system (Linear/Notion/Stripe taste) |

† Also published as an official French gov skill in [`etalab-ia/skills`](https://github.com/etalab-ia/skills).

→ More on each in [`skills/`](skills/)

## External skills I use

Skills I rely on daily but that ship from elsewhere:

| Skill | Source |
|---|---|
| `rag-parse` | Anthropic builtin — parse PDFs, DOCX, PPTX, XLSX into markdown locally |
| `skill-creator` | Anthropic builtin |

## Agents (4)

| Agent | Use |
|---|---|
| `cadrer` | Socratic 20–30 min product framing dialog (zero tech jargon) |
| `runtime` | Step-by-step GitHub + skills + hosting setup |
| `obsidian-vault-manager` | Manage notes, links, frontmatter in an Obsidian vault |
| `obsidian-vault-organizer` | Reorganize and refactor a vault structure |

## MCP servers

Grouped by use-case, see [`mcp/README.md`](mcp/README.md):

- **For work** — Docs (La Suite), Gmail, Drive
- **For data** — data.gouv, data.education, Parlement (Tricoteuses), Leximpact, Open Legi, Pappers
- **For code** — Context7, Hugging Face, Chrome DevTools
- **Experiment** — DVF (real-estate MCP App)

## Install

```bash
git clone https://github.com/benoitvx/benoit-os.git ~/Dev/benoit-os
cd ~/Dev/benoit-os
cp .env.example .env       # fill in your secrets
./install.sh
```

The installer:
- symlinks `skills/` into `~/.claude/skills/` (edits flow back to the repo)
- copies `agents/` and `commands/` into Claude Code
- installs the statusline
- creates `~/.claude/settings.json` from template (won't overwrite existing)
- clones MCP server source repos (`mcp-docs`, etc.) into `~/Dev/`
- renders MCP configs from `.env`

## Related repos

This is the dotfiles. The actual MCP servers and skills with their own audience live in dedicated repos:

- [`benoitvx/mcp-docs`](https://github.com/benoitvx/mcp-docs) — Python MCP server for La Suite Docs API
- [`benoitvx/dvf-mcp-app`](https://github.com/benoitvx/dvf-mcp-app) — TS MCP App for French real-estate data
- [`benoitvx/eig-vibe`](https://github.com/benoitvx/eig-vibe) — Bundle for non-technical PMs to ship POCs through Claude Code
- [`benoitvx/data-gouv-skill`](https://github.com/benoitvx/data-gouv-skill) — Reusable skill + Python lib for the French open-data catalog
- [`benoitvx/agent-vm`](https://github.com/benoitvx/agent-vm) — Sandboxed VMs to run AI coding agents safely

See [`docs/ecosystem.md`](docs/ecosystem.md) for the full map.

## Why this exists

Operators in 2026 don't just use AI agents — they ship their own agent infrastructure. This repo is what that looks like for one person: the skills, agents, MCPs and configs that compound. Every new project I start inherits the same instincts and primitives. That's the leverage.

→ Read more in [`docs/how-i-work.md`](docs/how-i-work.md)

## License

MIT — see [LICENSE](LICENSE).
