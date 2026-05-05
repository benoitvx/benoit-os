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
├── weekly-watch/        # Template réutilisable de pipeline veille hebdo
├── docs/                # Carte écosystème + ma façon de bosser avec les agents
└── install.sh           # Installeur one-shot
```

## Où je fais tourner tout ça — `agent-vm`

L'essentiel de mon travail avec les agents se passe **dans [agent-vm](https://github.com/benoitvx/agent-vm)** — des VMs Lima sandboxées scopées à un dossier local, pré-configurées avec Chrome DevTools MCP, Docker et les outils dev. Ça résout le problème "donner de l'autonomie à l'agent sans exposer la machine" et c'est la fondation sur laquelle tout le reste de ce repo se branche.

Les skills, agents et MCPs de Benoit OS sont pensés pour s'exécuter dans une session agent-vm — c'est la combinaison safety + leverage que je prends par défaut.

## Skills (6)

| Skill | Trigger | Rôle |
|---|---|---|
| `pause-session` | `/pause-session` | Sauve l'état d'une session Claude Code pour reprise via `claude --resume` |
| `save-article` | `/save-article <url>` | Sauvegarde un article web en markdown propre dans un vault Obsidian |
| `react-dsfr` † | mention DSFR / react-dsfr | Crée des UI React conformes au Design System de l'État |
| `rgaa` † | mention RGAA / accessibilité | Audit et application du référentiel RGAA 4.1.2 |
| `securite-anssi` † | mention ANSSI / durcissement | Applique les règles essentielles de sécurité ANSSI |
| `design-principles` | `/design-principles` | Applique un design system minimal et précis (taste Linear/Notion/Stripe) |

† Aussi publié comme skill officiel État dans [`etalab-ia/skills`](https://github.com/etalab-ia/skills).

## Skills externes que j'utilise

Skills que j'utilise au quotidien mais qui viennent d'ailleurs :

| Skill | Source |
|---|---|
| `rag-parse` | Anthropic builtin — parse PDF, DOCX, PPTX, XLSX en markdown localement |
| `skill-creator` | Anthropic builtin |

## Agents (4)

| Agent | Usage |
|---|---|
| `cadrer` | Dialogue socratique de 20-30 min pour cadrer un POC produit |
| `runtime` | Setup pas-à-pas GitHub + skills + hébergement |
| `obsidian-vault-manager` | Gère notes, liens, frontmatter dans un vault Obsidian |
| `obsidian-vault-organizer` | Réorganise et refactorise la structure d'un vault |

## MCPs

Voir [`mcp/README.md`](mcp/README.md) pour le détail :

- **For work** — Docs (La Suite), Gmail, Drive
- **For data** — data.gouv, data.education, Parlement (Tricoteuses), Leximpact, Open Legi, Pappers
- **For code** — Context7, Hugging Face, Chrome DevTools
- **Experiment** — DVF (MCP App immobilier)

## Recettes

- [`weekly-watch/`](weekly-watch/) — pipeline **veille technologique hebdo** réutilisable (cron + collecteur RSS/Atom + workflow GHA + prompt de synthèse). Extrait d'une pipeline que je fais tourner en prod pour le département IAE de la DINUM.

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
