# VDS Commercial Intelligence — Revenue Command Center

> **Single source of truth:** `pinolissimo/vds-commercial-intelligence` · `main`  
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **VDS7:** precisione > volume · evidenza > inferenza · duplicate FIRST_CONTACT tolerance = **0**

**Snapshot:** 1 settembre 2026 · 10:08 Europe/Madrid  
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
| Tuesday bounce/reconciliation events | **2** |
| Local SME 999 canonical records | **31** |
| Local SME 999 contacted / Sent verified | **8 / 8** |
| Local SME hard bounces | **4** |
| Meetings | **0** |
| Proposals | **0** |
| Revenue won | **€0** |

The numerical Monday target was **30+**, but only **21** candidates survived every final gate. The shortfall is intentional: no stale, duplicate, guessed, geography-ineligible, price-gated, ambiguous-route or weak-fit candidate was converted into an email merely to reach the target.

➡️ [Monday wave 01](outreach/2026-08-31-partner-hunt-morning-wave-01.json) · [Monday wave 02](outreach/2026-08-31-partner-hunt-morning-wave-02.json) · [Suppression registry](governance/suppression-registry.json)

---

## 🚨 Current commercial events

### Piscina Municipal de Sitges — HARD BOUNCE / PUBLIC-ENTITY BOUNDARY REVIEW

Hostinger INBOX **UID 1283** reports a permanent delivery failure for `info@pmsitges.cat`: **SMTP 550 5.1.1 — User unknown in virtual alias table**. The bounce attachment contains the original authenticated outgoing message, timestamped **1 Sep 2026 · 09:45:57 Europe/Madrid**, subject `Una propuesta digital concreta para Piscina Municipal de Sitges`.

A matching message was **not found in the latest Hostinger Sent delta**, therefore the CRM does **not** claim `SENT_VERIFIED`. The delivery attempt itself is nevertheless proven by the RFC822 payload inside the bounce and permanently consumes first-contact uniqueness: **no blind resend, no second cold first-contact, no alternative-address reset**.

This event also exposed a QA boundary issue: no canonical record existed before the attempt and the identity appears to be a **municipal/public sports facility**. A reconciliation record has now been created, the failed route is emergency-suppressed, and the identity is `REVIEW_REQUIRED_PUBLIC_ENTITY_BOUNDARY`. Automated LOCAL_SME_999 outreach is blocked; any legitimate public-sector route belongs under the user-managed procurement boundary.

➡️ [Reconciliation record](local-no-website/spain/catalonia/barcelona/sitges/municipal-sports-facility/LOCAL-ES-CT-B-SITGES-PISCINA-MUNICIPAL.json) · [Action queue](views/action-queue.json) · [Emergency suppression](governance/suppression-emergency-2026-08-28.json)

### SO Design Online — FIRST_CONTACT SENT / VERIFIED

The live official careers page was reverified on 1 Sep and still lists **WordPress Website Builder — Remote / Contract or project-based**, with the exact application route `support@sodesign.online`. Global repository/suppression, Gmail Sent and Hostinger Sent checks were clear before execution. A personalized application was sent from exactly `info@visualdesignstudio.es` with a role-tailored English PDF CV and portfolio. Official Hostinger `INBOX.Sent` **UID 149** verifies transmission.

**State:** `WAITING_FOR_REPLY`. No second proactive first contact may be generated. Substantive positive/referral/pricing/proposal/call replies require USER action.

➡️ [Opportunity](opportunities/OPP-REMOTE-SO-DESIGN-ONLINE-WORDPRESS-BUILDER-2026.json) · [Verified outreach event](outreach/2026-09-01-so-design-online-first-contact.json)

### Aunar Viajes — UNMATCHED HARD BOUNCE / REVIEW_REQUIRED

Hostinger INBOX **UID 1282** reports delivery failure to `info@aunarviajes.com`: DNS host/domain not found. No matching canonical repository identity and no Hostinger Sent message to that recipient were found during immediate reconciliation. **Do not resend or infer campaign ownership.** Keep as `REVIEW_REQUIRED` until origin is established.

