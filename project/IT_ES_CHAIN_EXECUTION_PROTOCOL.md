# VDS Unified Acquisition Loop — Transactional Execution Protocol

Version: 2.0  
Effective: 2026-09-04

## Purpose

Mandatory shared contract for the scheduled VDS acquisition engine. The former four-stage scheduled chain is consolidated into one stateful sequential task to reduce task-slot usage and discovery-to-send latency while preserving all safety, deduplication, route, delivery-verification and audit invariants.

## Active architecture

Exactly TWO scheduled tasks are active for this subsystem:

1. `VDS Unified Acquisition Loop` — hourly operational engine and SOLE scheduled first-contact sender.
2. `VDS Performance + Reply Watch` — independent watchdog/reply monitor; NEVER sends first-contact outreach.

The former scheduled `VDS Direct Route Miner`, `VDS High-Yield Job Miner` and `VDS Batch Dispatcher` are retired/disabled. No other scheduled task may execute VDS first-contact outreach.

## Unified sequential state machine

Every Unified Loop run executes, in order:

`PRECHECK -> DISCOVERY -> CHEAP_FILTER -> ROUTE_CLOSURE -> FINAL_QUALIFICATION -> READY_CERTIFICATION -> ACQUIRE_DISPATCH_LEASE -> JIT_DEDUP -> DISPATCH_ALL_EXECUTABLE -> VERIFY_SENT -> COMMIT_AFTER_EACH_SEND -> DAILY_METRICS -> RELEASE_LEASE -> RUN_AUDIT`

A run may reuse fresh canonical evidence from prior runs and must not redo expensive stable checks without a freshness/conflict reason.

If a phase cannot complete for one candidate, record an explicit state/reason and continue with independent candidates where safe. Never discard a good opportunity merely because manual action is required: record `MANUAL_ROUTE_REQUIRED` with the exact route and operational information for owner notification.

## Canonical state

Repository: `pinolissimo/vds-commercial-intelligence`, branch `main`.

Required shared files include:
- `views/it-es-partner-apply-ready-queue.json`
- `views/it-es-partner-apply-recipients.json`
- `data/it-es-partner-apply-ledger.jsonl`
- `reports/it-es-partner-apply-cumulative.md`
- `reports/it-es-batch-dispatcher-runs.jsonl`
- `governance/it-es-dispatch-lease.json`
- `assets/cv/document-qa-manifest.json`
- `project/DAILY_METRICS_PROTOCOL.md`

Public professional-document manifest:
- repository `pinolissimo/Portfolio`, branch `main`
- `documents/public-document-manifest.json`

GitHub state is necessary but not sufficient for first-contact deduplication. Before READY certification use current indexed history plus fresh mailbox evidence as required; immediately before EACH send repeat organization-level JIT dedup against GitHub + Hostinger Sent + Gmail Sent.

## Canonical identity invariant

FIRST_CONTACT is unique by commercial organization identity, not by email, vacancy, office, source, geography, campaign or workstream. A different recipient or listing NEVER resets prior-contact history.

## Execution states

`DISCOVERED -> QUALIFYING -> VERIFIED_NON_EXECUTABLE | READY_TO_APPLY -> DISPATCH_RECHECK -> VERIFIED_EMAIL_SENT | VERIFIED_SUBMISSION | DELIVERY_STATE_UNKNOWN | BLOCKED_FINAL_GATE | RETRY_REQUIRED`

Explicit non-executable/retry reasons include:
- `MANUAL_ROUTE_REQUIRED`
- `ALREADY_CONTACTED`
- `REVIEW_REQUIRED`
- `HOLD_STALE`
- `LEGAL_GEOGRAPHIC_BLOCK`
- `ROUTE_UNRESOLVED`
- `DOCUMENT_PUBLIC_LINK_UNAVAILABLE`
- `LEGAL_CHANNEL_BLOCKER`
- `DELIVERY_STATE_UNKNOWN`

## Discovery and throughput policy

