# Chat Map — VDS Job & Client Acquisition

Use one ChatGPT Project with specialized chats. All chats read/write the same canonical GitHub repository and must respect global deduplication.

## 00 — COMMAND CENTER
Purpose: overall status, Next Best Actions, cross-workstream priorities, KPI and final decisions.

Read first:
- root `README.md`;
- `views/next-best-actions.json`;
- active/reply/follow-up views;
- latest QA audit.

## 10 — EU OPPORTUNITY SCANNER
Purpose: discover and qualify funded/recent EU projects.

Primary instructions: `project/workstreams/EU_PROJECTS.md`.

Outputs: `eu-projects/`, `opportunities/OPP-EU-*.json`, research logs and operational views.

## 11 — EU OUTREACH REVIEW
Purpose: final verification, dedup/suppression check and tailored outreach preparation for EU opportunities.

No positive reply may be answered automatically.

## 20 — COLLABORATION SCANNER
Purpose: fresh freelance/P.IVA/autónomo/contract/outsourcing/white-label opportunities.

Primary instructions: `project/workstreams/COLLABORATIONS.md`.

Outputs: company/territory files, opportunity JSON, research logs and coverage views.

## 21 — COLLABORATION OUTREACH REVIEW
Purpose: final review of high-fit unsent opportunities; tailored application/contact; exact sent-state tracking.

Never count prepared drafts as sent.

## 30 — REPLY & FOLLOW-UP WATCH
Purpose: mailbox reconciliation, reply classification, overdue follow-up detection and suppression maintenance.

Priority: positive replies/referrals before new discovery.

## 40 — CRM QA / AUDIT
Purpose: deduplication, source/evidence checks, state consistency, campaign metrics and dashboard reconciliation.

Primary standard: `QA_AUDIT_STANDARD.md`.

## 50 — STRATEGY / EXPERIMENTS
Purpose: improve scoring, targeting, message strategy, portfolio positioning and conversion experiments without contaminating canonical facts.

Any experimental metric/model must be explicitly marked uncalibrated until validated.

## Routing rule
- EU funded project lead → 10/11.
- freelance/job/agency/outsourcing lead → 20/21.
- replies/follow-ups → 30.
- data inconsistencies → 40.
- cross-workstream priority decision → 00.

The user should be able to ask "punto della situazione" in 00 — COMMAND CENTER and receive one unified, repository-backed view of both workstreams.
