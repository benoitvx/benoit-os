#!/usr/bin/env python3
"""cc2vibe — pont de migration Claude Code <-> Mistral Vibe.

Établit une *source unique* avec pont bidirectionnel entre les deux CLI agentiques :
- instructions : AGENTS.md = vérité, CLAUDE.md = @AGENTS.md (les deux outils convergent) ;
- skills       : Vibe lit les mêmes .claude/skills via `skill_paths` (zéro duplication) ;
- agents/MCP/settings : conversion vers le format Vibe (config.toml / TOML) ;
- non portable (hooks/RTK, statusLine, commands custom, MCP OAuth) : rapporté, pas bloqué.

Python 3.8+, stdlib uniquement. Voir README.md pour l'usage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS_MAP = json.loads((HERE / "mappings" / "tools.json").read_text(encoding="utf-8"))
MODELS_MAP = json.loads((HERE / "mappings" / "models.json").read_text(encoding="utf-8"))
# Champs internes des fichiers de mapping (préfixés '_') à ignorer.
TOOLS_MAP = {k: v for k, v in TOOLS_MAP.items() if not k.startswith("_")}
MODELS_MAP = {k: v for k, v in MODELS_MAP.items() if not k.startswith("_")}

# Motifs trahissant un contenu spécifique à Claude Code dans une skill.
CLAUDE_SPECIFIC = re.compile(r"claude\s+--resume|Sessions Claude|CLAUDE\.md|\.claude/|/home/.+\.claude", re.I)


# --------------------------------------------------------------------------- #
# Contexte & utilitaires                                                       #
# --------------------------------------------------------------------------- #
class Ctx:
    """Chemins source/cible résolus pour le mode projet ou global."""

    def __init__(self, args):
        self.dry = args.dry_run
        self.actions: list[str] = []
        self.warnings: list[str] = []
        if args.global_:
            home = Path.home()
            vibe_home = Path(os.environ.get("VIBE_HOME", home / ".vibe"))
            self.scope_name = "global"
            self.claude_md = home / ".claude" / "CLAUDE.md"
            self.agents_md = vibe_home / "AGENTS.md"
            self.claude_skills = home / ".claude" / "skills"
            self.claude_agents = home / ".claude" / "agents"
            self.settings_json = home / ".claude" / "settings.json"
            self.mcp_sources = [home / ".claude" / ".mcp.json"]
            self.vibe_dir = vibe_home
            self.report = vibe_home / "MIGRATION-REPORT.md"
        else:
            root = Path(args.project).resolve()
            self.scope_name = f"projet ({root})"
            self.claude_md = root / "CLAUDE.md"
            self.agents_md = root / "AGENTS.md"
            self.claude_skills = root / ".claude" / "skills"
            self.claude_agents = root / ".claude" / "agents"
            self.settings_json = root / ".claude" / "settings.json"
            self.mcp_sources = [root / ".mcp.json", root / ".claude" / ".mcp.json"]
            self.vibe_dir = root / ".vibe"
            self.report = root / "MIGRATION-REPORT.md"
        self.vibe_config = self.vibe_dir / "config.toml"
        self.vibe_skills = self.vibe_dir / "skills"
        self.vibe_agents = self.vibe_dir / "agents"
        self.vibe_prompts = self.vibe_dir / "prompts"

    def write(self, path: Path, content: str):
        rel = path
        if self.dry:
            self.actions.append(f"[dry-run] écrirait {rel} ({len(content)} o)")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.actions.append(f"écrit {rel} ({len(content)} o)")

    def warn(self, msg: str):
        self.warnings.append(msg)

    def bak_path(self, path: Path) -> Path:
        return path.parent / (path.name + ".bak")

    def backup(self, path: Path):
        """Sauvegarde path -> path.bak avant réécriture. Ne touche jamais un .bak existant
        (préserve l'original pristine même si bridge est rejoué)."""
        if not path.exists():
            return
        bak = self.bak_path(path)
        if bak.exists():
            self.actions.append(f"sauvegarde déjà présente, conservée : {bak}")
            return
        if self.dry:
            self.actions.append(f"[dry-run] sauvegarderait {path} -> {bak}")
            return
        shutil.copy2(path, bak)
        self.actions.append(f"sauvegardé {path} -> {bak}")


def toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_list(items) -> str:
    return "[" + ", ".join(toml_str(str(i)) for i in items) + "]"


def parse_frontmatter(text: str):
    """Parseur YAML-frontmatter minimal (stdlib only).

    Gère `key: value`, listes inline `[a, b]` ou `a, b`, et listes en bloc `- item`.
    Renvoie (dict, corps).
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    meta: dict = {}
    key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                meta[key] = []  # potentielle liste en bloc qui suit
            elif val.startswith("[") and val.endswith("]"):
                meta[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            elif "," in val and key.lower() in ("allowed-tools", "tools", "disallowed-tools"):
                meta[key] = [x.strip() for x in val.split(",") if x.strip()]
            else:
                meta[key] = val.strip("'\"")
        elif line.lstrip().startswith("-") and key is not None and isinstance(meta.get(key), list):
            meta[key].append(line.lstrip()[1:].strip().strip("'\""))
    return meta, body


def map_tools(tools):
    """Mappe une liste de noms d'outils CC -> Vibe ; renvoie (mappés, inconnus)."""
    out, unknown = [], []
    for t in tools:
        t = t.strip()
        if not t:
            continue
        if t in TOOLS_MAP:
            out.append(TOOLS_MAP[t])
        else:
            out.append(t)  # MCP & co : conservés tels quels
            if t not in TOOLS_MAP.values():
                unknown.append(t)
    # dédup en gardant l'ordre
    seen, deduped = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped, unknown


def map_model(model: str) -> str:
    return MODELS_MAP.get(model, MODELS_MAP.get("default", "devstral-2"))


def ensure_config_key(ctx: Ctx, key: str, toml_line: str) -> bool:
    """Ajoute `toml_line` à config.toml si `key` absent. Renvoie True si modifié."""
    existing = ctx.vibe_config.read_text(encoding="utf-8") if ctx.vibe_config.exists() else ""
    if re.search(rf"(?m)^\s*{re.escape(key)}\s*=", existing):
        ctx.actions.append(f"config.toml : `{key}` déjà présent, laissé tel quel")
        return False
    header = "" if existing.endswith("\n") or not existing else "\n"
    ctx.write(ctx.vibe_config, existing + header + toml_line.rstrip() + "\n")
    return True


# --------------------------------------------------------------------------- #
# Sous-commandes                                                               #
# --------------------------------------------------------------------------- #
def resolve_imports(path: Path, depth=0, seen=None) -> str:
    """Inline récursivement les lignes `@fichier` d'un CLAUDE.md (max 5 niveaux)."""
    seen = seen or set()
    if depth > 5 or path in seen or not path.exists():
        return ""
    seen.add(path)
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*@(\S+)\s*$", line)
        if m:
            target = (path.parent / m.group(1)).resolve()
            inlined = resolve_imports(target, depth + 1, seen)
            out.append(f"<!-- inliné depuis {m.group(1)} -->\n{inlined}" if inlined else line)
        else:
            out.append(line)
    return "\n".join(out)


def cmd_bridge(ctx: Ctx):
    """Source unique : AGENTS.md canonique + CLAUDE.md = @AGENTS.md."""
    if not ctx.claude_md.exists():
        ctx.warn(f"Aucun {ctx.claude_md} : pont d'instructions ignoré.")
        return
    canonical = resolve_imports(ctx.claude_md).strip() + "\n"
    # Sauvegardes avant toute réécriture -> `restore` = simple copie du .bak.
    # `already_bridged` (un CLAUDE.md.bak existe déjà) signale que AGENTS.md a été *généré*
    # par un bridge précédent : on ne le sauvegarde pas (sinon on capturerait du contenu généré).
    # On ne préserve donc un AGENTS.md que s'il était *écrit par l'utilisateur* avant le 1er bridge.
    already_bridged = ctx.bak_path(ctx.claude_md).exists()
    ctx.backup(ctx.claude_md)
    if not already_bridged:
        ctx.backup(ctx.agents_md)
    ctx.write(ctx.agents_md, canonical)
    # CLAUDE.md ne devient qu'un import vers AGENTS.md.
    if ctx.scope_name == "global":
        # Dirs distincts (~/.claude vs ~/.vibe) -> import par chemin absolu.
        import_line = f"@{ctx.agents_md}\n"
    else:
        import_line = "@AGENTS.md\n"
    ctx.write(ctx.claude_md, import_line)
    ctx.actions.append("Instructions : AGENTS.md = source de vérité, CLAUDE.md l'importe.")
    ctx.actions.append("Pour défaire : `cc2vibe restore` (restaure les .bak).")


def cmd_restore(ctx: Ctx):
    """Annule `bridge`. CLAUDE.md (et un AGENTS.md pré-existant) sont restaurés depuis leur .bak.
    Un AGENTS.md *généré* par bridge (pas de .bak) est supprimé pour revenir à l'état d'origine."""
    did = False
    # CLAUDE.md : toujours depuis son .bak.
    claude_bak = ctx.bak_path(ctx.claude_md)
    if claude_bak.exists():
        if ctx.dry:
            ctx.actions.append(f"[dry-run] restaurerait {claude_bak} -> {ctx.claude_md}")
        else:
            shutil.copy2(claude_bak, ctx.claude_md)
            ctx.actions.append(f"restauré {ctx.claude_md} depuis {claude_bak}")
        did = True
    # AGENTS.md : .bak -> restaurer l'original utilisateur ; sinon -> supprimer le fichier généré.
    agents_bak = ctx.bak_path(ctx.agents_md)
    if agents_bak.exists():
        if ctx.dry:
            ctx.actions.append(f"[dry-run] restaurerait {agents_bak} -> {ctx.agents_md}")
        else:
            shutil.copy2(agents_bak, ctx.agents_md)
            ctx.actions.append(f"restauré {ctx.agents_md} depuis {agents_bak}")
        did = True
    elif ctx.agents_md.exists():
        if ctx.dry:
            ctx.actions.append(f"[dry-run] supprimerait {ctx.agents_md} (généré par bridge)")
        else:
            ctx.agents_md.unlink()
            ctx.actions.append(f"supprimé {ctx.agents_md} (généré par bridge)")
        did = True
    if not did:
        ctx.warn("Aucune sauvegarde .bak trouvée à restaurer (bridge jamais appliqué ?).")


def cmd_skills(ctx: Ctx):
    """Partage les .claude/skills via skill_paths + convertit celles à réécrire."""
    if not ctx.claude_skills.exists():
        ctx.warn(f"Aucun dossier {ctx.claude_skills} : skills ignorées.")
        return
    # 1) Vibe lit directement les fichiers existants -> pas de duplication.
    path_for_toml = ".claude/skills" if ctx.scope_name != "global" else str(ctx.claude_skills)
    ensure_config_key(ctx, "skill_paths", f"skill_paths = {toml_list([path_for_toml])}")

    # 2) Conversion ciblée des skills qui référencent des outils/modèles à renommer
    #    ou du contenu spécifique Claude.
    skill_files = sorted(ctx.claude_skills.glob("*/SKILL.md"))
    for sf in skill_files:
        name = sf.parent.name
        meta, body = parse_frontmatter(sf.read_text(encoding="utf-8"))
        needs_copy = False
        new_meta_lines = []
        for k, v in meta.items():
            if k.lower() in ("allowed-tools", "tools", "disallowed-tools") and isinstance(v, list):
                mapped, _ = map_tools(v)
                if mapped != v:
                    needs_copy = True
                new_meta_lines.append(f"{k}: {', '.join(mapped)}")
            elif k.lower() == "model" and isinstance(v, str):
                mm = map_model(v)
                if mm != v:
                    needs_copy = True
                new_meta_lines.append(f"{k}: {mm}")
            elif isinstance(v, list):
                new_meta_lines.append(f"{k}: [{', '.join(v)}]")
            else:
                new_meta_lines.append(f"{k}: {v}")
        if CLAUDE_SPECIFIC.search(body):
            ctx.warn(f"Skill `{name}` contient des références spécifiques Claude Code "
                     f"(p.ex. `claude --resume`, « Sessions Claude/ ») — à adapter pour Vibe.")
        if needs_copy:
            fm = "---\n" + "\n".join(new_meta_lines) + "\n---\n\n"
            ctx.write(ctx.vibe_skills / name / "SKILL.md", fm + body)
        else:
            ctx.actions.append(f"Skill `{name}` : compatible telle quelle (lue via skill_paths).")


def cmd_agents(ctx: Ctx):
    """.claude/agents/*.md -> .vibe/agents/<n>.toml + prompts/<n>.md."""
    if not ctx.claude_agents.exists():
        ctx.actions.append("Aucun sous-agent custom à convertir.")
        return
    for af in sorted(ctx.claude_agents.glob("*.md")):
        meta, body = parse_frontmatter(af.read_text(encoding="utf-8"))
        name = meta.get("name", af.stem)
        model = map_model(meta.get("model", "default"))
        tools = meta.get("tools", []) or meta.get("allowed-tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",") if t.strip()]
        mapped, _ = map_tools(tools)
        lines = [
            f'agent_type = "subagent"',
            f"active_model = {toml_str(model)}",
            f"system_prompt_id = {toml_str(name)}",
        ]
        if meta.get("description"):
            lines.insert(0, f"description = {toml_str(meta['description'])}")
        if mapped:
            lines.append(f"enabled_tools = {toml_list(mapped)}")
        ctx.write(ctx.vibe_agents / f"{name}.toml", "\n".join(lines) + "\n")
        ctx.write(ctx.vibe_prompts / f"{name}.md", body.strip() + "\n")
        ctx.warn(f"Agent `{name}` : `system_prompt_id` pointe vers ~/.vibe/prompts/{name}.md — "
                 f"vérifier que Vibe le résout (sinon déplacer le prompt sous VIBE_HOME).")


def _load_mcp_servers(ctx: Ctx):
    """Agrège les serveurs MCP depuis .mcp.json et settings.json (clé mcpServers)."""
    servers = {}
    candidates = list(ctx.mcp_sources)
    if ctx.settings_json.exists():
        candidates.append(ctx.settings_json)
    for c in candidates:
        if not c.exists():
            continue
        try:
            data = json.loads(c.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            ctx.warn(f"{c} : JSON illisible, ignoré.")
            continue
        servers.update(data.get("mcpServers", {}))
    return servers


def cmd_mcp(ctx: Ctx):
    """Serveurs MCP -> blocs [[mcp_servers]] dans .vibe/mcp.generated.toml."""
    servers = _load_mcp_servers(ctx)
    ctx.warn("MCP : les serveurs connectés via claude.ai (OAuth) ne sont pas lisibles depuis un "
             "fichier et **ne sont pas supportés par Vibe** (pas d'OAuth) — à reconfigurer à la main.")
    if not servers:
        ctx.actions.append("Aucun serveur MCP déclaré dans un fichier (.mcp.json / settings.json).")
        return
    blocks = ["# Généré par cc2vibe — à fusionner dans config.toml.",
              "# ⚠️ Retirer toute ligne `mcp_servers = []` de config.toml avant d'ajouter ces blocs.\n"]
    for name, cfg in servers.items():
        b = ["[[mcp_servers]]", f"name = {toml_str(name)}"]
        if cfg.get("command"):
            b.append('transport = "stdio"')
            b.append(f"command = {toml_str(cfg['command'])}")
            if cfg.get("args"):
                b.append(f"args = {toml_list(cfg['args'])}")
            if cfg.get("env"):
                env_items = ", ".join(f"{toml_str(k)} = {toml_str(v)}" for k, v in cfg["env"].items())
                b.append(f"env = {{ {env_items} }}")
        elif cfg.get("url"):
            b.append('transport = "http"')
            b.append(f"url = {toml_str(cfg['url'])}")
            if cfg.get("headers"):
                hdr = ", ".join(f"{toml_str(k)} = {toml_str(v)}" for k, v in cfg["headers"].items())
                b.append(f"headers = {{ {hdr} }}")
        else:
            ctx.warn(f"MCP `{name}` : ni `command` ni `url` reconnus, bloc partiel.")
        blocks.append("\n".join(b))
    ctx.write(ctx.vibe_dir / "mcp.generated.toml", "\n\n".join(blocks) + "\n")


def cmd_settings(ctx: Ctx):
    """settings.json -> config.toml (partiel) + rapport des non-portables."""
    if not ctx.settings_json.exists():
        ctx.actions.append("Aucun settings.json à convertir.")
        return
    try:
        s = json.loads(ctx.settings_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        ctx.warn(f"{ctx.settings_json} : JSON illisible.")
        return
    if "theme" in s:
        ensure_config_key(ctx, "theme", f"theme = {toml_str(s['theme'])}")
    perms = s.get("permissions", {})
    if perms.get("allow"):
        ctx.actions.append(f"Permissions `allow` ({len(perms['allow'])}) -> à traduire en "
                           f"`enabled_tools`/`[tools.*] permission` (revue manuelle conseillée).")
    if s.get("hooks"):
        names = ", ".join(s["hooks"].keys())
        ctx.warn(f"**Hooks non portables** ({names}) : Vibe n'a pas de système de hooks. "
                 f"Le hook RTK (`rtk hook claude`) n'a pas d'équivalent — pas d'économie de tokens "
                 f"côté Vibe. Alternative : invoquer `rtk proxy <cmd>` manuellement.")
    if s.get("statusLine"):
        ctx.warn("**statusLine non portable** : pas d'équivalent documenté côté Vibe.")


# --------------------------------------------------------------------------- #
# Rapport                                                                      #
# --------------------------------------------------------------------------- #
def write_report(ctx: Ctx, ran: list[str]):
    lines = [
        "# Rapport de migration Claude Code -> Mistral Vibe",
        "",
        f"_Périmètre : {ctx.scope_name} — commandes : {', '.join(ran)}_",
        "",
        "## ✅ Actions réalisées",
        "",
    ]
    lines += [f"- {a}" for a in ctx.actions] or ["- (aucune)"]
    lines += ["", "## ⚠️ À traiter manuellement", ""]
    lines += [f"- {w}" for w in ctx.warnings] or ["- (rien)"]
    lines += [
        "",
        "## Rappels format Vibe",
        "",
        "- Instructions lues depuis `AGENTS.md` (projet : remonte les dossiers parents).",
        "- Skills : `skill_paths` dans `config.toml` peut pointer vers `.claude/skills` (fichiers partagés).",
        "- Commands custom : non supportées par Vibe -> à envelopper en skills.",
        "- TOML : retirer `mcp_servers = []` avant d'ajouter des blocs `[[mcp_servers]]`.",
        "",
    ]
    ctx.write(ctx.report, "\n".join(lines))


COMMANDS = {
    "bridge": cmd_bridge,
    "skills": cmd_skills,
    "agents": cmd_agents,
    "mcp": cmd_mcp,
    "settings": cmd_settings,
}
ALL_ORDER = ["bridge", "skills", "agents", "mcp", "settings"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="cc2vibe", description="Pont de migration Claude Code <-> Mistral Vibe.")
    p.add_argument("command", choices=list(COMMANDS) + ["all", "report", "restore"],
                   help="bridge | skills | agents | mcp | settings | all | report | restore")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--project", default=".", help="Racine du projet (défaut : dossier courant).")
    g.add_argument("--global", dest="global_", action="store_true",
                   help="Cibler la config globale (~/.claude <-> ~/.vibe).")
    p.add_argument("--dry-run", action="store_true", help="N'écrit rien, montre les actions.")
    args = p.parse_args(argv)

    ctx = Ctx(args)
    if args.command == "restore":
        cmd_restore(ctx)
        ran = ["restore"]
    else:
        ran = ALL_ORDER if args.command in ("all", "report") else [args.command]
        if args.command != "report":
            for c in ran:
                COMMANDS[c](ctx)
    write_report(ctx, ran)

    head = "DRY-RUN — aucune écriture" if ctx.dry else "Migration appliquée"
    print(f"== cc2vibe : {head} ({ctx.scope_name}) ==")
    for a in ctx.actions:
        print(f"  ✓ {a}")
    if ctx.warnings:
        print("  -- À traiter manuellement --")
        for w in ctx.warnings:
            print(f"  ! {w}")
    print(f"\nRapport : {ctx.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
