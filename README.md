# VDS Commercial Intelligence — Revenue Dashboard

> **Repository dedicata:** questo repository è il **single source of truth commerciale** di Visual Design Studio. Nessun dato CRM deve essere scritto nelle repository demo o VDS Engine.
>
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **Standard:** VDS7 · precisione > volume · evidenza > inferenza · zero doppio first-contact

**Ultimo aggiornamento:** 28 agosto 2026 · 20:35 Europe/Madrid  
**CRM:** v3 Revenue Operating System · dedicated repository  
**Migrazione:** **IN PROGRESS — core + decision views + campaigns/reports migrated; canonical records progressing**  
**Ricerca:** **SECOND DEEP PASS ACTIVE**

## 🎯 GOAL TODAY

| Target | Stato | Evidenza |
|---|---|---|
| **≥ 1 nuovo cliente / incarico retribuito oggi** | **PARTIAL_PROGRESS** | referral positivo BEYOND BARRIERS; nessun meeting/proposal/win ancora confermato |

## ⚡ Next Best Actions

| # | Azione | Owner | Stato |
|---:|---|---|---|
| **1** | **HANDLE_REFERRAL — BEYOND BARRIERS** | USER | **CRITICAL · SLA BREACHED** |
| **2** | **RECONCILE_MAILBOX / SUPPRESSION** | AUTOMATION | **CRITICAL QA** |
| **3** | **Studiart — Piacenza** | AUTOMATION | **NEW · HIGH FIT** |
| **4** | **Vaivén Estudio — Galicia** | AUTOMATION | **NEW · HIGH FIT** |
| 5 | Second deep territorial pass | AUTOMATION | ACTIVE |

[Next Best Actions →](views/next-best-actions.json) · [Action Queue →](views/action-queue.json) · [Deep Research Queue →](views/deep-research-queue.json)

## 🗺️ Copertura territoriale

**Broad pass completato su tutti i territori:** Italia **20/20 regioni**, Spagna **19/19 territori** (17 comunidades + Ceuta + Melilla).

Il broad pass non equivale a copertura esaustiva. Prima del secondo pass erano a zero lead qualificati **11 regioni italiane** e **11 territori spagnoli**.

### Second deep pass — progressi

- **Emilia-Romagna:** nuovo lead qualificato **Studiart (Piacenza)**.
- **Galicia:** nuovo lead qualificato **Vaivén Estudio (Lugo)**.
- Restano **20 territori** a zero o sotto revisione approfondita.

[Regional Coverage →](views/regional-coverage.json) · [Second Deep Pass →](research/2026-08-28-second-deep-pass.json)

## 🔎 Metodo di ricerca potenziato

Il secondo pass non usa una singola query per regione. La ricerca è strutturata su:

- provincia per provincia;
- capoluoghi + città secondarie;
- annunci freelance/contract recenti;
- pagine ufficiali `Lavora con noi` / `Colabora con nosotros`;
- segnali outsourcing / white-label / overflow;
- WordPress, frontend, UX/UI, web app e sviluppo custom;
- società communication/dissemination e fornitori progetti UE;
- pipeline separata attività locali senza sito;
- verifica indipendente prima di qualificare un lead.

**Più volume di ricerca, non più spam.** Un'organizzazione entra nella pipeline solo con un motivo concreto e verificabile.

## 📬 Stato CRM verificato prima del deep pass

| Metrica | Valore |
|---|---:|
| Partner qualificati canonici Italia/Spagna | **28** |
| Opportunity canoniche pre-deep-pass | **34** |
| First-contact-style send events reali oggi in Sent | **35** |
| Organizzazioni/destinatari unici first-contacted oggi | **33** |
| Duplicate first-contact violations rilevate | **2** |
| Positive reply / referral qualificato | **1** |
| Meeting | **0** |
| Proposte | **0** |
| Contratti vinti | **0** |
| Revenue vinta | **€0** |

I nuovi lead del secondo deep pass vengono aggiunti progressivamente ai conteggi solo dopo canonicalizzazione completa.

## 🔴 BEYOND BARRIERS

Referral positivo verso due figure Communication & Dissemination.

- Stato: `POSITIVE_REPLY_USER_ACTION_REQUIRED`
- Owner: **USER**
- Automazione risposta: **FORBIDDEN**

[Opportunity →](opportunities/OPP-EU-BEYOND-BARRIERS-WEB.json) · [Referral log →](replies/2026-08-28-beyond-barriers-referral.json)

## 🛡️ Anti-duplicate / Quality Gates

Qualsiasi nuovo primo contatto deve superare QG-01..QG-12 e controllare **primary suppression + emergency suppression + historical Sent/outreach**.

[Primary Suppression →](governance/suppression-registry.json) · [Emergency Suppression →](governance/suppression-emergency-2026-08-28.json) · [Quality Gates →](governance/OUTREACH_QUALITY_GATES.md)

## 🧠 Decision Engine v3

```text
EVIDENCE + EVENTS + FRESHNESS
            ↓
       LEAD HEALTH
            ↓
    NEXT BEST ACTION
            ↓
      COMMERCIAL SLA
            ↓
        ACTION QUEUE
            ↓
       EVENT / OUTCOME
            ↺
```

[Lead Health →](views/lead-health.json) · [Commercial SLA →](views/commercial-sla.json) · [Economics →](views/pipeline-economics.json)

## 🏪 Local businesses senza sito

Pipeline separata, quality-gated e ancora in ricerca. Nessun prospect viene promosso senza verifica multi-source dell'assenza di un sito funzionale e business case specifico.

[Local No-Website Index →](local-no-website/master-index.json)

## 🚚 Migrazione repository

La separazione definitiva verso `pinolissimo/vds-commercial-intelligence` è attiva. Dashboard, core governance, suppression, campagne, contatti, outreach, replies, report, analytics, schema e decision views sono già nel repository dedicato. La migrazione dei record canonici company/opportunity continua in parallelo alla ricerca territoriale.

[MIGRATION STATUS →](MIGRATION_STATUS.json)

## Principio operativo

**Nessun volume commerciale giustifica una regressione di qualità. Più ricerca, più opportunità qualificate, più contatti utili — ma zero doppio first-contact e zero dati inventati.**
