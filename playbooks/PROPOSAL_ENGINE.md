# VDS Commercial Intelligence — Proposal Engine

## Trigger

Si attiva quando un opportunity entra in uno dei seguenti stati:

- `POSITIVE_REPLY_USER_ACTION_REQUIRED`
- `MEETING`
- `PROPOSAL`
- richiesta esplicita di prezzo/budget/CV/portfolio/proposta

## Human boundary

Il sistema **non invia autonomamente** una proposta, non decide condizioni economiche definitive e non negozia. Prepara un dossier decisionale e una bozza per controllo utente.

## Proposal dossier obbligatorio

1. Company/project identity.
2. Decision maker e ruolo.
3. Thread summary con segnali commerciali.
4. Problema/bisogno verificato.
5. VDS fit specifico.
6. Portfolio/case study più pertinente.
7. Scope consigliato.
8. Dipendenze e rischi.
9. Pricing evidence disponibile.
10. Range o prezzo suggerito solo se supportato da base reale; altrimenti `TO_DEFINE_WITH_USER`.
11. Obiezioni prevedibili.
12. Call-to-action consigliata.
13. Deadline/SLA.
14. Confidence e fonti.

## Proposal readiness score

0–100 basato su:
- bisogno definito 20;
- decision maker 15;
- scope definibile 15;
- budget/rate evidence 10;
- portfolio match 15;
- relationship strength 10;
- timing 10;
- technical feasibility 5.

Soglie:
- 80–100 READY_FOR_USER_PROPOSAL
- 60–79 NEEDS_1_2_DETAILS
- 40–59 DISCOVERY_NEEDED
- <40 NOT_READY

## Output

`proposal-dossiers/<opportunity-id>.md`

Ogni dossier deve distinguere chiaramente VERIFIED, INFERRED e TO_DEFINE_WITH_USER.

## Regola

Velocità sì, ma nessun preventivo improvvisato: il dossier riduce il tempo tra interesse e proposta senza sacrificare precisione.