# VDS Commercial Intelligence — Revenue CRM Architecture v3

## Missione

Questo repository è il **single source of truth commerciale** di Visual Design Studio e deve guidare la conversione, non limitarsi a registrare attività.

**North Star:** `qualified conversations → meetings → proposals → contracts → € won`.

Il CRM v3 introduce un livello decisionale sopra il modello dati v2: Next Best Action, Lead Health, Commercial SLA, suppression globale, quality gates, attribution, snapshot storici, win/loss e learning loop.

## Entità canoniche

### COMPANY
Una sola scheda per organizzazione. Contiene intelligence aziendale, contatti, decision maker, relazioni, evidence, score e timeline.

### CONTACT
Persona specifica collegata a una company/project: ruolo, seniority, decision influence, canali pubblici verificati e relationship state.

### OPPORTUNITY
Possibilità commerciale concreta. Una company può avere più opportunity nel tempo.

### CAMPAIGN
Segmento e positioning di outreach misurabile.

### EVENT
Evento append-only: discovery, qualification, send, reply, referral, follow-up, meeting, proposal, won/lost, suppression, audit correction.

## Decision layer

```text
EVIDENCE + EVENTS + FRESHNESS + STATUS
                ↓
         LEAD HEALTH ENGINE
                ↓
      NEXT BEST ACTION ENGINE
                ↓
         COMMERCIAL SLA
                ↓
          ACTION QUEUE
                ↓
      HUMAN / AUTOMATION ACTION
                ↓
             EVENT
                ↺
```

## Next Best Action

Ogni opportunity attiva deve avere **una sola azione primaria**. Ordine base:

1. `RESPOND_POSITIVE_REPLY` — USER only.
2. `HANDLE_REFERRAL` — USER only quando implica relazione/negoziazione.
3. `SEND_PROPOSAL` — USER only.
4. `SCHEDULE_MEETING` — USER only.
5. `FOLLOW_UP_DUE` — automation solo se consentito dal contesto.
6. `FIND_BETTER_CONTACT`.
7. `APPLY_ACTIVE_ROLE`.
8. `SEND_FIRST_CONTACT` — solo se quality gate e contesto legale lo consentono.
9. `REVERIFY`.
10. `NURTURE` / `WAIT`.

L'engine deve produrre `action`, `reason`, `owner`, `due_at`, `expected_commercial_impact`, `confidence`.

## Lead Health Score 0–100

Score dinamico distinto dal Revenue Priority iniziale. Componenti:

- Commercial intent/status: 0–25
- Freshness: 0–20
- VDS fit: 0–20
- Relationship/referral strength: 0–15
- Decision-maker quality: 0–10
- SLA/actionability: 0–10

Penalità:
- source stale/expired;
- bounce senza contatto sostitutivo;
- due follow-up senza risposta;
- opportunity non più attiva;
- contatto non decisionale quando esiste un decisore migliore.

Classi: `CRITICAL 85–100`, `HOT 70–84`, `WARM 50–69`, `COOL 30–49`, `DORMANT <30`.

## Probability & Forecasting

Non inventare probabilità. Il CRM distingue:

- `operational_prior_pct`: prior usato solo per ranking, marcato `UNCALIBRATED`;
- `calibrated_probability_pct`: utilizzabile per weighted pipeline solo quando esiste campione sufficiente;
- `estimate_confidence`.

La calibrazione parte solo dopo un numero sufficiente di outcome reali per stage/segmento. Fino ad allora `weighted_pipeline_value = null` se non esiste una probabilità calibrata difendibile.

## Lead aging / decay

Il Lead Health decade con il tempo quando non esistono nuovi segnali. La priority non resta HOT indefinitamente.

- active job: reverify rapidamente;
- evergreen partner page: decay lento;
- positive reply/referral: nessun decay finché SLA aperto;
- expired source: forte penalità immediata.

## Contact intelligence

Company e persone sono separati. Ogni contact può avere:

- role / organization;
- decision influence: `LOW/MEDIUM/HIGH/FINAL`;
- relationship: `UNKNOWN/COLD/WARM/ACTIVE/STRATEGIC`;
- source/evidence;
- preferred public channel;
- last interaction;
- do-not-contact state.

