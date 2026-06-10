# Référence de migration Claude Code ↔ Mistral Vibe

Doc de fond derrière `cc2vibe.py`. Sources : doc officielle Vibe (configuration, agents-skills,
mcp-servers), retours d'expérience communautaires, et le convertisseur `himmelreich-it/agent-skill-converter`.

## Table de correspondance

| Concept | Claude Code | Mistral Vibe | Stratégie cc2vibe |
|---|---|---|---|
| Instructions globales | `~/.claude/CLAUDE.md` | `~/.vibe/AGENTS.md` | Source unique `AGENTS.md`, `CLAUDE.md` = import |
| Instructions projet | `./CLAUDE.md` | `./AGENTS.md` (remonte les parents) | idem (`@AGENTS.md`) |
| Skills | `.claude/skills/<n>/SKILL.md` | `~/.vibe/skills/` **ou** `skill_paths` | **Même standard** → `skill_paths = [".claude/skills"]` |
| Sous-agents | `.claude/agents/<n>.md` (MD+YAML) | `.vibe/agents/<n>.toml` + `prompts/<n>.md` | Conversion MD → TOML + prompt |
| Slash commands | `.claude/commands/*.md` | ❌ pas de commands custom | Envelopper en skills (manuel) |
| MCP | `.mcp.json` / settings | `config.toml` `[[mcp_servers]]` | Conversion ; **OAuth non supporté** |
| Settings | `settings.json` (JSON) | `config.toml` (TOML) | Conversion partielle |
| Hooks | `settings.json` → hooks | ❌ pas de hooks | **Non portable** → rapport (impacte RTK) |
| Modèles | `opus`/`sonnet`/`haiku` | `devstral-2`, `mistral-*` | `mappings/models.json` |
| Outils | `Read`/`Write`/`Bash`/`TodoWrite`/`Task` | `read_file`/`write`/`bash`/`todo`/`task` | `mappings/tools.json` |

## Le pont bidirectionnel (résout la « reprise »)

1. **Instructions** — `AGENTS.md` devient la **source de vérité**. `CLAUDE.md` est réduit à un import
   (`@AGENTS.md` en projet ; `@<chemin absolu>` en global, dossiers distincts). Claude Code suit
   l'import, Vibe lit `AGENTS.md` nativement → **zéro divergence**. Les `@RTK.md` & co sont **inlinés**
   dans `AGENTS.md` (le support `@import` côté Vibe n'est pas garanti).
2. **Skills** — `config.toml` reçoit `skill_paths` pointant sur `.claude/skills`. Vibe lit **les mêmes
   fichiers `SKILL.md`** → une seule maintenance. Copie convertie uniquement si la frontmatter cite des
   outils/modèles à renommer.
3. **MCP / settings** — formats incompatibles (JSON↔TOML) : générés à part, à fusionner dans `config.toml`.

### Annuler le pont (`restore`)

`bridge` **sauvegarde** `CLAUDE.md` en `CLAUDE.md.bak` avant réécriture ; le `.bak` pristine n'est
**jamais** écrasé si on rejoue `bridge`. `cc2vibe.py restore` :
- restaure `CLAUDE.md` depuis son `.bak` ;
- restaure un `AGENTS.md` qui **préexistait** (depuis `AGENTS.md.bak`) — sinon **supprime** l'`AGENTS.md`
  généré par bridge, pour revenir exactement à l'état d'origine.

## Non portables (rapportés, pas bloquants)

- **Hooks / RTK** : Vibe n'a pas de hooks. Le hook `rtk hook claude` (réécriture des commandes Bash pour
  économiser des tokens) **ne fonctionne pas sous Vibe**. Repli : `rtk proxy <cmd>` à la main.
- **statusLine** : pas d'équivalent documenté.
- **Commands custom** : à reconstruire en skills (une skill peut exposer une commande `/`).
- **MCP OAuth / claude.ai** : Vibe ne gère pas encore l'OAuth → reconfigurer les serveurs manuellement
  (stdio/clé d'API uniquement).

## Pièges connus

- **TOML** : si `config.toml` contient `mcp_servers = []`, le **supprimer** avant d'ajouter des blocs
  `[[mcp_servers]]` (sinon le parseur TOML échoue).
- **Frontmatter YAML replié** (`description: >-` multi-lignes) : le parseur minimal de `cc2vibe.py` ne
  reconstruit pas ces blocs. Sans impact tant que la skill est *partagée* via `skill_paths` (fichier
  d'origine intact) ; ne poserait problème que sur une *copie convertie* — à revoir à la main le cas échéant.
- **Noms de modèles/outils Vibe** : susceptibles d'évoluer → ajuster `mappings/*.json`, pas le script.

## Vérification (end-to-end)

1. `python3 cc2vibe.py all --dry-run` → revoir les actions et avertissements.
2. Appliquer, puis dans le projet :
   - `vibe` : `AGENTS.md` chargé, skills visibles (picker `/` ou `/help`), outils MCP attendus présents.
   - `claude` : instructions toujours lues (via l'import `@AGENTS.md`).
3. Ouvrir `MIGRATION-REPORT.md` : RTK/hooks, statusLine, MCP OAuth bien signalés comme manuels.

## Sources

- Vibe — Configuration : https://docs.mistral.ai/vibe/code/cli/configuration
- Vibe — Agents & Skills : https://docs.mistral.ai/mistral-vibe/agents-skills
- Vibe — MCP servers : https://docs.mistral.ai/vibe/code/cli/mcp-servers
- Vibe — Install & setup : https://docs.mistral.ai/vibe/code/cli/install-setup
- Convertisseur de référence : https://github.com/himmelreich-it/agent-skill-converter
- Retour d'expérience (recréer une command Claude dans Vibe) : https://medium.com/@gareth.hallberg_55290/recreating-a-claude-command-in-mistral-vibe-4f489ca9e6d0
