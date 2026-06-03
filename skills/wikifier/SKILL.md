---
name: wikifier
description: Walk an Obsidian vault and automatically add `[[Name]]` wikilinks to plain-text mentions of canonical entities (sheets under `Entities/` or `Entités/`). Dry-run by default (markdown report), `--apply` to modify files. Invoke when the user says "wikify the vault", "add backlinks", "/wikifier", or after creating new canonical entity sheets.
---

# wikifier

Densifies backlinks in a vault following Karpathy's [LLM Wiki pattern](../../docs/karpathy-pattern.md) by wikifying plain-text mentions of canonical entities.

## Workflow

### 1. Dry-run (default)

```bash
python3 ".claude/skills/wikifier/scripts/wikify.py"
```

Writes a markdown report to stdout: lists the files and `[[Name]]` links that would be created, **without modifying anything**.

### 2. Present to the user

Top files by number of wikilinks created, plus the top entities. Confirm before applying.

### 3. Apply

```bash
python3 ".claude/skills/wikifier/scripts/wikify.py" --apply
```

Modifies files in place. No internal backup — make sure the user has a commit / snapshot first.

### 4. Re-run `/vault-lint`

To verify no broken link was introduced.

## Rules

**Wikified**:
- Exact match (case-sensitive) of the full canonical name of an `Entities/` sheet
- Word boundary before/after to avoid "Albert API" → "Albert" + " API"

**Skipped**:
- YAML frontmatter (between the two leading `---`)
- Fenced code blocks (` ``` `)
- Inline code (`` `...` ``)
- Existing wikilinks (`[[X]]` is not re-wikified)
- Markdown links (`[text](url)`)
- Raw URLs (`http://...`, `https://...`)
- Self-reference: the sheet `Alice Martin.md` does not wikify "Alice Martin" in its own body
- **One link per name per file** (first occurrence only) — keeps the result readable

**Priority**: longest names first (e.g. "MCP Gateway" matches before "MCP", "Albert API" before "Albert").

## Configuration

Edit the constants at the top of `scripts/wikify.py`:

- `EXCLUDE_PATH_PREFIXES` — raw-source folders to skip (default examples: `<meeting-notes>/Inbox`, `<watch>/Sources`). Replace with the actual relative paths in your vault.
- `EXCLUDE_DIRS` — folders to skip globally.
- `SKIP_FILES` — files that should never be modified (`Index.md`, `CLAUDE.md`, `log.md`, the entity catalog itself).
- `ENTITIES_ROOTS` — root folder name(s) for the canonical entities layer (default: `Entités`, `Entities`).

## Implementation notes

- Python stdlib only — no external dependencies.
- Coverage: the entire vault except the raw-source folders, `.git`, `.obsidian`, `.claude`, `node_modules`, `.agents`.
- Skips `Entities/Index.md` (self-references everywhere).
- Recommend running after creating new entity sheets — the skill doesn't track changes automatically.
- Vault root auto-detected by walking up from the script until `CLAUDE.md` or `.obsidian/` is found.

## See also

- [`docs/karpathy-pattern.md`](../../docs/karpathy-pattern.md) — the pattern this skill supports
- [`skills/vault-lint/`](../vault-lint/) — run after `--apply` to verify no broken link
- [`skills/ficher/`](../ficher/) — creates new entity sheets; offer `/wikifier --apply` after
