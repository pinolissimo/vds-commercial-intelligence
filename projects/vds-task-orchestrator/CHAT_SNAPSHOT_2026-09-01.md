# Chat Snapshot — VDS Task Orchestrator

Date: 2026-09-01

This file preserves the decisions, operating model, and configuration established in the ChatGPT conversation concerning the new scheduled commercial tasks.

## Why this was separated

The user explicitly requested that this automation thread be treated as a different, dedicated project because the local VDS application is already responsible for autonomous client/partner acquisition. The ChatGPT task layer is therefore documented separately to avoid mixing responsibilities.

## Key decisions established in conversation

1. The local VDS application is the primary autonomous research/acquisition engine.
2. Redundant ChatGPT discovery/outreach automations were disabled to free slots.
3. `VDS Reply Watch` was retained because monitoring inbound commercial replies adds value without duplicating the local engine.
4. Four ChatGPT automation slots were dedicated to a complementary high-throughput application system.
5. Discovery and dispatch were separated to reduce duplication and increase throughput.
6. A shared persistent GitHub queue and append-only dedup ledger were made mandatory.
7. Applications are accumulated in batches: **no dispatch until at least 10 fully executable `READY_TO_APPLY` candidates exist**.
8. Once the threshold is reached, the sole dispatcher executes the complete valid batch in the same run where safe.
9. Territory was expanded from Italy/Spain to relevant Italian- and Spanish-language opportunities across Europe.
10. The system was explicitly launched at full operating cadence.

## Current task topology

### VDS Spain Discovery
Schedule: hourly at `:00` Europe/Madrid.

Responsibilities:
- Spain discovery and qualification.
- Spanish-language / Spanish-market EU opportunities when genuinely relevant.
- No sending.
- Adds only fully verified executable candidates to shared READY queue.

### VDS Italy Discovery
Schedule: hourly at `:15` Europe/Madrid.

Responsibilities:
- Italy discovery and qualification.
- Italian-language / Italian-market European opportunities when genuinely relevant and cross-border eligible.
- No sending.
- Adds only fully verified executable candidates to shared READY queue.

### VDS High-Yield Discovery
Schedule: hourly at `:30` Europe/Madrid.

Responsibilities:
- High-conversion source families across Italy, Spain and relevant multilingual EU markets.
- Prioritizes recurring collaboration, agency overflow, white-label, WordPress/WPO/maintenance and similar demand.
- Tracks source yield and avoids simply duplicating country workers.
- No sending.

### VDS Batch Dispatcher
Schedule: hourly at `:45` Europe/Madrid.

Responsibilities:
- Sole application dispatcher.
- Reads shared queue.
- If executable queue < 10 -> no send.
- If executable queue >= 10 -> final revalidation, dedup, reservation, QA, send/submit valid batch, verify evidence, update GitHub ledger/index/report.

### VDS Reply Watch
Schedule: hourly during daytime operating window.

Responsibilities:
- Monitors commercial replies and delivery events.
- Prioritizes positive responses, referrals, requests for information, proposal/budget requests and call/meeting requests.
- Correlates replies to canonical commercial identities.

## Shared GitHub architecture

Canonical repository:
`pinolissimo/vds-commercial-intelligence`

Shared files:
- `data/it-es-partner-apply-ledger.jsonl`
- `views/it-es-partner-apply-recipients.json`
- `views/it-es-partner-apply-ready-queue.json`
- `reports/it-es-partner-apply-cumulative.md`

Dedicated project documentation:
- `projects/vds-task-orchestrator/README.md`
- `projects/vds-task-orchestrator/CHAT_SNAPSHOT_2026-09-01.md`

## Anti-duplication model

Primary invariant:

`DUPLICATE_FIRST_CONTACT_TOLERANCE = 0`

Canonical uniqueness concept:

`FIRST_CONTACT::<canonical_identity_id>`

