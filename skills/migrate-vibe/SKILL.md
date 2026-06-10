---
name: migrate-vibe
description: Migre / synchronise une config Claude Code vers Mistral Vibe et établit un pont bidirectionnel (AGENTS.md source unique, skills partagées via skill_paths). Utiliser quand l'utilisateur veut rendre un projet (ou sa config globale) utilisable à la fois avec Claude Code et Mistral Vibe, dit "migrer vers vibe", "/migrate-vibe", "préparer ce projet pour Vibe", "synchroniser CLAUDE.md et AGENTS.md", ou se plaint de devoir refaire sa config en passant de Claude Code à Vibe.
---

# migrate-vibe

Pont de migration Claude Code ↔ Mistral Vibe, piloté par le script `cc2vibe.py` **bundlé dans cette
skill** (`~/.claude/skills/migrate-vibe/cc2vibe.py`, installé par symlink via `install.sh`).
Python 3.8+, stdlib uniquement — aucune dépendance.

## Ce que ça résout

Claude Code et Vibe divergent sur les conventions (`CLAUDE.md` vs `AGENTS.md`, settings JSON vs
`config.toml`, hooks, MCP…). Alterner entre les deux sur un projet casse la « reprise ». Cet outil
établit une **source unique** + un pont bidirectionnel, et **rapporte** ce qui n'est pas portable.

## Workflow

Soit `CC2VIBE=~/.claude/skills/migrate-vibe/cc2vibe.py`.

1. **Toujours commencer par un dry-run** (n'écrit rien) et montrer le résultat avant d'appliquer :
   ```bash
   python3 "$CC2VIBE" all --dry-run                          # projet courant
   python3 "$CC2VIBE" all --project /chemin/projet --dry-run
   python3 "$CC2VIBE" all --global --dry-run                 # config globale ~/.claude <-> ~/.vibe
   ```

2. **Lire le récap.** Le script liste les actions (✓) et les points manuels (!). Présenter à
   l'utilisateur, en insistant sur les **non-portables** : hooks (dont **RTK** → pas d'économie de
   tokens côté Vibe), `statusLine`, commands custom, serveurs **MCP OAuth/claude.ai**.

3. **Appliquer après accord** (retirer `--dry-run`). Le mode `--global` **réécrit**
   `~/.claude/CLAUDE.md` en simple import — confirmer explicitement avant.
   ```bash
   python3 "$CC2VIBE" all --project /chemin/projet
   python3 "$CC2VIBE" bridge --global
   ```

4. **Vérifier** : lancer `vibe` (AGENTS.md chargé, skills visibles), relancer `claude` (instructions
   toujours lues via `@AGENTS.md`), ouvrir le `MIGRATION-REPORT.md` à la racine du projet.

## Sous-commandes

`bridge` (instructions) · `skills` · `agents` · `mcp` · `settings` · `all` · `report` · `restore`.
Flags : `--project <path>` (défaut : courant) | `--global` | `--dry-run`.

**Annuler** : `bridge` sauvegarde `CLAUDE.md` en `.bak` avant réécriture ;
`python3 "$CC2VIBE" restore --project /chemin/projet` revient à l'état d'origine (restaure le `.bak`,
supprime un `AGENTS.md` généré). Rassurer l'utilisateur là-dessus avant d'appliquer.

## Le pont bidirectionnel (résout la « reprise »)

- **Instructions** : `AGENTS.md` = source de vérité, `CLAUDE.md` réduit à `@AGENTS.md`. Les deux outils
  convergent. Les `@imports` (ex. `@RTK.md`) sont inlinés dans `AGENTS.md`.
- **Skills** : `config.toml` reçoit `skill_paths = [".claude/skills"]` → Vibe lit **les mêmes fichiers
  `SKILL.md`** (même standard Agent Skills). Copie convertie uniquement si la frontmatter cite des
  outils/modèles à renommer.
- **MCP/settings** : formats incompatibles (JSON↔TOML) → générés à part, à fusionner dans `config.toml`.

## Adaptations connues à signaler

- **Tables de mapping** : `mappings/tools.json` et `mappings/models.json` (à côté du script) sont
  éditables — ajuster les noms de modèles/outils Vibe si Mistral les fait évoluer.
- **Skill `pause-session`** : spécifique Claude (`claude --resume`, dossier « Sessions Claude/ ») →
  proposer une variante Vibe si l'utilisateur l'utilise sous Vibe.
- **Hooks/RTK, statusLine, commands custom, MCP OAuth** : non portables → détaillés dans `MIGRATION.md`
  et le rapport généré.

Référence complète (table de correspondance, pièges, vérification, sources) : voir
[`MIGRATION.md`](./MIGRATION.md) dans ce dossier.
