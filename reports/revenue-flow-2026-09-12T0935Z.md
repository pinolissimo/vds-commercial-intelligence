# VDS Revenue Flow — 2026-09-12 09:35Z

## Funnel outcomes

- Teslhub: QUALIFIED_POSITIVE_REPLY → MINI_PROPOSAL_SENT → CALL_INTENT. Inbound UID 1444 explicitly requested a first idea and offered phone/WhatsApp as next step. Reply provider UID 461 verified.
- XTechAI: QUALIFIED_POSITIVE_REPLY / REFERRAL_TO_PARTNER_ONBOARDING. Inbound UID 1443 confirms VDS fits their external collaborator network and routes to official Partner Network registration. Manual onboarding required.
- Cosmotech: outbound provider UID 459 hard-bounced; inbox bounce UID 1445, 550 5.4.1 recipient rejected. Does not count as successful outbound. Never blind retry.

## New first contact

### LDP Strategic Advisory
- Decision: SEND_NOW → VERIFIED_EMAIL_SENT
- Provider UID: 462
- Recipient: info@ldpadvisory.it
- Archetype: AGENCY_EXTERNAL_CAPACITY
- Variant: VALUE_MICRO_COMMITMENT
- Micro CTA: SEND_2_RELEVANT_EXAMPLES
- Evidence: official collaboration page welcomes external consultants/specialists; advisory model builds flexible teams and coordinates outside experts.

## Discovery decisions

- BP Nexus — REJECT_DUPLICATE. Explicit freelance/subcontracting route is strong, but Hostinger Sent shows UID 171 and 172.
- Agomir Comunicare — REJECT_DUPLICATE. Explicit partner/freelance web development/UX-UI need; Sent UID 350.
- Web Crew — REJECT_DUPLICATE. Explicit external freelance use; Sent UID 228 and 232.
- Left Handed Studio — REJECT_DUPLICATE. Exact Web Developer Front-end candidacy route; Sent UID 178 and duplicate UID 337.
- Petr Sejba agency — MANUAL_APPLY. Strong active freelance web designer/developer opportunity; official workflow explicitly requires collaboration application form.
- InClinic — MANUAL_APPLY. Web developer opening, but application workflow/form/email protection prevents a safely verified explicit address in this run.
- Giango Comunicazione — WAIT_RESEARCH. Official email is valid and no provider duplicate, but the currently exposed roles are content/account/graphic oriented; web-development fit is not strong enough for SEND_NOW.
- Modular Tres — REJECT. Collaboration is construction/technical trades, not VDS commercial fit.
- Ikergune — MANUAL_APPLY. Collaboration network including EU projects exists, but official route is form and there is no sufficiently specific current web/dissemination purchase signal.
- Coditalia — REJECT. Primarily sells white-label development capacity to agencies rather than showing demand for external VDS capacity.
- UPCOM — MANUAL_APPLY. Collaboration page uses mandatory form.
- Haz Conexión — REJECT. Collaboration offer is social/content focused, not a verified buyer need for VDS web production.

## Counts

- Serious candidates evaluated: 12
- Direct-email harvest evaluated: 7
- SEND_NOW: 1
- Provider-verified FIRST_CONTACT: 1
- Provider-verified commercial replies/funnel advancement: 2 (Teslhub, XTechAI)
- MANUAL_APPLY: 4
- WAIT_RESEARCH: 1
- REJECT: 6
- Duplicates: 4
- Route failures: 0
- Hard bounce corrections detected: 1 (Cosmotech UID 459 / bounce UID 1445)
- Delivery state unknown: 0

## Archetype / A-B

New first contact:
- AGENCY_EXTERNAL_CAPACITY: 1
- VALUE_MICRO_COMMITMENT: 1
- CREDENTIALS_CLASSIC: 0

Downstream:
- Teslhub: SME_WEB_IMPROVEMENT; VALUE_MICRO_COMMITMENT path has produced a qualified positive reply and explicit mini-proposal/call progression.
- XTechAI: AGENCY_EXTERNAL_CAPACITY; prior external-capacity positioning produced a qualified acceptance into the partner onboarding path.

## Provider state

Provider evidence is authoritative. A reconciliation payload for UID 459, 461 and 462 was written to `state/provider-outbound-live-reconcile-2026-09-12T0935Z.json`. The live overlay itself was not replaced because the available GitHub write action requires whole-file replacement and an unsafe replacement could overwrite concurrent Watchdog/worker writes.
