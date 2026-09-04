# VDS Global Organization Dedup Protocol v1.0

Effective: 2026-09-04

## Purpose

This protocol is mandatory for EVERY VDS automation or interactive workflow that can create a first commercial/job contact. It provides one organization-level identity layer across commercial outreach, job applications, agency/white-label discovery, EU-project intelligence and future workstreams.

## Hard invariant

`NO_DUPLICATE_FIRST_CONTACT_GLOBAL`

A commercial organization/employer may receive only one unsolicited/proactive first contact unless a later message is a clearly documented continuation, reply-driven follow-up, recruiter-requested reroute or owner-authorized exception.

A different email, person, office, vacancy, source, geography, campaign, workstream or automation NEVER resets first-contact history.

## Canonical files

- `views/global-organization-index.json` — compact cross-workstream identity/contact cache.
- `governance/global-contact-reservations.json` — short-lived pre-send reservations.
- `views/cross-signal-opportunities.json` — ranked cross-source opportunity view.
- Existing workstream recipient indexes/ledgers remain authoritative historical evidence.
- Hostinger Sent and Gmail Sent remain mandatory external evidence before live send.

The global index is a fast cache, not a replacement for provider/canonical evidence.

## Canonical identity

Prefer deterministic identity keys in this order:
1. verified registrable organization domain, e.g. `org:example.com`;
2. verified legal/company identity when domain is absent;
3. conservative normalized organization key only when independently verified.

Store aliases, brands, domains and known recruiter/company names under the same canonical organization when evidence supports equivalence. Ambiguous identity => `REVIEW_REQUIRED`, no send.

## Mandatory pre-send sequence

Every sender MUST execute immediately before EACH provider call:

`REFETCH_GLOBAL_INDEX -> REFRESH_WORKSTREAM_HISTORY -> CHECK_HOSTINGER_SENT -> CHECK_GMAIL_SENT -> RESOLVE_CANONICAL_ORG -> CHECK_ACTIVE_RESERVATION -> RESERVE_ORG_ATOMICALLY -> RECHECK_PROVIDER/CANONICAL_STATE -> SEND -> VERIFY_SENT -> COMMIT_GLOBAL_CONTACT -> RELEASE_RESERVATION`

If any step is ambiguous or fails closed, do not send.

## Provider reconciliation

A recipient/address-only search is insufficient. Reconcile using organization name, canonical domain, aliases, known recipient domains, subjects/context and workstream records where needed.

Any credible prior first-contact evidence blocks a new first contact even when the newly discovered route uses another address.

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

An unexpired reservation owned by another run blocks sending. Never overwrite another active reservation blindly. Stale reservation recovery requires provider + canonical reconciliation first.

Reservation is released only after verified Sent + canonical commit, or after a confirmed zero-send abort.

## Global contact commit

After provider verification and before the next send, update the global organization index with:
- canonical key;
- organization;
- aliases/domains when known;
- first-contact timestamp;
- workstream/source task;
- recipient;
- provider UID/evidence;
- status `CONTACTED`;
- last action.

Also update the originating workstream ledger/index. Historical evidence must never be deleted merely to permit another first contact.

## Job vs commercial collision policy

A prior general commercial first contact to an organization normally blocks a new unsolicited job-application first contact to the same employer, and vice versa, unless the new action is a clearly distinct authoritative recruitment continuation that is documented and justified. When uncertain, `REVIEW_REQUIRED`.

## Cross-signal use

Discovery/ranking tasks should enrich the same organization with signals instead of creating duplicate organizations. Signals may include:
- LinkedIn/public job signal;
- official careers signal;
- agency external-collaborator/white-label signal;
- EU project/dissemination signal;
- website/performance/digital-need signal;
- reply/referral signal;
- previous contact status.

Multiple independent fresh signals increase priority, never permission to bypass dedup.

## Default safety rule for future tasks

Any future VDS task with outbound capability is NON-COMPLIANT unless its prompt explicitly requires this protocol, global organization identity resolution, atomic reservation and fresh Hostinger/Gmail Sent reconciliation before each first contact.
