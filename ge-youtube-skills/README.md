# Great Elephant Law — YouTube Growth Skill Package

A chainable set of Claude skills for growing the **Great Elephant Law** YouTube
channel (personal injury + criminal defense), built from the strategy research
report. Priority: **subscriber growth and views**, with **attorney-advertising
compliance** baked into every step.

---

## What's in here

| Skill | Step | Does | Hands off to |
|---|---|---|---|
| `ge-compliance` | shared | Attorney-advertising guardrail loaded by every skill (preamble, banned-language list, disclaimers, attribution, state flags). **Edit the firm profile here once.** Auto-loads the LA overlay when governing rules = Louisiana. | (all) |
| `ge-compliance-la` | shared | Louisiana overlay: LSBA filing-number regime, Rule 7.8 exemptions (does YouTube need filing?), no-non-lawyer-spokesperson ban, mandatory past-results language, La. R.S. 37:223 settlement-fee disclosure. **Louisiana controls.** | (all, via ge-compliance) |
| `ge-audit` | entry/quarterly | Channel health audit across branding, content mix, packaging, SEO, Shorts funnel, engagement, compliance posture, growth signals + ranked fixes | `ge-ideate`, `ge-package` |
| `ge-competitor` | research | Studies rival + exemplar channels, extracts what works, maps content gaps + an ownable angle | `ge-ideate` |
| `ge-ideate` | 1 | 10 ranked video ideas across Reaction / FAQ / "What to do if…" / Local-explainer | `ge-script` |
| `ge-script` | 2 | Retention-engineered script + hook (0–10s), pattern interrupts, compliant CTA, clip-able moments | `ge-package`, `ge-seo`, `ge-shorts` |
| `ge-package` | 3 | 3 titles + 3 thumbnail briefs + synergy check + A/B test plan | `ge-publish` |
| `ge-seo` | 4 | 200+ word description, chapters, tags (broad+geo+brand), AI-discoverability block | `ge-shorts`, `ge-publish` |
| `ge-shorts` | 5 | 3–5 vertical Shorts that funnel non-subscribers to the long-form | `ge-publish` |
| `ge-publish` | 6 | Pre-publish gating checklist + final CLEAR/HOLD verdict (hard compliance gate) | `ge-community` |
| `ge-community` | 7 | Pinned comment, first-hour reply plan, 5 compliant reply templates | `ge-analyze` |
| `ge-analyze` | 8 | Funnel diagnosis, retention curves, search queries, 3 next actions | back to `ge-ideate` |

The eight steps form a loop: **Ideate → Script → Package → SEO → Shorts →
Publish → Community → Analyze → (back to Ideate).**

```
ge-ideate ─► ge-script ─►─┬─► ge-package ─┐
                          ├─► ge-seo ──────┼─► ge-publish ─► ge-community ─► ge-analyze
                          └─► ge-shorts ───┘                                      │
   ▲                                                                             │
   └──────────────────────  winning topics & queries feed back  ────────────────┘
```

---

## SET THIS FIRST (required)

Open `ge-compliance/SKILL.md` and fill in the **FIRM PROFILE** block:
`CITY_STATE`, `RESPONSIBLE_ATTORNEY`, `FIRM_WEBSITE`, `FIRM_PHONE`, and the
`GOVERNING_RULES` state. Until these are set, the skills will flag output as
`[COMPLIANCE: firm profile incomplete]`. Have the responsible attorney review and
approve this file — it encodes the disclaimers and banned-language rules.

**If you operate in Louisiana** (Great Elephant Law's home jurisdiction), set
`GOVERNING_RULES` to include Louisiana and the `ge-compliance-la` overlay loads
automatically. It is stricter than the generic ABA guardrail — notably the
**no-non-lawyer-spokesperson** ban (the attorney must be the on-camera voice in ad
content), the **mandatory past-results disclaimer language**, the **La. R.S.
37:223 settlement-fee disclosure** if you state dollar amounts, and the **LSBA
filing-number / Rule 7.8 exemption** analysis for whether YouTube content must be
filed. Confirm the filing posture with the responsible attorney / LSBA Ethics
Counsel — the skill flags it rather than self-clearing.

---

## Install / sync

These follow your standard skill conventions (YAML frontmatter, STEP 0 intake
hard stop, STEP 0.5 shared-protocol load). To deploy into your environment:

1. Review each `SKILL.md` (and have the attorney sign off on `ge-compliance`).
2. Commit the nine folders to your skills GitHub repo (source of truth), with the
   sync agent paused if you're doing a bulk add, then let the normal pull
   forward-sync them to `~/.claude/skills/`. **Do not** edit the on-disk copies as
   the primary.
3. (Optional, for live data) Add a YouTube Data API MCP server so `ge-analyze` and
   `ge-ideate` can pull real channel/search data:
   - `ZubeidHendricks/youtube-mcp-server` (video mgmt, Shorts, analytics)
   - `kirbah/mcp-youtube` (token-optimized, transcripts at 0 quota cost)
   - Mind the YouTube Data API quota: 10,000 units/day; search calls ~100 units each.
4. (Optional) Reference `AgriciDaniel/claude-youtube` (MIT) for additional
   sub-skills (audit, competitor, monetize) you may want to adapt later.

---

## How to run it (typical week)

**One-time / quarterly setup:** run `ge-audit` to baseline the channel and
`ge-competitor` to map gaps and an ownable angle — both feed `ge-ideate`.

1. `ge-ideate` for the city/topic → pick the top idea.
2. `ge-script` on that idea → get the script + clip-able moments.
3. `ge-package` + `ge-seo` on the script → titles, thumbnails, description.
4. `ge-shorts` on the transcript → 3–5 Shorts for the launch week.
5. `ge-publish` → gating checklist; fix any HOLD before uploading.
6. `ge-community` right after publish → pinned comment + first-hour replies.
7. `ge-analyze` at 48h / 7d / 28d → 3 next actions → feed back into `ge-ideate`.

Suggested cadence from the research: **1 long-form/week** (FAQ or local-explainer),
each repurposed into **3–5 Shorts**, adding **1–2 reaction videos/week** once the
evergreen core is running.

---

## Compliance note (read this)

Per ABA guidance, the lawyer remains responsible for marketing output even when an
AI tool drafts it. These skills are **drafting aids with guardrails**, not a
substitute for the responsible attorney's review before anything publishes.
`ge-publish` is a hard gate: it returns **HOLD** if any banned phrase or required
disclaimer is missing. State rules vary materially (e.g., Florida ad-submission
and celebrity-endorsement rules; New York firm-name and advertising-definition
rules) — the `[COMPLIANCE REVIEW]` flags route those to the attorney.

---

## Provenance

Built from the strategy research report (attorney-channel benchmarks: Bruce
Rivers, Attorney Tom, The DUI Guy, Gerry Oginski; 2025–2026 YouTube/Shorts
mechanics; ABA Model Rules 7.1/7.2 and state-bar variation; and open-source
references including `AgriciDaniel/claude-youtube` and YouTube Data API MCP
servers). Third-party stats in the report are estimates; platform mechanics change
— re-verify periodically.
