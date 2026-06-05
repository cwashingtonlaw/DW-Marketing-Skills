---
name: ge-compliance-la
description: >
  Louisiana-specific attorney-advertising compliance reference for the Great
  Elephant Law YouTube skills. This is NOT triggered directly — it is a reference
  file loaded by ge-compliance (and through it, every ge- YouTube skill) when the
  firm's governing jurisdiction is Louisiana. It layers the Louisiana Rules of
  Professional Conduct 7.1–7.10 advertising regime on top of the generic ABA
  guardrail: the LSBA filing-number rules, the Rule 7.8 exemptions that decide
  whether YouTube content must be filed, the no-nonlawyer-spokesperson ban, the
  past-results disclaimer language, and the La. R.S. 37:223 settlement-fee
  disclosure. Read this whenever GOVERNING_RULES includes Louisiana.
---

# ge-compliance-la — Louisiana Advertising Rules (Shared Reference)

> **Scope.** Layers on top of `ge-compliance`. Where the two differ, **Louisiana
> controls** for Great Elephant Law. This is a drafting guardrail, NOT legal
> advice on the rules themselves — the responsible attorney and, where needed,
> LSBA Ethics Counsel make the final call.
>
> **Currency.** Reflects the Louisiana advertising rules as amended effective
> **January 1, 2022** (filing-number regime) and La. R.S. 37:223 (effective
> Jan. 1, 2021). Re-verify against the current LSBA Handbook on Solicitation and
> Lawyer Advertising before relying on any specific below.

---

## 1. THE BIG ONE — DOES YOUTUBE CONTENT HAVE TO BE FILED WITH THE LSBA?

Louisiana requires non-exempt advertisements to be **filed with the LSBA Rules of
Professional Conduct Committee** (prior to or concurrently with first
dissemination) and to **display an LSBA-assigned filing number**. The named lawyer
certifies the ad was filed (Rule 7.2(a), 7.7).

**But there are two exemptions that usually cover YouTube:**

- **Rule 7.8(g) — computer-accessed communications.** Websites, social media, and
  computer-accessed communications under Rule 7.6(b) are **exempt from the
  pre-filing/review requirement.** YouTube is a computer-accessed platform, so a
  firm's own channel content generally falls here.
- **Rule 7.8(a) — minimal-content exemption.** Communications containing only
  Rule 7.2(a)-required content plus Rule 7.2(b)-permissible content are exempt.

**Practical rule for this channel — emit a flag, don't self-clear:**
```
[LA FILING CHECK]: This appears to be computer-accessed content (likely exempt
from pre-filing under Rule 7.8(g)). BUT exemption depends on content. Confirm with
the responsible attorney whether (a) it stays within the exemption, or (b) a
voluntary LSBA filing + filing number is warranted. Do NOT assert it is exempt.
```

Caveats the skill must respect:
- The exemption is for the *filing* requirement. The **content rules (7.1, 7.2(c))
  still fully apply** to YouTube.
- The exemption does **not** cover **unsolicited electronic communications**
  (e.g., cold outreach emails/DMs to prospective clients) — those are governed by
  Rule 7.4/7.6(c) and are NOT exempt. Keep YouTube outreach to non-solicitation.
