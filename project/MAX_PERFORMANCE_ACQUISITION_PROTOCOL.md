# VDS Max-Performance Acquisition Protocol v1.0

Effective: 2026-09-04

## Objective

Maximize the probability of generating paid web-development work for Visual Design Studio by optimizing the entire funnel, not raw lead volume.

North-star funnel:

`DISCOVERED -> SEMANTIC_PASS -> VERIFIED -> HOT -> READY -> SENT -> REPLIED -> POSITIVE -> MEETING -> PROPOSAL -> WON`

The system must optimize expected downstream value while preserving factual accuracy, route integrity, platform rules and `NO_DUPLICATE_FIRST_CONTACT_GLOBAL`.

## Mandatory adaptive inputs

Every active discovery/ranking/execution task MUST read when present:
- `views/high-frequency-discovery-latest.json`
- `views/high-frequency-discovery-qualified-seeds.json`
- `views/search-source-performance.json`
- `views/territory-yield-radar.json`
- `views/acquisition-performance.json`
- `config/adaptive-search-runtime.json`
- `views/cross-signal-opportunities.json`
- `views/provider-contact-suppression-index.json`
- `project/GLOBAL_ORGANIZATION_DEDUP_PROTOCOL.md`

## Capacity allocation

Default discovery/research budget:
- 70% exploitation: highest current territory x source x intent combinations;
- 20% exploration: under-sampled Spain/Italy regions/provinces/source families;
- 10% strategic reserve: newly emerging high-intent signals, EU-project timing, direct-email vacancies or reply-driven opportunities.

The allocation is adaptive, never a rigid quota. Quality gates never weaken to fill volume.

## Territory lifecycle

Use the Territory Yield Radar lifecycle:
- `EXPLORATION`: establish a meaningful sample;
- `HARVEST`: concentrate search while marginal downstream yield remains high;
- `COOLDOWN`: pause concentrated effort after saturation or harvest cap;
- `REVISIT`: return after cooldown and resample;
- `LOW_YIELD_VERIFIED`: retain only a small exploration floor.

Never permanently abandon Spain or Italy. Country -> region -> province -> city/cluster enrichment should be verified whenever it materially improves attribution.

## Source and query optimization

Do not optimize for `raw_signals` alone. Attribute each material candidate using, where available:
- `source_id` / source family;
- `query_id` or search intent;
- country/region/province/city;
- segment (`AGENCY_WHITE_LABEL`, `JOB_DIRECT`, `EU_PROJECT`, `WPO_MAINTENANCE`, `LOCAL_CLIENT`, other);
- route type;
- message/CTA variant;
- discovery and send timestamps.

Prefer sources/queries producing VERIFIED/HOT/READY/SENT/POSITIVE outcomes. Penalize high noise, stale results, duplicates, inaccessible routes and geo incompatibility.

## Semantic gate before deep verification

High-frequency RAW signals MUST pass a cheap semantic intent gate before consuming expensive verification capacity.

A keyword match inside a description is insufficient. Evaluate:
1. job/opportunity title and role family;
2. core requested capability;
3. Spain/Italy/EU-remote compatibility;
4. freshness;
5. contract/external-collaborator compatibility;
6. negative/mismatch role signals;
7. authoritative source/route potential.

Examples:
- `Remote Office Assistant` mentioning WordPress in body -> normally REJECT/HOLD;
- `Frontend / WordPress Developer` -> promote;
- US-only .NET/Angular role without EU eligibility -> reject despite HTML/CSS keywords.

## Commercial-priority hierarchy

Highest expected value signals:
1. explicit current external/freelance/white-label/overflow demand + direct authoritative route;
2. agency recurring capacity / subcontracting / production partner demand;
3. high-fit direct-email job/collaboration opportunity;
4. early-stage funded EU project with Communication/Dissemination/web ownership evidence;
5. current maintenance/WPO/rebuild problem with a credible buyer;
6. cold generic company fit without explicit demand.

Recurring work potential receives priority over low-value one-off work when other gates are similar.

## Messaging and CTA optimization

Every first contact must be opportunity-specific and use one clear low-friction CTA.

Recommended CTA by segment:
- Agency/white-label: propose starting with one small task/sprint/project to test operational fit;
- Job/direct vacancy: ask for inclusion in the selection / short call and link the most relevant CV/portfolio;
- EU project: offer a concise discussion of web/dissemination scope and implementation needs;
- WPO/maintenance: offer a short evidence-based priority assessment, not an open-ended free consultancy;
- End client: connect one concrete business outcome to a focused next step.

Do not use generic self-description where a specific verified need is available.

## Controlled message experiments

Track `message_variant` and `cta_variant`. Change only one material variable at a time. Do not declare a winner on tiny samples; use at least 20 comparable sends per arm where feasible and prioritize positive-response quality over opens or raw replies.

## Follow-up policy

Owner authorization: one professional follow-up is permitted for eligible HOT/HOT+ direct-email first contacts when all conditions hold:
- exactly one verified first contact exists;
- no inbound reply, bounce, opt-out, rejection, referral closure, manual hold or owner stop;
- opportunity remains current/relevant;
- at least 6 business days have elapsed since first contact;
- no prior follow-up exists;
- authoritative recipient is still valid;
- global organization history and provider state are coherent.

Follow-up must be short, contextual, non-pressuring and preferably in the existing thread. Record action as `FOLLOWUP_1`, never as a new FIRST_CONTACT. Maximum automatic follow-ups = 1. Never follow up an explicit rejection/opt-out/bounce.

## Anti-dup / provider performance

Routine dedup is JSON-first using:
- global organization index;
- global sent-email index;
- provider-contact suppression index;
- workstream history;
- active organization reservations.

Hostinger Sent is authoritative and is queried only for targeted reconciliation/recovery and post-send verification when indexed state is coherent. Gmail is notifications/BCC only.

## Performance KPIs

Track at minimum:
- raw -> semantic-pass rate;
- semantic-pass -> verified rate;
- verified -> HOT rate;
- HOT -> READY rate;
- READY -> verified-send rate;
- sent -> reply rate;
- sent -> positive-reply rate;
- positive -> meeting/proposal/won rate;
- duplicate/stale/route-failure rates;
- time-to-READY;
- time-to-send;
- source x territory x segment downstream yield;
- contacts per positive reply;
- WON attribution when known.

## Continuous improvement rule

Every Watchdog cycle should inspect deltas, not blindly recompute history. A sustained performance regression must produce a concrete diagnosis and a safe adjustment to source weights, territory allocation, semantic filters, route verification or messaging. Never improve a vanity metric by lowering quality.