Search Spain and Italy as Tier 1 in parallel where possible, plus EU language-compatible opportunities where authoritative evidence shows Italian/Spanish relevance or EU-remote compatibility. Prioritize explicit current paid demand, direct authoritative routes, WordPress/frontend/performance/maintenance/agency-overflow fit, recurring potential and fastest plausible path to paid work.

Use cheap-first triage. Maximize unique plausible organizations without deep-checking obvious rejects. Reuse fresh route/identity evidence. Deep-check only candidates likely to become executable READY. Optimize throughput without lowering qualification thresholds.

## VDS fit policy

Evaluate truthful fit across WordPress/frontend/web development, performance/WPO, maintenance, UX/UI implementation, integrations, IT systems/support, cybersecurity awareness, IoT/maker and technical troubleshooting where relevant.

VDS Engine may be used as benefit-level evidence of performance-oriented, versatile, maintainable and quality-focused delivery, verifiable from `https://www.visualdesignstudio.es/` and where useful `https://www.visualdesignstudio.es/vds-demo/#top`. Never disclose proprietary internals or fabricate capabilities, seniority or certifications.

Official LinkedIn supporting evidence when useful: `https://www.linkedin.com/in/giuseppe-allocca-itechnician/`.

## READY certification

A candidate may enter `READY_TO_APPLY` only when all mandatory gates are resolved:
1. canonical organization identity;
2. current need/freshness from authoritative evidence;
3. truthful VDS fit;
4. no explicit authoritative exclusion of freelancers/contractors/external collaborators;
5. exact official execution route;
6. Unified Loop can execute that exact route;
7. exact authoritative recipient for email routes;
8. unsupported form/platform routes become `MANUAL_ROUTE_REQUIRED`;
9. organization-level dedup across canonical state and available Sent evidence;
10. no active reservation/contact collision;
11. document requirement known and verified public link available when required/beneficial;
12. legal/channel/geographic state resolved.

Unknown mandatory gate => not READY.

## Contract-model policy

Full-time, permanent/indefinite, salary, benefits, ordinary employee wording, hybrid/on-site wording, location reference, or absence of freelance terminology do NOT by themselves block an external freelance/autónomo proposal.

Block contract model only on explicit authoritative equivalents of: no freelancers, no contractors, employees only, no external collaborators. This never overrides genuine legal, geographic, route, stale, licensing/certification or dedup blockers.

## Dispatch transaction and sole-writer rule

Only `VDS Unified Acquisition Loop` may acquire the live dispatch lease or execute first-contact sends.

Dispatch order:

`ACQUIRE_LEASE -> READ_LATEST_QUEUE -> SANITIZE -> FINAL_DEDUP -> ROUTE_RECHECK -> FRESHNESS_RECHECK -> DOCUMENT_LINK_RECHECK -> EXECUTABLE_READY_COUNT -> DISPATCH_ALL_EXECUTABLE -> VERIFY_SENT -> COMMIT_AFTER_EACH_SEND -> RELEASE_LEASE`

Before queue or contacted-state writes, refetch latest canonical state, merge rather than overwrite, and verify the resulting identity exactly once.

## Dispatch floor — HARD OWNER POLICY

There is NO fixed minimum batch threshold.

- `EXECUTABLE_READY_COUNT = 0` -> no send.
- `EXECUTABLE_READY_COUNT >= 1` -> dispatch every currently valid executable identity in the same run.

No valid executable READY item may remain parked merely because the batch is small.

## Delivery-completion invariant

A genuinely executable READY identity must not remain unsent because of a safely resolvable technical/process problem.

For resolvable dependency failures:
1. identify exact cause;
2. repair deterministic canonical state;
3. re-read affected dependencies;
4. rerun JIT dedup and route/freshness gates;
5. continue in the SAME run when safe;
6. otherwise record `RETRY_REQUIRED:<exact reason>` for the next Unified Loop run.

Never bypass dedup, route authority, legal/geographic blockers, explicit no-freelance exclusions, lease ownership or provider-state ambiguity.

## Public document delivery — LINK ONLY

Automatic professional applications use verified public GitHub document links only. Automatic email attachments must be empty.

Canonical approved CVs:
- ES: `https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_CV_Generico_ES.pdf`
- IT: `https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_CV_Generico_IT.pdf`
- EN: `https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_Master_CV_EN.pdf`