The same organization must not receive a fresh first contact because a worker found:
- a different email;
- a different employee;
- another job listing;
- another office/city;
- another campaign;
- another source;
- another workstream.

Before admission to READY or before dispatch, check canonical CRM, suppression, prior campaigns, GitHub ledger/index/queue, Hostinger Sent and Gmail Sent.

Use per-identity reservation to prevent concurrent workers from claiming the same organization.

## Batch policy

Owner decision:

> Accumulate at least 10 eligible applications and then send them together.

Operational interpretation:
- threshold applies only to genuinely executable candidates;
- `MANUAL_ROUTE_REQUIRED`, stale, duplicate, ambiguous, weak-fit or legally blocked items do not count;
- do not lower quality to reach 10;
- once >=10 is reached, dispatcher should execute the entire currently valid batch rather than artificially stopping at 10.

## Target geography

### Spain
Nationwide systematic search with priority regions beginning with Catalonia and Madrid.

### Italy
Nationwide systematic search with priority regions beginning with Lombardia, Piemonte, Veneto and Emilia-Romagna.

### Italian-language / Italian-market Europe
Examples explicitly added:
- Ticino: Lugano, Bellinzona, Locarno, Mendrisio
- San Marino
- Koper / Capodistria
- Izola / Isola
- Piran / Pirano
- Pula / Pola
- Rovinj / Rovigno
- Rijeka / Fiume

### Spanish-language / Spanish-market Europe
Relevant multilingual hubs and remote-EU roles only when the role itself is genuinely Spanish-language, Spanish-market, Spain-facing, or explicitly seeks Spanish-speaking EU contractors.

### Multilingual EU hubs
Potential search cities include Brussels, Luxembourg, Amsterdam, Dublin, Berlin, Paris, Lisbon, Vienna, Prague and Warsaw, but only when Italian/Spanish market relevance or contractor eligibility is evidenced.

## Opportunity profile

Search for explicit current demand for:
- external/freelance web developers;
- recurring agency collaborators;
- WordPress/WooCommerce;
- frontend implementation;
- WPO/performance/Core Web Vitals;
- maintenance;
- UX/UI implementation;
- HTML/CSS/JavaScript/PHP where appropriate;
- web infrastructure/hosting;
- agency overflow;
- white-label development;
- project-based technical support.

## Application positioning

Use:

`Giuseppe Allocca — Visual Design Studio ES`

as an external freelance collaborator / technical partner available for ongoing work.

Portfolio:
https://www.visualdesignstudio.es/

Proprietary architecture may be mentioned only in terms of benefits such as performance, quality and maintainability.

## Sender and evidence

Commercial sender:
`info@visualdesignstudio.es`

Owner copy where supported:
`allocca.pino@gmail.com`

Hostinger Sent is authoritative evidence for email dispatch.

Ambiguous send state:
`DELIVERY_STATE_UNKNOWN`

Never blindly resend after ambiguous status.

## Estimated operational potential discussed

Planning estimates, not guarantees:
- conservative: 8–15 executable opportunities/day;
- realistic operating band: around 20–40 qualified applications/day when sufficient current demand exists;
- strong days: potentially 40–70, subject to quality and deliverability gates.

Initial positive-response planning hypothesis for highly targeted, demand-driven applications:
- approximately 2–5% commercially positive response rate;
- roughly 1 positive response per 20–50 strong applications.

These estimates must be superseded by actual VDS measurements as soon as sample size becomes meaningful.

## Optimization objective

Do not maximize raw email count.

Optimize:

`POSITIVE_REPLY / QUALIFIED_APPLICATION`

and ultimately:

`WON_REVENUE / APPLICATION`

Search effort should progressively move toward the source × country × sector × language-market combinations that generate actual replies, calls, proposals and wins.

## Current operational status

The user explicitly instructed the system to run at **full power / full operating cadence** and to keep the owner informed especially about positive replies and meaningful commercial events.

This snapshot is intended to be the stable project handoff for future conversations about these ChatGPT-managed tasks.
