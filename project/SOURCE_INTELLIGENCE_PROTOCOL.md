# VDS Source Intelligence Protocol

## Obiettivo
Trasformare VDS Commercial Intelligence in un motore multi-source: selezione delle fonti, indipendenza, freshness e rendimento storico sono segnali di primo livello.

## Regola base
Più URL non significano automaticamente più evidenza. Fonti che replicano lo stesso annuncio appartengono alla stessa `independence_group` e non vanno conteggiate due volte.

## Ruoli fonte
`DISCOVERY`, `IDENTITY`, `NEED`, `CONTACT_ROUTE`, `FRESHNESS`, `BUYER_PATH`, `CORROBORATION`.

## Tier
- `T1_PRIMARY`: sito ufficiale azienda/progetto, trust base 1.00.
- `T1_INSTITUTIONAL`: registro pubblico/UE/procurement ufficiale, 0.95.
- `T2_SPECIALIST`: job/freelance marketplace specialistico, 0.80.
- `T3_AGGREGATOR`: aggregatore generalista, 0.60.
- `T4_SIGNAL`: social/news/directory, 0.45–0.55.

## Source Confidence Score — SCS
Indice operativo 0–100, non probabilità:
- authority/tier 0–30;
- corroborazione indipendente 0–25;
- freshness 0–20;
- identity/domain 0–10;
- bisogno esplicito 0–10;
- route/buyer path 0–5.

Classi: `85–100 STRONG_MULTI_SOURCE`, `70–84 QUALIFIED_SOURCE_BASE`, `55–69 VERIFY_MORE`, `<55 DISCOVERY_ONLY`.
Conflitti o identità ambigua => `REVIEW_REQUIRED` indipendentemente dallo score.

## Cross-source gate
Prima di `QUALIFIED` preferire:
1. fonte primaria/istituzionale per identità;
2. fonte indipendente per bisogno/freshness;
3. route verificata quando si dichiara contactability.

Una fonte ufficiale può provare più dimensioni, ma prima di FIRST_CONTACT va cercata corroborazione indipendente quando economicamente sensato.

### EU projects
Catena forte: `grant/project official → WP/task/deliverable → beneficiary/owner → official contact route`.

### Collaborations
Catena forte: `current need/listing → official company identity → explicit application route → independent corroboration`.

## Source families
1. company/career/partner pages;
2. specialist job boards;
3. freelance/contract marketplaces;
4. professional networks;
5. agency/outsourcing/white-label ecosystems;
6. procurement/tender portals;
7. EU funding/project registries;
8. programme-specific funding portals;
9. chambers/industry associations/clusters;
10. incubators/accelerators;
11. universities/research directories;
12. company/project news and social signals;
13. local business directories;
14. search engines as discovery routers only.

## Territory × source matrix
Per ciascuna regione italiana e comunità/città autonoma spagnola tracciare: famiglie eleggibili, famiglie scansionate di recente, coverage %, qualified per family, contacted per family, positive replies per family, last scan, next family.

Pochi lead + bassa copertura fonti = `UNDER_SEARCHED`, non `LOW_OPPORTUNITY`.

## Source yield learning
Per fonte/famiglia: discoveries, qualified, contacted, replies, positive replies, meetings, proposals, wins, last useful hit, estimated search cost.

La priorità della prossima ricerca combina:
`territorial under-coverage + source-family under-coverage + historical yield + freshness potential + commercial fit - search cost - recent zero-result penalty`.

Indicazione exploration/exploitation: circa 75% su combinazioni ad alto rendimento e 25% su fonti/territori sotto-testati.

## Resource optimization
Batchare ricerche compatibili, riusare evidenze fresche, evitare query zero-result appena eseguite, scalare aggregatore→specialista→primaria durante discovery e approfondire HOT/HOT+ fino al buyer path.

## Safety
SCS e multi-source non sostituiscono mai deduplica globale, suppression, outreach policy o Sent verification. FIRST_CONTACT resta bloccato finché l'identità commerciale non è riconciliata globalmente.

Registry machine-readable: `config/source-registry.json`.
Vista umana: `views/source-coverage.md`.
