# VDS Human Review — High-Value Recoverable Opportunities Protocol

Version: 1.1  
Effective: 2026-09-06

## Purpose

Preserve commercially strong opportunities that automation cannot safely execute, then convert recoverable blockers into a short, reasoned owner questionnaire so valuable opportunities are not lost merely because automation cannot decide a personal/business judgement call.

This queue is NOT a bypass around route, legal, opt-out, deduplication or explicit no-freelance/no-agency constraints. It is a recovery and strategic-review layer for SOFT-BLOCKED high-value opportunities.

Canonical outputs:
- `views/human-review-high-value.json` — machine-readable queue and owner-question state.
- `reports/human-review-high-value.md` — owner-facing ranked review list and pending questions.

## Entry gate

An opportunity enters `HUMAN_REVIEW_HIGH_VALUE` only when ALL are true:
1. canonical organization identity is resolved;
2. VDS fit or commercial value is HIGH/HOT/HOT+;
3. evidence is current enough to justify review, or there is a documented recurring/historical pattern with a current business-fit signal;
4. automation cannot safely execute FIRST_CONTACT for a SOFT reason;
5. no hard do-not-contact condition applies;
6. organization-level dedup does not show an existing first contact unless the item is explicitly a routed continuation/follow-up review.

Default review threshold: score >= 75, or lower only when strategic value is exceptional and explicitly justified.

## Review classes

Use one primary `review_class`:

- `MANUAL_ROUTE` — ATS/form/Easy Apply/platform required or unsupported by automation.
- `B2B_ALTERNATIVE` — internal hiring/job signal exists but an external overflow/white-label/B2B angle may be commercially legitimate.
- `PARTNER_ANGLE` — organization sells or operates white-label/subcontracting/partner services but does not explicitly request external capacity; human judgement needed on reciprocal partnership pitch.
- `ROUTE_AMBIGUITY` — strong fit and organization is contactable, but exact application/collaboration route is unclear or generic contact may be inappropriate for automated use.
- `CONTRADICTORY_EVIDENCE` — evidence supports strong fit but statements about external collaboration, location, contract model or route conflict.
- `HISTORICAL_RECURRING_SIGNAL` — stale/closed explicit opportunity, but credible evidence suggests recurring freelance/partner usage and current business fit.
- `DECISION_MAKER_REVIEW` — a relevant public decision maker exists but automated route authority is unresolved.
- `CROSS_BORDER_REVIEW` — strong fit but tax, contracting, language, location or cross-border execution requires owner judgement.
- `OWNER_BUSINESS_DECISION` — all external facts are sufficiently resolved but execution depends on an owner-only preference/commitment such as rate, availability, travel, employment-vs-freelance model, truthful seniority wording, or willingness to use a manual route.

## Hard exclusions — NEVER convert to outreach by human-review logic

Do NOT place an item in the recoverable queue when the authoritative source contains:
- explicit `no freelancers`, `no contractors`, `no agencies`, `no external collaborators`, or equivalent;
- opt-out, unsubscribe, rejection with no invitation to recontact, or `DO_NOT_CONTACT` state;
- legal/procurement restriction that clearly forbids the proposed contact/contract model;
- unresolved or false organization identity;
- guessed/derived email as the only contact route;
- stale/closed opportunity with no independent current business-fit signal;
- duplicate first contact to the same canonical organization, unless the review is specifically a compliant continuation of an existing thread.

These remain `HARD_REJECT` / `DO_NOT_CONTACT` / `ALREADY_CONTACTED` and must not be reframed as a workaround.

## Owner-question rule — mandatory for recoverable blockers

Every NEW high-value soft-blocked item must contain an `owner_question_pack` unless the only correct action is already an obvious `MANUAL_APPLY` with no owner judgement required.

Questions MUST concern facts or decisions only the owner can authoritatively provide. Examples:
- willingness to submit through a manual form/platform;
- willingness to accept employment, hybrid/on-site work, travel or a specific geography;
- preferred/acceptable freelance, P.IVA/autónomo, project, retainer or employment model;
- rate, daily rate or weekly availability when the form requires owner-supplied commercial terms;
- whether a stated seniority/years/leadership claim is truthfully supportable from the owner's actual experience;
- permission to use a particular approved CV/portfolio asset when owner approval is required;
- whether the owner wants a legitimate B2B alternative angle explored when a vacancy itself is not freelance.

Questions MUST NOT ask the owner to research facts that the system can determine from authoritative sources. The engine must first exhaust reasonable research for current status, company identity, route, recipient authority, freshness, public requirements, platform instructions, legal/channel state and prior-contact history.

### Question-pack schema

Each record should contain:

```json
"owner_question_pack": {
  "review_state": "AWAITING_OWNER_ANSWER",
  "questions": [
    {
      "question_id": "<canonical-key>:Q1",
      "question": "<one precise decision question>",
      "answer_type": "YES_NO|CHOICE|NUMBER|FREE_TEXT",
      "choices": [],
      "why_it_matters": "<specific gate affected>",
      "unlock_if": "<what answer could make possible>",
      "owner_answer": null,
      "answered_at": null
    }
  ],
  "questioned_at": null,
  "last_material_change_at": "<timestamp>",
  "next_gate_after_answer": "REVERIFY_AND_RECLASSIFY"
}
```

