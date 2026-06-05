---
name: ge-publish
description: >
  Pre-publish gating checklist for Great Elephant Law YouTube uploads. ALWAYS
  invoke for "publish checklist," "ready to upload," "pre-publish," "is this ready
  to post," "upload checklist," "going live," or before any video/Short ships.
  Runs a gating checklist covering thumbnail, A/B variants, disclaimers (on-screen
  + description), end screens/cards, chapters, captions/transcript, geo-keywords,
  and state-bar disclaimer verification — and produces a final CLEAR / HOLD
  verdict. Step 6 of the Great Elephant Law YouTube workflow; hands off to
  ge-community.
---

# ge-publish — Pre-Publish Gating Checklist (Step 6 of 8)

## STEP 0 — INTAKE HARD STOP
Confirm what's shipping: **long-form, Short, or both**, and gather the assets
produced upstream (title, thumbnail, description, chapters, captions). If anything
is missing, list it and stop — do not green-light an incomplete upload.

## STEP 0.5 — LOAD SHARED PROTOCOL
Read `ge-compliance/SKILL.md`. This skill is the final compliance gate before
publishing. It must run the full COMPLIANCE CHECK and refuse to mark CLEAR if any
hard-banned phrase or required disclaimer is missing.

## STEP 1 — RUN THE CHECKLIST
Mark each ✅ / ❌ / ⚠️ with a note:

```
PACKAGING
[ ] Custom thumbnail uploaded (not auto-generated)
[ ] 2–3 A/B thumbnail variants loaded in Test & Compare (if >~1k impressions expected)
[ ] Title keyword-front-loaded, <60 chars, no banned words
[ ] Title ↔ thumbnail add information (don't echo)

METADATA
[ ] Description 200+ words; first 125 chars = keyword summary
[ ] Chapters/timestamps added
[ ] Tags: broad + geo + long-tail + brand
[ ] Geo-keyword present in title/description/spoken content
[ ] Captions/transcript uploaded

ENGAGEMENT SETUP
[ ] End screen → related long-form + subscribe
[ ] Cards → relevant video/playlist
[ ] Pinned comment drafted (hand to ge-community)
[ ] (Shorts) funnel link to long-form in description + pinned comment

COMPLIANCE (gating — all must pass)
[ ] On-screen "not legal advice" disclaimer present in the video
[ ] Description disclaimer block present (A, + B/C as applicable)
[ ] Responsible attorney name + city present
[ ] "Attorney advertising" label present (per state)
[ ] No "best/expert/specialist/guarantee/win" anywhere
[ ] Case results (if any) carry the results disclaimer
[ ] [COMPLIANCE REVIEW] flags resolved or routed to attorney
[ ] State-specific step done (e.g., FL ad submission / NY firm-name use) — if applicable
```

## STEP 2 — VERDICT
Output:
```
PUBLISH VERDICT: <CLEAR TO PUBLISH | HOLD>
Blockers: <none | list each ❌/⚠️ and the fix>
Attorney review required: <yes/no — why>
```
If any COMPLIANCE gating item is ❌, the verdict is **HOLD**, no exceptions.

## STEP 3 — HANDOFF
> **Next step:** After publishing, run **ge-community** for the first-hour
> engagement plan, then **ge-analyze** after 48 hours and again at 7/28 days.

---

### EMBEDDED PROMPT (the engine — fill the brackets)
> Run the Great Elephant Law pre-publish gating checklist for "**[TITLE]**"
> (**[long-form/Short/both]**). Check packaging, metadata, engagement setup, and —
> as a hard gate — compliance: on-screen + description disclaimers, responsible
> attorney + city, "attorney advertising" label, no banned language, results
> disclaimer where needed, and any state-specific requirement
> (**[STATE]**). Output a ✅/❌/⚠️ checklist and a final CLEAR/HOLD verdict; mark
> HOLD if any compliance gate fails. Apply ge-compliance.
