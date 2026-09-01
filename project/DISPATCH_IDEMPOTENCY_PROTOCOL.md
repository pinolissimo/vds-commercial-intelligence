# VDS Dispatcher Idempotency Protocol

Version: 1.0
Effective: 2026-09-01

This protocol is mandatory for every scheduled, interactive or recovery execution of the IT/ES dispatcher. It supplements `project/IT_ES_CHAIN_EXECUTION_PROTOCOL.md` and exists to prevent overlapping executors from sending the same first contact.

## Hard invariant
At most ONE live dispatcher executor may own a batch at any instant. A user-triggered immediate run, a scheduled :45 run, a recovery run and any other execution surface are the same logical dispatcher and MUST share the same lease and identity reservations.

## Run lease
Canonical lease path: `state/it-es-dispatch-lease.json`.

Before any LIVE execution:
1. Fetch the lease immediately before acquiring it.
2. If an unexpired LIVE lease exists, do NOT send. Become MONITOR_ONLY and reconcile its progress from Hostinger Sent + canonical state.
3. Otherwise write a new lease containing `run_id`, `mode=LIVE`, `owner`, `acquired_at`, `expires_at`, `state=ACTIVE` and the candidate identity set.
4. Re-read the lease after write. Sending is authorized only if the stored `run_id` exactly equals the executor's run id.
5. Refresh the lease during long runs. Mark `COMPLETED`, `FAILED` or `ABORTED` when done. Never silently delete evidence of a run.

A stale lease may be superseded only after Hostinger Sent and the canonical recipient index are reconciled for every reserved identity.

## Per-identity send transaction
The batch-level preflight is NOT sufficient. Immediately before EACH external send:
1. Refetch current recipient index / ledger / READY queue.
2. Refetch/reconcile Hostinger Sent for that exact recipient and canonical organization.
3. Confirm the batch lease is still owned by this `run_id`.
4. Create/update an identity reservation for this `run_id` before sending.
5. Re-read reservation and require exact ownership.
6. If any new Sent evidence or contacted state exists, SKIP as `ALREADY_CONTACTED_RACE_RECONCILED`.
7. Send exactly once.
8. Verify provider Sent evidence and attachment metadata.
9. Persist VERIFIED_EMAIL_SENT in recipient index / ledger and remove the identity from READY BEFORE moving to the next organization.

No executor may process the next identity while the previous identity's provider state is unresolved.

## Idempotency key
Logical key: `FIRST_CONTACT::<canonical_identity_key>`.

A successful or ambiguous provider attempt permanently consumes this key until reconciled. A timeout, gateway error or missing response is `DELIVERY_STATE_UNKNOWN`, never authorization to retry automatically.

## Interactive immediate runs
An immediate user request to 'run now', 'reset counters', 'first use' or equivalent resets only the run counters. It NEVER clears historical deduplication, recipient state, leases or consumed idempotency keys.

If another live executor is already active, the immediate request attaches to that run as MONITOR_ONLY rather than starting a second sender.

## Incident 2026-09-01
During the first live immediate batch two execution contexts overlapped. The primary run had already sent AMO Marketing (UID 168) and BP Nexus (UID 171) before a second execution context retried them, creating duplicate UIDs 169 and 172. The second executor stopped as soon as the collision was detected.

This incident proves that pre-batch Sent reconciliation alone is insufficient. Run lease + per-identity recheck + write-after-each-send are mandatory from this version onward.

## Fail closed
Missing lease dependency, ambiguous lease ownership, reservation collision, provider uncertainty or inability to perform exact pre-send Sent reconciliation => do not send that identity. Record the blocker and continue only where safety remains provable.
