# VDS Command Center Task Bridge Protocol

Version: 1.0
Status: production invariant

## Purpose

The Command Center is an additive control plane around the existing VDS acquisition tasks. It MUST NOT replace, weaken, pause, reschedule or bypass the production discovery/sending architecture.

## Canonical files

- `command-center/commands/pending.json` — owner directives created by the dashboard/OpenAI router.
- `command-center/commands/processed.json` — idempotent per-worker consumption receipts.
- `api/v1/ai-command/latest.json` — latest interpreted command for the UI.

## Worker IDs

Exactly these production workers consume dashboard directives:

- `AGENCY_RADAR` → VDS Agency + EU Signal Radar
- `LINKEDIN_HUNTER` → VDS LinkedIn Job Hunter
- `UNIFIED_LOOP` → VDS Unified Acquisition Loop

## Read order on every normal worker run

1. Run the worker's existing mandatory reads and safety checks.
2. Read `command-center/commands/pending.json` if present.
3. Read `command-center/commands/processed.json` if present.
4. Select commands where:
   - `status == PENDING_TASK_BRIDGE`;
   - this worker ID appears in `target_workers`;
   - command is not expired;
   - no receipt exists for the tuple `(command_id, worker_id)`.
5. Consume selected commands oldest-first, without skipping the worker's normal cycle.
6. Apply the directive only as an overlay to priorities/search scope/execution intent that the worker already owns.
7. Re-run every existing gate before any state promotion or external provider action.
8. Append one receipt per consumed command and worker.

## Idempotency

A receipt key is `command_id + worker_id`. If the same worker sees a command again after a successful or blocked receipt, it MUST NOT execute it again.

Receipt schema:

```json
{
  "command_id": "CMD-...",
  "worker_id": "AGENCY_RADAR",
  "consumed_at": "ISO-8601 Europe/Madrid",
  "result": "APPLIED|NO_ACTION|BLOCKED|EXPIRED|REVIEW_REQUIRED",
  "summary": "short factual result",
  "external_send_count": 0,
  "provider_uids": [],
  "normal_cycle_completed": true,
  "existing_gates_preserved": true
}
```

`external_send_count` and `provider_uids` are evidence fields only. A receipt NEVER authorizes or proves a send without the normal provider verification evidence.

## Routing

The AI router assigns `target_workers` deterministically:

- job/direct-job search or job send → `LINKEDIN_HUNTER`
- agency, white-label, EU-project, WPO/direct-buyer research → `AGENCY_RADAR`
- commercial READY send/priority directives → `UNIFIED_LOOP`
- broad acquisition priority/refresh directives → all relevant workers

If routing is ambiguous, target all relevant read/analysis workers but do not broaden external-send authority.

## Non-bypass invariants

No dashboard command may override:

- global organization first-contact dedup;
- provider suppression/history;
- active reservation/lease rules;
- exact authoritative route/recipient requirements;
- freshness/current-demand checks;
- geography/remote/legal/channel compatibility;
- truthful VDS fit;
- manual-route preservation;
- sending window;
- Hostinger Sent verification;
- hard opt-out/prohibition;
- maximum one eligible follow-up.

A directive asking to lower quality, ignore dedup, guess contacts, bypass a route, resend ambiguous delivery, or activate another sender MUST be recorded as `REVIEW_REQUIRED` or `BLOCKED` and not executed.

## Availability invariant

Command consumption is subordinate to the existing worker mission. Failure to read, parse or write Command Center files MUST NOT stop normal discovery, qualification, reply monitoring or already-authorized production execution. Persist the bridge error when possible and continue the normal cycle safely.

## Concurrency

Before updating `processed.json`, refetch its latest SHA and merge the new receipt into the existing array. Never replace unrelated receipts. Retry a SHA conflict by refetching/merging; do not hold or pause the acquisition engine.

## Retention

Pending commands have a default TTL of 24 hours unless the router assigns a shorter explicit expiry. Completed/expired commands can remain in the bounded pending history; workers rely on receipts + expiry, not destructive queue removal, which avoids race conditions between workers.
