# VDS Commercial Intelligence — Contact Lifecycle v2

Questo documento definisce stato canonico, transizioni, priorità operative e audit trail del CRM commerciale VDS.

## Stati

`RESEARCH` → organizzazione individuata ma non verificata.  
`QUALIFIED` → azienda/opportunità verificata e compatibile.  
`READY_TO_CONTACT` → canale valido e messaggio pronto.  
`CONTACTED` → primo contatto inviato e verificato in Sent.  
`FOLLOW_UP_DUE` → follow-up scaduto.  
`FOLLOW_UP_SENT` → follow-up inviato e verificato.  
`NEGATIVE_AUTO_REPLIED` → risposta negativa chiara gestita automaticamente con BCC.  
`NURTURE` → nessuna opportunità immediata, relazione da mantenere.  
`FUTURE_OPPORTUNITY` → il contatto ha esplicitamente lasciato aperta una futura collaborazione.  
`LOST` → opportunità chiusa senza prospettiva concreta.  
`REVIEW_REQUIRED` → risposta ambigua: nessuna automazione di risposta.  
`POSITIVE_REPLY_USER_ACTION_REQUIRED` → interesse commerciale: controllo esclusivamente umano.  
`MEETING` → call/incontro concordato o svolto.  
`PROPOSAL` → proposta economica/tecnica inviata.  
`WON` → contratto/incarico acquisito.  
`LOST_AFTER_PROPOSAL` → opportunità persa dopo proposta.  
`MONITOR` → lead strategico senza azione immediata.

## Funnel

```text
RESEARCH
  -> QUALIFIED
  -> READY_TO_CONTACT
  -> CONTACTED
       |-> FOLLOW_UP_DUE -> FOLLOW_UP_SENT
       |-> NEGATIVE_AUTO_REPLIED -> LOST | NURTURE | FUTURE_OPPORTUNITY
       |-> REVIEW_REQUIRED
       |-> POSITIVE_REPLY_USER_ACTION_REQUIRED
                -> MEETING
                -> PROPOSAL
                -> WON | LOST_AFTER_PROPOSAL
```

## Priorità delle code

1. `POSITIVE_REPLY_USER_ACTION_REQUIRED` — massima priorità; nessuna risposta automatica.
2. `REVIEW_REQUIRED` — revisione umana.
3. `FOLLOW_UP_DUE` — azioni commerciali scadute.
4. `READY_TO_CONTACT` — lead qualificati nuovi.
5. `NURTURE` / `FUTURE_OPPORTUNITY` — monitoraggio trigger futuri.
6. `RESEARCH` — verifica nuovi candidati.

## Follow-up

- Primo follow-up: 3 giorni lavorativi dal primo contatto.
- Secondo/finale: 7 giorni lavorativi dopo il primo follow-up, solo se opportunità ancora valida.
- Dopo due follow-up senza risposta: interrompere outreach attivo e passare a `MONITOR` o `NURTURE` se strategico.
- Ogni follow-up deve essere preceduto da controllo mailbox e, per annunci attivi, da riverifica della fonte.

## Reply policy

### Negativa chiara
Risposta automatica breve, professionale, nella lingua del thread:
- ringraziare per tempo e attenzione;
- prendere atto senza pressione;
- lasciare aperta disponibilità a nuove opportunità o cambiamenti;
- saluto cordiale;
- BCC obbligatorio a `allocca.pino@gmail.com`;
- verifica obbligatoria in Sent;
- evento `NEGATIVE_AUTO_REPLY_SENT` nella timeline.

### Positiva o potenzialmente positiva
**Mai risposta automatica.** Classificare `POSITIVE_REPLY_USER_ACTION_REQUIRED`, aggiornare dashboard e notificare l'utente.

### Ambigua
**Mai risposta automatica.** Classificare `REVIEW_REQUIRED`.

## Opportunity lifecycle

La company e l'opportunity sono separate. Una company può generare più opportunity nel tempo. La chiusura di una opportunity non rende automaticamente `LOST` l'intero account.

## Economics

Quando emergono dati reali, ogni opportunity può contenere:
- valore minimo/massimo stimato;
- probabilità;
- weighted value;
- recurring potential;
- proposta inviata;
- revenue vinta.

**Non inventare mai valori economici.** In assenza di evidenza, mantenere i campi monetari `null`.

## Freshness

Prima di un follow-up su un'opportunità pubblicata verificare:
- fonte ancora online;
- data di pubblicazione;
- eventuale scadenza;
- stato CURRENT / EVERGREEN / STALE / EXPIRED / TO_VERIFY.

## Audit trail minimo

Ogni evento deve conservare:
- `event_id`;
- timestamp;
- tipo evento;
- canale;
- actor;
- from/to;
- subject quando applicabile;
- previous/new status;
- outcome;
- evidence/log reference;
- next action;
- due date.

La timeline è append-only: nessun evento commerciale significativo deve essere cancellato.

## Integrità

- `SENT` richiede verifica nella cartella Sent.
- `REPLIED` richiede messaggio realmente ricevuto.
- `MEETING` richiede accordo concreto.
- `PROPOSAL` richiede proposta effettivamente inviata.
- `WON` richiede conferma commerciale reale.
- Il README e `master-index.json` devono riflettere l'ultimo stato valido.
