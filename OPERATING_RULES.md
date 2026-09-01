# VDS Commercial Intelligence — Operating Rules v2

## Mission
Generare lavoro retribuito trasformando ricerca, qualificazione, contatti, risposte e follow-up in una pipeline commerciale misurabile e auditabile.

## Single source of truth
`commercial-intelligence/` su GitHub è la fonte canonica. Dashboard, report, schede azienda, opportunity e log devono restare coerenti.

## Copertura geografica
La ricerca viene svolta territorio per territorio:
- Italia: tutte le 20 regioni;
- Spagna: tutte le 17 comunidades autónomas, più Ceuta e Melilla come coverage separata.

Per ogni territorio cercare: opportunità freelance/contract attive, agenzie con collaboratori esterni, outsourcing/white-label, software house con fabbisogno web/frontend, società di comunicazione EU e altri segnali concreti di capacità esterna richiesta. Una regione può restare senza lead se nessun candidato supera la soglia qualitativa.

## Qualification gate
Un lead diventa `READY_TO_CONTACT` solo con dominio verificato, attività pertinente, canale business valido, fit specifico, deduplica completata, evidenza datata, opportunity/freshness definite e contesto di contatto appropriato.

## Scoring
- `opportunity_score`: lavoro disponibile ora.
- `outsourcing_score`: uso verificato di collaboratori esterni.
- `vds_fit_score`: compatibilità tecnica/commerciale.
- `revenue_potential_score`: potenziale economico/ricorrenza.
- `revenue_priority_score`: priorità finale.
- `freshness_score`: attualità dell'opportunità.

## Priorità operativa
1. Risposte positive ricevute.
2. Follow-up scaduti su lead HOT.
3. Opportunità attive fresche.
4. Partnership strutturali con outsourcing esplicito.
5. Nuovi lead qualificati.
6. Ricerca esplorativa.

## Outreach
Messaggi one-to-one e personalizzati, nella lingua del destinatario quando possibile, con riferimento a un bisogno/modello verificato e CTA a bassa frizione. Nessun doppio contatto senza controllo della timeline. Invio automatico solo quando il canale invita esplicitamente candidature/collaborazioni; gli altri casi richiedono approvazione.

## Document QA gate — mandatory before every send
Nessun CV, portfolio, PDF, DOCX, proposta, lettera o altro allegato professionale può essere inviato senza un controllo finale completo sul file esatto che verrà allegato.

Il gate è bloccante e deve verificare almeno:
- rendering visivo di **tutte le pagine** del documento finale;
- assenza di testo tagliato, sovrapposto, fuori margine o con spaziature anomale;
- tipografia coerente: font, gerarchie, dimensioni, interlinea, pesi e allineamenti;
- encoding e glifi corretti, inclusi accenti, ñ, apostrofi, bullet e simboli;
- grafica, immagini e fotografia nitide e correttamente posizionate;
- dati di contatto, URL, LinkedIn, email, telefono e nomi verificati carattere per carattere;
- lingua coerente con candidatura e destinatario;
- contenuto veritiero e coerente con il profilo master;
- PDF apribile, non corrotto, con numero di pagine atteso e testo estraibile quando previsto;
- verifica del PDF finale **dopo** la conversione, non solo del DOCX sorgente.

Per i documenti generati/modificati, il workflow obbligatorio è: `edit/create → render → visual inspection → fix → re-render → final preflight → send`.
Se anche un solo controllo fallisce, stato `DOCUMENT_QA_FAILED` e **invio vietato** fino alla correzione.

## Campaign intelligence
Ogni messaggio appartiene a una campagna. Misurare: sent, replies, reply rate, positive replies, meetings, proposals, wins e revenue won.

## Economics
Non inventare valori monetari. I campi restano `null` finché non emergono budget, tariffa, range, proposta o contratto. Distinguere sempre pipeline non valorizzata da pipeline valorizzata.

## Freshness
Le opportunità attive devono essere riverificate prima dei follow-up. Annunci scaduti passano a `EXPIRED/STALE`; la company può restare `MONITOR` se strategica.

## Follow-up
Primo follow-up dopo 3 giorni lavorativi; secondo/finale dopo altri 7 giorni lavorativi, se l'opportunità è ancora valida. Stop dopo due follow-up senza risposta.

## Reply handling
Risposta negativa chiara: risposta automatica cortese e registrata. Risposta positiva o potenzialmente positiva: nessuna risposta automatica, stato `POSITIVE_REPLY_USER_ACTION_REQUIRED`. Risposta ambigua: `REVIEW_REQUIRED`.

## Data quality
Una company canonica può avere più opportunity. Timeline append-only. Ogni informazione che influenza scoring deve avere evidenza. Dati non verificati marcati `TO_VERIFY`.

## Obiettivi di copertura
- 150+ organizzazioni grezze esplorate tra Italia e Spagna.
- 40–70 lead realmente qualificati come primo target operativo.
- Qualità prima della quantità.
- KPI finale: `conversazioni → meeting → proposte → contratti → revenue`.
