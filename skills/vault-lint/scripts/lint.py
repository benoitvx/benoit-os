#!/usr/bin/env python3
"""vault-lint — Consistency audit for an Obsidian vault using Karpathy's LLM Wiki pattern.

Detects:
- name duplicates (make `[[X]]` wikilinks ambiguous)
- broken wikilinks (`[[X]]` pointing nowhere)
- orphan canonical entity sheets (no backlink elsewhere)
- entity sheets with incomplete or mismatched frontmatter (`type:` / `status:`)

Modes:
- default: audit, markdown report on stdout.
- `--fix`: apply trivial corrections (missing frontmatter on entity sheets). Does NOT touch
  duplicates, broken links, or type mismatches.

Configuration — edit the constants below to match your vault.
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path


def find_vault_root() -> Path:
    """Walk up from this script until a marker file is found (CLAUDE.md or .obsidian/)."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "CLAUDE.md").is_file() or (parent / ".obsidian").is_dir():
            return parent
    return Path(os.getcwd())


VAULT_ROOT = find_vault_root()

# Obsidian wikilinks: [[X]], [[X|alias]], [[X#section]], [[X.md]], [[Foo/Bar]]
WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+?)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")

EXCLUDE_DIRS = {".git", ".obsidian", "node_modules", ".claude", ".trash", ".agents"}

# Path prefixes (relative to vault root) to exclude — the "raw sources" layer
# of Karpathy's pattern (transcripts, inbox dumps, web captures).
# Replace with the actual paths used in your vault.
EXCLUDE_PATH_PREFIXES = (
    "<meeting-notes>/Inbox",
    "<watch>/Sources",
)

# Files allowed to exist under the same basename multiple times.
ALLOWED_DUPLICATE_NAMES = {
    "Index",
    "_README",
    "README",
    "CLAUDE",
    "claude",
    "SKILL",
    "_docs",
}

# Weekly / monthly series accepted as duplicates (independent series per folder).
HEBDO_PATTERN = re.compile(r"^(Hebdo S\d{2}|S\d{2}|Week \d{2}|W\d{2})$")

# Binary / data extensions — not notes; ignore as wikilink targets (Obsidian embeds).
NON_NOTE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic", ".ico", ".bmp",
    ".pdf", ".sketch", ".base", ".csv", ".xlsx", ".xls", ".docx", ".pptx",
    ".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a",
    ".zip", ".tar", ".gz", ".rar",
    ".html", ".htm", ".json", ".yaml", ".yml",
}

# Map your entity subfolders to expected `type:` values. Supports FR + EN folder names.
PATH_TO_TYPE = {
    # FR
    "Personnes": "personne",
    "Organisations": "organisation",
    "Produits": "produit",
    "Concepts": "concept",
    # EN
    "People": "person",
    "Organizations": "organization",
    "Products": "product",
}

# Per-language default `status:` value used when --fix needs to insert it.
FR_TYPES = {"personne", "organisation", "produit"}  # "concept" is shared FR/EN
EN_TYPES = {"person", "organization", "product"}
VALID_TYPES = FR_TYPES | EN_TYPES | {"concept"}
VALID_STATUS = {"actif", "archive", "active", "archived"}

# Root folder name(s) for the canonical entities layer.
ENTITIES_ROOTS = ("Entités", "Entities")


def default_status_for(rel: Path, expected_type: str) -> str:
    """Pick the right status default (FR/EN) when --fix has to insert one.

    "concept" is ambiguous on its own (same word both languages), so we
    fall back to the root folder name (`Entités/` → FR, `Entities/` → EN).
    """
    if expected_type in EN_TYPES:
        return "active"
    if expected_type in FR_TYPES:
        return "actif"
    # `concept` — disambiguate via the root folder name
    return "actif" if str(rel).startswith("Entités/") else "active"


def is_excluded(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    s = str(path)
    return any(s.startswith(prefix) for prefix in EXCLUDE_PATH_PREFIXES)


def is_allowed_duplicate(name: str) -> bool:
    if name in ALLOWED_DUPLICATE_NAMES:
        return True
    if HEBDO_PATTERN.match(name):
        return True
    return False


def is_non_note_target(raw_target: str) -> bool:
    """True if the wikilink points to a binary/data file (Obsidian embed)."""
    basename = raw_target.split("/")[-1].lower()
    return any(basename.endswith(ext) for ext in NON_NOTE_EXTENSIONS)


def scan_files(root: Path) -> tuple[dict[str, list[Path]], list[Path]]:
    """Return (basename → [relative_paths], all_relative_paths)."""
    by_name: dict[str, list[Path]] = defaultdict(list)
    all_files: list[Path] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root)
        if is_excluded(rel):
            continue
        all_files.append(rel)
        by_name[path.stem].append(rel)
    return dict(by_name), all_files


INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def strip_inline_code(line: str) -> str:
    """Mask backtick-delimited inline code so wikilinks inside it aren't picked up."""
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def extract_wikilinks_with_codeblocks(text: str):
    """Yield (basename, raw_target, lineno) ignoring fenced code blocks and inline code."""
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        scan_line = strip_inline_code(line)
        for m in WIKILINK_RE.finditer(scan_line):
            raw = m.group(1).strip()
            if raw.endswith(".md"):
                raw = raw[:-3]
            if not raw:
                continue
            if is_non_note_target(raw):
                continue
            basename = raw.split("/")[-1]
            yield basename, raw, lineno


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_with_delimiters, body). Empty frontmatter if none."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return "", text
    lines = text.splitlines(keepends=True)
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return "".join(lines[: i + 1]), "".join(lines[i + 1 :])
    return "", text


def is_entity_path(rel: Path) -> bool:
    return any(str(rel).startswith(f"{root}/") for root in ENTITIES_ROOTS)


def expected_type_for(rel: Path) -> str | None:
    """Expected `type:` for an entity sheet based on its folder. None if not applicable."""
    if not is_entity_path(rel):
        return None
    if rel.name == "Index.md":
        return None
    parts = rel.parts
    if len(parts) < 2:
        return None
    return PATH_TO_TYPE.get(parts[1])


def check_entites_frontmatter(all_files: list[Path]) -> list[tuple[Path, str, str]]:
    """Return [(path, issue_type, details)] for entity sheets with incomplete frontmatter.

    issue_type ∈ {'no_frontmatter', 'no_type', 'no_status', 'type_mismatch', 'status_invalid'}
    """
    issues: list[tuple[Path, str, str]] = []
    for rel in all_files:
        expected = expected_type_for(rel)
        if expected is None:
            continue
        try:
            text = (VAULT_ROOT / rel).read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        fm, _body = split_frontmatter(text)

        if not fm:
            issues.append((rel, "no_frontmatter", expected))
            continue

        type_match = re.search(r"^type:\s*(\S+)\s*$", fm, re.MULTILINE)
        status_match = re.search(r"^status:\s*(\S+)\s*$", fm, re.MULTILINE)

        if not type_match:
            issues.append((rel, "no_type", expected))
        elif type_match.group(1) not in VALID_TYPES:
            issues.append((rel, "type_mismatch", f"{type_match.group(1)} → {expected}"))
        elif type_match.group(1) != expected:
            issues.append((rel, "type_mismatch", f"{type_match.group(1)} → {expected}"))

        if not status_match:
            issues.append((rel, "no_status", default_status_for(rel, expected)))
        elif status_match.group(1) not in VALID_STATUS:
            issues.append((rel, "status_invalid", status_match.group(1)))

    return issues


