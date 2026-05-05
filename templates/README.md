# Templates

Drop-in files to bootstrap a new project.

## CLAUDE.md / INSTRUCTIONS.md

| Template | When to use |
|---|---|
| [`beta.gouv.md`](beta.gouv.md) | French government / beta.gouv project. Covers DSFR, RGAA, ANSSI, French commit conventions, validate loop, gitleaks, dependency policy. |

### How to use

```bash
# At the root of a fresh project, copy the template as CLAUDE.md or INSTRUCTIONS.md
cp benoit-os/templates/beta.gouv.md ./CLAUDE.md

# Then edit the four "Adapt to your project" sections (Context, Architecture,
# Recommended Stack, CI). Everything else is sane defaults.
```

Claude Code auto-loads `CLAUDE.md` from the project root as durable context. Other AI coding assistants (OpenCode, Mistral Vibe, Cursor) generally load `INSTRUCTIONS.md` or `.cursorrules` — pick the filename that fits your toolchain.

## Source & attribution

`beta.gouv.md` is a vendored copy of [`etalab-ia/skills/templates/instructions/beta.gouv.md`](https://github.com/etalab-ia/skills/blob/main/templates/instructions/beta.gouv.md), kept here for offline access and quick scaffolding. Upstream is the source of truth for updates.
