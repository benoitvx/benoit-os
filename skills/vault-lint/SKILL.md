---
name: vault-lint
description: Audit the consistency of an Obsidian vault structured with Karpathy's LLM Wiki pattern — detect broken wikilinks, name duplicates that make `[[X]]` ambiguous, orphan canonical entity sheets (no backlink), and entity sheets with incomplete frontmatter (missing or mismatched `type:` / `status:`). `--fix` mode auto-fills missing frontmatter. Invoke when the user says "lint the vault", "/vault-lint", or after a large reorg / batch creation of entity sheets.
---

# vault-lint

Audits the consistency of an Obsidian vault following Karpathy's [LLM Wiki pattern](../../docs/karpathy-pattern.md) (Wiki + Entities layers).

## Workflow

### 1. Run the scan (audit)

```bash
python3 ".claude/skills/vault-lint/scripts/lint.py"
```

The script reads every `*.md` in the vault (excluding `.git`, `.obsidian`, `.claude`, `node_modules`, plus any raw-source path prefixes you've configured), extracts wikilinks `[[X]]` / `[[X|alias]]` / `[[X#section]]`, checks the frontmatter of `Entities/` (or `Entités/`) sheets, and writes a markdown report to stdout.

### 2. `--fix` mode (trivial auto-corrections)

```bash
python3 ".claude/skills/vault-lint/scripts/lint.py" --fix
```

Applies **non-ambiguous** fixes: adds `type:` + `status:` frontmatter to entity sheets that don't have it, or fills in a missing single field. The type is inferred from the folder path (e.g. `Entities/People/*` → `person`, `Entities/Organizations/*` → `organization`).

**Not auto-fixable** (human required):
- Name duplicates (rename / merge — case-by-case)
- Broken wikilinks (target to invent or pick from candidates)
- Type mismatch (path says "person" but frontmatter says "organization" — classification error to clarify)
- Invalid status (value other than `active` / `archived`)

### 3. Present the report

Four sections:
- **Name duplicates** — files sharing the same basename → `[[X]]` becomes ambiguous
- **Broken wikilinks** — `[[X]]` that points to no file
- **Orphan entity sheets** — sheets in `Entities/` never referenced elsewhere
- **Incomplete entity frontmatter** — sheets without `type:` / `status:` or with invalid values

### 4. Propose fixes for the non-auto-fixable

- **Duplicates**: rename the less canonical sheet or merge. Always confirm with the user.
- **Broken wikilinks**: three cases — typo to correct (propose the mapping), sheet to create via `/ficher`, or obsolete link to delete. List options.
- **Orphans**: not necessarily a bug — a sheet can be freshly created and not yet referenced. List but don't delete. `/wikifier --apply` can densify if the new sheet is mentioned plain-text elsewhere.
- **Type mismatch**: the sheet is probably in the wrong subfolder. Propose moving it.

## Configuration

Edit the constants at the top of `scripts/lint.py` to match your vault layout:

- `EXCLUDE_DIRS` — folders to skip globally (`.git`, `.obsidian`, etc.)
- `EXCLUDE_PATH_PREFIXES` — raw-source folders to skip (default examples: `<meeting-notes>/Inbox`, `<watch>/Sources`). Replace with the actual relative paths in your vault.
- `ALLOWED_DUPLICATE_NAMES` — names that legitimately appear multiple times (`Index`, `_README`, `CLAUDE`, `SKILL`, weekly series like `S01.md`, etc.)
- `PATH_TO_TYPE` — mapping of your entity subfolders to the expected `type:` value. Default: `Personnes`/`People` → `personne`/`person`, etc. Adapt to your language.
- `VALID_TYPES`, `VALID_STATUS` — the vocabulary your frontmatter uses.

## Implementation notes

- Pure Python stdlib (`pathlib`, `re`, `collections`, `argparse`) — no external dependencies.
- Wikilinks `[[Foo/Bar]]` are resolved by their basename `Bar` (matches Obsidian behavior).
- Pure section anchors `[[#section]]` (no filename) are ignored.
- Wikilinks inside protected zones are ignored: frontmatter, fenced code blocks (` ``` `), inline code (`` `...` ``), URLs, markdown links, binary embeds (`.png`, `.pdf`, …).
- Vault root is auto-detected by walking up from the script until `CLAUDE.md` or `.obsidian/` is found.

## See also

- [`docs/karpathy-pattern.md`](../../docs/karpathy-pattern.md) — the pattern this skill enforces
- [`skills/wikifier/`](../wikifier/) — adds wikilinks (run before `vault-lint` to baseline)
- [`skills/ficher/`](../ficher/) — creates new entity sheets with the right frontmatter
