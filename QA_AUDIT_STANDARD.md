# VDS Commercial Intelligence — QA Audit Standard v4

## Obiettivo
Mantenere il sistema commerciale allo standard VDS7: affidabilità, tracciabilità, zero regressioni, dati verificati, automazioni controllabili, nessuna azione dichiarata senza evidenza e nessuna ottimizzazione basata su numeri inventati.

## Principio read-first
Ogni audit ricostruisce prima lo stato reale da GitHub e, per gli eventi email, dalla mailbox. Le sintesi precedenti non fanno fede se confliggono con repository o Sent/Inbox.

## Principio preventivo
QA non è solo post-run. I controlli bloccanti devono essere applicati nei punti di transizione:
- `DISCOVERED → QUALIFIED`: source/evidence gate;
- `QUALIFIED → READY_TO_CONTACT`: identity/contactability/dedup gate;
- `READY_TO_CONTACT → FIRST_CONTACT`: QG-01..QG-12 + suppression + global identity + Sent-history gate;
- `CONTACTED → FOLLOW_UP`: reply/bounce/SLA gate;
- `REPLIED → next state`: reply classification + user-action safety gate.

Se un controllo bloccante è incompleto o ambiguo: `REVIEW_REQUIRED`, nessun avanzamento irreversibile e nessun invio.

## Controlli obbligatori

### 1. Integrità CRM
- JSON validi e coerenti con gli schema correnti.
- Un solo record canonico per organizzazione.
- Nessuna opportunity orfana o duplicata.
- Timeline append-only e transizioni coerenti.
- Company, Contact, Opportunity e Campaign referenziati correttamente.
- La migrazione v2→v3 non invalida record storici compatibili.

### 2. Outreach e suppression
- Nessun primo contatto duplicato alla stessa organizzazione/progetto commerciale.
- `governance/suppression-registry.json` controllato prima di nuovi invii.
- Finché il backfill storico non è completo, controllo obbligatorio anche di Sent e outreach pre-CRM.
- Ogni `SENT` deve avere evidenza in Sent; recipient, subject e timestamp devono coincidere.
- Quality gates QG-01..QG-12 applicati prima del primo contatto.
- Nessuna risposta positiva/potenzialmente positiva o ambigua può ricevere auto-reply.
- Negative auto-reply: lingua, tono, audit BCC e Sent verification.

### 3. Decision Engine
- Ogni opportunity actionable ha una sola Next Best Action primaria.
- Ranking coerente con SLA, commercial intent, freshness, Lead Health e source quality.
- Lead Health 0–100 ricostruibile dal modello; nessun punteggio arbitrario non documentato.
- Aging/decay applicato senza cancellare storia.
- `POSITIVE_REPLY_USER_ACTION_REQUIRED`, referral, proposal request e SLA breach hanno priorità sulla nuova ricerca.

### 4. Probability / economics
- Operational prior chiaramente marcato `UNCALIBRATED` finché non esiste campione minimo.
- Nessun prior presentato come probabilità empirica.
- Weighted pipeline `null` finché mancano valore economico e probability calibrata difendibile.
- Nessun budget, rate, proposal value o won revenue inventato.

### 5. Source Intelligence & Evidence Quality
Leggere `project/SOURCE_INTELLIGENCE_PROTOCOL.md` e `config/source-registry.json`.

Controlli obbligatori:
- ogni evidenza materiale ha fonte e data;
- identità aziendale/progetto supportata preferibilmente da fonte primaria o istituzionale;
- need/freshness corroborati da fonte indipendente quando economicamente sensato;
- `independence_group` impedisce di contare mirror dello stesso annuncio come prove indipendenti;
- search engine e directory non sono prova finale quando è disponibile una fonte primaria;
- contact/application/buyer route distingue `VERIFIED`, `INFERRED`, `TO_VERIFY`;
- Source Confidence Score, se presente, è ricostruibile e dichiarato indice operativo, non probabilità;
- conflitti tra fonti => `REVIEW_REQUIRED` anche con score elevato;
- una fonte ufficiale può provare più dimensioni ma non elimina il global duplicate gate;
- source counters/yield sono riconciliabili agli eventi CRM.

Hard fail pre-promotion:
- `QUALIFIED` basato solo su mirror/aggregatori senza verifica identità;
- freshness mancante per opportunità time-sensitive;
- email/ruolo/contatto inventato o dedotto senza evidenza;
- fonte citata che non supporta realmente il claim usato per qualificare.