Use 1–3 questions maximum per opportunity. Prefer one decisive question over several weak questions. Do not ask multiple questions whose answers would not change the next action.

`review_state` values:
- `AWAITING_OWNER_ANSWER`
- `PARTIALLY_ANSWERED`
- `ANSWERED_RECHECK_REQUIRED`
- `RESOLVED_SEND_NOW`
- `RESOLVED_MANUAL_APPLY`
- `RESOLVED_HOLD`
- `RESOLVED_REJECT`

## Required record schema

Every queue record should contain, where available:
- `canonical_identity_key`
- `organization`
- `country`
- `website`
- `opportunity_url`
- `source_urls`
- `evidence_summary`
- `evidence_strength`
- `signal_date`
- `score`
- `priority`
- `why_high_value`
- `automatic_block_reason`
- `review_class`
- `safe_alternative_angles`
- `known_public_contacts`
- `authoritative_routes`
- `decision_maker`
- `language`
- `dedup_status`
- `do_not_bypass_constraints`
- `recommended_human_checks`
- `recommended_action`
- `owner_question_pack`
- `owner_decision` (`PENDING`, `APPROVE_OUTREACH`, `MANUAL_APPLY`, `HOLD`, `REJECT`)
- `created_at`
- `updated_at`
- `source_task`

## Human-review presentation

The owner-facing report must rank the queue by expected commercial value and show for each item:
1. why it is attractive;
2. exactly why automation stopped;
3. what is fact vs inference;
4. what route/contact is publicly verified;
5. one or more SAFE possible angles, clearly labelled as hypotheses;
6. the 1–3 owner-only questions whose answers materially affect execution;
7. what each answer would unlock or rule out;
8. a suggested outreach type if approved: `APPLICATION`, `B2B_OVERFLOW`, `PARTNERSHIP`, `MANUAL_FORM`, or `NO_ACTION`.

Do not draft or send the final message automatically from this queue before the owner answers the material question(s). Owner review is required first.

## Answer handling — mandatory

When the owner answers a question:
1. persist the exact answer against `question_id` without reinterpretation;
2. set `ANSWERED_RECHECK_REQUIRED` when all material questions are answered;
3. re-read current authoritative evidence, dedup/suppression/reservation state and route before any action;
4. reclassify to exactly one operational outcome: `SEND_NOW`, `MANUAL_APPLY`, `WAIT_RESEARCH`, or `REJECT`;
5. never treat an owner answer as permission to bypass legal/channel/dedup/route constraints;
6. if the answer resolves the only soft blocker and all live hard gates pass, allow the normal sender to execute; do not create a separate sender.

## Retroactive recovery

Execution workers should inspect recent `REJECTED`, `HOLD`, `MANUAL_ROUTE_REQUIRED`, `REVIEW_REQUIRED`, `ROUTE_UNRESOLVED`, `CONTRACT_MODEL_UNCLEAR`, `WAIT_RESEARCH`, and equivalent states and promote qualifying SOFT-BLOCKED high-value items into this queue.

Backfill `owner_question_pack` for existing high-value PENDING items when the missing decision is owner-only. Do not repeatedly question items that have not materially changed.

Never promote hard exclusions.

## Lifecycle

`DISCOVERED -> VERIFIED_HIGH_VALUE -> SOFT_BLOCKED -> HUMAN_REVIEW_HIGH_VALUE -> AWAITING_OWNER_ANSWER -> ANSWERED_RECHECK_REQUIRED -> operational outcome`

Owner decision paths:
- answer permits normal automatic route -> live recheck -> `SEND_NOW` if every hard gate passes;
- `MANUAL_APPLY` -> preserve exact form/ATS/platform instructions;
- `HOLD` -> retain with review date/trigger if useful;
- `REJECT` -> close with reason.

## Watchdog behavior

`VDS Performance + Reply Watch` must surface only NEW or materially changed high-value human-review items, avoiding repeated alerts for unchanged records.

For every surfaced item it must present, in concise Italian:
- organization/opportunity;
- score/priority and why it matters;
- exact automatic blocker;
- only the unanswered owner questions, numbered;
- what becomes possible if the answer resolves the blocker.

If several items are pending, rank by commercial value and ask about the strongest first. A single alert may include multiple opportunities, but no more than 5 at once. Preserve lower-ranked items in the queue for later review.

The watchdog should alert immediately for a NEW HOT+/score >= 90 recoverable item; lower-priority items can be grouped into the next review batch/report. Owner alert may be surfaced in ChatGPT and, when configured/available, emailed to `allocca.pino@gmail.com` with subject `VDS — Revisione umana opportunità bloccate`.

## Principle

The system must distinguish:

**AUTOMATION CANNOT SAFELY SEND**

from

**THE OPPORTUNITY HAS NO COMMERCIAL VALUE.**

High-value soft blocks are preserved and actively escalated into answerable owner decisions; hard prohibitions are respected and never bypassed.
