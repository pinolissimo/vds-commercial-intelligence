# VDS Global Organization Dedup Protocol v1.1

Effective: 2026-09-04

## Purpose

This protocol is mandatory for EVERY VDS automation or interactive workflow that can create a first commercial/job contact. It provides one organization-level identity layer across commercial outreach, job applications, agency/white-label discovery, EU-project intelligence and future workstreams.

## Hard invariant

`NO_DUPLICATE_FIRST_CONTACT_GLOBAL`

A commercial organization/employer may receive only one unsolicited/proactive first contact unless a later message is a clearly documented continuation, reply-driven follow-up, recruiter-requested reroute or owner-authorized exception.

A different email, person, office, vacancy, source, geography, campaign, workstream or automation NEVER resets first-contact history.

## Canonical files

- `views/global-organization-index.json` — compact cross-workstream identity/contact cache.
- `views/global-sent-email-index.json` — fast cache of provider-verified professional outbound messages.
- `governance/global-contact-reservations.json` — short-lived pre-send reservations.
- `views/cross-signal-opportunities.json` — ranked cross-source opportunity view.
- Existing workstream recipient indexes/ledgers remain authoritative historical evidence.
- Hostinger Sent is the SOLE provider source of truth for professional outbound mail.

Gmail is used only for owner notifications/BCC copies and is NOT a professional outbound source and is NOT required for routine professional-email deduplication.

The JSON indexes are fast operational caches. They accelerate normal checks but never override credible Hostinger/canonical historical evidence.

## Canonical identity

Prefer deterministic identity keys in this order:
1. verified registrable organization domain, e.g. `org:example.com`;
2. verified legal/company identity when domain is absent;
3. conservative normalized organization key only when independently verified.

Store aliases, brands, domains and known recruiter/company names under the same canonical organization when evidence supports equivalence. Ambiguous identity => `REVIEW_REQUIRED`, no send.

## Mandatory pre-send sequence

Every sender MUST execute immediately before EACH provider call:

`READ_GLOBAL_SENT_INDEX -> REFETCH_GLOBAL_ORG_INDEX -> REFRESH_WORKSTREAM_HISTORY -> RESOLVE_CANONICAL_ORG -> CHECK_ACTIVE_RESERVATION -> RESERVE_ORG_ATOMICALLY -> TARGETED_HOSTINGER_SENT_CHECK_IF_REQUIRED -> RECHECK_CANONICAL_STATE -> SEND -> VERIFY_HOSTINGER_SENT -> COMMIT_SENT_INDEX -> COMMIT_GLOBAL_CONTACT -> RELEASE_RESERVATION`

Routine dedup should normally be satisfied by the small JSON indexes + canonical workstream history. A targeted Hostinger Sent query is mandatory when:
- the organization is absent from the JSON cache but historical ambiguity exists;
- the cache is stale/inconsistent;
- provider UID continuity is broken;
- a reservation recovery is required;
- immediately validating the just-executed send.

Do NOT rescan the full Hostinger Sent mailbox on every candidate when the indexed state is current and coherent.

If any mandatory step is ambiguous or fails closed, do not send.

## Provider reconciliation

Hostinger Sent is the authoritative provider evidence for professional outbound mail from `info@visualdesignstudio.es`.

A recipient/address-only search is insufficient when reconciliation is needed. Use organization name, canonical domain, aliases, known recipient domains, subjects/context and workstream records where necessary.

Any credible prior first-contact evidence blocks a new first contact even when the newly discovered route uses another address.

Gmail BCC/notification copies may support owner visibility but never establish or invalidate professional-send state.

## Sent-email JSON index

`views/global-sent-email-index.json` stores one compact record per provider-verified professional outbound message, including at minimum:
- provider UID;
- sent timestamp;
- canonical organization key;
- organization;
- recipient;
- subject;
- workstream/task;
- action type;
- verification state.

After EVERY Hostinger-verified professional send, append/merge the message into this index in the same run before moving to the next organization.

Provider UID is unique. The same UID must never be counted twice. The index should support immediate questions such as today's sends, sends by workstream, sends by organization and anti-dup checks without rescanning the mailbox.

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

An unexpired reservation owned by another run blocks sending. Never overwrite another active reservation blindly. Stale reservation recovery requires Hostinger + canonical reconciliation first.

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

Also update the originating workstream ledger/index and `views/global-sent-email-index.json`. Historical evidence must never be deleted merely to permit another first contact.

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

Any future VDS task with outbound capability is NON-COMPLIANT unless its prompt explicitly requires this protocol, global organization identity resolution, atomic reservation, current JSON sent-index checks and Hostinger Sent verification of every actual professional send.
