# IT/ES Scheduled Acquisition Chain — Dry-Run Verification

Date: 2026-09-01
Mode: DRY_RUN / NO EXTERNAL COMMUNICATION
Result: PASS

## Scope
Validated the repaired scheduled chain:

`Search Fanout (:00) -> Direct Route (:15) -> High-Yield Job (:30) -> Batch Dispatcher (:45) -> Performance + Reply Watch`

The dispatcher was disabled before testing so no scheduled live send could occur during remediation.

## Structural fixes verified
- Shared mandatory contract added: `project/IT_ES_CHAIN_EXECUTION_PROTOCOL.md`.
- All three producer tasks now treat `READY_TO_APPLY` as certified/executable, not provisional.
- Producers must re-fetch latest queue/ledger/index and reconcile available Sent evidence immediately before writing.
- Organization-level FIRST_CONTACT dedup is mandatory across recipients/listings/sources/workstreams.
- Form/platform-only routes cannot be substituted with generic email.
- Producers must sanitize an invalid existing READY item when they discover it.
- Dispatcher threshold uses final `EXECUTABLE_READY_COUNT`, never raw queue count.
- Dispatcher has mandatory zero-send observability in `reports/it-es-batch-dispatcher-runs.jsonl`.
- Performance Watch independently checks missing dispatcher cycles, invalid READY states and Sent-vs-dispatch inconsistencies.

## Real-state replay
Pre-fix queue contained 10 READY records. Hostinger Sent history proved two were already contacted:
- Ibérica Studio — prior first contact on 2026-08-31.
- Boneluv — prior first contact on 2026-08-31.

Expected repaired behavior:
`RAW 10 -> remove 2 ALREADY_CONTACTED -> EXECUTABLE 8 -> threshold false -> 0 sends`.

Observed dry-run result: PASS.
The canonical queue was sanitized to 8 records.

## Test matrix

| Scenario | Raw | Removed | Executable | Expected decision | Result |
|---|---:|---:|---:|---|---|
| Replay: 10 with 2 prior contacts | 10 | 2 | 8 | BLOCK / 0 sends | PASS |
| Current sanitized queue | 8 | 0 | 8 | BLOCK / 0 sends | PASS |
| Synthetic 10 clean executable | 10 | 0 | 10 | WOULD DISPATCH 10 | PASS |
| Synthetic 11 with 1 form-only | 11 | 1 | 10 | WOULD DISPATCH 10 | PASS |
| Race: 10 then 1 manual send appears | 10 | 1 | 9 | BLOCK / 0 sends | PASS |

All dry-run records set `attempted=0`, `verified_email_sent=0`, `verified_submission=0`.

## Mailbox safety verification
Hostinger Sent was read after the simulation. No new message appeared during remediation/testing. Latest Sent remained UID 167, timestamp `2026-09-01T17:44:32Z`, the previously user-directed Talentchef message.

Therefore the remediation and simulation generated zero real outbound messages.

## Current operational state
- Search Fanout: repaired protocol applied.
- Direct Route Miner: repaired protocol applied.
- High-Yield Job Miner: repaired protocol applied.
- Performance + Reply Watch: repaired independent audit logic applied.
- Batch Dispatcher: repaired protocol applied but intentionally DISABLED after the dry-run safety test, to respect the instruction not to send any real message during this operation.
- Certified READY queue after sanitization: 8.

## Go-live gate
Before live reactivation, dispatcher configuration is already prepared for LIVE operation. Re-enabling the dispatcher is the only remaining operational switch; no code/protocol change is required.

## Residual risk model
This architecture materially reduces the previous failure mode by enforcing the same certification contract upstream and downstream and by making silent dispatcher cycles detectable. As with any tool-driven agentic workflow, provider/tool availability and unexpected external state can still block execution; these conditions now fail closed and must be logged rather than silently ignored.
