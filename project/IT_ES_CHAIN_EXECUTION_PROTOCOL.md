# VDS Acquisition Chain — Adaptive Execution Protocol

Version: 3.1  
Effective: 2026-09-04

## Purpose

Canonical shared contract for the VDS acquisition architecture. The system combines high-frequency GitHub discovery with five specialized ChatGPT Tasks, global organization-level deduplication, adaptive source/territory ranking, controlled outbound execution, high-value human-review recovery and reply/performance monitoring.

## Active architecture

Exactly FIVE VDS acquisition Tasks are expected active:

1. `VDS LinkedIn Job Hunter` — hourly at :00 Europe/Madrid. Job discovery/qualification 24/7; authorized job/application sender only 09:00–19:00 inclusive.
2. `VDS Agency + EU Signal Radar` — hourly at :38. Intelligence/discovery only; NEVER sends first contact or follow-up.
3. `VDS Cross-Signal Ranker` — hourly at :43. Merge/ranking/state only; NEVER sends first contact or follow-up.
4. `VDS Unified Acquisition Loop` — hourly at :48. Commercial/client/agency/EU discovery/qualification 24/7; authorized commercial sender only 09:00–19:00 inclusive.
5. `VDS Performance + Reply Watch` — hourly at :55. Independent watchdog/reply/outcome monitor; NEVER sends acquisition first contacts/follow-ups.

Legacy scheduled senders/miners including `VDS Direct Route Miner`, `VDS High-Yield Job Miner`, `VDS Batch Dispatcher`, `VDS IT/ES Auto Apply`, `VDS Partner Hunt` and equivalent retired senders MUST remain disabled.

In addition, GitHub Actions `VDS High-Frequency Discovery Fanout` runs approximately every 15 minutes and is DISCOVERY/ANALYSIS ONLY. It never sends outreach.

## Mandatory shared protocols

Every active acquisition Task must obey, where relevant:
- `project/GLOBAL_ORGANIZATION_DEDUP_PROTOCOL.md` v1.3+
- `project/MAX_PERFORMANCE_ACQUISITION_PROTOCOL.md` v1.1+
- `project/DAILY_METRICS_PROTOCOL.md` v3.0+
- `project/HUMAN_REVIEW_HIGH_VALUE_PROTOCOL.md` v1.0+

Operational/adaptive inputs include:
- `views/provider-contact-suppression-index.json`
- `views/global-organization-index.json`
- `views/global-sent-email-index.json`
- `governance/global-contact-reservations.json`
- `views/high-frequency-discovery-latest.json`
- `views/high-frequency-discovery-qualified-seeds.json`
- `views/search-source-performance.json`
- `views/territory-yield-radar.json`
- `views/territory-enrichment-queue.json`
- `views/acquisition-performance.json`
- `config/acquisition-runtime-command.json`
- `views/search-mission-plan.json`
- `views/cross-signal-opportunities.json`
- `views/human-review-high-value.json`

Canonical repository: `pinolissimo/vds-commercial-intelligence`, branch `main`.

## Provider and communication ownership

Professional outbound mail is sent ONLY from Hostinger mailbox `info@visualdesignstudio.es`.

`allocca.pino@gmail.com` is notifications/BCC only. Gmail is NOT a professional outbound source and MUST NOT be used for routine professional-email deduplication.

Authorized acquisition senders:
- LinkedIn Job Hunter for job/application lane;
- Unified Acquisition Loop for commercial/client/agency/EU lane.

All other active Tasks are non-senders.

## Sending window

External acquisition `FIRST_CONTACT` and policy-compliant `FOLLOWUP_1` emails are permitted only from 09:00 through 19:00 Europe/Madrid inclusive.

Outside the window all search, verification, enrichment, ranking, READY preparation, dedup and queueing continue normally, but external acquisition email count must remain zero.

## Global identity and dedup invariant

`NO_DUPLICATE_FIRST_CONTACT_GLOBAL`

FIRST_CONTACT is unique by canonical commercial organization/employer identity, not by email, vacancy, person, office, geography, campaign, source or workstream.

Routine dedup is JSON-first using provider suppression, global organization/sent indexes, workstream history and active organization reservations. Hostinger Sent is the provider source of truth and is queried selectively for ambiguity/recovery/UID gaps and post-send verification. A different recipient or new vacancy NEVER resets prior contact history.

## Reservation / concurrency model

