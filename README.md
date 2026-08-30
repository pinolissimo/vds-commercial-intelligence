# VDS Commercial Intelligence — Revenue Command Center

> **Single source of truth:** `pinolissimo/vds-commercial-intelligence` · `main`  
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **VDS7:** precisione > volume · evidenza > inferenza · duplicate FIRST_CONTACT tolerance = **0**

**Snapshot:** 30 agosto 2026 · 13:00 Europe/Madrid  
**Operating mode:** **CONVERSION FIRST · THREE COMMERCIAL WORKSTREAMS · PROCUREMENT SEPARATE**  
**QA:** `FAIL_CORRECTED` — Local SME transition-gate regression corrected; historical mailbox reconciliation remains open.

---

## 🎛️ Executive Dashboard

| Opportunity | Verified first contacts | Qualified not contacted | Positive referral | Meeting | Proposal | Revenue won |
|---:|---:|---:|---:|---:|---:|---:|
| **69** | **28** | **41** | **1** | **0** | **0** | **€0** |

**Partner accounts:** 63 · **pipeline activation:** 40.6%.

The 69 canonical opportunities belong to the EU Projects / Collaborations CRM. `LOCAL_SME_999` is intentionally counted separately so raw local discoveries never inflate qualified opportunity metrics. Public procurement is also kept operationally separate and user-managed.

| Commercial segment | Current volume | Operational meaning |
|---|---:|---|
| 🎯 **Direct Commercial — actionable** | **24** | Personalized outreach/application only after final dedup, freshness and route gate |
| 🟠 **Direct Commercial — HOLD** | **3** | Contract/cross-border evidence still incomplete |
| 🏛️ **Public Procurement — manual** | **5** | User-owned GO/NO-GO and tender review; never automated outreach |
| 🏪 **Local SME 999 — raw/deep review** | **3 / 3** | Sitges cohort under QA hold; **0 qualified, 0 ready, 0 contacted** |

---

## 🏪 Local SME 999 — QA HOLD BEFORE QUALIFICATION

The first local cohort was discovered in **Sitges · Garraf · Barcelona · Catalonia · Spain** across three activities: laundry, car wash and physiotherapy.

| Metric | Value |
|---|---:|
| Raw discovered | **3** |
| Deeply reviewed | **3** |
| Under research | **3** |
| Rejected | **0** |
| Qualified | **0** |
| Ready for contact review | **0** |
| Ready to contact | **0** |
| Contacted | **0** |
| Replies | **0** |
| Wins | **0** |

A VDS7 audit found that the three new records had been promoted to `READY_FOR_CONTACT_REVIEW` while `suppression_checked=false`. Because global organization-level deduplication, suppression and historical Sent reconciliation are mandatory before Local SME qualification, all three were deterministically returned to `RESEARCH` with append-only QA events. **No outreach had occurred.**

Current research cohort:

- **La Lavandería Sitges** — strong local reputation signal (4.7 / 63) and website-gap evidence, but deeper public/social evidence and global dedup remain incomplete.
- **Ech2Onet** — 4.7 / 59, Google local + Visit Sitges identity/contact evidence; Hostinger Sent search to its public email returned zero, but organization-level global dedup remains mandatory.
- **Equilibri, Centre de Fisioteràpia** — historical domain reported obsolete/noncurrent; direct social/public-presence verification and source-lineage review remain incomplete.

Spain tax messaging is backed by official Agencia Tributaria sources and may be used only conditionally. No guaranteed deduction, fixed saving or percentage claim is permitted.

➡️ [Local SME master](local-no-website/master-index.json) · [Local QA-held index](local-no-website/views/qualified-index.md) · [€999 offer](local-no-website/config/offer-999.json) · [Tax policy](local-no-website/config/tax-policy.json)

---

## 🚀 Direct Commercial Conversion Plan

### Tier 1 — strongest buyer intent / fit
**Aplum Studio → Grownnectia → Virtual Marketing Spain → Mucui → Mobyleshop → Onebit → Zmot Lab**

- **Aplum:** freelance 1 year + possible continuity; WordPress/Elementor/HTML/CSS/PHP with GSAP/Figma/UX-UI as explicit pluses.
- **Grownnectia:** P.IVA, continuous infrastructure + WordPress/WooCommerce; listing currently valid through 28 Sep 2026.
- **Virtual Marketing Spain:** verified freelancer-network listing; WordPress/Elementor/WooCommerce + AI/no-code, continuous opportunity flow, possible stable long-term collaboration.

### Tier 2 — strong recurring/agency collaboration
**Global Service Impresa → Aderen → Vaivén Estudio → Digityze → Dream Big Design → Studiart**

### Tier 3 — valid but extra constraints
**Hays España → Mindrift → Robert Half Contracting**

**DNA Agency** remains blocked until the exact current application route is re-established.

➡️ [Direct Commercial Pipeline](views/direct-commercial-pipeline.json) · [Monday Direct Outreach Pack](reports/MONDAY-DIRECT-OUTREACH-PACK-2026-08-31.md) · [Application Copy Pack](reports/MONDAY-APPLICATION-COPY-PACK-2026-08-31.md) · [Exact Contact Route Matrix](views/direct-contact-route-matrix.json)

Because today is Sunday, new commercial first contacts/follow-ups remain blocked by the Monday–Friday working-hours policy.

---

## ✉️ Current-day outreach evidence

