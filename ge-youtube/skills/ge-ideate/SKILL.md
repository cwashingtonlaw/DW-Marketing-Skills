---
name: ge-ideate
description: >
  Video idea generator for the Great Elephant Law YouTube channel (personal
  injury + criminal defense). ALWAYS invoke for "video ideas," "what should I
  post," "YouTube ideas," "content ideas," "ideate," "topic ideas," "next video,"
  "give me video topics," or any request to brainstorm YouTube content for the
  firm. Produces a ranked list of 10 ideas across three formats (Reaction /
  FAQ / "What to do if…" / Local-explainer), each tagged with search-intent
  keyword, hook angle, thumbnail concept, and Shorts potential. First step of the
  Great Elephant Law YouTube workflow; hands off to ge-script.
---

# ge-ideate — YouTube Idea Generator (Step 1 of 8)

## STEP 0 — INTAKE HARD STOP
Before generating, confirm you have (ask only for what's missing):
- **Target city/region** for this batch (local SEO anchor).
- **Practice-area focus**: Personal Injury, Criminal Defense, or both.
- **Any current input**: recent local news, a viral legal case, common client
  questions, or a theme. If none, proceed from evergreen practice-area questions.

If the user uploaded a file (transcript, analytics export, news article), read it
first and mine it for topics before generating.

## STEP 0.5 — LOAD SHARED PROTOCOL
Read `ge-compliance/SKILL.md` and apply the COMPLIANCE PREAMBLE and banned-language
list to every title/hook you generate. Titles must never contain banned words.

## STEP 1 — GENERATE
Produce **10 ideas**, balanced across these formats (aim ~4 FAQ/"what to do if",
~3 Reaction/commentary, ~3 Local-explainer):

| Format | What it is | Why it grows the channel |
|---|---|---|
| **Reaction / Commentary** | Opinion on a viral/high-profile or local case, bodycam, or courtroom clip | Highest subscriber-velocity format (the Rivers / Attorney Tom engine) |
| **FAQ / Client-question** | Answers one specific consumer question | Evergreen, compounds for years (the Oginski engine) |
| **"What to do if…"** | Step-by-step for a situation (arrested, in a wreck) | High search intent + high Shorts potential |
| **Local-explainer** | "[CITY] [topic] law" | Ranks for local search; attracts qualified local viewers |

For EACH idea output exactly this block:

```
#<n> — <FORMAT>
Title:        <keyword-front-loaded, <60 chars, no banned words>
Search intent:<the query a viewer would type>
Primary keyword: <broad + geo variant>
Hook angle:   <bold-claim | question | result-first — one line>
Thumbnail:    <face + emotion + <=3 words concept>
Shorts:       <High/Med/Low — and the clip-able moment>
Compliance:   <CLEAR | flag note>
```

## STEP 2 — RANK
Sort the 10 by a simple growth score = (search demand × Shorts potential ×
local relevance), and mark the **top 3 "build next."** Note which 2–3 ideas could
form a series/playlist.

## STEP 3 — HANDOFF
End with:
> **Next step:** Pick an idea and run **ge-script** with the chosen Title +
> Primary keyword to write the retention-engineered script.

Run the STEP-0.5 COMPLIANCE CHECK block before finishing.

---

### EMBEDDED PROMPT (the engine — fill the brackets)
> Generate 10 YouTube video ideas for **Great Elephant Law** targeting **[CITY]**.
> Mix three formats: (a) reaction/commentary on a recent viral or high-profile
> **[PI/criminal]** case, (b) evergreen "What to do if…" client questions,
> (c) local-explainer ("[CITY] [topic] law"). For each: a keyword-front-loaded
> title (<60 char, no "best/expert/guarantee"), the search intent, primary +
> geo keyword, a one-line hook, a thumbnail concept, and Shorts potential
> (High/Med/Low + the clip-able moment). Rank by growth potential and flag the
> top 3. Apply the ge-compliance preamble.
