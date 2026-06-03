---
name: ficher
description: Create a canonical entity sheet `Entities/<category>/<Name>.md` with a pre-filled template (frontmatter `type:` + `status:` + sections Identity / Why it matters / Notes). Updates `Entities/Index.md`. Then offers `/wikifier` to densify backlinks toward the new sheet and `/vault-lint` to validate. Invoke when the user says "ficher <name>", "/ficher <name>", or encounters a new entity (person, organization, product, concept) to canonize in the vault.
---

# ficher

Creates a new canonical entity sheet in `Entities/` (or `Entités/`) following Karpathy's [LLM Wiki pattern](../../docs/karpathy-pattern.md), as documented in `CLAUDE.md` § "New entity encountered".

## Invocation

```
/ficher <name>
/ficher <name> <free contextual hints>
```

Examples:
- `/ficher Alice Martin` — minimal
- `/ficher Bob Smith CTO OrgX` — with hints (CTO at OrgX → person, ecosystem subfolder)
- `/ficher MesQuestions` — product (from context)
- `/ficher Open Data Platform` — concept / public service

## Workflow

### 1. Detect / clarify the category

Target categories:
- `Entities/People/Internal/` — your team, direct colleagues
- `Entities/People/Partners/` — partner orgs' contacts (or break out by partner)
- `Entities/People/Ecosystem/` — external, cabinet, vendors
- `Entities/Organizations/` — orgs, partners, collectives
- `Entities/Products/` — products (ONLY if no dedicated Wiki folder exists in `Products/` or equivalent)
- `Entities/Concepts/` — doctrines, governance bodies, technical building blocks

Adapt subfolders to your own vault. If hints in the prompt make the category obvious: proceed without asking. Otherwise ask in one shot:

```
For `<name>`:
- Type: person / organization / product / concept?
- (If person) subfolder: Internal? Partners? Ecosystem?
- Context / why this sheet now? (1 sentence)
```

### 2. Check that no sheet already exists

```bash
find Entities -iname "<name>*.md"
```

If match: show the existing sheet and ask whether to enrich it, whether it's a homonym to disambiguate (`Name (qualifier).md`), or whether the confusion comes from an alias (update the existing sheet's Notes section with the alias).

### 3. Check for a Wiki duplicate (especially for products)

For products, check whether a dedicated Wiki folder already exists:

```bash
find Products -iname "<name>*.md" -not -path "Entities/*"
```

If match: do **not** create an `Entities/Products/` sheet. The Wiki sheet is the canonical one (see `Entities/Index.md` § decision). Optionally enrich the Wiki sheet with `type:`/`status:` frontmatter and mention it in the "Products — dedicated Wiki sheet (outside `Entities/`)" section of `Entities/Index.md`.

### 4. Create the sheet with template

Template by type:

#### Person template
```markdown
---
type: person
status: active
---

# <Canonical name>

## Identity
- **Alias**: <if relevant>
- **Role**: <function / title>
- **Organization**: <team, department, company>
- **Email**: <if known>

## Why it matters
<1–3 lines: link to your goals / mission, what to remember, topics on which this person is a key contact>

## Notes
- <transcription aliases, common misspellings>
- <cross-references, distinctions from homonyms>
- <recurring 1:1: `<meeting-notes>/.../...`>
```

#### Organization template
```markdown
---
type: organization
status: active
---

# <Canonical name>

## Identity
- **Full name**: <if acronym>
- **Type**: <agency / association / private / NGO / collective>
- **Parent / affiliation**: <if applicable>
- **URL**: <if relevant>

## Why it matters
<link to your goals, axes concerned, role in the ecosystem>

## Notes
- <transcription deformations, aliases>
- <not to be confused with X>
```

#### Product template
```markdown
---
type: product
status: active
---

# <Canonical name>

## Identity
- **Type**: <one-line description>
- **Tagline**: <official pitch if available>
- **URL**: <if available>
- **Contact**: <contact email>

## Team
- **Product lead**: <person>
- <other key roles>

## Why it matters
<positioning in the strategy / your goals>

## Notes
- <local sub-sheet if any: `Products/X/`>
- <not to be confused with Y>
```

#### Concept template
```markdown
---
type: concept
status: active
---

# <Canonical name>

## Identity
- **Full name**: <if acronym>
- **Type**: <doctrine / body / framework / technical building block>
- **Owner / operator**: <person or organization>

## Why it matters
<role in the broader framework / your goals, articulation with other concepts>

## Notes
- <transcription deformations>
- <to articulate with X, Y>
```

### 5. Wikify other entities cited in the sheet body

In the body you just wrote, spot plain-text mentions of other entities already sheeted in `Entities/` (read `Entities/Index.md` for the list) and wikify them directly (`[[Name]]`). One link per name in the sheet (first occurrence). No need to re-run `/wikifier` for this — do it by hand at writing time.

### 6. Update `Entities/Index.md`

- **Counter at the top**: increment the total.
- **Subcategory counter**: update the tree line (e.g. `People/Internal/ (33) ...` → `(34)`).
- **Subcategory list**: add a concise entry under the right header.

### 7. Update the counter in root `Index.md`

Line `| Entities/ | ... | N |` → N+1.

### 8. Offer finishing actions

```
Sheet created: Entities/<category>/<Name>.md
Entities index updated (counter + entry).

Do you want to:
- Run `/wikifier --apply` to densify backlinks toward [[Name]] across the vault?
- Run `/vault-lint` to validate?
```

If the user validates: run the commands. Otherwise: signal that these can be run later.

## Rules

- **Canonical name**: the filename = full canonical name (`Alice Martin.md`, not `Alice.md`). Filesystem-unfriendly characters replaced (e.g. `Compar:IA` → `Compar IA.md`).
- **Mandatory frontmatter**: `type:` (person | organization | product | concept) and `status:` (active | archived).
- **Minimum sections**: Identity / Why it matters / Notes. An empty section is OK for v1 (enrich progressively).
- **Wikify internal references** in the sheet body directly at creation.
- **If a Wiki folder already exists**: do not create an `Entities/Products/` duplicate. Enrich the Wiki sheet if needed.
- **Do not invent**: if info is missing (exact role, email, etc.), leave an explicit placeholder (`to be specified`) rather than guessing.

## Pointers

- `Entities/Index.md` — catalog, source of truth.
- `CLAUDE.md` § "New entity encountered" — synthesis of the same workflow on the vault side.
- [`skills/wikifier/`](../wikifier/) — densifies backlinks toward the new sheet across the vault.
- [`skills/vault-lint/`](../vault-lint/) — verifies 0 duplicates / 0 orphans / 0 broken links after creation.
- [`docs/karpathy-pattern.md`](../../docs/karpathy-pattern.md) — the broader pattern.