Exactly **1 commercial FIRST_CONTACT** is verified today:

- **Pump Communication** — `info@pumpcommunication.com` — Hostinger `INBOX.Sent` UID **116** — 30 Aug 2026 09:03:28 Europe/Madrid — subject `Candidatura freelance Web Designer & Developer — Visual Design Studio`.

Hostinger UID **117** is an internal alert to `allocca.pino@gmail.com` and is **not** counted as commercial outreach.

Current-day duplicate FIRST_CONTACT violations: **0**.

---

## 🇪🇺 EU Projects

Early-funded watchlist: **11** projects · **0 contactable now** · **1 already contacted/suppressed**.

Priority research remains WP/task → responsible beneficiary → buyer/contact route before any promotion. `TO_VERIFY` and inferred digital needs are never treated as proven procurement opportunities.

**SENSORAMA** remains globally suppressed from a new FIRST_CONTACT because Sent UID 79 proves prior outreach.

### BEYOND BARRIERS — WAITING FOR INBOUND

The explicit user decision remains authoritative: `WAITING_FOR_INBOUND` · no follow-up · no solicitation · reopen only on genuinely new inbound.

[Opportunity](opportunities/OPP-EU-BEYOND-BARRIERS-WEB.json) · [EU watchlist](eu-projects/early-funded-watchlist-2026-08-28.json)

---

## 🏛️ Public Procurement — USER MANAGED

Public administrations, municipalities, institutional bodies and regulated procurement remain a separate manual funnel. No automated first-contact outreach or bid submission.

Current manual opportunities: **5**. Nearest deadlines: ABAQUA 03/09, ProBurgos 04/09, Los Realejos 10/09, Autoridad Portuaria de Sevilla 14/09, Diputació de Barcelona 08/10.

➡️ [Manual Public Procurement Report](reports/MANUAL-PROCUREMENT-OPPORTUNITIES.md) · [Public Procurement Pipeline](views/public-procurement-pipeline.json)

---

## 🔻 Funnel

| Stage | Volume |
|---|---:|
| Canonical EU/Collaboration opportunities | **69** |
| Verified first contacts | **28** |
| Qualified not contacted | **41** |
| Direct commercial actionable | **24** |
| Public procurement manual | **5** |
| Reply threads | **1** |
| Positive referrals | **1** — passive inbound wait |
| Meetings | **0** |
| Proposals | **0** |
| Won | **0** |
| Local SME raw / qualified / contacted | **3 / 0 / 0** |

Probability model remains **UNCALIBRATED**. Weighted pipeline remains `null`. The configured **€999** Local SME offer is a product price, not won or weighted pipeline revenue.

---

## 🗺️ Coverage

- **Italy collaborations:** 17/20 territories with at least one qualified account; 32 accounts with verified region + 1 remote/geography-to-verify.
- **Spain collaborations:** 16/19 territories with at least one qualified account; 25 accounts with verified territory + 2 remote/geography-to-verify.
- **Local SME:** Spain → Catalonia → Barcelona → Garraf → Sitges currently has 3 raw/deep-review candidates; no qualified local prospect after QA correction.
- Incomplete zero-result territories remain `UNDER_SEARCHED`, never `LOW_OPPORTUNITY` merely because current yield is low.

---

## 🛡️ Safety / QA

- **Latest audit:** `FAIL_CORRECTED` — [2026-08-30 13:00](audits/2026-08-30-1300.md).
- Current-day verified commercial FIRST_CONTACT: **1**.
- Current-day duplicate FIRST_CONTACT violations: **0**.
- Historical duplicate events preserved: **Persuadis** and **Marmellata Lab**.
- Ten older 28 Aug recipients remain pending canonicalization and are a hard overlap-risk constraint.
- `BATMAN / nobody@knows.us` remains `REVIEW_REQUIRED`.
- Local SME candidates remain `RESEARCH` until global dedup/suppression/Sent-history and residual source checks pass.
- BEYOND BARRIERS remains passive `WAITING_FOR_INBOUND`.
- No guessed contacts, unsupported budgets, invented probabilities, rates, availability or tax savings may advance a commercial gate.

---

## Top Next Actions

1. Complete global dedup/suppression/Sent-history reconciliation for the 3 Local SME identities and deepen remaining source evidence.
2. On the next working day, review the strongest 24 direct-commercial opportunities for personalized gated execution.
3. Continue canonicalization of the 10 historical recipients and resolve `BATMAN / nobody@knows.us` before any overlap-sensitive action.
4. Continue EU watchlist deepening for explicit Communication/Dissemination WP/task and responsible beneficiary routes; never regenerate BEYOND BARRIERS solicitation.
5. Keep public procurement in the user-managed GO/NO-GO lane, with ABAQUA and ProBurgos nearest deadlines.

---

## Canonical operational views

- [Master index](master-index.json)
- [Direct Commercial Pipeline](views/direct-commercial-pipeline.json)
- [Public Procurement Pipeline](views/public-procurement-pipeline.json)
- [Next Best Actions](views/next-best-actions.json)
- [Action Queue](views/action-queue.json)
- [Commercial SLA](views/commercial-sla.json)
- [Success Indicators](views/success-indicators.json)
- [Active Opportunities](views/active-freelance-opportunities.json)
- [Local SME 999](local-no-website/master-index.json)

> **Conversion > activity. Evidence > inference. Revenue > vanity metrics.**
