# DW Marketing Skills

A Claude Code **plugin marketplace** for Daniels & Washington law-firm marketing,
with attorney-advertising compliance built into every skill.

This repo is both a **plugin** (the skills you install) and a **marketplace**
(the catalog Claude Code reads to offer those plugins).

## Plugins

| Plugin | Skills | What it does |
|---|---|---|
| [`ge-youtube`](./ge-youtube) | 12 | Great Elephant Law YouTube growth loop: compliance guardrails → audit → ideate → script → package → SEO → Shorts → publish gate → community → analyze → (back to ideate). |

## Install

Add this repo as a marketplace, then install the plugin:

```
/plugin marketplace add cwashingtonlaw/DW-Marketing-Skills
/plugin install ge-youtube@dw-marketing
```

To install from a local clone instead:

```
/plugin marketplace add /path/to/DW-Marketing-Skills
/plugin install ge-youtube@dw-marketing
```

Once installed, the `ge-*` skills load automatically when their trigger phrases
come up (e.g. "ideate video ideas," "review my analytics," "is this ad
compliant"). See [`ge-youtube/README.md`](./ge-youtube/README.md) for the full
skill chain and the **required firm-profile setup** in `ge-compliance`.

## Repo layout

```
.claude-plugin/
  marketplace.json        # marketplace catalog (lists the plugins below)
ge-youtube/
  .claude-plugin/
    plugin.json           # plugin manifest
  README.md               # plugin docs + skill chain
  skills/
    ge-analyze/SKILL.md
    ge-audit/SKILL.md
    ... (12 skills)
```

## Compliance note

Per ABA guidance, the responsible attorney remains accountable for marketing
output even when an AI tool drafts it. These skills are **drafting aids with
guardrails**, not a substitute for attorney review before anything publishes.
`ge-publish` is a hard gate that returns **HOLD** if any banned phrase or
required disclaimer is missing.
