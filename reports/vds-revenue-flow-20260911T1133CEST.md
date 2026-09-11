# VDS Revenue Flow — 2026-09-11 11:33 CEST

## Outcome

- Serious candidates decisioned: 45
- Direct-email / route harvest evaluated: 31
- SEND_NOW: 1
- Provider-verified FIRST_CONTACT: 1
- MANUAL_APPLY: 10
- WAIT_RESEARCH: 8
- REJECT: 26
- Provider/canonical duplicates inside REJECT: 8
- Route failures / application-only routes: 5
- DELIVERY_STATE_UNKNOWN: 0

## Provider-verified outbound

- Provider UID: 425
- Organization: Visibelle Digital
- Canonical identity: org:visibelledigital.com
- Recipient: contact@visibelledigital.com
- Subject: WordPress / Divi web production support
- Sent at: 2026-09-11T09:34:52Z
- Archetype: AGENCY_EXTERNAL_CAPACITY
- Variant: CREDENTIALS_CLASSIC
- Micro CTA: DISCUSS_CURRENT_WEB_WORKLOAD
- BCC owner: true
- Attachments: 0
- Provider Sent verification: PASS
- Immediate bounce check: no bounce observed in INBOX after send

## Strong fresh evidence used

Visibelle Digital: current public site invites portfolios and explicitly lists a Web Developer profile with Divi, WordPress, custom HTML/CSS/JS and performance/conversion-first builds. Official route contact@visibelledigital.com. Pre-send Hostinger Sent search returned zero matches; repository search for organization/address returned zero matches.

## Duplicate blocks confirmed provider-side

- ReMedia / rleonzi@remediagroup.it — prior Sent UID 357
- So Design Online / support@sodesign.online — prior Sent UIDs 149 and 396
- Logorapid / trabajo@logorapid.com — prior Sent UID 170
- Boneluv / hola@boneluv.com — prior Sent UID 124
- Mobyleshop / infovistalegre@mobyleshop.com — prior Sent UID 203
- Additional canonical duplicates identified from live/audit history: Studio Magnani, eFarm Group, Lucasweb / IAIblue family already contacted

## Manual-apply examples

- The Hoop Studio — application-only route
- Workana WordPress collaboration opportunities — platform route
- R3volution — application form
- VueloIV — Apply route
- Adviva — candidacy form
- Amalthea — route address not safely extractable; no guessing
- Molecole — application form
- Haz Marca — application form
- Visilay — contact route masked/not safely extractable
- Laborda.digital — profile submission form

## WAIT_RESEARCH blockers

Typical blockers: no sufficiently current buyer-side external-capacity trigger, route not authoritative enough, or current evidence not strong enough to justify automatic first contact. One bounded research attempt only per candidate.

## Archetype mix

- AGENCY_EXTERNAL_CAPACITY: 35
- SME_WEB_IMPROVEMENT: 1
- EU_DISSEMINATION_SPECIALIST: 9

## A/B commercial test

- CREDENTIALS_CLASSIC sent: 1 (UID 425)
- VALUE_MICRO_COMMITMENT sent: 0

No fit/route/dedup gate was relaxed for experiment balance.

## Downstream funnel

No new professional inbound after INBOX UID 1430 during this run. Therefore no new qualified positive reply, referral, call/interview, proposal, won, or revenue event was attributed in this cycle.

## Live provider bridge

The large `state/provider-outbound-live.json` could not be safely replaced because the connector returned truncated full-file content. To avoid destructive overwrite, UID 425 was queued idempotently at `state/provider-outbound-reconcile-20260911T093452Z-uid425.json`. Provider Sent UID 425 remains authoritative and MUST NOT be resent. Reconciliation commit: `2f5b36addd6fef9969d85b6b1735134f443d3fcd`.