def fix_frontmatter_issue(rel: Path, issue_type: str, details: str) -> bool:
    """Fix a trivial issue (no_frontmatter, no_type, no_status). Return True if modified.

    Does NOT fix: type_mismatch, status_invalid (human required).
    """
    if issue_type in ("type_mismatch", "status_invalid"):
        return False

    path = VAULT_ROOT / rel
    text = path.read_text(encoding="utf-8")

    if issue_type == "no_frontmatter":
        status = default_status_for(rel, details)
        new_fm = f"---\ntype: {details}\nstatus: {status}\n---\n\n"
        path.write_text(new_fm + text, encoding="utf-8")
        return True

    fm, body = split_frontmatter(text)
    if not fm:
        return False
    lines = fm.splitlines(keepends=True)

    if issue_type == "no_type":
        lines.insert(1, f"type: {details}\n")
    elif issue_type == "no_status":
        insert_idx = len(lines) - 1
        for i in range(1, len(lines)):
            if lines[i].rstrip() == "---":
                insert_idx = i
                break
        lines.insert(insert_idx, f"status: {details}\n")
    else:
        return False

    path.write_text("".join(lines) + body, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Obsidian vault consistency.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply trivial corrections (missing frontmatter on entity sheets).",
    )
    args = parser.parse_args()

    by_name, all_files = scan_files(VAULT_ROOT)

    # 1. Duplicates
    duplicates = {
        name: paths
        for name, paths in by_name.items()
        if len(paths) > 1 and not is_allowed_duplicate(name)
    }

    # 2. Broken wikilinks + backlink counts
    broken_links: dict[str, list[tuple[str, int]]] = defaultdict(list)
    link_counts: dict[str, int] = defaultdict(int)
    for rel in all_files:
        try:
            text = (VAULT_ROOT / rel).read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for basename, raw, lineno in extract_wikilinks_with_codeblocks(text):
            link_counts[basename] += 1
            if basename not in by_name:
                broken_links[raw].append((str(rel), lineno))

    # 3. Orphan entity sheets
    entites_files = [f for f in all_files if is_entity_path(f) and f.name != "Index.md"]
    orphans = [f for f in entites_files if link_counts.get(f.stem, 0) == 0]

    # Report
    out = []
    out.append("# vault-lint report\n")
    out.append(f"Vault: `{VAULT_ROOT.name}`")
    out.append(f"Markdown files scanned: **{len(all_files)}**\n")

    if duplicates:
        out.append(f"## ⚠️ Name duplicates ({len(duplicates)})\n")
        out.append("Multiple files share the same basename — `[[Name]]` wikilinks are ambiguous.\n")
        for name, paths in sorted(duplicates.items()):
            out.append(f"- **{name}** ({len(paths)}×):")
            for p in paths:
                out.append(f"  - `{p}`")
        out.append("")
    else:
        out.append("## ✅ No name duplicates\n")

    if broken_links:
        n_total = sum(len(v) for v in broken_links.values())
        out.append(f"## ❌ Broken wikilinks ({len(broken_links)} targets, {n_total} occurrences)\n")
        sorted_targets = sorted(broken_links.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        for target, occs in sorted_targets:
            out.append(f"- `[[{target}]]` — {len(occs)} occ.")
            for src, line in occs[:5]:
                out.append(f"  - `{src}:{line}`")
            if len(occs) > 5:
                out.append(f"  - … (+{len(occs)-5} more)")
        out.append("")
    else:
        out.append("## ✅ No broken wikilinks\n")

    if orphans:
        out.append(f"## 🌱 Orphan entity sheets ({len(orphans)})\n")
        out.append("No wikilink points to these sheets from the rest of the vault.\n")
        for o in sorted(orphans, key=str):
            out.append(f"- `{o}`")
        out.append("")
    else:
        out.append("## ✅ All entity sheets have at least 1 backlink\n")

    # 4. Entity frontmatter
    fm_issues = check_entites_frontmatter(all_files)

    fixable_issues = [i for i in fm_issues if i[1] not in ("type_mismatch", "status_invalid")]

    fixed_count = 0
    if args.fix and fixable_issues:
        for rel, issue_type, details in fixable_issues:
            if fix_frontmatter_issue(rel, issue_type, details):
                fixed_count += 1
        fm_issues = check_entites_frontmatter(all_files)
        fixable_issues = [i for i in fm_issues if i[1] not in ("type_mismatch", "status_invalid")]

    if fm_issues:
        out.append(f"## ⚠️ Incomplete entity frontmatter ({len(fm_issues)})\n")
        if args.fix:
            out.append(f"**Fix applied**: {fixed_count} automatic corrections.\n")
            if fm_issues:
                out.append("Remaining issues (human required):\n")
        else:
            n_fixable = len(fixable_issues)
            if n_fixable:
                out.append(f"{n_fixable} auto-fixable with `--fix` (missing frontmatter, absent type/status field).\n")

        issue_labels = {
            "no_frontmatter": "No frontmatter",
            "no_type": "Missing `type:` field",
            "no_status": "Missing `status:` field",
            "type_mismatch": "Type ≠ path (human required)",
            "status_invalid": "Invalid status (human required)",
        }
        by_kind: dict[str, list[tuple[Path, str]]] = defaultdict(list)
        for rel, issue_type, details in fm_issues:
            by_kind[issue_type].append((rel, details))
        for kind in ("no_frontmatter", "no_type", "no_status", "type_mismatch", "status_invalid"):
            entries = by_kind.get(kind, [])
            if not entries:
                continue
            out.append(f"### {issue_labels[kind]} ({len(entries)})")
            for rel, details in sorted(entries, key=lambda x: str(x[0])):
                out.append(f"- `{rel}` — {details}")
            out.append("")
    else:
        if args.fix and fixed_count:
            out.append(f"## ✅ Entity frontmatter: {fixed_count} corrections applied, all OK\n")
        else:
            out.append("## ✅ Entity frontmatter consistent\n")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