Both authorized senders MUST atomically reserve the canonical organization in `governance/global-contact-reservations.json` immediately before provider action. A conflicting active reservation blocks that send.

Unified additionally owns the commercial dispatch lease `governance/it-es-dispatch-lease.json` for its commercial lane. LinkedIn Job Hunter does not use that commercial lease but MUST use the same global organization reservation and dedup layer.

## Discovery and adaptive-search model

Search Spain and Italy continuously and systematically, plus strategically strong EU-remote/language-compatible opportunities.

Default capacity allocation from `MAX_PERFORMANCE_ACQUISITION_PROTOCOL.md`:
- ~70% exploitation of highest-yield resolved territory × source × intent combinations;
- ~20% under-sampled Spain/Italy exploration;
- ~10% strategic reserve for emerging direct demand / EU timing / high-value signals.

Use `views/search-mission-plan.json` as the preferred current high-intent territorial agenda. Consume semantic-pass seeds before raw feed noise. Country-only unresolved buckets are enrichment demand, never HARVEST targets. No-data/tiny-sample territories remain EXPLORATION until a meaningful sample exists.

## Funnel / north star

Optimize:

`DISCOVERED -> SEMANTIC_PASS -> VERIFIED -> HOT -> READY -> FIRST_CONTACT_SENT -> REPLIED -> POSITIVE -> MEETING -> PROPOSAL -> WON`

For strong opportunities that cannot become READY for a SOFT reason, preserve a parallel recovery path:

`VERIFIED_HIGH_VALUE -> SOFT_BLOCKED -> HUMAN_REVIEW_HIGH_VALUE -> OWNER_DECISION -> normal gates if approved`

Raw lead count is not the north-star KPI. Prefer recurring/partner economics and shortest truthful path to paid work.

## Cross-signal rule

All discovery streams must merge by canonical organization identity. Multiple independent fresh signals increase priority/confidence but NEVER bypass dedup, freshness, route, legal/channel or truthful-fit gates.

Provider suppression/history overrides stale `UNCONTACTED` labels. Cross-Signal Ranker must repair conflicting states every run.

## READY certification

A candidate can become executable READY only when all relevant gates are resolved:
1. canonical organization identity;
2. current authoritative demand/need and freshness;
3. truthful VDS fit;
4. geographic/legal/channel compatibility;
5. exact authoritative application/collaboration route;
6. exact authoritative recipient for email route;
7. sender can execute that exact route;
8. global history/suppression indicates no prohibited FIRST_CONTACT collision;
9. no conflicting reservation;
10. required public professional-document link is available where needed;
11. no explicit authoritative blocker.

Unsupported form/platform/Easy Apply/ATS => `MANUAL_ROUTE_REQUIRED` with exact URL/reason/instructions. Never substitute a generic email.

If a candidate is high-value but fails READY only for a SOFT, reviewable reason, evaluate it under `project/HUMAN_REVIEW_HIGH_VALUE_PROTOCOL.md` instead of discarding it.

## VDS fit and positioning

Evaluate truthful fit across WordPress/frontend/web development, WooCommerce, performance/WPO/Core Web Vitals, maintenance, migrations/rebuilds, responsive/mobile-first, UX/UI implementation, integrations, hosting/domain/DNS, IT systems/support, cybersecurity awareness, IoT/maker and technical troubleshooting where genuinely relevant.

VDS Engine is described only at benefit level: performance, quality, versatility, maintainability and pragmatic implementation. Never disclose proprietary internals or fabricate capabilities/seniority/certifications/rates/availability.

## Dispatch floor

Within the allowed sending window there is NO fixed minimum batch threshold:
- executable READY = 0 -> send none;
- executable READY >= 1 -> authorized sender should execute all currently valid identities for its lane in that run, subject to provider/reservation/route gates.

No valid READY item may remain parked merely because the batch is small.

## Email execution

One-to-one via Hostinger from `info@visualdesignstudio.es`. BCC `allocca.pino@gmail.com` where supported. Use the recipient's natural professional language. Messages must be concise, opportunity-specific and truthful.

Mandatory signature:

Giuseppe Allocca  
Visual Design Studio  
Web Developer · VDS Engine  
https://www.visualdesignstudio.es/  
info@visualdesignstudio.es  
+34 646 457 747

Add one compact language-matched privacy/confidentiality line; proactive commercial outreach includes a simple opt-out.

