# VDS Commercial Intelligence — Outreach Quality Gates

Un messaggio commerciale non può passare a `SENT` se non supera tutti i gate applicabili.

## First-contact hard gates

| Gate | Requirement | Fail action |
|---|---|---|
| QG-01 Identity | Organizzazione reale e verificata | BLOCKED |
| QG-02 Dedup company | Nessun duplicato canonico | MERGE/REVIEW |
| QG-03 Suppression | Registry + outreach history controllati | BLOCKED |
| QG-04 Contact | Canale verificato e coerente | DRAFT/RESEARCH |
| QG-05 Evidence | Motivo specifico supportato da fonte | DRAFT/RESEARCH |
| QG-06 Freshness | Opportunità ancora attuale o evergreen valida | REVERIFY |
| QG-07 Personalization | Messaggio riferito all'attività/bisogno reale | DRAFT |
| QG-08 Language | Lingua adeguata al destinatario | DRAFT |
| QG-09 Offer fit | Servizio/portfolio coerente col bisogno | DRAFT |
| QG-10 Channel/legal | Contesto consente l'azione prevista | APPROVAL_REQUIRED/BLOCKED |
| QG-11 Existing thread | Nessun thread/reply che renda improprio un nuovo first-contact | BLOCKED |
| QG-12 Sent audit | Dopo invio esiste evidenza nella cartella Sent | non marcare SENT |

## Reply gates

### Negative reply
Auto-reply consentito solo se classificazione ad alta confidenza e secondo la policy approvata. Verificare Sent e audit BCC.

### Positive / potentially positive
**AUTOMATION SEND = FORBIDDEN.** Stato `POSITIVE_REPLY_USER_ACTION_REQUIRED`.

### Ambiguous
**AUTOMATION SEND = FORBIDDEN.** Stato `REVIEW_REQUIRED`.

## Proposal / pricing / meeting
Sempre controllo utente. Il sistema prepara intelligence e draft, non decide prezzo o condizioni commerciali autonomamente.

## Local no-website
Oltre ai gate standard:
- assenza del sito deve essere cross-checked;
- l'attività deve essere qualitativamente valida e attiva;
- deve esistere un business case concreto per il sito;
- la personalizzazione deve citare elementi reali dell'attività;
- cold email non autorizzata resta `DRAFT/APPROVAL_REQUIRED` quando il contesto non è chiaramente appropriato.

## QA
Ogni audit deve campionare gli invii recenti e verificare che i gate fossero soddisfatti. Un invio senza gate verificabili è una non-conformità VDS7.