# 🇮🇹 Italia — Regional Commercial Coverage

> Vista territoriale derivata del CRM canonico. Non duplicare company/opportunity/contact records qui.
> Source of truth: `opportunities/`, company/project records, `contacts/`, campaigns, suppression, Sent history.

## Uso
Ogni run del `VDS Opportunity Scanner` aggiorna questa vista solo per cambiamenti materiali. Il ciclo deve coprire tutte le 20 regioni, privilegiando territori sotto-coperti e segnali freschi. `VDS Partner Hunt` può effettuare outreach solo dopo global dedup + QG-01..QG-12 + Sent verification.

| Regione | Coverage | Scansione | Trovate | Qualificate | Contattate | Reply+ | Ultimo scan | Next action |
|---|---|---|---:|---:|---:|---:|---|---|
| Abruzzo | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Basilicata | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Calabria | TO_SCAN | PRIORITY | — | — | — | — | 2026-08-29 | continue only on new collaboration signal |
| Campania | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Emilia-Romagna | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Friuli-Venezia Giulia | QUALIFIED_TRACK | ACTIVE | 1 | 1 | 0 | 0 | 2026-08-29 | daily outreach review for canonical Mediaimmagine opportunity; continue round-robin discovery |
| Lazio | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Liguria | TO_SCAN | PRIORITY | — | — | — | — | 2026-08-29 | continue only on explicit external-capacity signal |
| Lombardia | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Marche | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Molise | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Piemonte | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Puglia | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Sardegna | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Sicilia | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Toscana | EXISTING_TRACK | ACTIVE | — | — | — | — | — | reconcile from canonical CRM |
| Trentino-Alto Adige/Südtirol | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Umbria | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Valle d'Aosta/Vallée d'Aoste | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |
| Veneto | TO_SCAN | PRIORITY | — | — | — | — | — | regional discovery pass |

## Target per regione
Freelance/P.IVA/contract; outsourcing/white-label; agenzie e software house con capacità esterna; web/frontend/WordPress; IT/infrastruttura quando coerente; collaborazione ricorrente. I progetti UE localizzati in Italia restano nel workstream `EU_PROJECTS` e possono essere conteggiati territorialmente solo come vista derivata.

## Regole di conteggio
- `Trovate`: opportunity canoniche scoperte con geografia verificata.
- `Qualificate`: opportunity che superano qualification gate.
- `Contattate`: FIRST_CONTACT realmente inviati e verificati in Sent oppure continuazioni/follow-up correttamente classificati.
- `Reply+`: risposta positiva/potenzialmente positiva/referral/request.
- Nessun numero viene inserito senza riconciliazione con il CRM canonico.
