# VDS Provider-First Event Architecture

## Authority
Hostinger Sent/Inbox is authoritative for delivery/receipt. GitHub is durable audit/cache. `api/v1/**` is a disposable read model and MUST be rebuildable.

## Canonical event identity
Provider mail: `hostinger:<mailbox>:<direction>:<provider_uid>`. External/manual mail: `<source>:<external_id>`.
Never deduplicate only by recipient, subject, organization, timestamp or worker.

## Write path
1. Worker performs business action.
2. Provider confirms action and UID.
3. Persist immutable/idempotent provider evidence immediately.
4. Reconciler may observe the same UID again; merge, never duplicate.
5. Projection pipeline rebuilds read models.
6. Invariant suite must pass before publication.

A repository failure after provider verification NEVER authorizes resend.
An ambiguous provider result becomes DELIVERY_STATE_UNKNOWN and NEVER triggers blind retry.

## Read path
Dashboard reads only `api/v1/**`. It never owns business truth and workers never depend on dashboard freshness to decide whether an email was sent.

## Event envelope
Recommended fields: `schema_version`, `provider`, `mailbox`, `provider_uid`, `direction`, `sent_at/received_at`, `canonical_identity_key`, `organization`, `recipient/sender`, `subject`, `workstream`, `state`, `action_type`, `count_as_successful_outbound`, `commercial_archetype`, `commercial_variant`, `micro_cta_type`, `attachments`, `bcc_owner`.

## Consumer checkpoints
Each consumer owns an independent checkpoint: revenue-flow, job-flow, eu-flow, reply-watch, projector. A consumer MUST NOT advance another consumer's checkpoint. Advance only after successful provider read and durable merge. Use a bounded overlap when querying newer UIDs; idempotency absorbs repeats.

## Projection contract
`build -> enrich -> outbound overlay -> inbound overlay -> health -> invariant validation -> publish`.
No partial projection may be published after validation failure.

## Required invariants
- stable event identities are unique in a projection;
- sent >= first contacts >= 0;
- dashboard/today/outbound counters agree;
- every counted outbound is VERIFIED_EMAIL_SENT and not explicitly excluded;
- every counted outbound has a stable identity;
- provider observation timestamp exists;
- provider read failure cannot advance freshness;
- projection failure cannot mutate provider truth.

## Health semantics
Expose independently: provider observation freshness, projection/reconciliation freshness, last outbound, last inbound, pending sources, delivery unknown, and projection validation. A quiet mailbox is not an unhealthy system.

## Scheduling
Prefer event-driven projection on provider-state pushes. Scheduled projection is a safety net only. Provider reconciliation is appended to existing acquisition/reply workers instead of consuming a dedicated automation slot.

## Failure domains
Provider unavailable: preserve checkpoint and do not infer delivery.
GitHub write conflict: re-read latest state, idempotently merge by event identity, retry boundedly.
Projection error: fail closed; keep last valid published read model.
Dashboard/UI error: no effect on provider or commercial state.