## Commercial SLA

- Positive reply / referral: user action same business day.
- Proposal/budget request: user action same business day.
- Review-required ambiguity: human review same business day.
- First follow-up: 3 business days after first contact if still valid.
- Second/final: 7 business days after first follow-up.
- Bounce: find replacement contact before any resend.
- SLA breach must appear at the top of the dashboard.

## Global Suppression Registry

`governance/suppression-registry.json` è controllato prima di qualsiasi invio. Contiene domain/email/company identifiers per:

- FIRST_CONTACT_ALREADY_SENT;
- DO_NOT_CONTACT;
- UNSUBSCRIBED;
- HARD_BOUNCE;
- INVALID_CONTACT;
- EXISTING_CLIENT;
- MANUAL_SUPPRESSION.

**Regola:** nessun primo contatto può essere inviato due volte alla stessa organizzazione.

## Outreach Quality Gate

Prima di un primo invio devono essere TRUE:

1. identity verified;
2. company/project deduplicated;
3. suppression registry checked;
4. contact route verified;
5. specific reason-to-contact stored;
6. personalization based on real evidence;
7. language appropriate;
8. portfolio/service angle relevant;
9. source freshness acceptable;
10. legal/channel context permits the intended action;
11. no existing active reply/thread that would make a new first-contact inappropriate.

Fail → `DRAFT/APPROVAL_REQUIRED` or `BLOCKED`, never SENT.

## Local no-website pipeline

Resta separata sotto `local-no-website/`. Introduce **Website Gap Score**:

- no dedicated functional website;
- business quality/reputation;
- ability to benefit economically from a site;
- digital gap vs competitors;
- public contactability;
- clear personalized website proposition.

Le attività marginali o non verificabili vengono scartate.

## Attribution

Ogni opportunity mantiene source + campaign + message variant + language + positioning. Le metriche devono poter rispondere a:

- quale segmento risponde di più;
- quale source produce positive replies;
- quale positioning porta a meeting/proposal/win;
- performance per paese/regione;
- time-to-first-reply e time-to-win.

## Snapshot e storico

`analytics/snapshots/YYYY-MM-DD.json` conserva KPI giornalieri espliciti. Git resta la storia completa, gli snapshot facilitano trend e confronto.

## Win / Loss

Ogni chiusura deve avere reason code, evidence e learning note. Esempi:

`PRICE`, `TIMING`, `INTERNAL_SUPPLIER`, `COMPETITOR`, `STACK_MISMATCH`, `NO_BUDGET`, `NO_RESPONSE`, `PROJECT_CANCELLED`, `WON_FIT`, `WON_REFERRAL`, `WON_SPEED`, `WON_SPECIALIZATION`.

## Learning loop

Il sistema non deve ottimizzare attività, ma revenue. Periodicamente valuta:

- segmenti con maggior positive-reply rate;
- lead source migliori;
- tempi di risposta;
- conversioni meeting/proposal/won;
- motivi di loss;
- quality-gate failures;
- false positive della ricerca;
- opportunità che consumano lavoro senza produrre segnali.

Le regole possono essere aggiornate solo con evidenza sufficiente e senza regressioni.

## Human-control boundary

- Negative chiare: risposta cortese automatica consentita secondo policy.
- Positive/potenzialmente positive: **mai risposta automatica**.
- Ambigue: **mai risposta automatica**.
- Proposal, prezzo, meeting, negoziazione: **USER controlled**.

## Dashboard

`README.md` = dashboard umana primaria.
`master-index.json` = stato aggregato machine-readable.

La dashboard deve mostrare prima di tutto:

1. GOAL TODAY;
2. Next Best Actions;
3. SLA breaches;
4. positive replies/referrals;
5. funnel e conversion;
6. pipeline economica;
7. campaign attribution;
8. coverage e research queues;
9. QA state.

## Principio VDS7

Precisione > volume. Evidenza > inferenza. Conversione > attività. Append-only > riscrittura. Nessun dato inventato. Nessun doppio primo contatto. Nessuna regressione silenziosa.