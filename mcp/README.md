# MCP servers

The MCP servers I run daily, grouped by use-case.

Three install patterns coexist:
- **Local** — configured in `claude_desktop_config.json` or `~/.claude/settings.json`. Use `claude-desktop.example.json` / `claude-code.example.json` as templates, with secrets from `.env`.
- **claude.ai connector** — enabled from the [claude.ai](https://claude.ai) UI under Settings → Connectors. No local config.
- **Plugin marketplace** — installed via `/plugin install` in Claude Code.

---

## MCP for work

Daily productivity MCPs that read and write across my work surfaces.

| MCP | Type | Source |
|---|---|---|
| **Docs** (La Suite) | Local | [`benoitvx/mcp-docs`](https://github.com/benoitvx/mcp-docs) — 25 tools wrapping the [La Suite Docs](https://docs.numerique.gouv.fr) API |
| **Gmail** | claude.ai connector | [claude.ai](https://claude.ai) → Settings → Connectors → Gmail |
| **Google Drive** | claude.ai connector | [claude.ai](https://claude.ai) → Settings → Connectors → Drive |

→ See `claude-desktop.example.json` for the **Docs** server config.

---

## MCP for data

MCPs that turn open public datasets and registries into agent-queryable surfaces.

| MCP | Type | Source |
|---|---|---|
| **data.gouv** | claude.ai connector | [`datagouv/datagouv-mcp`](https://github.com/datagouv/datagouv-mcp) · [data.gouv.fr](https://www.data.gouv.fr) |
| **data.education** | Local | supergateway → [`mcp.huwise.com`](https://mcp.huwise.com) · [data.education.gouv.fr](https://data.education.gouv.fr) |
| **Parlement (Tricoteuses)** | claude.ai connector | [tricoteuses.fr](https://tricoteuses.fr) — actors, amendments, votes, sessions, dossiers |
| **Leximpact** | claude.ai connector | [leximpact.an.fr](https://leximpact.an.fr) — communes, EPCI, départements, circonscriptions |
| **Open Legi** | claude.ai connector | [legifrance.gouv.fr](https://www.legifrance.gouv.fr) — codes, jurisprudence, JORF |
| **Pappers** | claude.ai connector | [pappers.fr](https://www.pappers.fr) — French companies, leaders, beneficial owners |

→ See `claude-desktop.example.json` for the **data.education** server config.

---

## MCP for code

MCPs used inside coding sessions for documentation, model search, and browser automation.

| MCP | Type | Source |
|---|---|---|
| **Context7** | Plugin marketplace | [`upstash/context7`](https://github.com/upstash/context7) — live library docs |
| **Hugging Face** | claude.ai connector | [huggingface.co](https://huggingface.co) — models, datasets, spaces |
| **Chrome DevTools** | Local | [`ChromeDevTools/chrome-devtools-mcp`](https://github.com/ChromeDevTools/chrome-devtools-mcp) |

---

## MCP Experiment

Custom MCP Apps and prototypes I'm shipping to explore the surface.

| MCP | Type | Source |
|---|---|---|
| **DVF** (real-estate) | Local MCP App | [`benoitvx/dvf-mcp-app`](https://github.com/benoitvx/dvf-mcp-app) — Paris real-estate prices over the data.gouv DVF dataset, full-stack MCP App with Leaflet UI |

---

## Install

For the **Local** MCPs:

```bash
# 1. Fill in secrets
cp ../.env.example ../.env
# edit ../.env

# 2. Render the configs (run from repo root)
./install.sh
```

For **claude.ai connectors**: enable each one manually in [claude.ai](https://claude.ai) Settings → Connectors.

For **plugin marketplaces**: run `/plugin marketplace add <repo>` then `/plugin install <name>` inside Claude Code.
