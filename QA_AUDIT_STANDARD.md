# VDS Commercial Intelligence — QA Audit Standard v3

## Obiettivo
Mantenere il sistema commerciale allo standard VDS7: affidabilità, tracciabilità, zero regressioni, dati verificati, automazioni controllabili, nessuna azione dichiarata senza evidenza e nessuna ottimizzazione basata su numeri inventati.

## Principio read-first
Ogni audit ricostruisce prima lo stato reale da GitHub e, per gli eventi email, dalla mailbox. Le sintesi precedenti non fanno fede se confliggono con repository o Sent/Inbox.

## Controlli obbligatori

### 1. Integrità CRM
- JSON validi e coerenti con gli schema correnti.
- Un solo record canonico per organizzazione.
- Nessuna opportunity orfana o duplicata.
- Timeline append-only e transizioni coerenti.
- Company, Contact, Opportunity e Campaign referenziati correttamente.
- La migrazione v2→v3 non invalida record storici compatibili.

### 2. Outreach e suppression
- Nessun primo contatto duplicato alla stessa organizzazione.
- `governance/suppression-registry.json` controllato prima di nuovi invii.
- Finché il backfill storico non è completo, controllo obbligatorio anche di Sent e outreach pre-CRM.
- Ogni `SENT` deve avere evidenza in Sent; recipient, subject e timestamp devono coincidere.
- Quality gates QG-01..QG-12 applicati prima del primo contatto.
- Nessuna risposta positiva/potenzialmente positiva o ambigua può ricevere auto-reply.
- Negative auto-reply: lingua, tono, audit BCC e Sent verification.

### 3. Decision Engine
- Ogni opportunity actionable ha una sola Next Best Action primaria.
- Ranking coerente con SLA, commercial intent, freshness e Lead Health.
- Lead Health 0–100 ricostruibile dal modello; nessun punteggio arbitrario non documentato.
- Aging/decay applicato senza cancellare storia.
- `POSITIVE_REPLY_USER_ACTION_REQUIRED`, referral, proposal request e SLA breach hanno priorità sulla nuova ricerca.

### 4. Probability / economics
- Operational prior chiaramente marcato `UNCALIBRATED` finché non esiste campione minimo.
- Nessun prior presentato come probabilità empirica.
- Weighted pipeline `null` finché mancano valore economico e probability calibrata difendibile.
- Nessun budget, rate, proposal value o won revenue inventato.

### 5. Qualità lead e freshness
- Fonte ufficiale o affidabile.
- Motivazione VDS specifica e verificabile.
- VERIFIED, INFERRED e TO_VERIFY separati.
- Opportunity scadute/stale declassate senza cancellare storia.
- Decision-maker intelligence supportata da evidenza.

### 6. Local no-website
- Attività reale verificata.
- Assenza di sito dedicato cross-checkata, non dedotta da una sola directory.
- Website Gap Score ricostruibile.
- Analisi dell'attività e personalized angle prima della bozza.
- Cold outreach non auto-inviato se channel/legal context non è chiaramente appropriato.
- Pipeline separata dal partner CRM.

### 7. Dashboard / KPI / attribution
- README, master-index e views coerenti.
- Conteggi account, opportunity, contacted, replies e campaign sent ricostruibili.
- Funnel calcolato sui dati reali e denominatori espliciti.
- Attribution non trae conclusioni statistiche da campioni insufficienti.
- Snapshot giornaliero coerente col master al momento dello snapshot.
- Link relativi puntano a file esistenti.

### 8. Commercial SLA e follow-up
- SLA same-business-day per positive reply/referral/proposal request.
- Follow-up: 3 business days e poi 7 business days secondo policy.
- Nessun follow-up dopo una risposta.
- Bounce: nessun resend allo stesso indirizzo senza replacement contact verificato.
- SLA breach sempre visibile in alto.

### 9. Copertura territoriale
- Italia: tutte le 20 regioni tracciate.
- Spagna: 17 comunidades + Ceuta + Melilla tracciate.
- Ricerca territoriale distinta dal numero di lead qualificati.
- Nessun territorio marcato completo senza evidenza sufficiente.

### 10. Proposal / Win-Loss / Learning
- Proposal dossier distingue VERIFIED / INFERRED / TO_DEFINE_WITH_USER.
- Prezzo e condizioni non vengono decisi/inviati automaticamente.
- Ogni WON/LOST registra reason code, evidence e learning note.
- Learning loop non modifica strategia su pochi casi isolati.

### 11. Audit delle affermazioni utente
- Ogni numero comunicato all'utente deve essere ricostruibile.
- Dati esplorativi non consolidati non vengono presentati come acquisiti.
- Qualsiasi discrepanza scoperta in un report viene corretta nello stesso audit quando deterministica.

## Classificazione
- `PASS` — nessuna anomalia materiale.
- `PASS_WITH_WARNINGS` — sistema coerente con rischi residui non bloccanti.
- `FAIL_CORRECTED` — incoerenza materiale trovata e corretta nello stesso audit.
- `FAIL_USER_ACTION_REQUIRED` — problema non correggibile automaticamente in sicurezza.

## Output
Ogni audit produce `audits/YYYY-MM-DD-HHMM.md` con timestamp, evidence, controlli, anomalie, correzioni, file modificati, stato finale, rischi residui e azioni raccomandate.

La dashboard viene aggiornata solo quando cambiano dati, KPI, stato, rischio operativo o architettura.