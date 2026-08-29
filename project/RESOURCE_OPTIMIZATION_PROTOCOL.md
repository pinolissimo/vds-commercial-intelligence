# VDS Resource Optimization Protocol — ALWAYS ON

## Objective
Massimizzare il valore commerciale ottenuto per unità di risorsa consumata: token, crediti API, chiamate esterne, tempo di esecuzione, storage, file, automazioni e traffico di ricerca, senza ridurre la qualità del sistema.

## Non-negotiable quality floor
L'ottimizzazione NON può mai indebolire:
- deduplica e prevenzione dei FIRST_CONTACT duplicati;
- suppression checks;
- verifica delle fonti e freshness;
- distinzione VERIFIED / INFERRED / TO_VERIFY;
- verifica Sent per ogni stato SENT;
- sicurezza nella gestione delle risposte positive/ambigue;
- QA e coerenza CRM;
- divieto di inventare email, ruoli, budget, probabilità o risultati.

## Decision rule
Per ogni attività usare il percorso meno costoso che può ancora produrre una risposta affidabile. Escalare a strumenti, modelli, ricerche o passaggi più costosi solo quando l'informazione aggiuntiva può materialmente cambiare una decisione commerciale, una qualificazione, la contactability, una priorità o un'azione dell'utente.

## Token / model economy
- leggere prima dati canonici, cache, log recenti e risultati già verificati;
- evitare di reinviare contesto invariato;
- usare prompt compatti e strutturati;
- preferire modelli/tool più economici per classificazione, parsing, dedup e controlli deterministici;
- riservare reasoning/deep research costosi ai casi ad alto valore o ambiguità sostanziale;
- produrre report incrementali invece di ricostruire ogni volta l'intero stato.

## Search / external-call economy
- cercare prima solo l'evidenza mancante;
- batchare lookup compatibili;
- non ripetere query che hanno appena prodotto zero risultati senza un nuovo segnale;
- riusare fonti ufficiali e verifiche già fresche;
- approfondire ricorsivamente solo finché il valore informativo marginale resta significativo;
- terminare un pass quando ulteriore ricerca è improbabile che cambi stato o score.

## Storage economy
- un solo record canonico per company/project/opportunity/contact;
- timeline append-only senza copie ridondanti;
- evitare snapshot, report e file duplicati quando una vista derivata è sufficiente;
- aggiornare README/dashboard solo per cambiamenti materiali;
- mantenere research log compatti, con riferimenti alle evidenze invece di duplicarne il testo;
- eliminare la proliferazione di workspace paralleli che descrivono lo stesso stato.

## Automation economy
- una sola automazione deve possedere ciascuna responsabilità critica;
- evitare scanner/reply watcher/outreach task sovrapposti;
- preferire una automazione multi-run giornaliera a più task equivalenti quando possibile;
- condition watch senza evento = nessuna notifica e nessun output rumoroso;
- delta-first: elaborare ciò che è cambiato dall'ultimo run prima di eseguire full scan.

## CRM / research economy
Ordine operativo:
1. leggere lo stato canonico;
2. identificare il gap informativo che blocca la decisione;
3. acquisire la minima evidenza sufficiente;
4. verificare qualità e dedup;
5. aggiornare solo i record realmente cambiati;
6. fermarsi quando il valore marginale scende sotto il costo della ricerca successiva.

## Quality-preserving escalation
Escalare automaticamente a verifica più profonda quando:
- opportunity è HOT/HOT+ ma manca una evidenza decisiva;
- si sta per eseguire FIRST_CONTACT;
- compare una risposta positiva/referral/proposal/call;
- fonti confliggono;
- identità del buyer/contact path è ambigua;
- un dato può causare duplicazione, invio errato o perdita di opportunità;
- QA rileva una incoerenza sistemica.

## Core metric
`commercial value / total resource cost`, subordinata sempre ai quality gates VDS7.

Principio finale: **economizzare tutto ciò che è ridondante; non economizzare mai sulla verifica che protegge qualità, reputazione o conversione commerciale.**
