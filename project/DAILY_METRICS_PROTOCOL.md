# VDS Daily Metrics Protocol v3.0

Purpose: make acquisition/search/outreach statistics immediate, deterministic, idempotent and cheap to query without routine mailbox-history scans.

## Time basis

All daily counters use `Europe/Madrid` calendar days (`00:00:00`–`23:59:59`). Historical files are permanent evidence and must not be rewritten merely because the architecture changes.

## Active daily writers

Each operational worker owns only its dedicated daily file:

- `VDS LinkedIn Job Hunter` -> `metrics/daily/YYYY-MM-DD-linkedin-jobs.json`
- `VDS Agency + EU Signal Radar` -> `metrics/daily/YYYY-MM-DD-agency-eu-radar.json`
- `VDS Cross-Signal Ranker` -> `metrics/daily/YYYY-MM-DD-cross-signal.json`
- `VDS Unified Acquisition Loop` -> `metrics/daily/YYYY-MM-DD-unified.json` and backward-compatible `metrics/daily/YYYY-MM-DD-dispatcher.json`
- `VDS Performance + Reply Watch` -> `metrics/daily/YYYY-MM-DD-summary.json` aggregate/outcomes only
- GitHub high-frequency discovery -> `metrics/high-frequency-discovery-state.json`, `metrics/high-frequency-semantic-gate.json`, `metrics/territory-yield-radar-state.json` plus current adaptive views; these are read by the daily summary rather than treated as competing daily writers.

No worker may increment another worker's operational counters.

## Idempotency

Every daily operational file MUST contain `counted_run_ids`. Before adding a delta, reject a run_id already counted. Provider UID must never be counted twice. A recovery/retry of the same run cannot duplicate statistics.

## LinkedIn/job daily schema

Track at minimum:
- `runs`
- `jobs_found`
- `jobs_unique`
- `jobs_verified_open`
- `semantic_pass`
- `jobs_matched`
- `high_fit`
- `ready_to_apply`
- `first_contacts_attempted`
- `first_contacts_verified_sent`
- `followup_1_verified_sent`
- `unique_employers_first_contacted`
- `manual_route_required`
- `already_contacted`
- `duplicates_blocked`
- `stale`
- `rejected`
- `cv_tailored`
- `canonical_cv_used`
- `spain_jobs`
- `italy_jobs`
- `remote_eu_jobs`
- `positive_replies_seen`
- `interviews_or_calls_seen`
- `bounces_seen`

Only Hostinger-verified FIRST_CONTACT messages increment first-contact counters. FOLLOWUP_1 is separate.

## Agency + EU Radar daily schema

Track at minimum:
- `runs`
- `raw_signals`
- `semantic_candidates_consumed`
- `unique_organizations`
- `agency_signals`
- `eu_project_signals`
- `explicit_demand_signals`
- `direct_routes_found`
- `territory_enriched`
- `cross_signal_merges`
- `already_contacted_orgs`
- `manual_route_candidates`
- `high_value_candidates`
- `spain_yield`
- `italy_yield`
- `eu_yield`
- source × territory × segment yield when compactly maintainable.

This worker never increments send counters.

## Cross-Signal daily schema

Track at minimum:
- `runs`
- `organizations_evaluated`
- `multi_signal_orgs`
- `hot_plus`
- `hot`
- `warm`
- `new_first_contact_executable`
- `queued_for_window`
- `manual_high_priority`
- `research_recipient`
- `territory_enrichment`
- `followup_1_eligibility`
- `duplicate_or_history_blocked`
- `already_contacted_waiting`
- `stale_or_uncertain`
- `cross_workstream_collisions_prevented`

This worker never increments provider-send counters.

## Unified daily schema

`metrics/daily/YYYY-MM-DD-unified.json` contains at least:

Research:
- `research.raw_signals`
- `research.semantic_candidates`
- `research.unique_organizations`
- `research.cheap_pass`
- `research.backlog_added`
- `research.duplicates`
- `research.stale_or_rejected`

Qualification:
- `qualification.route_closed`
- `qualification.deep_checked`
- `qualification.ready_added`
- `qualification.manual_route_required`
- `qualification.explicit_no_freelance`
- `qualification.route_failures`
- `qualification.blocked`
- `qualification.territory_enriched`

Dispatch:
- `dispatch.raw_ready_seen`
- `dispatch.executable_ready_seen`
- `dispatch.first_contacts_attempted`
- `dispatch.first_contacts_verified_sent`
- `dispatch.followup_1_verified_sent`
- `dispatch.unique_organizations_first_contacted`
- `dispatch.duplicates_blocked`
- `dispatch.retry_required`
- `dispatch.delivery_state_unknown`
- `dispatch.spain_first_contacts`
- `dispatch.italy_first_contacts`
- `dispatch.eu_language_compatible_first_contacts`

