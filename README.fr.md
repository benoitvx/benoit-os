# Benoit OS

> Mon OS agentique perso — skills, agents, serveurs MCP, slash commands, statusline et configs qui se composent sur chaque projet que je touche.

C'est les dotfiles que je voudrais si je devais setup un nouveau Mac et être productif dès le jour 1 avec Claude Code, Claude Desktop, et l'écosystème MCP que j'utilise au quotidien.

## Contenu

```
benoit-os/
├── skills/              # Skills Claude Code (auto-chargés par trigger)
├── agents/              # Sub-agents Claude Code
├── commands/            # Slash commands
├── mcp/                 # Configs MCP (templates, sans secrets)
├── config/              # Template settings.json + statusline
├── plugins/             # Plugins locaux
├── docs/                # Carte écosystème + ma façon de bosser avec les agents
└── install.sh           # Installeur one-shot
```

## Skills (6)

| Skill | Trigger | Rôle |
|---|---|---|
| `pause-session` | `/pause-session` | Sauve l'état d'une session Claude Code pour reprise via `claude --resume` |
| `save-article` | `/save-article <url>` | Sauvegarde un article web en markdown propre dans un vault Obsidian |
| `react-dsfr` | mention DSFR / react-dsfr | Crée des UI React conformes au Design System de l'État |
| `rgaa` | mention RGAA / accessibilité | Audit et application du référentiel RGAA 4.1.2 |
| `securite-anssi` | mention ANSSI / durcissement | Applique les règles essentielles de sécurité ANSSI |
| `design-principles` | `/design-principles` | Applique un design system minimal et précis (taste Linear/Notion/Stripe) |

## Agents (4)

| Agent | Usage |
|---|---|
| `cadrer` | Dialogue socratique de 20-30 min pour cadrer un POC produit — issu d'[eig-vibe](https://github.com/benoitvx/eig-vibe) |
| `runtime` | Setup pas-à-pas GitHub + skills + hébergement — issu d'[eig-vibe](https://github.com/benoitvx/eig-vibe) |
| `obsidian-vault-manager` | Gère notes, liens, frontmatter dans un vault Obsidian |
| `obsidian-vault-organizer` | Réorganise et refactorise la structure d'un vault |

## MCPs

Voir [`mcp/README.md`](mcp/README.md) pour le détail :

- **For work** — Docs (La Suite), Gmail, Drive
- **For data** — data.gouv, data.education, Parlement (Tricoteuses), Leximpact, Open Legi, Pappers
- **For code** — Context7, Hugging Face, Chrome DevTools
- **Experiment** — DVF (MCP App immobilier)

## Install

```bash
git clone https://github.com/benoitvx/benoit-os.git ~/Dev/benoit-os
cd ~/Dev/benoit-os
cp .env.example .env       # remplir les secrets
./install.sh
```

L'installeur :
- symlink `skills/` dans `~/.claude/skills/` (les modifs reviennent dans le repo)
- copie `agents/` et `commands/` dans Claude Code
- installe la statusline
- crée `~/.claude/settings.json` depuis le template (n'écrase pas un existant)
- clone les repos source des MCPs (`mcp-docs`, etc.) dans `~/Dev/`
- rend les configs MCP depuis `.env`

## License

MIT — voir [LICENSE](LICENSE).
