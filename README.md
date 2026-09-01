# VDS Commercial Intelligence — Revenue Command Center

> **Single source of truth:** `pinolissimo/vds-commercial-intelligence` · `main`  
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **VDS7:** precisione > volume · evidenza > inferenza · duplicate FIRST_CONTACT tolerance = **0**

**Snapshot:** 1 settembre 2026 · 09:07 Europe/Madrid  
**Operating mode:** **ACTIVE DISCOVERY · INBOUND MONITORING · ROUTE-SAFE EXECUTION**  
**QA:** mandatory identity / freshness / route / geography / fit / suppression / global dedup / Gmail Sent / Hostinger Sent gates enforced per recipient.

---

## 🎛️ Executive Dashboard

| KPI | Current verified state |
|---|---:|
| Monday commercial emails verified in Hostinger Sent | **21** |
| Tuesday 1 Sep verified FIRST_CONTACT | **1** |
| Current priority direct-email queue | **0** |
| Monday duplicate FIRST_CONTACT violations | **0** |
| Tuesday duplicate FIRST_CONTACT violations | **0** |
| Monday positive referrals | **1** |
| Monday negative replies | **1** |
| Monday hard bounces | **4** |
| New unmatched bounce requiring reconciliation | **1** |
| Local SME 999 contacted | **8 / 8 qualified** |
| Local SME hard bounces | **3** |
| Meetings | **0** |
| Proposals | **0** |
| Revenue won | **€0** |

The numerical Monday target was **30+**, but only **21** candidates survived every final gate. The shortfall is intentional: no stale, duplicate, guessed, geography-ineligible, price-gated, ambiguous-route or weak-fit candidate was converted into an email merely to reach the target.

➡️ [Monday wave 01](outreach/2026-08-31-partner-hunt-morning-wave-01.json) · [Monday wave 02](outreach/2026-08-31-partner-hunt-morning-wave-02.json) · [Suppression registry](governance/suppression-registry.json)

---

## 🚨 Current commercial events

### SO Design Online — FIRST_CONTACT SENT / VERIFIED

The live official careers page was reverified on 1 Sep and still lists **WordPress Website Builder — Remote / Contract or project-based**, with the exact application route `support@sodesign.online`. Global repository/suppression, Gmail Sent and Hostinger Sent checks were clear before execution. A personalized application was sent from exactly `info@visualdesignstudio.es` with a role-tailored English PDF CV and portfolio. Official Hostinger `INBOX.Sent` **UID 149** verifies transmission.

**State:** `WAITING_FOR_REPLY`. No second proactive first contact may be generated. Substantive positive/referral/pricing/proposal/call replies require USER action.

➡️ [Opportunity](opportunities/OPP-REMOTE-SO-DESIGN-ONLINE-WORDPRESS-BUILDER-2026.json) · [Verified outreach event](outreach/2026-09-01-so-design-online-first-contact.json)

### Aunar Viajes — UNMATCHED HARD BOUNCE / REVIEW_REQUIRED

Hostinger INBOX **UID 1282** reports delivery failure to `info@aunarviajes.com`: DNS host/domain not found. No matching canonical repository identity and no Hostinger Sent message to that recipient were found during immediate reconciliation. **Do not resend or infer campaign ownership.** Keep as `REVIEW_REQUIRED` until origin is established.

### Daniele Debernardis — POSITIVE REFERRAL

Daniele replied after the first contact and **forwarded the request to his colleague Fabio Vanacore**, who was placed in CC. This is a genuine routed referral and is now a **USER-action** thread. No automated reply and no separate first-contact solicitation to Fabio was generated.

### MarkeThink — CLOSED / NEGATIVE REPLY

MarkeThink replied that its selection process is already in the final stage and it is **not accepting new applications**. The opportunity is closed for this round; no follow-up is generated.

---

## ✉️ Monday 2026-08-31 — verified execution

All items below were sent one-to-one from exactly `info@visualdesignstudio.es` and verified in official Hostinger `INBOX.Sent` before being recorded.

| UID | Organization / project | Route | Outcome |
|---:|---|---|---|
| 118 | Visioni | `info@visioni.info` | SENT |
| 119 | Evo Sistemi | `info@evosistemi.com` | SENT |
| 120 | Ibérica Studio | `trabajo@ibericastudio.com` | **HARD BOUNCE** |
| 121 | Daniele Debernardis | `info@danieledebernardis.it` | **REFERRAL RECEIVED** |
| 124 | Boneluv | `hola@boneluv.com` | SENT |
| 125 | Cantabria Web Design | `info@cantabriawebdesign.es` | SENT |
| 126 | Polish Bioinformatics Society (PTBI) | `zarjad@ptbi.org.pl` | SENT |
| 127 | Quirogris | `quirogris@gmail.com` | **HARD BOUNCE** |
| 128 | Mythic Tattoo Studio | `mythictattooestudio.16@gmail.com` | SENT |
| 129 | Adara Rituals de Bellesa | `adararituals@gmail.com` | SENT |
| 130 | Ech2Onet | `ech2onet@gmail.com` | SENT |
| 131 | Madhaus Tattoo | `madhaustattoo@gmail.com` | SENT |
| 132 | Nova 12 | `paubess@yahoo.com.ar` | **HARD BOUNCE** |
| 133 | Estètica Integral Vng | `esteticaintegralvng@gmail.com` | SENT |
| 134 | Brush Estilistes Cubelles | `loreabella2014@gmail.com` | **HARD BOUNCE** |
| 135 | MarkeThink | `info@correo.cat` | **NEGATIVE REPLY / CLOSED** |
| 136 | Rudz Tech | `rudra@rudztech.com` | SENT + CV |
| 137 | Nexìbo | `collab@nexibo.agency` | SENT + CV |
| 138 | Azuanet | `cv@azuanet.com` | SENT + CV |
| 139 | Veintemillas | `jobs@veintemillas.com` | SENT + CV |
| 140 | CareTalyst | `info@caretalyst.com` | SENT + CV |

