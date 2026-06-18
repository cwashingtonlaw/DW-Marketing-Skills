---
name: ge-seo
description: >
  YouTube SEO and metadata optimizer for Great Elephant Law videos. ALWAYS invoke
  for "SEO," "video description," "optimize the description," "tags," "metadata,"
  "chapters," "timestamps," "keywords for this video," or after packaging. Produces
  a 200+ word description (keyword-front-loaded summary in the first 125 chars),
  timestamps/chapters, a tag set (broad + geo + brand), hashtags, and AI/LLM
  discoverability notes — with the compliance disclaimer block and responsible-
  attorney attribution inserted. Step 4 of the Great Elephant Law YouTube workflow;
  hands off to ge-shorts and ge-publish.
---

# ge-seo — SEO & Metadata Optimizer (Step 4 of 8)

## STEP 0 — INTAKE HARD STOP
Confirm: **final title**, **primary keyword + geo variant**, **city/state**,
**firm website/phone**, and the **chapter beats** (from the script timecodes if
available). If a transcript exists, use it to surface secondary keywords.

## STEP 0.5 — LOAD SHARED PROTOCOL
Read `ge-compliance/SKILL.md`. The description MUST end with Disclaimer A (+ B/C
as applicable) and the attribution block. Strip banned language from all metadata.

## STEP 1 — DESCRIPTION (200+ words)
- **First 125 characters:** a punchy summary containing the primary keyword
  (this is what shows above the fold and in search).
- **Body:** 200+ words in natural language — what the video covers, who it helps,
  the city/practice-area context, secondary keywords woven in (not stuffed).
- **Resource links:** firm website, related video, playlist, consultation link.
- **Chapters/timestamps:** `0:00 Intro` style list (enables chapters + helps
  AI/search parse the video).
- **Disclaimer + attribution:** insert verbatim from ge-compliance.

## STEP 2 — TAGS & HASHTAGS
- **Tags:** a mix of — broad ("personal injury lawyer," "criminal defense
  attorney"), **geo** ("[CITY] car accident attorney," "[CITY] DUI lawyer"),
  topic/long-tail ("what to do after a car accident in [STATE]"), and **brand**
  ("Great Elephant Law").
- **Hashtags:** 3–5, including one geo and one practice-area.

## STEP 3 — AI / LLM DISCOVERABILITY (GEO/AEO)
Because YouTube is heavily cited by AI answer engines and Google AI Overviews,
add:
- A clean **summary paragraph** an LLM could quote.
- A short **Q&A block** ("Q: What should I do after a wreck in [CITY]? A: …")
  mirroring real search questions.
- A note to **upload the transcript/captions** (improves both accessibility and
  machine parsing).

## STEP 4 — OUTPUT + HANDOFF
Deliver: description, tags, hashtags, chapters, AI-discoverability block, and the
COMPLIANCE CHECK.
> **Next step:** Run **ge-shorts** to repurpose, then **ge-publish** to ship.

---

### EMBEDDED PROMPT (the engine — fill the brackets)
> Write the YouTube SEO package for "**[TITLE]**" (primary keyword **[KEYWORD]**,
> geo **[CITY, STATE]**, firm site **[WEBSITE]**). Description: 200+ words, with
> the first 125 characters a punchy keyword-rich summary; weave in secondary
> keywords naturally; add chapter timestamps from **[SCRIPT BEATS]**; include
> resource links. Provide a tag set mixing broad + geo + long-tail + brand terms,
> 3–5 hashtags, and an AI-discoverability block (quotable summary + a short Q&A
> mirroring search questions). Append the ge-compliance disclaimer block and the
> responsible-attorney + city attribution. Output a compliance check.
