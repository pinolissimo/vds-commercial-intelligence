# VDS Human Review — High-Value Recoverable Opportunities Protocol

Version: 1.0  
Effective: 2026-09-04

## Purpose

Preserve commercially strong opportunities that automation cannot safely execute, so the owner can perform a reasoned human review and decide whether there is a legitimate, truthful and policy-compliant way to contact the organization.

This queue is NOT a bypass around route, legal, opt-out, deduplication or explicit no-freelance/no-agency constraints. It is a recovery and strategic-review layer for SOFT-BLOCKED high-value opportunities.

Canonical outputs:
- `views/human-review-high-value.json` — machine-readable queue.
- `reports/human-review-high-value.md` — owner-facing ranked review list.

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
6. what the owner must verify before contact;
7. a suggested outreach type if approved: `APPLICATION`, `B2B_OVERFLOW`, `PARTNERSHIP`, `MANUAL_FORM`, or `NO_ACTION`.

Do not draft or send the final message automatically from this queue. Owner review is required first.

## Retroactive recovery

Discovery/ranking workers should also inspect recent `REJECTED`, `HOLD`, `MANUAL_ROUTE_REQUIRED`, `REVIEW_REQUIRED`, `ROUTE_UNRESOLVED`, `CONTRACT_MODEL_UNCLEAR`, and equivalent states and promote qualifying SOFT-BLOCKED high-value items into this queue.

Never promote hard exclusions.

## Lifecycle

`DISCOVERED -> VERIFIED_HIGH_VALUE -> SOFT_BLOCKED -> HUMAN_REVIEW_HIGH_VALUE -> owner decision`

Owner decision paths:
- `APPROVE_OUTREACH` -> return to normal route/dedup/pre-send gates; no safety gate is waived.
- `MANUAL_APPLY` -> preserve exact form/ATS/platform instructions.
- `HOLD` -> retain with review date/trigger if useful.
- `REJECT` -> close with reason.

## Watchdog behavior

`VDS Performance + Reply Watch` should surface only NEW or materially changed high-value human-review items, avoiding repeated alerts for unchanged records.

## Principle

The system must distinguish:

**AUTOMATION CANNOT SAFELY SEND**

from

**THE OPPORTUNITY HAS NO COMMERCIAL VALUE.**

High-value soft blocks are preserved for human reasoning; hard prohibitions are respected and never bypassed.
