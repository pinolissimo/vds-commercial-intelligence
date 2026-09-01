# VDS Task Orchestrator

Dedicated project area for the ChatGPT-managed commercial automations created on 2026-09-01.

## Purpose

This project isolates the **ChatGPT automation layer** from the local VDS client-acquisition application and from the broader commercial-intelligence architecture.

The local VDS application remains the main autonomous client/partner research engine. This project documents and governs only the **ChatGPT scheduled task system** used for complementary job/partner acquisition and reply monitoring.

## Active architecture

Five active automation slots are currently allocated as follows:

| Minute | Task | Responsibility |
|---|---|---|
| `:00` | VDS Spain Discovery | Spain + Spanish-language EU opportunity discovery/qualification |
| `:15` | VDS Italy Discovery | Italy + Italian-language EU opportunity discovery/qualification |
| `:30` | VDS High-Yield Discovery | Cross-market high-yield multilingual EU opportunity discovery |
| `:45` | VDS Batch Dispatcher | Sole dispatcher; sends/submits only when executable READY queue >= 10 |
| hourly 08:00–22:00 | VDS Reply Watch | Detects and classifies commercial replies, with priority to positive replies |

Each discovery worker runs at most once per hour, but schedules are staggered so the acquisition system performs a meaningful control-loop event roughly every 15 minutes.

## Shared queue

Canonical shared queue:

`views/it-es-partner-apply-ready-queue.json`

Only fully verified, deduplicated, executable opportunities count toward the batch threshold.

### Batch rule

- If executable `READY_TO_APPLY < 10`: send nothing.
- If executable `READY_TO_APPLY >= 10`: dispatcher performs final checks and executes the entire valid batch in the same run when safe.
- Weak, stale, ambiguous, duplicate, legally blocked, or non-executable opportunities must never be used to reach the threshold.

## Search scope

### Spain / Spanish-language market

Primary Spain coverage:
- Catalonia
- Madrid
- Comunitat Valenciana
- Basque Country
- Andalusia
- Galicia
- Asturias / Cantabria
- Murcia
- Aragón
- Castilla y León
- Castilla-La Mancha
- Balearic / Canary Islands
- remaining Spanish provinces

Expanded EU coverage when the actual opportunity is explicitly Spanish-language, Spanish-market, Spain-facing, or open to Spanish-speaking EU contractors, including major multilingual hubs such as Brussels, Luxembourg, Amsterdam, Dublin, Berlin, Paris and Lisbon.

### Italy / Italian-language market

Primary Italy coverage:
- Lombardia
- Piemonte
- Veneto
- Emilia-Romagna
- Lazio
- Toscana
- Liguria
- Campania
- Puglia
- Sicilia
- remaining Italian regions

Expanded Italian-language / Italian-market coverage includes, where cross-border eligibility is explicit:
- Ticino: Lugano, Bellinzona, Locarno, Mendrisio
- San Marino
- Koper / Capodistria
- Izola / Isola
- Piran / Pirano
- Pula / Pola
- Rovinj / Rovigno
- Rijeka / Fiume
- wider EU multilingual hubs only when the opportunity genuinely targets Italian speakers/market or accepts Italian-speaking EU contractors

## Target opportunities

Prioritize current explicit demand for:
- freelance / external web developers
- WordPress / WooCommerce
- frontend implementation
- HTML / CSS / JavaScript / PHP where appropriate
- WPO / performance / Core Web Vitals
- web maintenance
- UX/UI implementation
- hosting / web infrastructure
- agency overflow
- white-label web production
- ongoing / recurring collaborations
- project-based external technical support

Primary organization types:
- web/digital agencies
- communication/branding studios
- software houses
- ecommerce agencies
- marketing agencies
- IT/web companies
- hosting/maintenance providers
- WPO/accessibility specialists
- tourism/hospitality digital suppliers
- SaaS/startups with external web-production demand

## Positioning

Applications position:

**Giuseppe Allocca / Visual Design Studio ES**

