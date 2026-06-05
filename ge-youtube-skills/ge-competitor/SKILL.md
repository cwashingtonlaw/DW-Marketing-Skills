---
name: ge-competitor
description: >
  Competitor analysis for the Great Elephant Law YouTube channel. ALWAYS invoke
  for "competitor analysis," "analyze competitors," "what are other lawyers
  doing," "competitor channels," "who's winning in my market," "content gap
  analysis," "what topics are they covering," or "find content gaps." Studies
  other attorney/legal YouTube channels (local rivals and national exemplars like
  Bruce Rivers, Attorney Tom, The DUI Guy, Gerry Oginski), extracts what's
  working (formats, packaging, cadence, topic clusters), and surfaces the gaps
  and angles Great Elephant Law can own. Adapted from the open-source
  claude-youtube `competitor` sub-skill. Feeds ge-ideate.
---

# ge-competitor — Competitor & Gap Analysis

## STEP 0 — INTAKE HARD STOP
Gather:
- **Competitors to analyze**: name 2–5 channels (local PI/criminal firms in
  **[CITY/REGION]** and/or national exemplars). If the user names none, default to
  the research benchmarks (Bruce Rivers, Attorney Tom, The DUI Guy/Larry Forman,
  Gerry Oginski) plus ask for local rivals.
- **Data source**: public channel browsing the user pastes in, or a YouTube Data
  API MCP server pull (search/most-popular by channel). Do NOT fabricate view
  counts or subscriber numbers — label estimates as estimates and missing data as
  missing.
- Great Elephant Law's **focus + city** for the gap comparison.

## STEP 0.5 — LOAD SHARED PROTOCOL
Read `ge-compliance/SKILL.md` (+ `ge-compliance-la/SKILL.md` if Louisiana). Any
topic ideas or angles that flow out of this analysis must respect banned-language
and disclaimer rules. Note: do NOT copy a competitor's non-compliant tactics
(e.g., result-promising, non-lawyer spokespeople) — flag them as what NOT to do.

## STEP 1 — PER-COMPETITOR BREAKDOWN
For each competitor:
```
CHANNEL: <name> (<subs/views — mark estimate>)
Format mix:     <reaction / FAQ / what-to-do / local — what dominates>
Top performers: <2–3 best videos + why they likely worked (topic, packaging)>
Packaging style:<title patterns, thumbnail patterns>
Cadence:        <how often / formats>
Topic clusters: <recurring themes/playlists>
What works:     <the replicable lever>
What NOT to copy:<any compliance-risky tactic>
```

## STEP 2 — PATTERN SYNTHESIS
Across all competitors, identify:
- The **formats and topics consistently winning** in this niche.
- The **packaging conventions** (so GEL fits the niche visually) and where GEL can
  **differentiate** (e.g., hyper-local angle competitors ignore).
- **Cadence norms** to match or beat.

## STEP 3 — GAP & OPPORTUNITY MAP
Produce:
- **Content gaps**: high-intent topics nobody local is covering (esp. geo +
  practice-area: "[CITY] [topic]").
- **Underserved audiences/questions** (e.g., specific charges, specific injury
  scenarios) GEL can own.
- **A differentiation angle** competitors can't easily copy (local presence,
  bilingual content, a specific practice concentration) — kept non-misleading.
- **5 concrete video ideas** seeded from the gaps (compliant titles).

## STEP 4 — HANDOFF
> **Next step:** Push the 5 gap-driven ideas into **ge-ideate** to expand and rank,
> then **ge-script** the winner.

Run the COMPLIANCE CHECK block before finishing.

---

### EMBEDDED PROMPT (the engine — fill the brackets)
> Analyze these competitor YouTube channels for **Great Elephant Law** (**[CITY]**,
> PI + criminal defense): **[LIST CHANNELS / "use research benchmarks + these
> local rivals: ___"]**. Data: **[PASTED PUBLIC INFO / MCP PULL]**. For each:
> format mix, top performers and why, title/thumbnail patterns, cadence, topic
> clusters, the replicable lever, and any compliance-risky tactic NOT to copy.
> Then synthesize the niche's winning formats/packaging, identify content gaps
> (especially hyper-local "[CITY] [topic]" angles competitors ignore), name an
> ownable differentiation angle (non-misleading), and propose 5 compliant,
> gap-driven video ideas. Do not invent subscriber/view numbers. Apply
> ge-compliance (+ ge-compliance-la if Louisiana) and output a compliance check.
