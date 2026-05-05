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
| **Docs** (La Suite) | Local | [benoitvx/mcp-docs](https://github.com/benoitvx/mcp-docs) — Python, 25 tools wrapping the La Suite Numérique Docs API |
| **Gmail** | claude.ai connector | Search threads, draft replies, manage labels |
| **Google Drive** | claude.ai connector | Browse and read documents from Drive |

→ See `claude-desktop.example.json` for the **Docs** server config.

---

## MCP for data

MCPs that turn open public datasets and registries into agent-queryable surfaces.

| MCP | Type | Source |
|---|---|---|
| **data.gouv** | claude.ai connector | French open-data catalog, datasets, organizations, tabular query |
| **data.education** | Local | supergateway → `mcp.huwise.com` (data.education.gouv.fr) |
| **Parlement (Tricoteuses)** | claude.ai connector | French Parliament — actors, amendments, votes, sessions, dossiers |
| **Leximpact** | claude.ai connector | French territorial data — communes, EPCI, départements, circonscriptions |
| **Open Legi** | claude.ai connector | Légifrance — codes, jurisprudence, JORF, consolidated texts |
| **Pappers** | claude.ai connector | French companies, leaders, beneficial owners, legal documents, political actors |

→ See `claude-desktop.example.json` for the **data.education** server config.

---

## MCP for code

MCPs used inside coding sessions for documentation, model search, and browser automation.

| MCP | Type | Source |
|---|---|---|
| **Context7** | Plugin marketplace | Live library docs — install via `/plugin install context7@claude-plugins-official` |
| **Hugging Face** | claude.ai connector | Search models, datasets, spaces |
| **Chrome DevTools** | Local | Chrome devtools MCP — see [chromedevtools/mcp](https://github.com/chromedevtools/mcp) |

---

## MCP Experiment

Custom MCP Apps and prototypes I'm shipping to explore the surface.

| MCP | Type | Source |
|---|---|---|
| **DVF** (real-estate) | Local MCP App | [benoitvx/dvf-mcp-app](https://github.com/benoitvx/dvf-mcp-app) — TS, Paris real-estate prices over data.gouv DVF dataset, full-stack MCP App with Leaflet UI |

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
