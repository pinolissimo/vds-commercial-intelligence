# VDS IT/ES Acquisition Chain — Transactional Execution Protocol

Version: 1.1
Effective: 2026-09-01

## Purpose
This protocol is the mandatory shared contract for the scheduled VDS IT/ES acquisition chain. It exists to prevent false READY states, duplicate first contact, silent dispatcher runs, route substitution and inconsistent state between discovery workers and execution.

## Scheduled chain
1. `:00` — Search Fanout
2. `:15` — Direct Route Miner
3. `:30` — High-Yield Job Miner
4. `:45` — Batch Dispatcher
5. Performance + Reply Watch — independent monitoring/alert layer

Discovery workers NEVER send or submit. The Batch Dispatcher is the only scheduled task authorized to execute first-contact applications.

## Canonical state
Repository: `pinolissimo/vds-commercial-intelligence`, branch `main`.

Required shared files:
- `views/it-es-partner-apply-ready-queue.json`
- `views/it-es-partner-apply-recipients.json`
- `data/it-es-partner-apply-ledger.jsonl`
- `reports/it-es-partner-apply-cumulative.md`
- `reports/it-es-batch-dispatcher-runs.jsonl`

GitHub state is necessary but not sufficient for deduplication. Before promotion to READY and again before dispatch, mailbox Sent evidence must be reconciled when available.

## Canonical identity invariant
FIRST_CONTACT is unique by commercial organization identity, not by email address, job listing, office, source, geography, campaign or workstream.

A different recipient or listing NEVER resets prior-contact history.

Canonical identity examples:
- `org:example.com`
- another deterministic organization-level key when no stable official domain exists.

## State machine
Allowed execution-facing states:

`DISCOVERED -> QUALIFYING -> VERIFIED_NON_EXECUTABLE | READY_TO_APPLY -> DISPATCH_RECHECK -> VERIFIED_EMAIL_SENT | VERIFIED_SUBMISSION | DELIVERY_STATE_UNKNOWN | BLOCKED_FINAL_GATE`

`VERIFIED_NON_EXECUTABLE` includes explicit reason codes such as:
- `MANUAL_ROUTE_REQUIRED`
- `ALREADY_CONTACTED`
- `REVIEW_REQUIRED`
- `HOLD_STALE`
- `CROSS_BORDER_TAX_BLOCKER`
- `ROUTE_UNRESOLVED`
- `DOCUMENT_QA_FAILED`
- `LEGAL_CHANNEL_BLOCKER`

Only `READY_TO_APPLY` records count toward the batch threshold.

## READY certification — mandatory producer gate
A discovery worker may write `READY_TO_APPLY` only when ALL of the following are true at write time:
1. canonical organization identity resolved;
2. current need/freshness verified from authoritative evidence;
3. truthful VDS fit verified;
4. geography/remote/cross-border eligibility resolved;
5. exact official execution route resolved;
6. route is executable by the scheduled dispatcher;
7. if email route: exact official application/collaboration recipient verified; generic unrelated contact email is insufficient;
8. if form/platform route: current dispatcher runtime is known to support that exact execution route; otherwise `MANUAL_ROUTE_REQUIRED`;
9. global dedup completed across canonical GitHub history, recipient index and available Hostinger/Gmail Sent evidence;
10. no active reservation/contact collision for the canonical identity;
11. CV/document requirement known; if a document is mandatory but cannot be prepared/QA'd by dispatcher, record non-executable rather than READY;
12. legal/channel state resolved.

If any item is unknown, ambiguous or unavailable, the candidate MUST NOT enter READY.

## Producer write discipline
Before modifying the shared READY queue, each producer MUST:
1. fetch the latest queue immediately before write;
2. reconcile the candidate with current ledger/recipient index and available Sent evidence;
3. reject an already-present canonical identity;
4. preserve unrelated entries created by other workers;
5. write the candidate once;
6. re-read the queue after write and verify its canonical identity appears exactly once;
7. record the promotion/non-promotion event in the append-only ledger or worker metrics.

A producer may never rely on a queue snapshot from the beginning of its run when writing at the end.

