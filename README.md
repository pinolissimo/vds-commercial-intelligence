# VDS Commercial Intelligence — Revenue Dashboard

> **Repository dedicata:** questo repository è il **single source of truth commerciale** di Visual Design Studio. Nessun dato CRM deve essere scritto nelle repository demo o VDS Engine.
>
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **Standard:** VDS7 · precisione > volume · evidenza > inferenza · zero doppio first-contact

**Ultimo aggiornamento:** 28 agosto 2026 · 20:58 Europe/Madrid  
**CRM:** v3 Revenue Operating System · dedicated repository  
**Migrazione:** **IN PROGRESS — core + decision views + campaigns/reports migrated; canonical records progressing**  
**Ricerca:** **SECOND DEEP PASS ACTIVE**  
**QA:** **FAIL_CORRECTED — audit 20:58; containment e viste riallineate**

## 🎯 GOAL TODAY

| Target | Stato | Evidenza |
|---|---|---|
| **≥ 1 nuovo cliente / incarico retribuito oggi** | **PARTIAL_PROGRESS** | referral positivo BEYOND BARRIERS; nessun meeting/proposal/win ancora confermato |

## ⚡ Next Best Actions

| # | Azione | Owner | Stato |
|---:|---|---|---|
| **1** | **HANDLE_REFERRAL — BEYOND BARRIERS** | USER | **CRITICAL · SLA BREACHED** |
| **2** | **RECONCILE_MAILBOX / SUPPRESSION** | AUTOMATION | **CRITICAL QA · BREACHED** |
| **3** | **Studiart — Piacenza** | AUTOMATION | **NEW · SCORE 98 · HIGH FIT** |
| **4** | **Vaivén Estudio — Galicia** | AUTOMATION | **NEW · SCORE 97 · HIGH FIT** |
| 5 | Nexìbo | AUTOMATION | HIGH FIT |
| 6 | WebGenova outsourcing route | AUTOMATION | HIGH FIT |
| 7 | Second deep territorial pass | AUTOMATION | ACTIVE |

[Next Best Actions →](views/next-best-actions.json) · [Action Queue →](views/action-queue.json) · [Deep Research Queue →](views/deep-research-queue.json)

## 🗺️ Copertura territoriale

**Broad pass completato su tutti i territori:** Italia **20/20 regioni**, Spagna **19/19 territori** (17 comunidades + Ceuta + Melilla).

Dopo il secondo deep pass:

- Italia: **10/20 regioni** con almeno un lead qualificato; **16 account** con regione verificata.
- Spagna: **9/19 territori** con almeno un lead qualificato; **12 account** con territorio verificato.
- **Emilia-Romagna:** nuovo lead qualificato **Studiart (Piacenza)**.
- **Galicia:** nuovo lead qualificato **Vaivén Estudio (Lugo)**.
- Restano **20 territori** a zero e in ricerca approfondita.

[Regional Coverage →](views/regional-coverage.json) · [Second Deep Pass →](research/2026-08-28-second-deep-pass.json)

## 🔎 Metodo di ricerca potenziato

Il secondo pass è strutturato su provincia/città e famiglie di query multiple: annunci freelance/contract, pagine ufficiali careers/collaboration, outsourcing/white-label/overflow, WordPress/frontend/UX/UI/web-app, communication/dissemination e pipeline locale separata senza sito.

**Più volume di ricerca, non più spam.** Un'organizzazione entra nella pipeline solo con un motivo concreto e verificabile.

## 📬 Stato CRM verificato

| Metrica | Valore |
|---|---:|
| Partner qualificati canonici Italia/Spagna | **30** |
| Opportunity canoniche complessive | **36** |
| Opportunity con first contact canonico verificato | **24** |
| First-contact-style send events reali oggi in Sent | **36** |
| Organizzazioni/destinatari unici first-contacted oggi | **34** |
| Destinatari post-snapshot ancora da canonicalizzare | **10** |
| Duplicate first-contact violations rilevate | **2** |
| Positive reply / referral qualificato | **1** |
| Meeting | **0** |
| Proposte | **0** |
| Contratti vinti | **0** |
| Revenue vinta | **€0** |

**Ultima evidenza Sent riconciliata:** UID **115**, `office@bscwebdesign.com`, 28 agosto 2026 19:05 Europe/Madrid. Il destinatario è in emergency suppression fino a canonicalizzazione completa.

## 🔴 BEYOND BARRIERS

Referral positivo verso due figure Communication & Dissemination.

- Stato: `POSITIVE_REPLY_USER_ACTION_REQUIRED`
- Owner: **USER**
- SLA: **BREACHED**
- Automazione risposta: **FORBIDDEN**

[Opportunity →](opportunities/OPP-EU-BEYOND-BARRIERS-WEB.json) · [Referral log →](replies/2026-08-28-beyond-barriers-referral.json)

## 🛡️ Anti-duplicate / Quality Gates

Qualsiasi nuovo primo contatto deve superare QG-01..QG-12 e controllare **primary suppression + emergency suppression + historical Sent/outreach**.

- Due violazioni storiche restano preservate come evidenza: **Persuadis** e **Marmellata Lab**.
- **10** destinatari unici post-snapshot sono bloccati da emergency suppression finché non vengono canonicalizzati.
- `BATMAN / nobody@knows.us` resta `REVIEW_REQUIRED`.

[Primary Suppression →](governance/suppression-registry.json) · [Emergency Suppression →](governance/suppression-emergency-2026-08-28.json) · [Quality Gates →](governance/OUTREACH_QUALITY_GATES.md)

## 🧠 Decision Engine v3

[Lead Health →](views/lead-health.json) · [Commercial SLA →](views/commercial-sla.json) · [Economics →](views/pipeline-economics.json) · [Funnel →](views/funnel.json)

- Lead Health BEYOND BARRIERS: **92 / CRITICAL**, ricostruibile dal modello.
- Probability model: **UNCALIBRATED**.
- Weighted pipeline: **null**.
- Nessun valore economico inventato.

## 🏪 Local businesses senza sito

Pipeline separata e quality-gated. Attualmente **0** prospect hanno superato la verifica multi-source completa; nessun cold outreach locale viene auto-inviato senza contesto appropriato.

[Local No-Website Index →](local-no-website/master-index.json)

## 🚚 Migrazione repository

La separazione definitiva verso `pinolissimo/vds-commercial-intelligence` è attiva. `pinolissimo/eu-funding-observatory` main non contiene il CRM commerciale. La branch temporanea `commercial-intelligence` dell'Observatory resta solo come sorgente di migrazione/storico fino a parity completa.

La migrazione dei record canonici company/opportunity è ancora **IN_PROGRESS**; non viene dichiarata parity finché i record storici mancanti non sono stati trasferiti e verificati.

[MIGRATION STATUS →](MIGRATION_STATUS.json)

## 🧪 QA 20:58

Audit: [2026-08-28-2058.md](audits/2026-08-28-2058.md)

Correzioni deterministiche applicate:

- schema opportunity esteso correttamente a CRM v3;
- Sent UID 115 aggiunto alla emergency suppression;
- regional coverage riallineata a Studiart e Vaivén;
- master, funnel, economics, action queue e Next Best Actions riallineati;
- nessuna email inviata o risposta commerciale modificata durante QA.

## Principio operativo

**Nessun volume commerciale giustifica una regressione di qualità. Più ricerca, più opportunità qualificate, più contatti utili — ma zero doppio first-contact e zero dati inventati.**
