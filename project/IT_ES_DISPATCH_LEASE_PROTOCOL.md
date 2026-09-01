# VDS IT/ES Dispatch Lease Protocol

Version: 1.0
Effective: 2026-09-01
Status: MANDATORY for every LIVE external communication executor.

## Why this exists
During the owner-triggered first live batch on 2026-09-01 two executors overlapped. Nine unique organizations were successfully contacted, but AMO Marketing and BP Nexus each received one additional concurrent duplicate message (Hostinger UIDs 169 and 172). Prompt-level `never send` instructions and identity reservations alone are not sufficient protection against a live concurrency race.

## Single-writer invariant
At any instant there may be exactly ONE LIVE dispatcher/executor capable of sending or submitting first-contact actions.

Canonical lock file:
`governance/it-es-dispatch-lease.json`

Before ANY external email/form/platform action, a LIVE executor MUST:
1. fetch the latest lease file and its GitHub blob SHA;
2. require `state=IDLE`, or a demonstrably expired stale lease that has first been reconciled against Sent/platform evidence;
3. atomically update the same file, using the fetched SHA, to `state=ACTIVE` with a unique `lease_id`, `owner`, `run_id`, `acquired_at`, and an expiry no longer than 15 minutes;
4. treat a GitHub 409/conflict as `LEASE_ACQUIRE_FAILED` and abort the entire external-action run with ZERO sends;
5. re-fetch the lease and verify its own `lease_id` before the first send.

No successful lease acquisition = no external communication.

## Per-identity just-in-time gate
Holding the global lease does not replace dedup. Immediately before EACH individual send/submission, while the lease is still owned, the executor must re-read:
- canonical recipient/identity index;
- relevant append-only ledger state;
- latest Hostinger Sent and, where relevant, Gmail Sent/platform evidence.

If new first-contact evidence for that organization exists, skip it as `ALREADY_CONTACTED_RACE_CAUGHT` and never send.

This check occurs after personalization/document QA and immediately before the irreversible provider call.

## Transaction order
`ACQUIRE_GLOBAL_LEASE -> READ_LATEST_QUEUE -> SANITIZE -> FINAL_DEDUP -> ROUTE/FRESHNESS/DOCUMENT_QA -> THRESHOLD -> for each identity: JIT_SENT_RECHECK -> SEND/SUBMIT -> VERIFY_PROVIDER_EVIDENCE -> COMMIT_LEDGER/INDEX/QUEUE -> next identity -> RELEASE_LEASE`

State must be committed after EACH verified send, not only at the end of the batch. This prevents another process from seeing a stale READY identity if the run is interrupted.

## Lease release
On normal completion, update the lease atomically to `IDLE` and record `last_released_at` and `last_run_id`.

On failure after acquisition, reconcile all provider evidence first, commit known outcomes, then release. If outcome is ambiguous, leave a short-lived `RECOVERY_REQUIRED` lease state and prohibit all new sends until reconciled.

## Stale lease recovery
A lease older than its `expires_at` is NOT automatically safe to overwrite. A recovering executor must first inspect Hostinger Sent/platform evidence for actions after `acquired_at`, reconcile them to the ledger/index/queue, then use an atomic SHA update to claim a new recovery lease. Blind takeover is forbidden.

## Discovery workers
Search Fanout, Direct Route Miner and High-Yield Job Miner are READ/RESEARCH/WRITE-STATE workers only. They must NEVER invoke Hostinger/Gmail send, form-submit, DM, application-submit or any equivalent external-action write tool. They never acquire the dispatch lease.

## Operator-triggered immediate live runs
Before an interactive immediate batch:
1. disable the scheduled Batch Dispatcher first;
2. acquire the same canonical global lease;
3. execute the transactional batch;
4. reconcile and release the lease;
5. only then re-enable the scheduled Batch Dispatcher.

Historical dedup/contact memory is never reset. A “first-use reset” resets only run/epoch counters.

## Monitoring
Performance + Reply Watch must flag as CRITICAL:
- more than one outbound first-contact to the same canonical identity;
- Sent activity while no valid ACTIVE lease exists;
- a second executor attempting to acquire an active lease;
- stale/recovery-required lease;
- a verified send that was not committed to index/ledger/queue before the next identity.

## Hard rule
The lease is a stronger invariant than throughput or batch threshold. If the lease mechanism cannot be read and atomically updated, LIVE sending is blocked.
