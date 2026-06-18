---
name: ge-audit
description: >
  Channel audit for the Great Elephant Law YouTube channel. ALWAYS invoke for
  "audit my channel," "channel audit," "review my channel," "channel health
  check," "what's wrong with my channel," "branding review," "channel setup
  review," or "is my channel optimized." Produces a structured health report
  across branding/identity, content mix, packaging patterns, SEO hygiene, Shorts
  funnel, compliance posture, and growth signals — with a prioritized fix list.
  Adapted from the open-source claude-youtube `audit` sub-skill and tuned for a
  personal injury + criminal defense law firm. Best run at the start of an
  engagement and quarterly thereafter. Feeds ge-ideate and ge-package.
---

# ge-audit — Channel Audit (entry / quarterly diagnostic)

## STEP 0 — INTAKE HARD STOP
Gather what's available (ask only for what's missing):
- Channel name/handle/URL and **subscriber count + total views** (rough is fine).
- **Channel data**: a YouTube Studio export, a pasted list of recent videos with
  titles/views/CTR/AVD, or a live pull via a YouTube Data API MCP server. If none,
  audit what you can from the public channel description the user provides.
- Target **city/region** and **practice-area focus**.
Do NOT invent metrics. If data is missing, audit qualitatively and mark gaps.

## STEP 0.5 — LOAD SHARED PROTOCOL
Read `ge-compliance/SKILL.md` (and `ge-compliance-la/SKILL.md` if Louisiana). The
audit must include a **compliance posture** section — channels that publish ad
content without disclaimers/identifiers carry real risk.

## STEP 1 — AUDIT DIMENSIONS
Score each **0–5** with a one-line rationale and the specific fix:

```
1. IDENTITY & BRANDING
   - Channel name = firm name? Banner with firm name + city? Pro headshot/logo?
   - About section: practice areas, city, contact, links, keywords?
2. CONTENT MIX
   - Balance across Reaction / FAQ / "What to do if…" / Local-explainer?
   - Evergreen core present (the compounding FAQ library)?
   - Posting consistency / cadence?
3. PACKAGING PATTERNS
   - Titles keyword-front-loaded, <60 chars? Thumbnails: face+emotion, legible on mobile?
   - Any banned language in titles/thumbnails? (compliance overlap)
4. SEO HYGIENE
   - Descriptions 200+ words? Chapters? Geo-keywords? Tags? Captions/transcripts?
5. SHORTS FUNNEL
   - Shorts present? Do they funnel to long-form? Cross-format flow?
6. ENGAGEMENT
   - Pinned comments? Reply activity? End screens/cards to long-form + site?
7. COMPLIANCE POSTURE  (gating — see ge-compliance)
   - Disclaimers on educational videos? Responsible attorney + city present?
   - LA: filing-number/Rule 7.8 posture noted? Non-lawyer spokesperson anywhere?
   - Any settlement $ figures without R.S. 37:223 fee disclosure?
8. GROWTH SIGNALS
   - CTR vs. ~4–5% bench; AVD/retention; subs-per-video; traffic sources.
```

## STEP 2 — SCORECARD + TOP FIXES
Output a scorecard table (dimension / score / one-line fix), an overall health
read, and the **5 highest-leverage fixes ranked by impact × effort**. Call out any
**compliance gap as a priority-1 item** regardless of growth score.

## STEP 3 — HANDOFF
> **Next step:** Feed the content-gap findings into **ge-ideate**, the packaging
> fixes into **ge-package**, and re-audit quarterly. Resolve any compliance gap
> before publishing new content.

Run the COMPLIANCE CHECK block before finishing.

---

### EMBEDDED PROMPT (the engine — fill the brackets)
> Audit the **Great Elephant Law** YouTube channel (**[CITY]**, PI + criminal
> defense). Data: **[STUDIO EXPORT / VIDEO LIST / MCP PULL / public info]**. Score
> 0–5 across: identity/branding, content mix, packaging, SEO hygiene, Shorts
> funnel, engagement, compliance posture, and growth signals — each with a
> one-line rationale and specific fix. Use benchmarks CTR ~4–5% and ≥70% retention
> at 30s. Produce a scorecard table, an overall health read, and the 5 highest-
> leverage fixes ranked by impact × effort. Treat any compliance gap (missing
> disclaimer, no responsible-attorney identifier, LA filing/spokesperson/R.S.
> 37:223 issues) as priority-1. Do not invent metrics. Apply ge-compliance
> (+ ge-compliance-la if Louisiana) and output a compliance check.
