# 🇪🇸 España — Territorial Commercial Coverage

> Vista territoriale derivata del CRM canonico. Non duplicare company/opportunity/contact records qui.
> Source of truth: `opportunities/`, company/project records, `contacts/`, campaigns, suppression, Sent history.

## Uso
Ogni run del `VDS Opportunity Scanner` aggiorna questa vista solo per cambiamenti materiali. Il ciclo deve coprire tutte le 17 comunidades autónomas più Ceuta e Melilla, privilegiando territori sotto-coperti e segnali freschi. `VDS Partner Hunt` può effettuare outreach solo dopo global dedup + QG-01..QG-12 + Sent verification.

| Comunidad / Ciudad autónoma | Coverage | Scansione | Trovate | Qualificate | Contattate | Reply+ | Ultimo scan | Next action |
|---|---|---|---:|---:|---:|---:|---|---|
| Andalucía | QUALIFIED_TRACK | ACTIVE | 1 | 1 | 0 | 0 | 2026-08-29 | review Autoridad Portuaria de Sevilla CONT26053 eligibility before 2026-09-14 10:00; continue source-family rotation |
| Aragón | TO_SCAN | PRIORITY | — | — | — | — | 2026-08-29 | historical procurement checked and rejected as already resolved; rotate to non-procurement source families |
| Principado de Asturias | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Illes Balears | QUALIFIED_TRACK | ACTIVE | 1 | 1 | 0 | 0 | 2026-08-29 | review ABAQUA SE/2026/11 tender eligibility before 2026-09-03 19:00; continue source-family rotation |
| Canarias | QUALIFIED_TRACK | ACTIVE | 1 | 1 | 0 | 0 | 2026-08-29 | review Los Realejos 2026/9564 tender eligibility before 2026-09-10; continue source-family rotation |
| Cantabria | QUALIFIED_TRACK | ACTIVE | 1 | 1 | 0 | 0 | 2026-08-29 | daily outreach review for canonical Cantabria Web Design white-label opportunity; continue source-family rotation |
| Castilla-La Mancha | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Castilla y León | QUALIFIED_TRACK | ACTIVE | 1 | 1 | 0 | 0 | 2026-08-29 | review ProBurgos C16.2026 tender eligibility before 2026-09-04; continue source-family rotation |
| Catalunya | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Comunitat Valenciana | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Extremadura | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Galicia | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Comunidad de Madrid | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Región de Murcia | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Comunidad Foral de Navarra | TO_SCAN | PRIORITY | — | — | — | — | 2026-08-29 | broad pass produced no new qualified buyer-side signal; rotate source family on next pass |
| País Vasco / Euskadi | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| La Rioja | TO_SCAN | PRIORITY | — | — | — | — | 2026-08-29 | current low-value procurement signal reviewed but not promoted; rotate to higher-value source families |
| Ceuta | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Melilla | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |

## Target per territorio
Freelance/autónomo/contract; outsourcing/white-label; agencias e software houses con capacidad externa; web/frontend/WordPress; IT/infrastructura quando coerente; colaboración recurrente. I progetti UE localizzati in Spagna restano nel workstream `EU_PROJECTS` e possono essere conteggiati territorialmente solo come vista derivata.

## Regole di conteggio
- `Trovate`: opportunity canoniche scoperte con geografia verificata.
- `Qualificate`: opportunity che superano qualification gate.
- `Contattate`: FIRST_CONTACT realmente inviati e verificati in Sent oppure continuazioni/follow-up correttamente classificati.
- `Reply+`: risposta positiva/potenzialmente positiva/referral/request.
- Nessun numero viene inserito senza riconciliazione con il CRM canonico.
