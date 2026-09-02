# Growth Intelligence — layer di priorità controllata

## Stato

Implementato come livello derivato e reversibile nel motore locale. Non crea
una nuova sorgente, non invia e-mail e non modifica il CRM canonico.

## Cosa calcola

- trigger pubblici già presenti nell'evidenza;
- freschezza e half-life dell'opportunità;
- segnali Website Audit già ottenuti;
- fascia di valore e probabilità di risposta *advisory*;
- un percorso di acquisizione primario per organizzazione;
- proposal readiness ed evidence pack VDS.

## Vincoli

`FIRST_CONTACT` rimane unico per organizzazione. Non sono ammessi destinatari
dedotti, bypass della rotta, bypass delle esclusioni o invii da questa layer.
L'attivazione di una feature Growth modifica solo il suo stato di esperimento
(`SHADOW` / `CANARY`), mai l'autorizzazione di invio.

## Baseline iniziale — 2 settembre 2026

Primo replay locale: 1.000 identità valutate, 0 bozze, 0 invii e 0 mutazioni
della pipeline. I risultati devono essere confrontati con la baseline prima di
qualsiasi promozione. Con 317 invii storici e 11 risposte, il modello reply non
è calibrato: resta una stima esplicativa e non decisionale.

## Operatività locale

- metriche: `GET /api/growth/metrics`
- refresh shadow: `POST /api/growth/refresh?limit=100`
- profilo: `GET /api/growth/candidate/{identity_key}`
- rollback/flag: `POST /api/growth/features/{feature}`

Dashboard: `http://127.0.0.1:7777/intelligence`.
