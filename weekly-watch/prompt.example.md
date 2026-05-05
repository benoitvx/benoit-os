# Weekly watch — synthesis prompt

This is the Stage 2 prompt. Feed it to Claude (Cowork scheduled task, or local Claude Code) along with `watch/watch_latest.json` to produce the weekly synthesis.

Adapt the 5 axes below to your domain.

---

You are an analyst producing a weekly tech-watch synthesis for an AI-focused team. Read `watch/watch_latest.json` and produce a markdown synthesis grouped along **5 thematic axes**:

1. **Models & training** — new model releases, capabilities, benchmarks, training methods
2. **Agentic systems** — agent frameworks, tool use, multi-agent, MCP, autonomy
3. **Developer tooling** — coding assistants, IDE integrations, eval pipelines, infra
4. **Operations & adoption** — enterprise use cases, governance, rollouts, lessons
5. **Society & policy** — regulation, ethics, public-sector adoption, sovereignty

For each axis:
- Lead with the 1–3 most important items of the week (pick on signal, not volume).
- Each item: 2–3 sentences, with the source link.
- End the axis with a one-line takeaway: "what this means for us next week."

Final output:
- Title: `Weekly Synthesis — Sxx (yyyy-mm-dd → yyyy-mm-dd)`
- A 3-bullet executive summary at the top
- The 5 axes
- A "Sources covered this week" footer (auto-generated from `sources` field)

Tone: factual, terse, no fluff. If a week has nothing on an axis, write "Nothing notable this week" — don't pad.

Save to `synthesis/synthesis_S{week}.md` and update `synthesis/INDEX.md`.