## Sent verification and commit

No `VERIFIED_EMAIL_SENT` state without official Hostinger Sent evidence.

After each provider action, verify recipient, subject, provider UID and relevant document/signature policy. Then, before moving to the next organization:
1. persist global sent ledger/index event with action type;
2. update global organization state while preserving original first-contact timestamp;
3. update provider suppression index;
4. update originating workstream ledger/index;
5. remove/update READY state;
6. increment the correct daily counter exactly once;
7. release organization reservation.

Provider ambiguity => `DELIVERY_STATE_UNKNOWN`; never blind resend.

## Follow-up

At most one automatic `FOLLOWUP_1` may be executed, only under the strict eligibility contract in `MAX_PERFORMANCE_ACQUISITION_PROTOCOL.md`. It is never a new FIRST_CONTACT and never increments first-contact counters. Rejection, bounce, opt-out, reply, owner stop or prior FOLLOWUP_1 blocks it.

## Manual-action and high-value review preservation

A strong opportunity that automation cannot complete must never be silently discarded.

Two distinct preservation paths apply:

1. `MANUAL_ROUTE_REQUIRED` — exact form/ATS/platform route is known but automation cannot execute it. Persist exact URL, reason, fit/freshness and owner next step.
2. `HUMAN_REVIEW_HIGH_VALUE` — opportunity is commercially strong but SOFT-BLOCKED and may justify owner reasoning about a legitimate alternative route or positioning. Persist it in `views/human-review-high-value.json` and surface it in `reports/human-review-high-value.md` according to `project/HUMAN_REVIEW_HIGH_VALUE_PROTOCOL.md`.

Typical recoverable review classes include internal hiring that may support a B2B overflow angle, reciprocal white-label/partner fit, route ambiguity, contradictory but promising evidence, recurring historical freelancer usage, decision-maker review and cross-border contracting questions.

HARD exclusions must never be converted into a workaround: explicit no-freelance/no-agency/no-external-collaborator language, opt-out/DO_NOT_CONTACT, legal prohibitions, unresolved identity, guessed-only contacts and duplicate first contacts remain blocked.

Workers should perform a retroactive recovery pass over recent `REJECTED`, `HOLD`, `MANUAL_ROUTE_REQUIRED`, `REVIEW_REQUIRED`, `ROUTE_UNRESOLVED`, `CONTRACT_MODEL_UNCLEAR` and equivalent states, promoting only qualifying SOFT-BLOCKED high-value opportunities.

No item in `HUMAN_REVIEW_HIGH_VALUE` may be automatically sent merely because it is in that queue. Owner review is required before it can re-enter normal READY/pre-send gates.

## Watchdog contract

Watchdog validates:
- all five expected Tasks active and legacy senders disabled;
- GitHub 15-minute fanout freshness/success;
- semantic and adaptive outputs current;
- provider UID continuity / global index reconciliation;
- zero duplicate first contacts;
- sending-window compliance;
- reservation/lease health;
- READY items not stranded without blockers;
- high-value SOFT-BLOCKED items preserved in the human-review queue rather than silently lost;
- owner is surfaced only NEW/materially changed `HUMAN_REVIEW_HIGH_VALUE` items, without duplicate alerts;
- source × territory × segment funnel yield;
- positive replies, meetings/proposals/wins and bounces;
- follow-up compliance;
- daily metrics completeness.

Watchdog may safely repair deterministic state/schedule/adaptive drift but NEVER send acquisition FIRST_CONTACT/FOLLOWUP_1 or clear historical contact memory.

## Hard invariants

1. Zero duplicate FIRST_CONTACT globally.
2. Only LinkedIn Job Hunter and Unified Acquisition Loop may send acquisition email, each only in its defined lane/window.
3. Gmail is notifications/BCC only.
4. Hostinger Sent is provider delivery evidence.
5. Global organization reservation before every acquisition send.
6. No route substitution.
7. No SENT state without provider verification.
8. No blind resend after ambiguous provider result.
9. Manual-route opportunities are preserved and surfaced.
10. High-value SOFT-BLOCKED opportunities are preserved for owner review; hard prohibitions are never bypassed.
11. Daily counters are incremental/idempotent and routine statistics require no historical mailbox rescan.
12. Adaptive optimization may reallocate search effort but never weaken safety or factual qualification gates.
13. Performance is judged primarily by qualified conversations / positive outcomes, not raw volume.
