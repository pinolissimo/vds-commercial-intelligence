# VDS Global Organization Dedup Protocol v1.2

Effective: 2026-09-04

## Purpose

Mandatory for EVERY VDS automation or interactive workflow capable of professional outbound first contact. It provides one organization-level identity and sent-history layer across commercial outreach, job applications, agency/white-label discovery, EU-project intelligence and future workstreams.

## Hard invariant

`NO_DUPLICATE_FIRST_CONTACT_GLOBAL`

A commercial organization/employer may receive only one unsolicited/proactive first contact unless a later message is a clearly documented continuation, reply-driven follow-up, recruiter-requested reroute or owner-authorized exception.

A different email, person, office, vacancy, source, geography, campaign, workstream or automation NEVER resets first-contact history.

## Professional mail ownership

- Professional outbound mail is sent ONLY from Hostinger mailbox `info@visualdesignstudio.es`.
- Hostinger Sent is the provider source of truth for professional outbound delivery evidence.
- Gmail is used ONLY for owner notifications and BCC copies. Gmail is NOT a professional outbound source and MUST NOT be queried for routine professional-email deduplication.

## Canonical fast registry

Routine first-contact dedup MUST be JSON-first.

Canonical files:
- `views/global-organization-index.json` — compact cross-workstream organization/contact cache.
- `views/global-sent-email-index.json` — compact fast lookup of provider-verified professional outbound messages.
- `data/global-sent-email-ledger.jsonl` — durable append-only chronological professional sent ledger.
- `governance/global-contact-reservations.json` — short-lived pre-send organization reservations.
- `views/cross-signal-opportunities.json` — ranked cross-source opportunity view.
- Existing workstream recipient indexes/ledgers remain supporting historical evidence.

The JSON indexes are the PRIMARY operational lookup path. Hostinger mailbox scans are fallback/reconciliation, not the normal query path.

## Canonical identity

Prefer deterministic identity keys in this order:
1. verified registrable organization domain, e.g. `org:example.com`;
2. verified legal/company identity when domain is absent;
3. conservative normalized organization key only when independently verified.

Store aliases, brands, domains and known recruiter/company names under the same canonical organization when evidence supports equivalence. Ambiguous identity => `REVIEW_REQUIRED`, no send.

## Mandatory pre-send sequence

Every sender MUST execute immediately before EACH provider call:

`READ_GLOBAL_SENT_INDEX -> READ_GLOBAL_ORG_INDEX -> READ_RELEVANT_WORKSTREAM_INDEX -> RESOLVE_CANONICAL_ORG -> CHECK_ACTIVE_RESERVATION -> RESERVE_ORG_ATOMICALLY -> TARGETED_HOSTINGER_RECONCILIATION_IF_REQUIRED -> RECHECK_INDEX_STATE -> SEND_HOSTINGER -> VERIFY_HOSTINGER_SENT -> APPEND_GLOBAL_SENT_LEDGER -> UPDATE_GLOBAL_SENT_INDEX -> UPDATE_GLOBAL_ORG_INDEX -> UPDATE_WORKSTREAM_STATE -> RELEASE_RESERVATION`

Routine dedup is normally satisfied by the compact JSON indexes plus relevant workstream history.

A targeted Hostinger Sent check is required only when one or more of these apply:
- canonical organization/history is absent or ambiguous;
- JSON cache is missing, stale or internally inconsistent;
- provider UID continuity indicates a gap;
- a stale reservation is being recovered;
- provider response is ambiguous;
- validating the message that was just sent.

DO NOT rescan the full Hostinger Sent mailbox for every candidate when indexed state is current and coherent.

Gmail is excluded from this sequence.

If any mandatory step is ambiguous or fails closed, do not send.

## Sent registry write contract

After EVERY Hostinger-verified professional send, in the SAME run and BEFORE the next organization:

1. append one immutable event to `data/global-sent-email-ledger.jsonl` where append is available; if append mutation is unavailable, persist an equivalent durable pending event and reconcile it later;
2. update `views/global-sent-email-index.json` by latest-SHA read/merge/write;
3. update `views/global-organization-index.json` status to `CONTACTED`;
4. update originating workstream ledger/index;
5. release reservation only after canonical commit.

Minimum sent record fields:
- `provider_uid`;
- `sent_at`;
- `canonical_identity_key`;
- `organization`;
- `recipient`;
- `subject`;
- `workstream` / task;
- `action_type` where useful;
- `state=VERIFIED_EMAIL_SENT`.

Provider UID is globally unique within the Hostinger Sent mailbox and MUST never be counted twice.

## Fast query policy

For ordinary questions and dedup checks:
- today's professional sends -> query `views/global-sent-email-index.json` by Europe/Madrid date;
- history for one organization -> query global organization + sent indexes;
- sends by workstream -> query global sent index;
- daily statistics -> use daily metrics first, then global sent index if needed;
- full Hostinger scans -> audit/recovery fallback only.

## Provider reconciliation

Hostinger Sent remains authoritative when evidence conflicts with JSON. Reconciliation should be targeted whenever possible using provider UID, recipient domain, organization aliases, subject/context and known timestamps. Any credible prior first-contact evidence blocks a new first contact even if another recipient is now available.

## Reservation rules

`governance/global-contact-reservations.json` prevents two VDS senders from racing on the same organization.

Before send, atomically reserve the canonical organization through latest-SHA compare-and-swap. Reservation contains:
- canonical organization key;
- worker/task name;
- run id;
- intended route/recipient;
- reserved_at;
- expires_at;
- state `ACTIVE`.

An unexpired reservation owned by another run blocks sending. Never overwrite another active reservation blindly. Stale reservation recovery requires targeted Hostinger + canonical reconciliation first.

Reservation is released only after verified Sent + canonical commit, or after a confirmed zero-send abort.

## Job vs commercial collision policy

A prior general commercial first contact to an organization normally blocks a new unsolicited job-application first contact to the same employer, and vice versa, unless the new action is a clearly distinct authoritative recruitment continuation that is documented and justified. When uncertain, `REVIEW_REQUIRED`.

## Cross-signal use

Discovery/ranking tasks enrich the SAME canonical organization instead of creating duplicates. Multiple independent fresh signals increase priority but NEVER permit bypassing first-contact history.

## Default safety rule for future tasks

Any future VDS task with outbound capability is NON-COMPLIANT unless its prompt explicitly requires this protocol, JSON-first global sent lookup, canonical organization identity resolution, atomic reservation and Hostinger Sent verification of every actual professional send.
