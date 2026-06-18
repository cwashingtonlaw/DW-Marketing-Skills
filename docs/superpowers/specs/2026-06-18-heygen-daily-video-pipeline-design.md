# Design Spec — HeyGen Daily Video Pipeline (`ge-video-pipeline`)

**Date:** 2026-06-18
**Repo:** `cwashingtonlaw/DW-Marketing-Skills` (marketplace `dw-marketing`)
**Status:** Approved design — pending spec review before implementation planning.

## 1. Goal

Publish at least one short-form video per day to the Great Elephant Law YouTube
channel, produced with HeyGen using a custom avatar + voice clone of the
responsible attorney, with attorney-advertising compliance enforced and a human
approval gate before anything goes live. Cross-posting to other social platforms
is supported through a pluggable distribution layer, added after the core
YouTube loop is proven.

## 2. Decisions locked during brainstorming

| Decision | Choice |
|---|---|
| Human-in-the-loop | **Approve-then-publish queue.** Agent does everything autonomously up to a staged, ready-to-publish state; the responsible attorney gives a single approve/reject; approval triggers the scheduled publish. |
| Primary target + format | **YouTube Shorts, daily** (vertical, ~30–60s). Long-form stays a separate, manually triggered track. |
| Avatar / voice | **Custom HeyGen avatar + voice clone of the responsible attorney.** Required to satisfy Louisiana's no-non-lawyer-spokesperson rule (`ge-compliance-la`). |
| Topic source | **Maintained content backlog/calendar.** `ge-ideate` proposes topics; attorney promotes them to `ready`; the daily job pulls the next `ready` item. |
| Distribution scope | **YouTube first, pluggable distribution interface.** Cross-post adapter added without reworking the pipeline. |
| Cross-post engine | **Opus Clip as the primary automated adapter** (API/webhooks or its Zapier MCP). SocialPilot is an optional manual/secondary tool. |
| Newsletter email | **Kit broadcast adapter** — emails the subscriber list the YouTube link, scheduled to send at the video's go-live time. (Kit posts to no social feeds, but its broadcast API fits the newsletter email.) |
| Unautomatable destinations | **Manual-post reminder** for Facebook personal, Instagram personal, and Snapchat in the approval notification. No third-party tool can automate these (Meta blocks personal-profile posting; no tool supports Snapchat). |
| Integration approach | **MCP connectors + scheduled headless Claude run** (Approach A). HeyGen via its MCP/API; YouTube via the Data API wrapped in a plugin script; launchd daily job; Gmail + Google Chat for notifications. |

## 3. Connector research summary (2026)

Auto-post / scheduling support against the nine requested destinations:

| Destination | Opus Clip | SocialPilot | Kit |
|---|---|---|---|
| Facebook personal profile | ❌ | ❌ | ❌ |
| Facebook business Page | ✅ (Pro) | ✅ | ❌ |
| Instagram personal | ❌ | ❌ | ❌ |
| Instagram business/creator | ✅ Reels | ✅ | ❌ |
| TikTok | ✅ | ✅ (publish may need a phone tap) | ❌ |
| YouTube + Shorts | ✅ | ✅ | ❌ |
| LinkedIn personal profile | ⚠️ unclear | ✅ | ❌ |
| LinkedIn company page | ⚠️ likely | ✅ | ❌ |
| X (Twitter) | ✅ (beta) | ✅ | ❌ |
| Snapchat | ❌ | ❌ | ❌ |
| **Claude-drivable** | ✅ API + webhooks + Zapier MCP, self-serve | ⚠️ REST API is Enterprise-tier only; Zapier text-oriented; no MCP | ✅ API/MCP but no social posting |

Conclusions: Opus Clip is the only one of the three Claude can drive cleanly
without an Enterprise contract, and it is video-native. SocialPilot has the
broadest coverage but gates its API behind Enterprise pricing. Kit posts to no
social platforms. Facebook personal, Instagram personal, and Snapchat cannot be
automated by any tool and are handled as manual reminders.

