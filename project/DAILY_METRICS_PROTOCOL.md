# VDS Daily Metrics Protocol v2.0

Purpose: make daily research/outreach statistics immediate, deterministic and cheap to query without rescanning mailboxes or historical ledgers.

## Time basis
All daily counters use `Europe/Madrid` calendar days. A daily file covers `00:00:00` through `23:59:59` local time for its date.

## Active writers
The unified architecture has two active writers:

- `VDS Unified Acquisition Loop` -> `metrics/daily/YYYY-MM-DD-unified.json` and the backward-compatible send projection `metrics/daily/YYYY-MM-DD-dispatcher.json`.
- `VDS Performance + Reply Watch` -> `metrics/daily/YYYY-MM-DD-summary.json` aggregate/outcomes only.

Historical v1 files (`search-fanout`, `direct-route`, `high-yield`, `dispatcher`) remain permanent read-only evidence for dates/runs produced before migration. Never delete or rewrite historical records solely because the architecture changed.

## Unified operational schema
`metrics/daily/YYYY-MM-DD-unified.json` contains at least:

- `date`
- `timezone`
- `updated_at`
- `runs`
- `counted_run_ids`
- `research.raw_signals`
- `research.unique_organizations`
- `research.cheap_pass`
- `research.backlog_added`
- `research.duplicates`
- `research.stale_or_rejected`
- `qualification.route_closed`
- `qualification.deep_checked`
- `qualification.ready_added`
- `qualification.manual_route_required`
- `qualification.explicit_no_freelance`
- `qualification.route_failures`
- `qualification.blocked`
- `dispatch.raw_ready_seen`
- `dispatch.executable_ready_seen`
- `dispatch.emails_attempted`
- `dispatch.emails_verified_sent`
- `dispatch.unique_organizations_sent`
- `dispatch.duplicates_blocked`
- `dispatch.retry_required`
- `dispatch.delivery_state_unknown`
- `dispatch.spain_sends`
- `dispatch.italy_sends`
- `dispatch.eu_language_compatible_sends`
- `manual_action.opportunities_preserved`
- `manual_action.notifications_required`

The Unified Loop updates only the delta produced by its current run. It must never derive normal daily counters by rescanning complete mailbox history.

## Dispatcher compatibility projection
`metrics/daily/YYYY-MM-DD-dispatcher.json` remains the fastest authoritative answer for automatic first-contact send counts and preserves compatibility with existing queries/dashboards.

Required fields:
- `date`
- `timezone`
- `updated_at`
- `runs`
- `counted_run_ids`
- `emails_attempted`
- `emails_verified_sent`
- `unique_organizations_sent`
- `duplicates_blocked`
- `manual_route_required`
- `retry_required`
- `delivery_state_unknown`
- `spain_sends`
- `italy_sends`
- `eu_language_compatible_sends`
- `provider_uids` when compactly maintainable

`emails_verified_sent` and `unique_organizations_sent` increment ONLY after official Hostinger Sent verification. Test messages, owner alerts, replies to existing conversations, internal reports and manual/interactively sent messages do NOT increment these automatic first-contact counters.

## Update rule
At the end of every Unified Loop run:
1. read the current day's unified file if present;
2. reject duplicate run IDs;
3. add only the current run delta;
4. write the full replacement using the latest blob SHA;
5. update the dispatcher compatibility projection with the same idempotent run ID;
6. verify the persisted send delta equals provider-verified sends for that run.

If a file is absent, create it with zeroed counters plus the current run delta.

## Idempotency
Every operational daily file must contain `counted_run_ids`. Before applying a run delta, check whether its `run_id` is already present. If yes, do not increment again. A provider UID already represented in the current day's send projection must never be counted twice even if a recovery run is repeated.

## Watchdog aggregate summary
`VDS Performance + Reply Watch` is the sole writer of `metrics/daily/YYYY-MM-DD-summary.json`.

On each watchdog run, read today's unified operational file, dispatcher compatibility projection and canonical current READY state, then write a compact aggregate containing at least:

- `date`
- `timezone`
- `updated_at`
- `research.raw_signals`
- `research.unique_organizations`
- `research.backlog_added`
- `qualification.ready_added_total`
- `qualification.manual_route_required`
- `dispatch.emails_verified_sent`
- `dispatch.unique_organizations_sent`
- `dispatch.spain_sends`
- `dispatch.italy_sends`
- `dispatch.eu_language_compatible_sends`
- `dispatch.duplicates_blocked`
- `dispatch.retry_required`
- `outcomes.positive_replies`
- `outcomes.bounces`
- `current_ready_count`
- `manual_action.pending_count` when available

The summary is a cache for fast statistics; the unified file and dispatcher projection remain authoritative for operational counters.

## Migration-day rule
For 2026-09-04 and any future architecture migration occurring mid-day, preserve already-written v1 counters and continue from the verified cumulative baseline. Do not double-count a run or provider UID merely because responsibility moved to the Unified Loop. The dispatcher compatibility projection must reflect the correct cumulative automatic-send total for the calendar day.

## Query policy
- `quante email oggi?` -> read today's `dispatcher.json` first.
- `quante opportunità trovate oggi?` -> read today's `unified.json` research counters.
- `quante READY oggi?` -> read today's `unified.json` qualification counters; current queue size comes from canonical READY state/summary.
- combined same-day pipeline statistics -> read today's `summary.json`.
- 7/30/90-day statistics -> aggregate daily summary/unified/dispatcher files; use v1 historical files for pre-migration dates where needed.
- mailbox/history reconciliation is fallback audit only when daily counters are missing, inconsistent or explicitly under audit.

## Manual-action preservation
A strong opportunity requiring a form/platform/human step must increment `manual_action.opportunities_preserved` and be persisted with exact route/reason. It must never disappear merely because automatic execution is unsupported. Owner notification is handled by the Watchdog when action is required.

## Retention
Never overwrite another date. Daily files are permanent lightweight historical records and can be aggregated directly for longitudinal statistics without mailbox scans.