- If the firm ever runs **paid YouTube/third-party ads** (banners, pre-roll,
  click-throughs on someone else's site), analyze separately — third-party
  internet advertising has its own treatment and may not be exempt the same way.

---

## 2. LOUISIANA-SPECIFIC HARD RULES (stricter than the generic ABA list)

Add these to the `ge-compliance` banned/caution list:

1. **NO non-lawyer spokesperson — even with a disclaimer.** Louisiana prohibits
   using any non-lawyer spokesperson in an advertisement. This is stricter than
   most states.
   → For YouTube: the **attorney must be the on-camera voice/speaker** in
   firm-advertising videos. A hired actor/narrator/influencer "speaking for the
   firm" is **prohibited**. Flag any script that implies a non-lawyer spokesperson.
2. **Past-results disclaimer is mandatory and specific.** Any reference to past
   results requires a disclaimer such as **"Past results are not a guarantee of
   future successes"** or **"Results may vary."** Use this exact-style language,
   not a vague paraphrase.
3. **Settlement/judgment amounts trigger fee disclosure (La. R.S. 37:223).** If a
   video states the **monetary amount of a settlement or judgment**, it must also
   **disclose the attorney fees paid from the gross recovery.**
   → Default posture for this channel: **avoid naming specific settlement/verdict
   dollar amounts in videos.** If the attorney wants to, the skill must flag the
   R.S. 37:223 fee-disclosure requirement.
4. **No promising results; no unsubstantiated comparisons.** Rule 7.2(c) bars
   promising results, comparisons that can't be factually substantiated, and
   testimonials about past results without the disclaimer.
5. **Paid testimonials/endorsements must disclose the payment.** And client
   portrayals by non-clients, or non-authentic scene depictions, require
   disclaimers.
6. **Specialization:** A lawyer may claim an area of practice/concentration, but
   must **not** falsely suggest **board certification.** Safe framing: "we handle"
   / "our practice focuses on" / "concentrating in." Avoid bare "specialist."

---

## 3. REQUIRED IDENTIFIERS (Rule 7.2(a))

Every firm-advertising video should carry, in the description (and ideally
on-screen/spoken where practical):
- **Full name of at least one responsible lawyer** → `[ATTORNEY NAME]`.
- **Location of practice** (a bona fide office location / city) →
  `[CITY, LOUISIANA]`.
- **"Attorney advertising"**-style identification consistent with the firm's
  practice.
- **LSBA filing number** *if* the content is filed/non-exempt
  → `[LSBA FILING #: ____ or "exempt per Rule 7.8(g) — confirmed by attorney"]`.

---

## 4. LOUISIANA DISCLAIMER BLOCK (use in place of the generic where LA governs)

**Educational / general content:**
> *This video is general information about Louisiana law, not legal advice, and
> does not create an attorney-client relationship. Laws change and every case is
> different — consult a licensed Louisiana attorney about your specific
> situation.*

**If any past result is mentioned (add):**
> *Past results are not a guarantee of future successes. Results may vary.*

**If a settlement/judgment dollar amount is mentioned (add — R.S. 37:223):**
> *[Disclose attorney fees paid from the gross recovery — REQUIRED by La. R.S.
> 37:223. Route to attorney to populate.]*

**Reaction/commentary (add):**
> *This is commentary on publicly reported information, not a statement of fact
> about any party and not legal advice.*

**Attribution:**
> *Attorney advertising. Great Elephant Law — [ATTORNEY NAME], [CITY], Louisiana.
> [PHONE] · [WEBSITE]. [LSBA Filing # ___ / Rule 7.8(g) exempt — confirm].*

---

## 5. LOUISIANA REVIEW FLAGS (raise for attorney / LSBA Ethics Counsel)

```
[LA COMPLIANCE REVIEW — <reason>]: <what to confirm> — route to [ATTORNEY NAME]
(and LSBA Ethics Counsel if needed) before publishing.
```
Trigger on:
- Any **settlement/verdict dollar figure** (R.S. 37:223 fee disclosure).
- Any **non-lawyer appearing to speak for the firm** (prohibited spokesperson).
- Any **testimonial / endorsement** (payment disclosure; authenticity).
- Any **comparison** to other lawyers/firms.
- Any **specialization/"specialist"** phrasing (board-certification risk).
- **Unsolicited outreach** (DMs/emails to prospects) — NOT exempt; separate rules.
- Uncertainty about whether content is **filing-exempt** under Rule 7.8.

---

## 6. SOURCES (verify current versions before relying)
- LSBA Rules of Professional Conduct, Article 7 (advertising), amendments
  effective Jan. 1, 2022 — lsba.org / lalegalethics.org (Rules 7.1, 7.2, 7.6,
  7.7, 7.8, 7.10).
- LSBA Handbook on Solicitation and Lawyer Advertising in Louisiana (2nd ed.).
- La. R.S. 37:223 (settlement/judgment amount → fee disclosure), eff. Jan. 1, 2021.
- Rule 7.8(g) computer-accessed-communication exemption; Rule 7.8(a) minimal-
  content exemption.

> These are summarized for drafting guardrails only. The responsible attorney is
> accountable for compliance and should consult LSBA Ethics Counsel on close calls
> (e.g., whether a given video is filing-exempt).