## Dispatcher transaction
The dispatcher MUST perform a full final reconciliation before calculating the threshold.

Order:
`READ_LATEST_QUEUE -> SANITIZE -> FINAL_DEDUP -> ROUTE_RECHECK -> FRESHNESS_RECHECK -> DOCUMENT_READINESS -> EXECUTABLE_READY_COUNT -> THRESHOLD_DECISION`

### Threshold — temporary live validation policy
Operator-approved temporary minimum: **7 certified executable candidates**. This temporary value is intended to validate the first real automatic dispatch cycle while preserving every quality gate. Raise it back to 10 when reservoir replenishment is consistently healthy.

- `EXECUTABLE_READY_COUNT < 7` -> send/submit NOTHING.
- `EXECUTABLE_READY_COUNT >= 7` -> execute the entire valid batch unless a provider/legal/deliverability blocker arises during execution.

The raw queue count is never the threshold value.

## Mandatory sanitization
Any stale/duplicate/non-executable item discovered by the dispatcher is immediately removed or demoted from READY and recorded with an exact reason. It must not remain as READY for the next cycle.

Manual sends performed interactively by the user/assistant are treated as external state changes. On the next producer/dispatcher reconciliation, matching identities must be removed from READY as `ALREADY_CONTACTED`.

## No route substitution
A form/platform-only opportunity may never be converted to email simply because a generic email exists elsewhere on the organization website. An email execution route must itself be authoritative for applications/collaboration.

## Document QA
Where CV/document attachment is required, the exact final PDF must pass the repository's mandatory document QA gate before send. Failed or unavailable QA blocks execution.

## Sent verification
After every email action, the dispatcher must confirm the message exists in official Hostinger Sent before recording `VERIFIED_EMAIL_SENT`.

Ambiguous state -> `DELIVERY_STATE_UNKNOWN`; never blindly resend.

## Observability — no silent runs
Every dispatcher run MUST append one record to `reports/it-es-batch-dispatcher-runs.jsonl`, including zero-send runs.

Minimum fields:
- `run_id`
- `scheduled_at` / `started_at` / `finished_at` when available
- `mode` (`LIVE` or `DRY_RUN`)
- `raw_ready_count`
- `sanitized_ready_count`
- `executable_ready_count`
- `threshold_reached`
- `removed_or_demoted[]`
- `attempted`
- `verified_email_sent`
- `verified_submission`
- `delivery_state_unknown`
- `remaining_ready_count`
- `dependency_failures[]`
- `result`

Valid result examples: `DISPATCHED`, `THRESHOLD_NOT_REACHED`, `BLOCKED_DEPENDENCY`, `FAILED`, `DRY_RUN_WOULD_DISPATCH`, `DRY_RUN_THRESHOLD_NOT_REACHED`.

If raw READY >=7 but final executable READY <7, the event is explicitly surfaced as `BATCH_BLOCKED_AFTER_FINAL_GATE`.

## Dry-run safety mode
A dry-run MUST execute every read, dedup, sanitization, route/freshness decision, threshold calculation and planned-message/document QA step but MUST NOT call any mail-send, form-submit, DM or platform submission action.

Dry-run may write audit/test records to GitHub. `attempted`, `verified_email_sent` and `verified_submission` remain zero. It reports what WOULD have happened.

## Monitoring contract
Performance + Reply Watch must treat `reports/it-es-batch-dispatcher-runs.jsonl` as the authoritative dispatcher execution log. It must not infer dispatch from queue changes or from prepared drafts.

It must flag:
- missing dispatcher run record for an expected scheduled cycle;
- raw >=7 but executable <7;
- stale/duplicate entries surviving in READY;
- any Sent message whose canonical identity was not recorded by dispatcher or a clearly identified manual interactive action;
- any producer that promotes a candidate without full READY certification.

## Hard invariants
1. Zero duplicate first contact.
2. Discovery tasks never send.
3. Only certified executable candidates enter READY.
4. Only final executable READY count controls batch threshold.
5. No platform/form-to-email substitution.
6. Every dispatcher cycle is auditable.
7. No SENT state without provider evidence.
8. Dry-run never performs external communication.
