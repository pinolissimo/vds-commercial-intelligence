# VDS Revenue Flow — Self-Healing Preflight Protocol

## Purpose

Prevent qualified opportunities from being lost or unnecessarily blocked because derived commercial state has drifted from durable provider-verified history. This protocol is mandatory for the self-contained Revenue Flow before candidate processing and before any provider action.

## Canonical recovery roots

1. `data/global-sent-email-ledger.jsonl` is the durable append-only commercial sent-event ledger.
2. Provider-verified Hostinger Sent evidence is the recovery authority when a provider event is newer than the durable ledger or delivery state is ambiguous.
3. The following are derived operational caches and MUST be repairable from durable/provider evidence:
   - `views/provider-contact-suppression-index.json`
   - `views/global-sent-email-index.json`
   - `views/global-organization-index.json`
4. `governance/global-contact-reservations.json` is independent live collision state and must never be reconstructed from sent history.

A stale derived cache is not itself a reason to discard an opportunity. It is a repair condition.

## Preflight reconciliation — every Revenue Flow run

Before qualifying candidates:

1. Read the durable sent ledger and compute the highest provider UID represented by provider-verified professional outbound events.
2. Read all three derived caches and compare both their UID coverage and canonical identity coverage against the durable ledger.
3. If a durable event is missing from a derived cache, merge it idempotently into that cache before candidate processing continues.
4. If Hostinger Sent has a newer verified professional event than the durable ledger, perform targeted provider reconciliation, append the durable ledger exactly once, then reconcile all three derived caches.
5. A write failure after a provider-verified send MUST NOT cause a resend. On the next run, the provider/durable event is recovered first and all caches are repaired before new provider calls.
6. Unrelated cache records must be preserved. Shared-state writes use latest-SHA refetch + merge semantics.
7. Reconciliation failure blocks only provider actions whose dedup/delivery state remains genuinely ambiguous. It must not prevent safe discovery, qualification, MANUAL_APPLY preservation, or research on unrelated identities.

## UID and identity invariants

For each durable `VERIFIED_EMAIL_SENT` / `FIRST_CONTACT` event:

- `provider-contact-suppression-index.json` must suppress the canonical organization domain (or exact historical identity address when domain identity is unavailable).
- `global-sent-email-index.json` must contain the provider UID exactly once.
- `global-organization-index.json` must contain the canonical organization identity with contacted state and provider evidence.
- A different vacancy, source, recipient, campaign, role or worker never resets FIRST_CONTACT history.

The maximum provider UID is a watermark, not a message-count surrogate. Gaps in UID numbering are permitted because provider mailboxes may contain non-commercial messages.

## Large GitHub snapshot rule

Large GitHub files such as `views/high-frequency-discovery-latest.json` may be returned without inline `content` by a simplified connector/API representation. Missing inline content MUST NOT be interpreted as an empty discovery snapshot.

A discovery file is considered truly empty only when one of these is confirmed:

- repository metadata reports byte size `0`, or
- direct blob/raw retrieval returns zero bytes.

Otherwise use a blob/raw-capable read path, SHA/size metadata, or the checked-out file. A large/truncated representation is a reader condition, not a discovery failure.

## Four operational decisions only

Every serious candidate receives exactly one candidate-level outcome:

- `SEND_NOW`
- `MANUAL_APPLY`
- `WAIT_RESEARCH`
- `REJECT`

The send-window gate is run-level execution policy, not a fifth candidate classification. A candidate that satisfies all business/route/dedup gates may remain `SEND_NOW` outside 09:00–19:00 Europe/Madrid, while provider action is deferred until an authorized run. Do not convert it to `WAIT_RESEARCH` merely because the window is closed.

`WAIT_RESEARCH` is used only when one real hard SEND_NOW fact remains unresolved and cannot be closed in the current run; store exactly one blocker and one next lookup.

## Provider action invariant

Immediately before EACH Hostinger provider call:

1. re-read provider suppression;
2. re-read global organization/sent history relevant to that identity;
3. re-read current reservations;
4. confirm no conflicting provider/durable reconciliation gap remains;
5. confirm 09:00–19:00 Europe/Madrid send window.

After EACH send:

1. verify Hostinger Sent recipient, subject and provider UID;
2. append durable sent event exactly once;
3. reconcile all three derived caches immediately;
4. persist workstream state/metrics;
5. release reservation only after durable contacted state exists.

Ambiguous delivery remains `DELIVERY_STATE_UNKNOWN`; never blind resend.

## Self-healing executable

Run `python scripts/revenue_flow_preflight.py --check` to validate invariants.
Run `python scripts/revenue_flow_preflight.py --repair` to repair deterministic cache drift from the durable ledger.

The executable never sends email and never creates commercial history that is absent from the durable ledger. Provider-to-ledger recovery remains a targeted Hostinger reconciliation step.

## North-star behavior

Fail closed only on real risk: duplicate contact, stale/false need, wrong or guessed route, explicit prohibition, truthful-fit failure, legal/channel conflict, active reservation collision, or ambiguous delivery. Do not fail closed merely because a recoverable derived cache is stale.