Manual action:
- `manual_action.opportunities_preserved`
- `manual_action.notifications_required`

The Unified Loop adds only the current run delta. It never reconstructs normal daily counters from full mailbox history.

## Backward-compatible dispatcher projection

`metrics/daily/YYYY-MM-DD-dispatcher.json` remains the fastest compatibility answer for automatic acquisition FIRST_CONTACT counts. Required fields include:
- `runs`
- `counted_run_ids`
- `emails_attempted` (compatibility alias for FIRST_CONTACT attempts)
- `emails_verified_sent` (FIRST_CONTACT only)
- `unique_organizations_sent` (FIRST_CONTACT only)
- `followup_1_verified_sent`
- `duplicates_blocked`
- `manual_route_required`
- `retry_required`
- `delivery_state_unknown`
- `spain_sends`
- `italy_sends`
- `eu_language_compatible_sends`
- `provider_uids` when compactly maintainable

Tests, internal/owner reports, replies/continuations and FOLLOWUP_1 do NOT increment `emails_verified_sent` or `unique_organizations_sent`.

## Provider / action-type counting

Professional acquisition Hostinger messages are classified by action type:
- `FIRST_CONTACT`
- `FOLLOWUP_1`
- `REPLY_CONTINUATION`
- `OWNER_AUTHORIZED_CONTINUATION`
- `INTERNAL_NOTIFICATION`
- `TEST_OR_ADMIN`

Only `FIRST_CONTACT` increments new-contact totals. FOLLOWUP_1 is tracked separately. Internal/test/reply/continuation traffic never inflates first-contact acquisition KPIs.

## Update rule

At the end of every operational run:
1. read today's owned metrics file if present;
2. reject duplicate `run_id`;
3. add only current-run delta;
4. persist using latest-SHA safe merge/write;
5. for provider sends, verify the provider UID/action type before incrementing;
6. confirm no provider UID is already represented.

Missing file -> create with zeros + current delta.

## Watchdog aggregate summary

Watchdog is the SOLE writer of `metrics/daily/YYYY-MM-DD-summary.json`.

On each run it should read current worker daily files, high-frequency/adaptive state, current READY/job queues, provider/global contact state and outcome/reply state, then write a compact aggregate containing at least:

Discovery:
- `discovery.raw_signals`
- `discovery.semantic_pass`
- `discovery.semantic_review`
- `discovery.semantic_reject`
- `discovery.unique_organizations`
- `discovery.current_source_ranking`
- `discovery.current_territory_harvest`
- `discovery.current_bottleneck`

Qualification:
- `qualification.hot_plus`
- `qualification.hot`
- `qualification.ready_added`
- `qualification.current_ready_count`
- `qualification.manual_route_required`
- `qualification.territory_enrichment_pending`

Execution:
- `execution.first_contacts_verified_sent`
- `execution.unique_organizations_first_contacted`
- `execution.followup_1_verified_sent`
- `execution.spain_first_contacts`
- `execution.italy_first_contacts`
- `execution.duplicates_blocked`
- `execution.delivery_state_unknown`

Outcomes:
- `outcomes.replies`
- `outcomes.positive_replies`
- `outcomes.interviews_or_calls`
- `outcomes.proposals`
- `outcomes.won`
- `outcomes.bounces`

Health:
- GitHub fanout freshness/success
- expected five-task state
- provider UID continuity
- reservation/lease health
- any unresolved anomaly

## Fast query policy

- “quante email/candidature automatiche oggi?” -> read dispatcher + LinkedIn daily files, count FIRST_CONTACT only unless user asks follow-ups too.
- “quanti follow-up oggi?” -> read LinkedIn + Unified `followup_1_verified_sent`.
- “quante opportunità trovate oggi?” -> read summary/discovery worker files.
- “quanti HOT/READY?” -> read cross-signal/unified/linkedin + current canonical queues.
- “come sta rendendo il motore?” -> read `summary.json` + `views/acquisition-performance.json` + source/territory views.
- 7/30/90-day stats -> aggregate daily JSON files, preserving historical schemas.
- mailbox/history scans -> fallback audit/recovery only when files are missing/inconsistent or explicitly requested.

## Migration-day rule

For 2026-09-04 preserve previously verified automatic-send baseline and all historical v1/v2 files. Architecture migration never authorizes double-counting. Provider UID/action type is the final idempotency key for actual sent messages.

## Manual-action preservation

Strong form/platform/human-required opportunities must be persisted with exact URL/route/reason and surfaced to owner. Their inability to auto-execute must never cause disappearance from metrics/state.

## Retention

Daily JSON files are permanent lightweight historical evidence. Never overwrite another date. They are designed for direct longitudinal aggregation without mailbox rescans.
