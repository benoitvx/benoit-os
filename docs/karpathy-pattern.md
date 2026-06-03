# Karpathy's LLM Wiki Pattern

How I structure an Obsidian vault so an LLM (Claude Code, mostly) can read, write, and stay coherent across hundreds of notes without drifting.

Adapted from Andrej Karpathy's gist: ["LLM-friendly personal wiki"](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## The 5 layers

| Layer | What it holds | Who maintains it | Folder example |
|---|---|---|---|
| **Raw sources** | Transcripts, web captures, inbox dumps. The LLM **reads** but never edits. | Pipelines + me | `<meeting-notes>/Inbox/`, `<watch>/Sources/` |
| **Wiki** | Structured notes, syntheses, meeting CRs, project pages. Maintained and consolidated by the LLM. | LLM + me | Everything else |
| **Canonical entities** | One file = one truth. People, orgs, products, concepts. Referenced everywhere via `[[Name]]`. | LLM (via `/ficher`) | `Entities/` |
| **Schema** | Conventions, glossary, workflows, references. The LLM reads this every turn. | Me | `CLAUDE.md` |
| **Nav** | Root index + structural changelog + lint/wikify skills. | LLM (via skills) | `Index.md`, `log.md` |

## Why it works

- **Wikilinks resolve by name, not path.** Move `Entities/People/Alice Martin.md` to `Entities/People/Internal/Alice Martin.md` and every `[[Alice Martin]]` keeps working. Means the LLM can reorganize folders without breaking the graph.
- **One canonical name per entity.** Avoids "Alice", "Alice M.", "A. Martin" all referring to the same person with no graph linking them. The `/ficher` skill enforces this on creation; `/vault-lint` audits drift over time.
- **Raw sources stay raw.** The LLM is told `<meeting-notes>/Inbox/` and `<watch>/Sources/` are read-only — it ingests them into the Wiki layer but never edits the originals. Anything ingested is then removed from the raw inbox (post-validation prompt in `correction-transcription`).
- **`CLAUDE.md` is the schema.** Loaded into every conversation. Documents the folder layout, naming conventions, wikilink rules, references to authoritative files (org chart, mission letter, master deck, etc.).
- **`log.md` is the changelog.** Structural changes only (folder reorgs, new conventions, skill creations). Not content edits. Lets future-me (and future-LLM) understand why the schema looks the way it does today.

## Skills that go with it

The pattern is just folders + conventions. These three skills make it operational:

| Skill | What it does |
|---|---|
| [`vault-lint`](../skills/vault-lint/) | Audits the vault — broken wikilinks, name duplicates that make `[[X]]` ambiguous, orphan canonical entities, incomplete frontmatter. `--fix` mode auto-fills missing `type:`/`status:` frontmatter on entity files. |
| [`wikifier`](../skills/wikifier/) | Walks the vault and adds `[[Name]]` wikilinks to plain-text mentions of canonical entities. Dry-run by default, `--apply` to write. One link per name per file (first occurrence). |
| [`ficher`](../skills/ficher/) | `/ficher <name>` — creates a new canonical entity sheet with the right template (person / organization / product / concept), updates `Entities/Index.md`, then offers to re-run `/wikifier` to densify backlinks. |

## Setting up the pattern in your own vault

1. **Create `CLAUDE.md`** at the vault root. List the folder structure, the mission/goal, naming conventions, the wikilink rule ("reference canonical entities once per file via `[[Name]]`"), and pointers to authoritative reference files.
2. **Create `Entities/`** with subfolders: `People/`, `Organizations/`, `Products/`, `Concepts/`. Add `Entities/Index.md` as the catalog (one entry per sheet, grouped by category).
3. **Create `Index.md`** at the vault root — catalog of top-level folders + entry points per goal/axis + pointers to sub-indexes.
4. **Create `log.md`** at the vault root — initialize the structural changelog. New entries at the top, grouped by change.
5. **Install the three skills** above. Run `/vault-lint` to baseline, then `/wikifier --apply` to densify backlinks once you have a few canonical sheets.
6. **Identify your raw-source folders** (inbox of meeting notes, web captures, etc.) and mark them as read-only in `CLAUDE.md`. The LLM ingests them into the Wiki layer; it doesn't edit them in place.

## Trade-offs

- **Upfront effort.** Creating 50–100 canonical entity sheets takes a few hours. Pays off when the LLM stops asking "who is X?" mid-conversation because it can `grep Entities/People/X.md` instead.
- **Discipline on naming.** "Alice Martin" (canonical) vs "Alice" (transcript shorthand) needs to be reconciled on every ingest. The skills make this mechanical, but it doesn't disappear.
- **Wikilinks are noisy in raw markdown.** A note can end up with 30+ `[[Name]]` links. Render in Obsidian (or any wikilink-aware viewer) — don't read the raw `.md` if you find that distracting.

## See also

- Karpathy's original gist: [LLM-friendly personal wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [`skills/vault-lint/SKILL.md`](../skills/vault-lint/SKILL.md)
- [`skills/wikifier/SKILL.md`](../skills/wikifier/SKILL.md)
- [`skills/ficher/SKILL.md`](../skills/ficher/SKILL.md)