## 4. Architecture

A new plugin **`ge-video-pipeline`** in the `dw-marketing` marketplace, alongside
`ge-youtube`. It reuses the existing content skills (`ge-ideate`, `ge-script`,
`ge-shorts`, `ge-package`, `ge-seo`, and the hard compliance gate `ge-publish`)
and adds generation, packaging-for-publish, scheduling, publishing, and
orchestration. A single **launchd daily job** runs a headless `claude` session —
the same operational pattern as the firm's court/jail tracker.

### 4.1 New skills

| Skill | Role | Trigger phrases |
|---|---|---|
| `ge-video-daily` | Orchestrator / headless daily entrypoint; runs the whole pipeline and stages output for approval | "run today's video," "daily video job" |
| `ge-heygen` | Wraps HeyGen: script → avatar+voice render → poll → download MP4 | "generate the HeyGen video," "render the avatar video" |
| `ge-distribute` | Pluggable distribution: v1 YouTube (native); v2 Opus Clip (social cross-post) + Kit (newsletter email) adapters | "schedule the video," "publish to YouTube," "cross-post the video," "email the newsletter" |
| `ge-content-queue` | Manages the backlog/calendar and the pending-approval queue; handles `approve`/`reject` | "content backlog," "approve today's video," "what's queued" |

### 4.2 Supporting scripts (TDD'd, in each skill's `scripts/`)

- `heygen_generate.py` — submit render job, poll status, download MP4.
- `youtube_schedule.py` — OAuth2; upload as private with `publishAt`.
- `opusclip_post.py` — v2 cross-post adapter (Opus Clip API / Zapier MCP).
- `kit_broadcast.py` — v2 newsletter adapter; create/schedule a Kit broadcast
  with the YouTube link, send time = the video's `publishAt`.
- `queue.py` — JSON state machine for backlog + pipeline + approval queue.
- `notify.py` — Gmail + Google Chat notifications (reuses existing connectors).
- `bin/` — launchd plist + installer.

## 5. Data flow (one day)

1. **launchd** fires `claude -p "run ge-video-daily"` each morning. Idempotent —
   keyed by date; re-runs are no-ops if today's item already exists.
2. **Pull topic** — `ge-content-queue` returns the next `ready` backlog item.
3. **Script** — `ge-script` → `ge-shorts` adapts it to a 30–60s vertical Short
   (hook, on-screen text, spoken disclaimer, compliant CTA, attribution).
4. **Generate** — `ge-heygen` renders with the attorney's `avatar_id`/`voice_id`,
   polls to completion, downloads `video.mp4`.
5. **Package** — `ge-package`/`ge-seo` produce title, description (with the
   disclaimer block), tags, and a thumbnail brief.
6. **Compliance gate** — `ge-publish` runs → CLEAR / **HOLD**. A HOLD never
   proceeds to the approval queue and never schedules.
7. **Stage + notify** — if CLEAR: status → `pending_approval`; the attorney gets a
   Gmail + Google Chat message containing the script summary, video link,
   compliance verdict, and the manual-post reminder (FB personal / IG personal /
   Snapchat).
8. **Approve** — on approval, `ge-distribute` (YouTube adapter) uploads the video
   as *private* with `publishAt` = the next open daily slot → status `scheduled`.
   **YouTube publishes it at the slot time with nothing running.** (v2: the Opus
   Clip adapter also schedules the cross-posts, and the Kit adapter schedules a
   newsletter broadcast with the YouTube link to send at the same go-live time —
   so the email links to an already-live video.)
9. **Backlog refill** — when the `ready` count drops below a threshold,
   `ge-ideate` proposes new topics as `proposed`; the attorney promotes them to
   `ready`, preserving editorial control.

## 6. Compliance (two gates)

1. **Automated** — `ge-publish` hard gate. Any compliance ❌ → **HOLD**; HOLD items
   never enter the approval queue and never schedule. `ge-compliance` /
   `ge-compliance-la` run every time.
