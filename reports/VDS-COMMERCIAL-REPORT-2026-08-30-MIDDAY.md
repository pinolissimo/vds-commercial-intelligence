# VDS Commercial Report — 2026-08-30 — Midday

## Stato sintetico

**QA VDS7: FAIL_CORRECTED.** Nessun nuovo evento positivo/referral/proposal/call oggi. Nessuna azione commerciale richiesta su BEYOND BARRIERS, che resta `WAITING_FOR_INBOUND` per decisione utente esplicita.

## 1. EU PROJECTS

- Early-funded watchlist: **11** progetti.
- Contactable now: **0**.
- Già contattati/soppressi nel watchlist: **1** (SENSORAMA; FIRST_CONTACT storico verificato, nessun secondo contatto consentito).
- Priorità di ricerca: REMEDIES 5.0, NAVI, HUBS4BUILD e altri candidati solo dopo ricostruzione `grant → WP/task → beneficiary owner → verified buyer/contact route`.
- BEYOND BARRIERS: **WAITING_FOR_INBOUND**, nessun follow-up/solicitation.
- Nuovi EU HOT/HOT+ promossi oggi: **0**.

## 2. COLLABORATIONS

- Canonical opportunities complessive EU/Collaborations: **69**.
- Contacted verificati: **28**.
- Qualified not contacted: **41**.
- Direct Commercial actionable: **24**.
- Direct Commercial HOLD: **3**.
- Public procurement manuale e separato: **5**.
- Oggi è domenica: la policy Monday–Friday blocca nuovi first-contact/follow-up anche sui lead altrimenti pronti.

### Outreach SENT oggi

**Esattamente 1 FIRST_CONTACT commerciale:**

- Pump Communication → `info@pumpcommunication.com`
- Hostinger `INBOX.Sent` UID **116**
- 30/08/2026 09:03:28 Europe/Madrid
- Subject: `Candidatura freelance Web Designer & Developer — Visual Design Studio`

Hostinger UID **117** è un alert interno inviato a `allocca.pino@gmail.com` e non viene contato come outreach.

### Replies / outcomes

Hostinger Inbox oggi: nessuna nuova risposta commerciale; solo una comunicazione marketing 360imprimir. Meetings **0**, proposals **0**, wins **0**, revenue won **€0**.

## 3. LOCAL SME 999

### KPI dopo QA

- Raw discovered: **3**
- Deeply reviewed: **3**
- Rejected: **0**
- Qualified: **0**
- Ready for contact review: **0**
- Ready to contact: **0**
- Contacted: **0**
- Replies: **0**
- Wins: **0**

### Breakdown

- Country: Spain — 3 raw/deep-review.
- Region: Catalonia — 3.
- Province: Barcelona — 3.
- Comarca: Garraf — 3.
- Municipality: Sitges — 3.
- Activity: Laundry 1 · Car wash 1 · Physiotherapy 1.

### Strongest current local research candidates

1. **La Lavandería Sitges** — score 86; reputation signal 4.7 / 63; no dedicated site surfaced in current search. QA hold: global organization-level suppression/Sent reconciliation incomplete and public/social profile depth still insufficient.
2. **Ech2Onet** — score 85; 4.7 / 59; Google local + Visit Sitges corroborate identity/contact and no dedicated-site link. Targeted Hostinger Sent search to `ech2onet@gmail.com` returned zero, but organization-level global dedup remains mandatory.
3. **Equilibri, Centre de Fisioteràpia** — score 83; active local practice; historical domain reported obsolete/noncurrent. QA hold: global dedup incomplete, reported Facebook presence not directly verified and directory lineage requires caution.

### Rejected examples

**0 rejected** in this cohort. The three candidates were not rejected; they were deterministically demoted from premature `READY_FOR_CONTACT_REVIEW` to `RESEARCH` until all qualification gates pass.

### Tax-policy coverage

Spain: **VERIFIED_OFFICIAL_SOURCE** via Agencia Tributaria. Marketing claim mode: conditional business-expense treatment only. No fixed tax saving, guaranteed percentage or universal deductibility claim allowed. Other planned countries: no tax claim until official authority verification exists.

## Source / territorial coverage

Source protocol remains multi-source and lineage-aware: mirror URLs do not count as independent evidence; search engines/directories are discovery/corroboration aids, not final proof when primary evidence exists. Low-yield territories with incomplete source-family coverage remain `UNDER_SEARCHED`.

Collaborations territorial coverage:

- Italy: **17/20** territories with at least one qualified account; 32 accounts with verified region + 1 remote/geography-to-verify.
- Spain: **16/19** territories with at least one qualified account; 25 accounts with verified territory + 2 remote/geography-to-verify.
- Local SME: current search footprint Spain → Catalonia → Barcelona → Garraf → Sitges only; expansion remains open.

## QA / dedup issues

**CRITICAL corrected:** all three new Local SME records had `suppression_checked=false` despite being promoted to `READY_FOR_CONTACT_REVIEW`. They were returned to `RESEARCH`, with append-only QA events. No outreach had occurred.

**MAJOR corrected:** local master/index and dashboard were inconsistent about qualified counts. They now expose raw/deep-review separately and correctly show 0 qualified.

Duplicate FIRST_CONTACT today: **0**. Historical duplicate violations preserved: **2** (Persuadis, Marmellata Lab). Ten older 28 Aug recipients remain pending canonicalization; `BATMAN / nobody@knows.us` remains REVIEW_REQUIRED.

## Pipeline KPI

- EU/Collaboration opportunities: **69**
- Verified contacted: **28**
- Qualified not contacted: **41**
- Direct commercial actionable: **24**
- Positive referral: **1 historical**, passive WAITING_FOR_INBOUND
- Meetings: **0**
- Proposals: **0**
- Won: **0**
- Revenue won: **€0**
- Probability model: **UNCALIBRATED**
- Weighted pipeline: **null**
- Local SME raw/qualified/contacted: **3 / 0 / 0**

## Top 5 next actions

1. Complete global organization-level dedup/suppression/Sent-history checks for the 3 Local SME identities, then deepen remaining public/social evidence before any re-qualification.
2. On Monday, process the strongest 24 Direct Commercial opportunities only after fresh route + global dedup + source freshness gates.
3. Canonicalize the 10 historical 28 Aug recipients and resolve BATMAN before any overlap-sensitive outreach.
4. Continue EU early-funded deep research to explicit Communication/Dissemination WP/task and responsible beneficiary routes; keep BEYOND BARRIERS passive.
5. Keep public procurement user-managed, with ABAQUA and ProBurgos as nearest deadline reviews.

Dashboard: https://github.com/pinolissimo/vds-commercial-intelligence/blob/main/README.md

Audit: https://github.com/pinolissimo/vds-commercial-intelligence/blob/main/audits/2026-08-30-1300.md
