#!/usr/bin/env python3
"""wikifier — Add `[[Name]]` wikilinks to plain-text mentions of canonical entities.

Modes:
- dry-run (default): markdown report on stdout, no modification.
- `--apply`: modify files in place.

Configuration — edit the constants below to match your vault.
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path


def find_vault_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "CLAUDE.md").is_file() or (parent / ".obsidian").is_dir():
            return parent
    return Path(os.getcwd())


VAULT_ROOT = find_vault_root()

EXCLUDE_DIRS = {".git", ".obsidian", "node_modules", ".claude", ".trash", ".agents"}

# Path prefixes (relative to vault root) to exclude — the "raw sources" layer of
# Karpathy's pattern (transcripts, inbox dumps, web captures).
# Replace with the actual relative paths in your vault.
EXCLUDE_PATH_PREFIXES = (
    "<meeting-notes>/Inbox",
    "<watch>/Sources",
)

# Files that should never be wikified.
SKIP_FILES = {
    "Entities/Index.md",
    "Entités/Index.md",
    "Index.md",
    "CLAUDE.md",
    "log.md",
}

# Root folder name(s) for the canonical entities layer.
ENTITIES_ROOTS = ("Entités", "Entities")

# Protected zones (per line)
WIKILINK_RE = re.compile(r"\[\[[^\]]*\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"https?://\S+")


def is_excluded(rel: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    s = str(rel)
    if any(s.startswith(p) for p in EXCLUDE_PATH_PREFIXES):
        return True
    return s.lower() in {sf.lower() for sf in SKIP_FILES}


def collect_canonical_names() -> dict[str, Path]:
    """Return {name: relative_path} for every sheet under the entities root(s)."""
    names: dict[str, Path] = {}
    for root_name in ENTITIES_ROOTS:
        root = VAULT_ROOT / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            if path.name == "Index.md":
                continue
            rel = path.relative_to(VAULT_ROOT)
            names[path.stem] = rel
    return names


def mask_protected(line: str) -> str:
    """Mask with spaces: wikilinks, markdown links, inline code, URLs."""
    line = WIKILINK_RE.sub(lambda m: " " * len(m.group(0)), line)
    line = MARKDOWN_LINK_RE.sub(lambda m: " " * len(m.group(0)), line)
    line = INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
    line = URL_RE.sub(lambda m: " " * len(m.group(0)), line)
    return line


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_with_delimiters, body)."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return "", text
    lines = text.splitlines(keepends=True)
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return "", text
    fm = "".join(lines[: end_idx + 1])
    body = "".join(lines[end_idx + 1 :])
    return fm, body


def build_name_regex(names: list[str]) -> re.Pattern:
    """Build a regex matching any canonical name, with word boundaries."""
    # Longest names first (priority)
    sorted_names = sorted(names, key=len, reverse=True)
    pattern = "|".join(re.escape(n) for n in sorted_names)
    # (?<!\w) and (?!\w) = Unicode-aware word boundaries in Python 3
    return re.compile(r"(?<!\w)(" + pattern + r")(?!\w)")


def wikify_file(
    path: Path,
    rel: Path,
    name_regex: re.Pattern,
    apply: bool,
) -> list[tuple[int, str, str]]:
    """Wikify a note. Returns [(lineno, name, original_line)]."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    fm, body = split_frontmatter(text)
    own_name = path.stem

    in_fence = False
    new_lines: list[str] = []
    suggestions: list[tuple[int, str, str]] = []
    already_linked: set[str] = set()  # names already wikified in THIS file

    body_lines = body.splitlines(keepends=False)
    body_ends_with_newline = body.endswith("\n")

    # Pre-scan: note names already present as `[[X]]` anywhere in the file
    # so we don't re-wikify a name that's already linked earlier
    for line in body_lines:
        for m in WIKILINK_RE.finditer(line):
            inner = m.group(0)[2:-2].split("|")[0].split("#")[0].strip()
            if inner.endswith(".md"):
                inner = inner[:-3]
            already_linked.add(inner.split("/")[-1])

    for lineno, line in enumerate(body_lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            new_lines.append(line)
            continue
        if in_fence:
            new_lines.append(line)
            continue

        masked = mask_protected(line)
        matches = list(name_regex.finditer(masked))

        if not matches:
            new_lines.append(line)
            continue

        # Filter: no self-reference + not already wikified in this file
        valid_matches = [
            m for m in matches
            if m.group(1) != own_name and m.group(1) not in already_linked
        ]
        if not valid_matches:
            new_lines.append(line)
            continue

        # If the SAME name appears multiple times on this line, keep only the first
        seen_on_line: set[str] = set()
        first_occurrence_matches = []
        for m in valid_matches:
            if m.group(1) in seen_on_line:
                continue
            seen_on_line.add(m.group(1))
            first_occurrence_matches.append(m)

        # Apply from last match to first to keep positions valid
        new_line = line
        for m in reversed(first_occurrence_matches):
            s, e = m.span()
            name = m.group(1)
            suggestions.append((lineno, name, line.strip()))
            new_line = new_line[:s] + f"[[{name}]]" + new_line[e:]
            already_linked.add(name)
        new_lines.append(new_line)

    new_body = "\n".join(new_lines)
    if body_ends_with_newline:
        new_body += "\n"
    new_text = fm + new_body

    if apply and suggestions and new_text != text:
        path.write_text(new_text, encoding="utf-8")

    return suggestions


def main() -> int:
    parser = argparse.ArgumentParser(description="Wikify an Obsidian vault.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply modifications. Without this flag: dry-run.",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=30,
        help="Max number of files to detail in the report (default: 30).",
    )
    args = parser.parse_args()

    names = collect_canonical_names()
    if not names:
        print("# wikifier report\n")
        print("No `Entities/` sheets found — nothing to wikify.")
        return 0

    name_regex = build_name_regex(list(names.keys()))

    total_links = 0
    files_touched: list[tuple[Path, list[tuple[int, str, str]]]] = []

    for path in VAULT_ROOT.rglob("*.md"):
        rel = path.relative_to(VAULT_ROOT)
        if is_excluded(rel):
            continue
        suggestions = wikify_file(path, rel, name_regex, apply=args.apply)
        if suggestions:
            files_touched.append((rel, suggestions))
            total_links += len(suggestions)

    out = []
    out.append("# wikifier report\n")
    out.append(f"Canonical entity sheets indexed: **{len(names)}**")
    out.append(f"Mode: {'APPLY (files modified)' if args.apply else 'DRY-RUN (no modification)'}\n")
    out.append(f"## {total_links} wikilinks created across {len(files_touched)} files\n")

    if not args.apply:
        out.append("> Re-run with `--apply` to write changes.\n")

    files_touched.sort(key=lambda x: -len(x[1]))

    for rel, suggestions in files_touched[: args.limit_files]:
        out.append(f"### `{rel}` ({len(suggestions)} wikilinks)\n")
        per_name: dict[str, int] = defaultdict(int)
        for lineno, name, ctx in suggestions:
            per_name[name] += 1
        for name, count in sorted(per_name.items(), key=lambda x: (-x[1], x[0])):
            out.append(f"- `[[{name}]]` × {count}")
        out.append("")

    if len(files_touched) > args.limit_files:
        out.append(f"… (+{len(files_touched) - args.limit_files} more files)\n")

    # Top 20 most-wikified entities (across all notes)
    global_counts: dict[str, int] = defaultdict(int)
    for _, suggestions in files_touched:
        for _, name, _ in suggestions:
            global_counts[name] += 1
    top = sorted(global_counts.items(), key=lambda x: (-x[1], x[0]))[:20]
    if top:
        out.append("## Top 20 wikified entities (all notes combined)\n")
        for name, count in top:
            out.append(f"- `[[{name}]]` — {count} mentions")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