Correct language mapping is required. Broken/missing public URL is a repairable dependency failure. Legacy attachment/Base64 bridges are deprecated. Google Drive is forbidden without explicit owner permission.

## Route integrity

Use the exact authoritative application/collaboration route. A form/platform-only opportunity may never be converted to generic email merely because another company email exists. Unsupported route => `MANUAL_ROUTE_REQUIRED` and preserve/notify rather than discard.

## Email policy

Send one-to-one from `info@visualdesignstudio.es` via Hostinger. BCC `allocca.pino@gmail.com` where supported. Use the natural professional language supported by the opportunity. Messages must be concise, opportunity-specific and truthful.

Mandatory text signature:

Giuseppe Allocca  
Visual Design Studio  
Web Developer · VDS Engine  
https://www.visualdesignstudio.es/  
info@visualdesignstudio.es  
+34 646 457 747

After the signature add one short language-matched privacy/confidentiality line; commercial outreach includes a simple opt-out. Do not add long boilerplate.

## Sent verification

After every provider action, confirm official Hostinger Sent evidence BEFORE recording `VERIFIED_EMAIL_SENT`.

Required verification:
- recipient;
- subject;
- provider UID;
- attachments array empty;
- required text signature/privacy footer.

Provider ambiguity => `DELIVERY_STATE_UNKNOWN`; never blind retry.

## Per-send commit

After each verified send and before the next identity:
1. update recipient index;
2. append/persist ledger event;
3. remove identity from READY;
4. record provider UID/evidence;
5. increment the current daily automatic-send counter exactly once.

## Daily metrics — mandatory

The Unified Loop and Watchdog MUST read and obey `project/DAILY_METRICS_PROTOCOL.md` every run.

Daily boundaries use `Europe/Madrid`. The Unified Loop owns operational counters; the Watchdog owns aggregate summary/outcomes. Updates are incremental and idempotent by `counted_run_ids`.

Fast statistics must read the small daily JSON files first; mailbox/history rescans are audit fallback only when missing/inconsistent.

## Observability

Every Unified Loop run must leave durable run evidence, including zero-send runs. Continue using `reports/it-es-batch-dispatcher-runs.jsonl` where feasible for backward-compatible dispatch observability; connector limitations may use durable per-run files under `data/it-es-partner-apply-ledger-pending/`.

Minimum run evidence:
- run_id/times/mode;
- discovery/qualification counts;
- raw/sanitized/executable READY counts;
- repairs attempted/completed;
- removed/demoted identities;
- attempted/verified sends;
- delivery-state unknown/retry-required;
- remaining READY;
- dependency failures;
- provider UIDs;
- document links used;
- attachment-empty verification;
- daily metrics update;
- final result.

## Watchdog contract

The independent Watchdog flags:
- expected Unified Loop cycle missing;
- executable READY surviving a completed Unified Loop without hard blocker;
- `RETRY_REQUIRED` surviving more than one safe cycle;
- stale/duplicate identities surviving READY;
- Sent message not reconciled to canonical state;
- READY promotion without full certification;
- attachment-policy regression;
- stale/ambiguous lease;
- any concurrent/legacy sender becoming active;
- missing/stale daily metrics;
- mismatch between provider-verified sends and daily counter;
- positive/referral/proposal/budget/call replies;
- hard bounces.

The Watchdog may repair safe scheduling/state drift but NEVER sends first-contact outreach or clears dedup/contact history.

## Hard invariants

1. Zero duplicate first contact.
2. Unified Loop is the sole scheduled first-contact sender.
3. Only certified executable candidates enter READY.
4. Floor 1: any executable READY count >=1 is dispatchable in the same run.
5. No route substitution.
6. Every operational run is auditable.
7. No SENT state without provider evidence.
8. Automatic application attachments are forbidden; verified public links only.
9. No blind retry after ambiguous provider response.
10. Safely resolvable technical faults must not strand valid READY work.
11. Daily counters are incremental, idempotent and queryable without historical mailbox scans.
12. Manual-route opportunities are preserved and surfaced, never silently discarded.