### Daniele Debernardis — POSITIVE REFERRAL

Daniele replied after the first contact and **forwarded the request to his colleague Fabio Vanacore**, who was placed in CC. This is a genuine routed referral. No automated reply and no separate first-contact solicitation to Fabio was generated.

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

The backlog-finalized cohort remains fully executed under the exact-one-proactive-first-contact rule. The additional Piscina Municipal record exists only for **bounce/QA reconciliation** and is not counted as a newly qualified/contacted SME.

| Metric | Value |
|---|---:|
| Canonical records | **31** |
| Under research / boundary review | **1** |
| Finalized rejected | **22** |
| Qualified | **8** |
| Ready to contact | **0** |
| Contacted / Sent verified | **8** |
| Hard bounces | **4** |
| Delivered or no bounce observed | **5** |
| Replies | **0** |
| Wins | **0** |

Hard-bounced addresses are suppressed and will never be blindly retried. A replacement route would require new authoritative evidence and organization-level continuation review. Public/municipal identities are excluded from automated LOCAL_SME_999 solicitation.

➡️ [Local SME master](local-no-website/master-index.json) · [€999 offer](local-no-website/config/offer-999.json) · [Tax policy](local-no-website/config/tax-policy.json)

---

## ⛔ Final-gate blocks / review queue

Current priority queue contains only authoritative **form/platform** routes plus QA reconciliation items; SO Design Online has been removed after verified contact.

- **Piscina Municipal de Sitges** — CRITICAL QA: failed route suppressed; no matching Sent UID; municipal/public-sector boundary review required; no resend.
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

Public administrations, municipalities, institutional bodies and regulated procurement remain a separate manual funnel. No automated first-contact outreach or bid submission. The Piscina Municipal reconciliation is explicitly held at this boundary until identity/procurement status is resolved.

➡️ [Manual Public Procurement Report](reports/MANUAL-PROCUREMENT-OPPORTUNITIES.md) · [Public Procurement Pipeline](views/public-procurement-pipeline.json)

---

## 🛡️ Safety / QA state

- Duplicate FIRST_CONTACT violations on 1 Sep: **0**.
- SO Design Online was verified in Hostinger Sent before CRM state advanced to CONTACTED.
- Piscina Municipal de Sitges bounce is proven by INBOX UID 1283, but **SENT is not claimed** because a matching Hostinger Sent UID was not verified.
- `info@pmsitges.cat` is blocked in emergency suppression; first-contact uniqueness is not reset by finding another address.
- Piscina Municipal is `REVIEW_REQUIRED_PUBLIC_ENTITY_BOUNDARY`; no automated LOCAL_SME resend or public-sector solicitation is permitted.
- Aunar Viajes unmatched bounce remains REVIEW_REQUIRED; no blind resend.
- Positive/referral/pricing/proposal/call threads remain USER action; no substantive positive response is auto-replied.
- No guessed email, invented rate, invented availability, unsupported budget or false freshness was used.
- Public procurement remains user-managed.
- BEYOND BARRIERS remains passive and untouched.

---

## Top Next Actions

1. **QA:** reconcile Piscina Municipal de Sitges as a municipal/public identity; keep the failed route suppressed and do not resend.
2. Monitor SO Design Online and remaining non-bounced contacts for replies, CV/portfolio requests, calls or proposals.
3. Reconcile the unmatched Aunar Viajes bounce before associating it with any campaign or prospect.
4. Keep the Daniele Debernardis → Fabio Vanacore referral as a routed continuation; no new first-contact path.
5. Execute form/platform opportunities only through their authoritative routes after individual final gates.
6. Continue discovery focused on fresh, explicit freelance/contract/white-label/overflow demand with authoritative routes.
7. Continue EU project deepening only where a defensible funded-project → responsible-beneficiary → digital-need route exists.

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
- [Job Source Intelligence](job-intel/README.md)
- [Public Procurement Intelligence](public-procurement/README.md)
- [Growth Intelligence](growth-intelligence/README.md)

> **Conversion > activity. Evidence > inference. Revenue > vanity metrics.**
