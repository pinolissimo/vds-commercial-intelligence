# VDS Job & Client Acquisition — Project Workspace

## Mission
Trasformare ricerca di opportunità, qualificazione, outreach, risposte e follow-up in nuovi incarichi retribuiti per Visual Design Studio.

## Source of truth
Repository canonico: `pinolissimo/vds-commercial-intelligence` (`main`).

Questo workspace NON contiene codice o documentazione di VDS Engine e NON deve essere spostato dentro repository demo o `eu-funding-observatory`.

## Workstream

### 1. EU Projects
Ricerca di progetti UE finanziati o in avvio con bisogno plausibile e verificabile di sito web, piattaforma, dissemination/communication support, visual/digital assets o sviluppo web collegato a WP/task/procurement.

Canonical paths:
- `eu-projects/`
- `opportunities/OPP-EU-*.json`
- `contacts/`
- `campaigns/`
- `research/`

### 2. Collaborations / Jobs
Ricerca di collaborazioni freelance/P.IVA/contract, outsourcing, white-label, partnership con agenzie/software house, annunci web/frontend/WordPress/IT pertinenti e opportunità remote o territoriali.

Canonical paths:
- `opportunities/OPP-IT-*.json`
- `opportunities/OPP-ES-*.json`
- `italy/`
- `spain/`
- `contacts/`
- `campaigns/`
- `research/`

## Shared Command Center
Entrambi i workstream confluiscono nello stesso CRM. La deduplica è globale: una company può avere più opportunity, ma non deve ricevere un doppio first-contact non intenzionale.

Priorità:
1. positive replies / referral;
2. follow-up HOT scaduti;
3. opportunità fresche ad altissimo fit;
4. partnership strutturali;
5. nuovi lead qualificati;
6. ricerca esplorativa.

KPI: `qualified conversations → meetings → proposals → contracts → € won`.

## Operating standard
Rimangono vincolanti:
- `OPERATING_RULES.md`
- `CONTACT_LIFECYCLE.md`
- `CRM_ARCHITECTURE.md`
- `QA_AUDIT_STANDARD.md`

## ChatGPT Project
Per il workspace ChatGPT usare `PROJECT_INSTRUCTIONS.md` come istruzioni di progetto e `CHAT_MAP.md` come mappa delle chat operative. Il repository GitHub rimane sempre la fonte canonica dei dati e dello stato operativo.
