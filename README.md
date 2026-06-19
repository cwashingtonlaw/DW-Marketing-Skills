# DW Marketing Skills

A Claude Code **plugin marketplace** for Daniels & Washington law-firm marketing,
with attorney-advertising compliance built into every skill.

This repo is both a **marketplace** (the catalog Claude Code reads) and the home
of two plugins that work together: one writes the content, the other produces and
ships it.

## Plugins

| Plugin | Skills | What it does |
|---|---|---|
| [`ge-youtube`](./ge-youtube) | 12 | Great Elephant Law YouTube growth loop: compliance guardrails → audit → ideate → script → package → SEO → Shorts → publish gate → community → analyze → (back to ideate). |
| [`ge-video-pipeline`](./ge-video-pipeline) | 4 | Daily HeyGen short-form video pipeline: content queue → render (attorney avatar) → compliance gate → approve → schedule to YouTube + newsletter + cross-post. |

### How they fit together

`ge-youtube` is the **content brain** (what to make and how to make it
compliant); `ge-video-pipeline` is the **production line** that turns a topic
into a published video. The pipeline *reuses* the ge-youtube skills at each step
rather than duplicating them:

```
        ┌──────────────── ge-youtube (content + compliance) ────────────────┐
        │  ge-ideate · ge-script · ge-shorts · ge-package · ge-seo ·         │
        │  ge-publish (hard compliance gate) · ge-compliance(-la)            │
        └──────────────────────────▲────────────────────────────────────────┘
                                    │ invoked by
   ┌──────────────────────── ge-video-pipeline ──────────────────────────────┐
   │ ge-content-queue · ge-video-daily (orchestrator) · ge-heygen · ge-distribute │
   │                                                                          │
   │  backlog ─▶ daily-start ─▶ [ge-script/ge-shorts] ─▶ ge-heygen render ─▶  │
   │  [ge-package/ge-seo] ─▶ [ge-publish gate] ─▶ stage ─▶ notify (Chat) ─▶   │
   │  ── attorney approves (ge-content-queue) ─▶ ge-distribute:               │
   │       YouTube (scheduled publishAt) + Kit newsletter + cross-post webhook │
   └──────────────────────────────────────────────────────────────────────────┘
```

Two gates hold throughout: the **automated** `ge-publish` HOLD gate and the
**human** attorney approval. Nothing schedules without both.

## Install

Add this repo as a marketplace, then install whichever plugin(s) you want:

```
/plugin marketplace add cwashingtonlaw/DW-Marketing-Skills
/plugin install ge-youtube@dw-marketing
/plugin install ge-video-pipeline@dw-marketing
```

To install from a local clone instead:

```
/plugin marketplace add /path/to/DW-Marketing-Skills
/plugin install ge-youtube@dw-marketing
```

`ge-youtube` is pure skills — it works the moment it's installed (after the
one-time firm-profile setup in `ge-compliance`). `ge-video-pipeline` additionally
ships a Python package + CLI; see its README for the venv + credentials setup.

## Setup pointers

- **ge-youtube:** fill in the **FIRM PROFILE** block in
  [`ge-youtube/skills/ge-compliance/SKILL.md`](./ge-youtube/skills/ge-compliance/SKILL.md)
  (`CITY_STATE`, `RESPONSIBLE_ATTORNEY`, `FIRM_WEBSITE`, `FIRM_PHONE`,
  `GOVERNING_RULES`) before publishing anything. See
  [`ge-youtube/README.md`](./ge-youtube/README.md).
- **ge-video-pipeline:** create the venv, `~/.config/ge-video/config.json`, and
  `~/.config/ge-video/secrets.json` (`HEYGEN_API_KEY`, `GCHAT_WEBHOOK_URL`,
  `KIT_API_KEY`, `CROSSPOST_WEBHOOK_URL`) plus the YouTube OAuth files, then
  `bin/install-launchd.sh` for the daily timer. Full steps in
  [`ge-video-pipeline/README.md`](./ge-video-pipeline/README.md). **Do one manual
  dry-run before enabling the timer.**

## Repo layout

```
.claude-plugin/
  marketplace.json          # marketplace catalog (lists both plugins)
ge-youtube/                  # content + compliance skills (no external deps)
  .claude-plugin/plugin.json
  README.md
  skills/                    # 12 ge-* skills
ge-video-pipeline/           # production line (Python package + skills + launchd)
  .claude-plugin/plugin.json
  README.md
  gevideo/                   # config, queue, slots, heygen, youtube, kit, crosspost, notify, cli
  skills/                    # ge-content-queue, ge-heygen, ge-distribute, ge-video-daily
  bin/                       # launchd wrapper, plist, installer
  tests/                     # pytest suite (offline; no live API calls)
docs/superpowers/            # design specs + implementation plans
```

## Compliance note

Per ABA guidance, the responsible attorney remains accountable for marketing
output even when an AI tool drafts it. These skills are **drafting aids with
guardrails**, not a substitute for attorney review before anything publishes.
`ge-publish` is a hard gate that returns **HOLD** if any banned phrase or required
disclaimer is missing, and the pipeline additionally requires explicit attorney
approval before it schedules. The Louisiana overlay (`ge-compliance-la`) enforces
the no-non-lawyer-spokesperson rule — only the responsible attorney's own HeyGen
avatar/voice is used for ad content.

The three destinations no third-party tool can automate — **Facebook personal,
Instagram personal, Snapchat** — are surfaced as a manual-post reminder in the
daily approval notification, never silently dropped.
