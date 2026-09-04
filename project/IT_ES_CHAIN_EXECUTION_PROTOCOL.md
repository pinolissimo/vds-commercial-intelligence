# VDS IT/ES Acquisition Chain — Transactional Execution Protocol

Version: 1.4  
Effective: 2026-09-04

## Purpose

Mandatory shared contract for the scheduled VDS IT/ES acquisition chain. It prevents false READY states, duplicate first contact, route substitution, silent stranded work and inconsistent state between discovery workers and execution.

## Scheduled chain

Current canonical cycle:
1. `:20` — Performance + Reply Watch / watchdog
2. `:25` — Search Fanout
3. `:35` — Direct Route Miner
4. `:45` — High-Yield Job Miner
5. `:55` — Batch Dispatcher

Discovery workers NEVER send or submit. Batch Dispatcher is the only scheduled first-contact sender.

## Canonical state

Repository: `pinolissimo/vds-commercial-intelligence`, branch `main`.

Required shared files:
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

GitHub state is necessary but not sufficient for deduplication. Before READY promotion and again immediately before dispatch, reconcile current mailbox Sent evidence when available.

## Canonical identity invariant

FIRST_CONTACT is unique by commercial organization identity, not by email, vacancy, office, source, geography, campaign or workstream.

A different recipient or listing NEVER resets prior-contact history.

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

## READY certification

A producer may write `READY_TO_APPLY` only when all mandatory gates are resolved:
1. canonical organization identity;
2. current need/freshness from authoritative evidence;
3. truthful VDS fit;
4. no explicit authoritative exclusion of freelance/contractors/external collaborators;
5. exact official execution route;
6. dispatcher can execute that exact route;
7. exact authoritative recipient for email routes;
8. unsupported form/platform routes become `MANUAL_ROUTE_REQUIRED`;
9. global organization-level dedup across GitHub state and available Hostinger/Gmail Sent;
10. no active reservation/contact collision;
11. document requirement known and corresponding verified public link available when required/beneficial;
12. legal/channel/geographic state resolved.

Unknown mandatory gate => not READY.

## Contract-model policy

The following do NOT by themselves block an external freelance/autónomo proposal:
- full-time;
- permanent/indefinite;
- salary;
- benefits;
- ordinary employee terminology;
- hybrid/on-site wording;
- location reference;
- absence of `freelance`, `contractor`, `autónomo` or `P.IVA`.

On contract model, block only explicit authoritative statements equivalent to:
- no freelancers;
- no contractors;
- employees only;
- no external collaborators.

This never overrides genuine legal, geographic, route, stale, licensing/certification or dedup blockers.

## Producer write discipline

Before queue write:
1. fetch latest queue;
2. reconcile index/ledger and fresh Sent evidence;
3. reject duplicate canonical identity;
4. preserve unrelated concurrent entries;
5. write once;
6. re-read queue and verify identity appears exactly once;
7. record promotion/non-promotion evidence.

Never write using a stale queue snapshot.

## Dispatcher transaction

Order:

`ACQUIRE_LEASE -> READ_LATEST_QUEUE -> SANITIZE -> FINAL_DEDUP -> ROUTE_RECHECK -> FRESHNESS_RECHECK -> DOCUMENT_LINK_RECHECK -> EXECUTABLE_READY_COUNT -> DISPATCH_ALL_EXECUTABLE -> VERIFY_SENT -> COMMIT_AFTER_EACH_SEND -> RELEASE_LEASE`

## Dispatch floor — HARD OWNER POLICY

There is NO fixed minimum batch threshold.

- `EXECUTABLE_READY_COUNT = 0` -> no send.
- `EXECUTABLE_READY_COUNT >= 1` -> dispatch every currently valid executable identity.

No valid executable READY item may be left parked merely because the queue is small.

## Delivery-completion invariant

A genuinely executable READY identity must not remain unsent because of a safely resolvable technical/process problem.

For resolvable dependency failures:
1. identify exact cause;
2. repair deterministic canonical state;
3. re-read affected dependencies;
4. rerun JIT dedup and route/freshness gates;
5. continue in the same run when safe;
6. otherwise record `RETRY_REQUIRED:<exact reason>` and retry on the next safe dispatcher cycle.

Never silently accumulate executable READY work.