2. **Human** — the attorney approval step. Nothing reaches YouTube without *both*
   the automated gate passing *and* explicit approval. The custom attorney
   avatar+voice satisfies the Louisiana no-non-lawyer-spokesperson rule.

## 7. State & storage

On-disk JSON state in a data directory outside the repo (git-ignored):

```
~/.local/share/ge-video/
  config.json        # avatar_id, voice_id, channel_id, publish time/timezone,
                     # backlog/buffer thresholds, firm-profile pointer
  backlog.json       # editorial calendar: topics with status proposed | ready
  pipeline/YYYY-MM-DD/
    script.md
    video.mp4
    metadata.json    # title, description, tags, thumbnail brief, compliance
                     # verdict, status
```

Item status flow:
`proposed → ready → generated → pending_approval → approved → scheduled →
published` (plus `hold` and `error`).

**"≥1/day" guarantee:** maintain a buffer of N scheduled-ahead days; if the buffer
or the `ready` backlog runs low, the daily notification nudges the attorney.
`publishAt` = the next unused daily slot at a fixed local time (default 12:00 CT).

## 8. Secrets & config

HeyGen API key, YouTube OAuth client + refresh token, Opus Clip credentials, and
the Kit API key live outside the repo (`~/.config/ge-video/`, `chmod 600`) and are
never committed. Non-secret IDs (avatar, voice, channel, Kit list/segment id, the
newsletter from-name/address) live in `config.json`. The README documents the
one-time setup: HeyGen avatar/voice creation, YouTube OAuth consent, Opus Clip
connection, Kit API key + list selection, and retrieving the IDs.

## 9. Error handling

- **HeyGen** failure/timeout → retry with backoff; after N attempts → status
  `error` + a "no video today, action needed" notification.
- **YouTube** OAuth expiry → auto-refresh; if refresh fails → notify to re-auth.
  Quota is a non-issue (one upload ≈ 1,600 of 10,000 daily units).
- **Opus Clip** (v2) failure → cross-posts fail soft; the YouTube publish still
  proceeds, and the failure is reported.
- **Kit** (v2) broadcast failure → fails soft; the YouTube publish still proceeds,
  and the failure is reported so the email can be sent manually.
- **Empty/low backlog** → notify "backlog low, run ge-ideate."
- **Hard rule:** never publish on HOLD or without approval. Every run appends to a
  pipeline log.
- **`--dry-run`** flag runs the whole flow but skips real HeyGen render, YouTube
  upload, and cross-posts.

## 10. Testing (TDD)

- **Unit:** `queue.py` state transitions, `publishAt` slot computation, metadata
  builder, compliance-verdict parsing.
- **Integration (mocked):** HeyGen, YouTube, Opus Clip, and Kit clients hit
  recorded/stub responses — no live API calls in tests.
- **Manual gate:** one real end-to-end Short, reviewed by the attorney, before the
  launchd timer is enabled.

## 11. Out of scope (this iteration)

- Long-form daily video (separate manual track).
- SocialPilot automated adapter (manual/secondary only unless Enterprise API is
  later acquired).
- Automated posting to Facebook personal, Instagram personal, Snapchat
  (manual-reminder only — not possible via any third-party tool).
- Post-publish analytics automation (`ge-analyze` remains manually invoked).

## 12. Build order (high level)

1. `ge-content-queue` + `queue.py` state machine (the backbone).
2. `ge-heygen` + `heygen_generate.py`.
3. `ge-distribute` YouTube adapter + `youtube_schedule.py`.
4. `ge-video-daily` orchestrator wiring steps 2–6 of the data flow + `notify.py`.
5. launchd installer (`bin/`); manual end-to-end test; enable timer.
6. v2 distribution behind the `ge-distribute` interface: Opus Clip adapter
   (`opusclip_post.py`) for social cross-posts, and the Kit adapter
   (`kit_broadcast.py`) for the newsletter email — both scheduled to the video's
   go-live time.
