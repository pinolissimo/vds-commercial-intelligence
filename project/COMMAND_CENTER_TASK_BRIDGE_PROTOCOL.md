# Visual Design Studio — 2026
# VDS Command Center Task Bridge Protocol

Version: 1.2
Status: production invariant

## Purpose

The Command Center is an additive control plane around the simplified VDS acquisition architecture. It MUST NOT weaken, pause, bypass or replace independent discovery or the two active execution flows.

## Production architecture

- GitHub high-frequency discovery remains independent and always-on.
- `LINKEDIN_HUNTER` -> **VDS Job Flow**: self-contained direct-job discovery/qualification/decision/application execution.
- `UNIFIED_LOOP` -> **VDS Revenue Flow**: self-contained commercial/agency/EU/direct-buyer discovery/qualification/decision/outreach execution.
- `AGENCY_RADAR` and the former Cross-Signal intermediate handoff are retired/disabled and MUST NOT be required for command execution.

The execution model is intentionally short:

`DISCOVERY -> QUALIFY/DECIDE -> SEND_NOW | MANUAL_APPLY | WAIT_RESEARCH | REJECT`

No dashboard command may recreate a mandatory multi-worker handoff between discovery and send.

## Canonical files

- `command-center/commands/pending.json` — owner directives created by the dashboard/OpenAI router.
- `command-center/commands/processed.json` — idempotent per-worker consumption receipts.
- `api/v1/ai-command/latest.json` — latest interpreted command for the UI.

## Worker IDs

Exactly these production workers consume dashboard directives:

- `LINKEDIN_HUNTER` → VDS Job Flow
- `UNIFIED_LOOP` → VDS Revenue Flow

## Read order on every normal worker run

1. Run the worker's minimal mandatory reads and hard safety checks.
2. Read `command-center/commands/pending.json` if present.
3. Read `command-center/commands/processed.json` if present.
4. Select commands where:
   - `status == PENDING_TASK_BRIDGE`;
   - this worker ID appears in `target_workers`;
   - command is not expired;
   - no receipt exists for `(command_id, worker_id)`.
5. Consume selected commands oldest-first without skipping the ordinary end-to-end worker cycle.
6. Apply the directive only as a priority/search/execution overlay inside the worker's existing authority.
7. Re-run all hard gates before any external provider action.
8. Append one receipt per consumed command and worker.

## Idempotency

A receipt key is `command_id + worker_id`. A worker that already has a receipt for a command MUST NOT execute it again.

Receipt schema:

```json
{
  "command_id": "CMD-...",
  "worker_id": "LINKEDIN_HUNTER|UNIFIED_LOOP",
  "consumed_at": "ISO-8601 Europe/Madrid",
  "result": "APPLIED|NO_ACTION|BLOCKED|EXPIRED|REVIEW_REQUIRED",
  "summary": "short factual result",
  "external_send_count": 0,
  "provider_uids": [],
  "normal_cycle_completed": true,
  "existing_gates_preserved": true
}
```

`external_send_count` and `provider_uids` are evidence fields only. A receipt NEVER authorizes or proves a send without normal provider verification.

## Routing

- job/direct-job/vacancy/application search or send → `LINKEDIN_HUNTER`
- agency/white-label/EU-project/WPO/direct-buyer/commercial search or send → `UNIFIED_LOOP`
- broad acquisition priority/refresh → both active workers

Never target retired `AGENCY_RADAR`.

## Hard non-bypass invariants

No dashboard command may override:

- organization-level first-contact dedup and suppression;
- active reservation rules;
- current/fresh need verification;
- truthful VDS fit;
- authoritative route/recipient requirements;
- legal/channel compatibility and opt-out/prohibition;
- send window;
- Hostinger Sent verification;
- manual-route preservation;
- maximum one eligible follow-up;
- ambiguous-delivery no-blind-resend rule.

Missing nonessential metadata, lack of explicit freelance wording, or obsolete internal intermediate-state labels are NOT independent hard blockers.

## Owner-copy prohibition — hard outbound invariant

Automated VDS acquisition messages MUST NOT create owner copies by BCC or CC.

For every automated `FIRST_CONTACT`, application, commercial outreach or other acquisition send:

- `bcc` MUST be empty;
- `cc` MUST be empty unless the owner explicitly authorizes a specific business recipient for that individual message;
- NEVER BCC or CC `allocca.pino@gmail.com`;
- NEVER BCC or CC `info@visualdesignstudio.es` back to itself;
- do not substitute another VDS/owner mailbox as a monitoring copy;
- provider verification MUST rely on authoritative Hostinger Sent + provider UID, not on a Gmail/VDS inbox copy;
- audit/state fields such as `bcc_owner` MUST be `null`, `false` or empty for automated acquisition sends;
- any automated send payload containing either owner address in BCC/CC is a hard pre-send failure and MUST NOT be submitted until the copy recipient is removed.

This invariant applies equally to `LINKEDIN_HUNTER`, `UNIFIED_LOOP`, GitHub Actions senders and any future VDS automated outbound path. It does not prevent a manually composed email from using CC/BCC when the owner explicitly requests it for that specific message.

## Duplicate protection — hard outbound invariant

Before every automated `FIRST_CONTACT`, duplicate protection applies both across history and inside the current execution batch/run:

- exact recipient email;
- canonical organization identity;
- corporate domain (except shared/free-mail domains, where organization/exact-address evidence is required);
- fresh Hostinger Sent evidence;
- fresh Gmail Sent evidence when available;
- in-memory/current-run exact email and canonical organization/domain reservations.

A positive or ambiguous match blocks a new first contact. Provider Sent evidence remains authoritative. A persistence failure after a provider-verified send MUST NEVER cause a resend.

## Availability invariant

Command handling is subordinate to the worker's ordinary mission. Failure to read, parse or write Command Center files MUST NOT stop discovery, qualification, reply monitoring or authorized execution. Persist the bridge error when possible and continue safely.

## Concurrency

Before updating `processed.json`, refetch latest state and merge the new receipt without replacing unrelated receipts. Retry conflicts by refetching/merging. Do not pause the acquisition engine.

## Retention

Pending commands have a default TTL of 24 hours unless the router assigns a shorter explicit expiry. Completed/expired commands may remain in bounded history; workers rely on receipts + expiry rather than destructive removal.