CareTalyst requested rate information; no numeric rate was invented. The application states that a precise quotation can be supplied once scope, workflow and turnaround are known.

---

## 🏪 Local SME 999

The backlog-finalized cohort is now fully executed under the exact-one-proactive-first-contact rule.

| Metric | Value |
|---|---:|
| Canonical records | **30** |
| Finalized rejected | **22** |
| Qualified | **8** |
| Ready to contact | **0** |
| Contacted / Sent verified | **8** |
| Hard bounces | **3** |
| Delivered or no bounce observed | **5** |
| Replies | **0** |
| Wins | **0** |

Hard-bounced addresses are suppressed and will never be blindly retried. A replacement route would require new authoritative evidence and organization-level continuation review.

➡️ [Local SME master](local-no-website/master-index.json) · [€999 offer](local-no-website/config/offer-999.json) · [Tax policy](local-no-website/config/tax-policy.json)

---

## ⛔ Final-gate blocks / review queue

Current priority queue contains only authoritative **form/platform** routes; SO Design Online has been removed after verified contact.

- **Sapres Technologies GmbH** — HOT+; Freelancermap application route; must confirm willingness for stated 5% Frankfurt onsite and rate requirements before submission.
- **Cayenne Global LLC** — HOT; Upwork-only route; 50+ proposals and strong B2B-tech example requirement materially affect conversion probability.
- **Ajax Creative** — HOT; official Freelancer Application route; generic email substitution forbidden.
- **Global Service Impresa** — cross-border Spain eligibility not established (`Remoto tutta Italia`).
- **Group easyweb** — French SIRET requirement blocks Spain-based autónomo unless eligibility changes.
- **LIVEAT / Adviva** — current freelance/external signals but cross-border eligibility insufficiently explicit.
- **Diwar Marketing** — strong fit but current demand freshness needs newer confirmation.
- **CodeQuadrat** — current Remote-Europe WordPress freelance role, but exact authoritative email recipient remains unresolved.

➡️ [Current Fast Revenue Queue](views/fast-revenue-queue.json) · [Fast revenue email queue](views/fast-revenue-email-queue.json) · [Direct route matrix](views/direct-contact-route-matrix.json)

---

## 🇪🇺 EU Projects

EU opportunities remain governed by the project → WP/task → responsible beneficiary → verified buyer/contact route chain. Inferred digital need is never enough for outreach.

### BEYOND BARRIERS — WAITING FOR INBOUND

The explicit user decision remains authoritative: `WAITING_FOR_INBOUND` · no follow-up · no solicitation · reopen only on a genuinely new inbound event or a new explicit user decision.

[Opportunity](opportunities/OPP-EU-BEYOND-BARRIERS-WEB.json) · [EU watchlist](eu-projects/early-funded-watchlist-2026-08-28.json)

---

## 🏛️ Public Procurement — USER MANAGED

Public administrations, municipalities, institutional bodies and regulated procurement remain a separate manual funnel. No automated first-contact outreach or bid submission.

➡️ [Manual Public Procurement Report](reports/MANUAL-PROCUREMENT-OPPORTUNITIES.md) · [Public Procurement Pipeline](views/public-procurement-pipeline.json)

---

## 🛡️ Safety / QA state

- Duplicate FIRST_CONTACT violations on 1 Sep: **0**.
- SO Design Online was verified in Hostinger Sent before CRM state advanced to CONTACTED.
- Gmail Sent and Hostinger Sent were checked at the final gate.
- SO Design Online is now hard-blocked from second FIRST_CONTACT in emergency suppression memory pending primary-registry normalization.
- Aunar Viajes unmatched bounce is REVIEW_REQUIRED; no blind resend.
- Positive/referral/pricing/proposal/call threads remain USER action; no substantive positive response is auto-replied.
- No guessed email, invented rate, invented availability, unsupported budget or false freshness was used.
- Public procurement remains user-managed.
- BEYOND BARRIERS remains passive and untouched.

---

## Top Next Actions

1. **USER:** review the Daniele Debernardis → Fabio Vanacore referral thread before any response or next step.
2. Monitor SO Design Online and remaining non-bounced contacts for replies, CV/portfolio requests, calls or proposals.
3. Reconcile the unmatched Aunar Viajes bounce before associating it with any campaign or prospect.
4. Execute form/platform opportunities only through their authoritative routes after individual final gates.
5. Continue discovery focused on fresh, explicit freelance/contract/white-label/overflow demand with authoritative routes.
6. Continue EU project deepening only where a defensible funded-project → responsible-beneficiary → digital-need route exists.

---

## Canonical operational views

- [Master index](master-index.json)
- [Direct Commercial Pipeline](views/direct-commercial-pipeline.json)
- [Current Fast Revenue Queue](views/fast-revenue-queue.json)
- [Fast Revenue Email Queue](views/fast-revenue-email-queue.json)
- [Public Procurement Pipeline](views/public-procurement-pipeline.json)
- [Next Best Actions](views/next-best-actions.json)
- [Action Queue](views/action-queue.json)
- [Commercial SLA](views/commercial-sla.json)
- [Success Indicators](views/success-indicators.json)
- [Active Opportunities](views/active-freelance-opportunities.json)
- [Local SME 999](local-no-website/master-index.json)

> **Conversion > activity. Evidence > inference. Revenue > vanity metrics.**
