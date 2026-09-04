# VDS Daily Metrics Protocol v1.0

Purpose: make daily research/outreach statistics immediate, deterministic and cheap to query without rescanning mailboxes or historical ledgers.

## Time basis
All daily counters use `Europe/Madrid` calendar days. A daily file covers `00:00:00` through `23:59:59` local time for its date.

## Single-writer files
Each active worker owns exactly one file per day and MUST NOT write another worker's file:

- Search Fanout -> `metrics/daily/YYYY-MM-DD-search-fanout.json`
- Direct Route Miner -> `metrics/daily/YYYY-MM-DD-direct-route.json`
- High-Yield Job Miner -> `metrics/daily/YYYY-MM-DD-high-yield.json`
- Batch Dispatcher -> `metrics/daily/YYYY-MM-DD-dispatcher.json`
- Performance + Reply Watch -> `metrics/daily/YYYY-MM-DD-summary.json` (aggregate only)

This prevents cross-worker write collisions.

## Update rule
At the end of every run, the worker must read its current daily file if present, add ONLY the delta produced by that run, update `updated_at`, and write the full replacement JSON using the latest blob SHA. If the file is absent, create it with zeroed counters plus the current run delta.

Never recount the full mailbox/history to update a counter. Historical provider/ledger scans remain validation evidence only, not the daily counting mechanism.

## Idempotency
Every worker file must contain `counted_run_ids`. Before applying a run delta, check whether its `run_id` is already present. If yes, do not increment again. Keep a compact list of run IDs for the current day.

## Worker schemas

### Search Fanout
Required counters:
- `runs`
- `raw_signals`
- `unique_organizations`
- `cheap_pass`
- `backlog_added`
- `immediate_ready_added`
- `duplicates`
- `stale_or_rejected`
- `spain_yield`
- `italy_yield`
- `eu_language_compatible_yield`

### Direct Route Miner
Required counters:
- `runs`
- `candidates_closed`
- `ready_added`
- `manual_route_required`
- `explicit_no_freelance`
- `stale`
- `duplicates`
- `route_failures`
- `spain_ready`
- `italy_ready`
- `eu_language_compatible_ready`

### High-Yield Job Miner
Required counters:
- `runs`
- `candidates_ranked`
- `deep_checked`
- `ready_added`
- `rejected`
- `blocked`
- `duplicates`
- `spain_ready`
- `italy_ready`
- `eu_language_compatible_ready`

### Batch Dispatcher
Required counters:
- `runs`
- `raw_ready_seen`
- `executable_ready_seen`
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
- `positive_replies_seen`
- `bounces_seen`

`emails_verified_sent` and `unique_organizations_sent` are authoritative only after Hostinger Sent verification. Test messages, owner alerts, replies to existing conversations, internal reports and manual/interactively sent messages do NOT increment these counters unless the dispatcher itself executed them as a new qualified first contact.

## Aggregate summary
`VDS Performance + Reply Watch` is the sole writer for `metrics/daily/YYYY-MM-DD-summary.json`. On each run it reads the four worker daily files and writes a compact aggregate containing at least:

- `date`
- `timezone`
- `updated_at`
- `research.raw_signals`
- `research.unique_organizations`
- `research.backlog_added`
- `qualification.ready_added_total`
- `dispatch.emails_verified_sent`
- `dispatch.unique_organizations_sent`
- `dispatch.spain_sends`
- `dispatch.italy_sends`
- `dispatch.eu_language_compatible_sends`
- `dispatch.duplicates_blocked`
- `dispatch.retry_required`
- `outcomes.positive_replies`
- `outcomes.bounces`
- `current_ready_count` from canonical READY queue

The summary is a cache for fast statistics; worker files remain the authoritative daily source for their own counters.

## Query policy
For questions such as `quante email oggi?`, read the dispatcher daily file first. For `quante opportunità trovate oggi?`, read Search Fanout. For combined pipeline statistics, read the daily summary. Only fall back to Hostinger/Gmail/GitHub historical reconciliation when a daily file is missing, inconsistent or explicitly under audit.

## Retention
Never overwrite another date. Daily files are permanent lightweight historical records and can be aggregated directly for 7/30/90-day statistics without mailbox scans.
