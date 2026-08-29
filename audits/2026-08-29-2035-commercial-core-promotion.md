# VDS7 QA Audit — Commercial Core promotion — 2026-08-29 20:35 Europe/Madrid

**Status:** PASS_WITH_RESIDUAL

## Scope
Delta audit for the Commercial Core mass-benchmark promotion into the canonical VDS commercial CRM. Scope is limited to qualification/persistence/deduplication safety. No email, application form, phone call or other first-contact action was performed.

## Commercial Core verification
- Core branch checkpoint: `0ef7b7ea65e7468dde34bee2626fc49533f36728`.
- Core CI run `33265091828`: PASS on Python 3.11, 3.12 and 3.13; compile and full pytest suite passed on every matrix job.
- VDS Mass Benchmark run `33265091829`: PASS.
- Live targets attempted/acquired/intelligence-completed: 7/7/7.
- Qualified: 7; review required: 0.
- Unsafe qualified: 0; errors: 0; unexpected errors: 0; violations: none.
- Safety gate: PASS.
- Model calls: 0; API cost: 0.
- Benchmark run id: `vds-mass-gh-33265091829-1`; report id: `bench_d0dedb9915ace593c37604b5d3ddcf83`.

## Fresh global duplicate gate
Immediately before CRM promotion, Onebit, Zmot Lab and Global Service Impresa were rechecked against:
1. canonical repository identity/search state;
2. `governance/suppression-registry.json`;
3. `governance/suppression-emergency-2026-08-28.json`;
4. Gmail Sent;
5. official Hostinger `info@visualdesignstudio.es` Sent folder.

Result: no first-contact/suppression match for the three promoted organizations at the 20:32 Europe/Madrid gate. This does not remove the mandatory requirement to re-run global dedupe immediately before any future first contact.

## Findings and resolutions

### Zmot Lab — canonical reference parity restored
The 20:03 QA audit correctly blocked Zmot because the lead referenced `OPP-IT-ZMOTLAB-SENIOR-PIVA` without a canonical opportunity record. This promotion creates the opportunity and restores the lead reference in the same atomic commit. The previous `QA_CORRECTION` event remains preserved; a new `QA_RESOLUTION` event records why the block can be removed.

### Onebit — structural freshness resolved without laundering an old event
Onebit's page carries an original publication date of 2025-05-02. The core does not overwrite or hide that date. The current official page still explicitly presents a freelance-P.IVA overflow collaboration model, so the claim is typed `structural_need` and evaluated from current observation. Ordinary time-sensitive `need`/hiring/procurement claims continue to prefer their publication timestamp and cannot be refreshed merely by recrawling.

### Global Service Impresa — current explicit role
The current official careers page explicitly presents a remote freelance developer/creative project collaboration covering WordPress, HTML/CSS/JS, e-commerce, custom software, graphics and integrations, with possible continuing collaboration. It passed the deterministic benchmark without review findings.

### Contact-route safety
No email address was guessed or reconstructed for Onebit or Global Service Impresa. Onebit retains official form/phone routes; Global Service retains its official application form/phone. Zmot stores `team@zmotlab.it` because it is explicitly published on the official role page.

## Canonical pipeline after promotion
- partner accounts: 58
- opportunities: 64
- canonical contacted opportunities: 27
- qualified not contacted opportunities: 37
- current-day verified first-contact organizations: 2
- current-day duplicate first-contact violations: 0
- positive replies/referrals requiring user action: 1
- meetings: 0
- proposals: 0
- won: 0
- won revenue: EUR 0

No pipeline probability, weighted value or prospective revenue was invented for these promotions.

## Residual risks outside this promotion
- BEYOND BARRIERS positive referral remains user-action-required and its same-business-day SLA is breached.
- Ten older 2026-08-28 first-contact recipients remain pending canonical reconciliation.
- BATMAN / `nobody@knows.us` remains unresolved and REVIEW_REQUIRED.
- Historical Persuadis and Marmellata Lab duplicate-first-contact violations remain preserved as audit evidence.

## Final classification
**PASS_WITH_RESIDUAL.** The three Commercial Core candidates are safe to exist in the canonical daily outreach review queue. This audit does not authorize outreach by itself; every future first contact still requires the normal global real-time dedupe, verified route and outreach-quality gates.
