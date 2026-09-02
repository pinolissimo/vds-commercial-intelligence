# VDS Job Source Intelligence

Questo filone interpreta annunci e pagine careers pubbliche come **segnali di domanda** per servizi esterni VDS. Non è un motore di candidature generiche e non possiede alcuna capacità di invio: l'unico inviatore resta il Batch Dispatcher canonico del motore locale.

## Percorso controllato

`DISCOVERED_JOB → NORMALIZED_JOB → CHEAP_FILTER_PASS → COMPANY_IDENTITY_RESOLVED → HIGH_FIT_CANDIDATE → OFFICIAL_SOURCE_VERIFIED → ROUTE_VERIFIED → GLOBAL_DEDUP_PASS → READY_TO_APPLY`

Stati terminali o di protezione: `BLOCKED_NO_EXTERNAL`, `MANUAL_ROUTE_REQUIRED`, `REVIEW_REQUIRED`, `HOLD_STALE`, `ALREADY_CONTACTED`.

Un portale è una scoperta, non una prova finale. Prima della promozione devono esistere: organizzazione canonica, fonte ufficiale attuale, interesse VDS verificabile, percorso esatto di candidatura/contatto e controllo deduplica/soppressione globale.

## Fonti e priorità

- **A1**: pagina careers o sito ufficiale dell'organizzazione.
- **A2**: API, RSS o feed strutturato pubblico dell'organizzazione.
- **A3**: pagina pubblica di un job board, solo se il percorso di candidatura è quello effettivo.
- **Discovery**: motore di ricerca e feed di alert; richiedono sempre verifica A1/A2/A3.

Non sono ammessi bypass CAPTCHA, account condivisi, scraping autenticato, sostituzione di form/piattaforme con una email generica o invio diretto.

## Integrazione locale

L'implementazione eseguibile è in `vds-commercial-swarm-engine`:

```powershell
vds-job-intel --input data/job-intel/example-signals.json --output data/job-intel/decisions.json
```

Il comando produce solo decisioni JSON locali. `READY_TO_APPLY` indica che il record può essere preso in carico dalla coda canonica; non invia e non marca alcun record come contattato.

## Misure da leggere in dashboard

- segnali unici/ora;
- organizzazioni canoniche/ora;
- contatti ufficiali e route esatte verificate/ora;
- `READY_TO_APPLY`/ora;
- duplicati, scaduti, percorsi manuali e blocchi espliciti;
- esito post-contatto: risposta, call, proposta, contratto.

Le metriche sono pubblicate in `views/job-intelligence.json`; non vengono sommate agli altri funnel finché non derivano da esecuzioni reali misurate.