This invariant NEVER permits bypassing dedup, route authority, legal/geographic blockers, explicit no-freelance exclusions, lease ownership or provider-state ambiguity.

## Public document delivery — LINK ONLY

Automatic professional applications use verified public GitHub document links only.

Canonical mapping is defined in `assets/cv/document-qa-manifest.json` and `pinolissimo/Portfolio/documents/public-document-manifest.json`.

Current approved public CVs:
- ES: `https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_CV_Generico_ES.pdf`
- IT: `https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_CV_Generico_IT.pdf`
- EN: `https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_Master_CV_EN.pdf`

Rules:
- automatic email attachments must be empty;
- correct language mapping required;
- link must be verified current before send when required/beneficial;
- broken/missing link is a repairable dependency failure, not a permanent discard;
- legacy Base64/PDF attachment bridges are deprecated for automatic delivery;
- Google Drive is forbidden without explicit owner permission.

## Mandatory sanitization

Any stale, duplicate or non-executable identity found by Dispatcher is immediately removed/demoted from READY with exact reason. It must not remain falsely READY for another cycle.

## No route substitution

A form/platform-only opportunity may never be converted to generic email merely because another company email exists.

## Sent verification

After every email provider action, confirm official Hostinger Sent evidence before recording `VERIFIED_EMAIL_SENT`.

Required verification:
- recipient;
- subject;
- provider UID;
- attachments array empty under LINK-ONLY policy.

Provider ambiguity -> `DELIVERY_STATE_UNKNOWN`; never blind retry.

## Per-send commit

After each verified send and before the next identity:
1. update recipient index;
2. append ledger event;
3. remove identity from READY;
4. record provider UID/evidence.

## Daily metrics — mandatory

All workers MUST read and obey `project/DAILY_METRICS_PROTOCOL.md` on every run.

Daily boundaries use `Europe/Madrid` calendar time. Each worker writes only its own file under `metrics/daily/` to prevent concurrent-writer collisions.

The Batch Dispatcher MUST update `metrics/daily/YYYY-MM-DD-dispatcher.json` in the SAME run after every provider-verified first-contact send. The daily send count is therefore authoritative without rescanning Hostinger/Gmail. Internal alerts, tests, owner reports, replies and manual/interactively executed messages never increment the automatic first-contact counter.

Every daily update is idempotent through `counted_run_ids`; the same run must never increment counters twice.

Fast query rule:
- `quante email oggi?` -> read today's dispatcher daily file;
- `quante opportunità oggi?` -> read today's Search Fanout daily file;
- pipeline/day statistics -> read today's summary file;
- 7/30/90-day statistics -> aggregate the relevant daily files;
- mailbox/history rescans are fallback audit only when a daily counter is missing or inconsistent.

## Observability

Every Dispatcher run appends to `reports/it-es-batch-dispatcher-runs.jsonl`, including zero-send runs.

Minimum fields:
- `run_id`
- times
- `mode`
- raw/sanitized/executable READY counts
- repairs attempted/completed
- removed/demoted identities
- attempted
- verified email sent
- verified submission
- delivery-state unknown
- retry-required identities
- remaining READY
- dependency failures
- provider UIDs
- document links used
- attachment-empty verification
- result

## Watchdog contract

Watchdog flags:
- expected worker/dispatcher cycle missing;
- executable READY surviving a dispatcher cycle without hard blocker;
- `RETRY_REQUIRED` surviving more than one safe dispatcher cycle;
- stale/duplicate identities surviving READY;
- Sent message not reconciled to canonical state;
- producer promotion without full READY certification;
- attachment-policy regression;
- stale/ambiguous lease;
- concurrent sender;
- missing/stale daily metrics file for an active worker;
- mismatch between provider-verified dispatcher sends and daily dispatcher counter.

## Hard invariants

1. Zero duplicate first contact.
2. Discovery tasks never send.
3. Only certified executable candidates enter READY.
4. Floor 1: any executable READY count >=1 is dispatchable.
5. No route substitution.
6. Every dispatcher cycle is auditable.
7. No SENT state without provider evidence.
8. Automatic application attachments are forbidden; verified public links only.
9. No blind retry after ambiguous provider response.
10. Safely resolvable technical faults must not strand valid READY work.
11. Daily counters are incremental, idempotent and queryable without historical mailbox scans.
