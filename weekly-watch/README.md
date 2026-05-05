# Veille — weekly watch pipeline template

A reusable template for an **operator multiplier**: a weekly cron that scrapes a list of RSS/Atom sources, commits a structured JSON snapshot to your repo, and feeds it to Claude (Cowork or otherwise) for thematic synthesis.

Extracted from a real pipeline I run for the IAE department of DINUM (the [`veille-IAE`](https://github.com/benoitvx/veille-IAE) repo, private). Stripped of domain-specific logic, ready to fork.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1 — GitHub Actions (weekly cron, e.g. Monday 7h UTC) │
│                                                             │
│  fetch.py + sources.yml                                     │
│    ├── Source A (RSS 2.0)                                   │
│    ├── Source B (Atom)                                      │
│    └── …                                                    │
│                          │                                  │
│                          ▼                                  │
│              watch/watch_latest.json                        │
│                  (git commit + push)                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2 — Claude (Cowork scheduled task, or local)         │
│                                                             │
│  Reads watch_latest.json                                    │
│  Applies prompt.md (5-axis thematic synthesis)              │
│  Outputs: weekly_synthesis_S{n}.md                          │
└─────────────────────────────────────────────────────────────┘
```

## What's inside

| File | Role |
|---|---|
| `fetch.py` | Generic RSS/Atom collector. Reads `sources.yml`, filters by date range, writes JSON. |
| `sources.example.yml` | List of feeds — copy to `sources.yml` and edit. |
| `prompt.example.md` | Skeleton prompt for the Stage 2 synthesis. |
| `.github/workflows/weekly-watch.yml` | Cron workflow that runs `fetch.py` and commits the JSON. |

## Quick start

```bash
# 1. Copy the template into your repo
cp -r benoit-os/weekly-watch/* my-watch-repo/

# 2. Configure sources
cd my-watch-repo
cp sources.example.yml sources.yml
# edit sources.yml with your feeds

# 3. Test locally
python fetch.py
cat watch/watch_latest.json | jq '.articles_count'

# 4. Push
git add . && git commit -m "init weekly watch" && git push

# 5. The GHA cron will trigger every Monday at 7h UTC
```

## Wiring Stage 2 (Claude synthesis)

Several options:

- **Claude Cowork scheduled task** — set up a recurring task that reads `watch_latest.json` and applies `prompt.md`. The task runs in the cloud, posts the synthesis back to your repo (or to wherever).
- **Local Claude Code** — `claude --resume` on Monday, manually trigger the synthesis from the new JSON commit.
- **Webhook in the GHA** — extend the workflow to POST the JSON to an external API after the commit.

## Why this exists

Most "tech watch" tooling stops at "we collected stuff." The synthesis layer is where the leverage is — turning 30 raw articles into a coherent weekly read for a team. This template gives you the collection layer and the wiring; Claude does the synthesis. Together: ~30 minutes of upkeep per week, ~5 minutes of consumption.

The IAE department has been running this for months. It's the kind of small, self-compounding workflow that defines an operator.
