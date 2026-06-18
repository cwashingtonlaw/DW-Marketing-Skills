---
name: ge-compliance
description: >
  Shared attorney-advertising compliance protocol for all Great Elephant Law
  YouTube skills. This skill is NOT triggered directly by user prompts — it is
  read as a reference protocol by every ge- YouTube skill before it produces any
  caption, title, description, script, comment, or thumbnail text. It centralizes
  the ABA Model Rule 7.1/7.2 guardrails, the firm's disclaimer language, the
  banned-phrase list, and the responsible-attorney attribution block so that
  compliance is consistent across the entire workflow. If you are a ge- skill and
  your SKILL.md says to load this protocol, read it now and apply it before
  generating any output.
---

# ge-compliance — Attorney-Advertising Guardrail (Shared Reference)

> **This is a shared reference skill, not a user-facing one.** Other `ge-`
> skills load it at STEP 0.5. It exists so the compliance rules live in ONE
> place (DRY). If a rule changes, change it here and every skill inherits it.

---

## FIRM PROFILE (edit these values once)

```
FIRM_NAME:           Great Elephant Law
PRACTICE_AREAS:      Personal Injury; Criminal Defense
CITY_STATE:          [CITY, STATE]            <-- EDIT
RESPONSIBLE_ATTORNEY:[ATTORNEY NAME]          <-- EDIT
FIRM_WEBSITE:        [https://FIRM-SITE.com]  <-- EDIT
FIRM_PHONE:          [PHONE]                  <-- EDIT
GOVERNING_RULES:     ABA Model Rules 7.1 & 7.2; [STATE] Bar advertising rules  <-- EDIT STATE
```

### STATE-SPECIFIC OVERLAY (load if applicable)
If `GOVERNING_RULES` names a state with its own reference file, load it now and
let it OVERRIDE this generic guardrail where they conflict:
- **Louisiana** → also read `ge-compliance-la/SKILL.md` (LSBA filing-number regime,
  Rule 7.8 exemptions, no-non-lawyer-spokesperson ban, mandatory past-results
  language, La. R.S. 37:223 settlement-fee disclosure). **Louisiana controls.**
- Other states → no overlay file yet; apply the generic rules and raise
  `[COMPLIANCE REVIEW]` flags for state-specific items.

If any bracketed value is still a placeholder when a skill runs, the skill must
flag it: `[COMPLIANCE: firm profile incomplete — set CITY_STATE / RESPONSIBLE_ATTORNEY before publishing]`.

---

## THE COMPLIANCE PREAMBLE (prepend to every generation task)

> You are assisting **Great Elephant Law**, a personal injury and criminal
> defense firm in **[CITY, STATE]**. The responsible attorney is
> **[ATTORNEY NAME]**. Follow attorney-advertising rules (ABA Model Rules 7.1
> and 7.2 and **[STATE]** Bar rules). NEVER use "best," "expert," "specialist,"
> "guarantee," "winning," or any promise or implication of a specific outcome.
> Do not state or imply specific case results. Include a "general information,
> not legal advice, no attorney-client relationship" disclaimer. On any
> case-result content, add "Past results do not guarantee future outcomes."
> Output the responsible attorney's name and city where required.

---

## BANNED / HIGH-RISK LANGUAGE (scan and strip)

Hard-banned (remove or rephrase, always):
- "best," "#1," "top," "leading" (as a self-superlative)
- "expert," "specialist," "specializing in" (unless the attorney holds the
  certification the state recognizes — default: treat as banned)
- "guarantee," "guaranteed," "we win," "we'll win," "always win"
- "promise," "ensure you get," "you will receive [$ / outcome]"
- Specific dollar results framed as typical ("we get clients $1M") without the
  results disclaimer AND context

Caution (allowed only with a disclaimer / context):
- Any past case result or settlement figure → requires the
  "past results do not guarantee future outcomes" disclaimer
- Client testimonials → must be genuine, not misleading, and may require
  disclaimers or be restricted in some states (e.g., FL) — flag for attorney review
- "Free consultation" → fine, but confirm it's actually offered
- Comparisons to other firms → flag for review

Acceptable framing instead:
- "experienced," "[X] years handling [practice area] cases," "dedicated,"
  "focused on," "we handle," "our practice includes"

---

## REQUIRED DISCLAIMERS (insert verbatim, choose by content type)

**A. General educational content (every video description + a spoken line):**
> *This video is general information, not legal advice, and does not create an
> attorney-client relationship. Every case is different — consult a licensed
> attorney in your jurisdiction about your specific situation.*

**B. Any case-result / settlement / verdict mention (add to A):**
> *Past results do not guarantee or predict a similar outcome in any future case.*

**C. Reaction / commentary on a real or pending case (add to A):**
> *This is commentary and opinion on publicly reported information. It is not a
> statement of fact about any party and not legal advice.*

**D. Attribution block (end of every description):**
> *Attorney advertising. Great Elephant Law — [ATTORNEY NAME], [CITY, STATE].
> [PHONE] · [WEBSITE]*

---

## STATE-VARIATION FLAGS (raise these for attorney review)

The skill cannot know every state's rule. When it detects any of the following,
it must emit a `[COMPLIANCE REVIEW]` flag rather than proceeding silently:
- A **case result, settlement amount, or win rate** is included.
- A **testimonial or endorsement** (incl. a paid creator/"YouTube personality") appears.
- A **comparison** to another firm/lawyer is made.
- The content is **primarily promotional** (not educational) — some states
  (e.g., NY) treat this as "advertising" with extra requirements; some (e.g., FL)
  require pre-submission of certain ads.
- A **specific legal outcome is promised or implied.**
- The video concerns a **pending case** (risk of trial-publicity rules).

Flag format:
```
[COMPLIANCE REVIEW — <reason>]: <what to check> — route to [ATTORNEY NAME] before publishing.
```

---

## COMPLIANCE CHECK OUTPUT (every skill ends its compliance pass with this)

```
COMPLIANCE CHECK
- Banned language found: <none | list>
- Disclaimer inserted: <A | A+B | A+C | n/a>
- Attribution block present: <yes/no>
- Responsible attorney + city present where required: <yes/no>
- Review flags: <none | list of [COMPLIANCE REVIEW] items>
- Verdict: <CLEAR TO PROCEED | HOLD FOR ATTORNEY REVIEW>
```

A skill must NOT mark output `CLEAR TO PROCEED` if any hard-banned phrase remains
or any required disclaimer is missing.

---

## DELEGATION NOTE

Per ABA guidance, the lawyer remains responsible for marketing output even when
an AI tool generates it. These skills are drafting aids. Nothing here is a
substitute for the responsible attorney's review before publishing. Disable any
platform AI feature that could auto-generate superlative ad copy
(e.g., "Best [City] Injury Attorney").