as an external freelance collaborator / technical partner, also available for ongoing collaboration.

Main portfolio:

https://www.visualdesignstudio.es/

The proprietary VDS architecture may only be described at benefit level: performance-oriented, quality-focused, maintainable, internally engineered workflow. No proprietary internals may be disclosed.

## CV policy

When a vacancy or route requests a CV or clearly benefits from one:
- use the latest user-provided master in the correct language;
- tailor only with truthful evidence;
- preserve the editable master;
- send PDF only unless DOCX is explicitly required;
- never invent skills, seniority, years, rates, availability, certifications, language level, tax status, or technologies.

## Global dedup invariant

Hard invariant:

`FIRST_CONTACT::<canonical_identity_id>` must be unique.

Different email, person, listing, office, geography, campaign, or workstream does **not** reset first-contact history.

Before queue admission or dispatch, reconcile:
- canonical CRM
- campaign/workstream history
- suppression registry
- GitHub append-only ledger
- active ready queue
- contacted-recipient index
- Hostinger Sent
- Gmail Sent

Existing contact evidence -> `ALREADY_CONTACTED`.
Ambiguous identity/history -> `REVIEW_REQUIRED`.
Never guess an email.

## Concurrency model

Use per-identity reservations, not a global lock.

Independent organizations may progress in parallel or rapid sequence. The same canonical organization identity must never be processed concurrently by two workers.

## Canonical GitHub state

- `data/it-es-partner-apply-ledger.jsonl` — append-only event ledger
- `views/it-es-partner-apply-recipients.json` — deduplicated contacted-organization index
- `views/it-es-partner-apply-ready-queue.json` — persistent executable queue
- `reports/it-es-partner-apply-cumulative.md` — cumulative human-readable report

## Dispatch sequence

`VERIFY_FINAL -> GLOBAL DEDUP -> CONFIRM RESERVATION -> PERSONALIZATION QA -> CV QA -> SEND/SUBMIT -> VERIFY SENT/EVIDENCE -> LEDGER UPDATE -> RECIPIENT INDEX UPDATE -> QUEUE REMOVE`

Email route:
- sender: `info@visualdesignstudio.es`
- BCC owner copy: `allocca.pino@gmail.com` where supported
- one-to-one only
- Hostinger Sent is authoritative send evidence
- ambiguous send state => `DELIVERY_STATE_UNKNOWN`; never blindly resend

Form/platform route:
- use the exact official application route when executable by available tools
- if it cannot be executed, mark `MANUAL_ROUTE_REQUIRED`
- do not force a generic email around a required platform/form
- manual-route items do not count toward the executable threshold of 10

## Reply monitoring

`VDS Reply Watch` remains active as a separate condition-watch task.

Priority events:
- positive reply
- referral
- request for information
- proposal/budget request
- call/meeting request
- routing to another decision-maker
- bounce
- negative response

Positive or materially actionable responses must be surfaced to the owner immediately.

## Optimization principle

Do not optimize for raw number of emails.

Primary commercial metric:

`POSITIVE_REPLY / QUALIFIED_APPLICATION`

Ultimate metric:

`WON_REVENUE / APPLICATION`

Source allocation should progressively shift toward source × country × sector × language-market combinations producing better downstream replies, proposals, calls and wins.

## Planning assumptions

Initial planning target (not a guarantee):
- realistic qualified send capacity: roughly 20–40 applications/day when enough current executable demand exists;
- strong days may exceed this;
- quality/dedup/route integrity always override volume.

Initial positive-response planning hypothesis for highly targeted demand-driven applications: approximately 2–5%, corresponding roughly to 1 commercially positive response per 20–50 high-quality applications. This is a planning assumption only and must be replaced by measured VDS data as soon as enough observations exist.

## Status

System launched at full operating cadence on 2026-09-01.

This directory is the dedicated project record for the ChatGPT-managed automation layer and must remain separate conceptually from the local VDS acquisition engine and other VDS repositories/projects.