### 6. Qualità lead e freshness
- Fonte ufficiale o affidabile.
- Motivazione VDS specifica e verificabile.
- VERIFIED, INFERRED e TO_VERIFY separati.
- Opportunity scadute/stale declassate senza cancellare storia.
- Decision-maker intelligence supportata da evidenza.
- Nessun lead promosso solo perché numericamente aumenta la pipeline.

### 7. Local no-website
- Attività reale verificata.
- Assenza di sito dedicato cross-checkata, non dedotta da una sola directory.
- Website Gap Score ricostruibile.
- Analisi dell'attività e personalized angle prima della bozza.
- Cold outreach non auto-inviato se channel/legal context non è chiaramente appropriato.
- Pipeline separata dal partner CRM.

### 8. Dashboard / KPI / attribution
- README, master-index e views coerenti.
- Conteggi account, opportunity, contacted, replies e campaign sent ricostruibili.
- Funnel calcolato sui dati reali e denominatori espliciti.
- Attribution non trae conclusioni statistiche da campioni insufficienti.
- Snapshot giornaliero coerente col master al momento dello snapshot.
- Link relativi puntano a file esistenti.
- Metriche source-yield non contano URL duplicati come discovery indipendenti.

### 9. Commercial SLA e follow-up
- SLA same-business-day per positive reply/referral/proposal request.
- Follow-up: 3 business days e poi 7 business days secondo policy.
- Nessun follow-up dopo una risposta.
- Bounce: nessun resend allo stesso indirizzo senza replacement contact verificato.
- SLA breach sempre visibile in alto.

### 10. Copertura territoriale e Source Matrix
- Italia: tutte le 20 regioni tracciate.
- Spagna: 17 comunidades + Ceuta + Melilla tracciate.
- Ricerca territoriale distinta dal numero di lead qualificati.
- Nessun territorio marcato completo senza evidenza sufficiente.
- Per ogni territorio, distinguere coverage geografica da source-family coverage.
- Pochi risultati + bassa source-family coverage => `UNDER_SEARCHED`, non `LOW_OPPORTUNITY`.
- `views/source-coverage.md`, `views/territorial-coverage.md`, `italy/README.md` e `spain/README.md` devono essere coerenti con i record canonici.

### 11. Proposal / Win-Loss / Learning
- Proposal dossier distingue VERIFIED / INFERRED / TO_DEFINE_WITH_USER.
- Prezzo e condizioni non vengono decisi/inviati automaticamente.
- Ogni WON/LOST registra reason code, evidence e learning note.
- Learning loop non modifica strategia su pochi casi isolati.
- Source-yield learning usa outcome reali e non promuove automaticamente fonti ad alto volume ma bassa conversione.

### 12. Audit delle affermazioni utente
- Ogni numero comunicato all'utente deve essere ricostruibile.
- Dati esplorativi non consolidati non vengono presentati come acquisiti.
- Qualsiasi discrepanza scoperta in un report viene corretta nello stesso audit quando deterministica.
- Un messaggio preparato/draft non viene mai contato come inviato.

## Severity model
- `BLOCKER`: rischio di invio errato/duplicato, identità falsa, claim SENT senza Sent evidence, risposta positiva gestita automaticamente, dato inventato.
- `CRITICAL`: lead/actionable state supportato da evidenza insufficiente, conflitto fonti non gestito, suppression inconsistente, canonical identity collision.
- `MAJOR`: KPI/dashboard/source coverage non riconciliati, freshness scaduta su lead prioritario, broken references.
- `MINOR`: metadati incompleti non decisivi, documentazione derivata stale senza impatto operativo.

`BLOCKER` o `CRITICAL` impediscono nuovi FIRST_CONTACT per l'identità/ambito coinvolto fino a correzione o review.

## Classificazione audit
- `PASS` — nessuna anomalia materiale.
- `PASS_WITH_WARNINGS` — sistema coerente con soli rischi MINOR/non bloccanti.
- `FAIL_CORRECTED` — anomalia materiale deterministica trovata e corretta nello stesso audit.
- `FAIL_USER_ACTION_REQUIRED` — problema non correggibile automaticamente in sicurezza.

## Output
Ogni audit produce `audits/YYYY-MM-DD-HHMM.md` con timestamp, evidence, controlli, severità, anomalie, correzioni, file modificati, stato finale, rischi residui e azioni raccomandate.

La dashboard viene aggiornata solo quando cambiano dati, KPI, stato, rischio operativo o architettura.
