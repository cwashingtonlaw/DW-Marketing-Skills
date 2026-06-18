---
name: ge-analyze
description: >
  Analytics reviewer and growth-loop closer for Great Elephant Law YouTube.
  ALWAYS invoke for "analytics review," "how did this video do," "channel
  performance," "review my numbers," "what's working," "retention review," "CTR
  review," "analyze last month," or after videos have run for 48 hours / 7 / 28
  days. Diagnoses the per-video funnel (impressions → CTR → average view duration
  → subscribers), classifies retention curves, identifies traffic sources and the
  search queries driving impressions, and produces 3 prioritized next actions that
  feed back into ge-ideate. Step 8 of 8 — closes the loop.
---

# ge-analyze — Analytics Reviewer (Step 8 of 8)

## STEP 0 — INTAKE HARD STOP
Confirm the data source: a **YouTube Studio CSV export**, a **pasted metrics
table**, or a **live pull via a YouTube Data/Analytics API MCP server** (e.g.,
ZubeidHendricks/youtube-mcp-server or kirbah/mcp-youtube). If none is available,
ask for at least: impressions, CTR, average view duration / % viewed, views,
subscribers gained, and traffic sources per video. Do not invent numbers — if a
metric is missing, say so.

## STEP 0.5 — LOAD SHARED PROTOCOL
Read `ge-compliance/SKILL.md`. (Analytics output is internal, but any suggested
new titles/topics that flow back to ge-ideate must still respect banned-language
rules.)

## STEP 1 — PER-VIDEO FUNNEL DIAGNOSIS
For each video, walk the funnel and locate the bottleneck:
```
VIDEO: <title>
Impressions: <n>  → CTR: <%>  → AVD/%viewed: <…>  → Views: <n>  → Subs: <n>
Funnel verdict:
  - Low impressions      → discovery problem (SEO/topic/thumbnail not surfacing)
  - High impr, low CTR    → packaging problem (title/thumbnail) → re-run ge-package
  - Good CTR, low AVD      → hook/retention problem → re-run ge-script hook
  - Good AVD, low subs     → CTA/value-payoff problem → adjust CTA + end screen
```
Benchmarks to apply: CTR ~4–5% good / 7%+ exceptional; aim ≥70% retention at 30s.

## STEP 2 — RETENTION CURVE CLASSIFICATION
Classify each curve: healthy decay / steep early drop (weak hook) / mid-video cliff
(pacing) / strong hold (replicate it). Name the timestamp of the biggest drop.

## STEP 3 — SOURCES & QUERIES
List top traffic sources (Browse / Search / Suggested / Shorts feed / External)
and the **exact search queries** generating impressions. Flag geo queries that are
converting — those are gold for a local firm and should spawn more local-explainers.

## STEP 4 — SHORTS → LONG-FORM FLOW
If Shorts are running, report views and whether they're driving subscribers and
long-form click-through. If Shorts get views but not subs, recommend tightening the
hook↔long-form alignment (a ge-shorts re-run).

## STEP 5 — THREE PRIORITIZED ACTIONS (loop back)
End with exactly 3 ranked next actions, each pointing to the skill that executes it:
```
1. <action> → run <ge-skill>
2. <action> → run <ge-skill>
3. <action> → run <ge-skill>
```
Feed winning topics/queries back into **ge-ideate** to start the next cycle.

## STEP 6 — STRATEGY THRESHOLDS
Note any threshold crossed that should change strategy:
- A topic cluster overperforms → build a playlist/series.
- Reaction outperforms FAQ (or vice versa) → reweight the content mix.
- A geo query converts → double down on that city/topic.

---

### EMBEDDED PROMPT (the engine — fill the brackets)
> Given this analytics data **[PASTE CSV / METRICS / MCP PULL]**, diagnose each
> video's funnel (impressions → CTR → AVD/%viewed → views → subscribers) and name
> the bottleneck; classify each retention curve and the biggest drop-off
> timestamp; list top traffic sources and the exact search queries driving
> impressions (flag converting geo queries); assess Shorts → long-form flow; then
> give exactly 3 prioritized next actions, each mapped to the ge- skill that
> executes it, and feed winning topics back to ge-ideate. Use the benchmarks
> CTR 4–5% good / 7%+ great and ≥70% retention at 30s. Do not invent missing
> numbers.
