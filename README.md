# VDS Commercial Intelligence — Revenue Dashboard

> **Repository dedicata:** questo repository è il **single source of truth commerciale** di Visual Design Studio. Nessun dato CRM deve essere scritto nelle repository demo o VDS Engine.
>
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **Standard:** VDS7 · precisione > volume · evidenza > inferenza · zero doppio first-contact

**Ultimo aggiornamento:** 28 agosto 2026 · 19:24 Europe/Madrid  
**CRM:** v3 Revenue Operating System · dedicated repository  
**Audit corrente:** **FAIL_CORRECTED**

## 🎯 GOAL TODAY

| Target | Stato | Evidenza |
|---|---|---|
| **≥ 1 nuovo cliente / incarico retribuito oggi** | **PARTIAL_PROGRESS** | referral positivo BEYOND BARRIERS; nessun meeting/proposal/win ancora confermato |

## 🚨 QA ALERT — stato operativo reale

L'audit delle 17:00 ha rilevato uno scostamento materiale tra CRM e mailbox dopo lo snapshot delle 13:45.

- **11** nuovi invii first-contact-style sono comparsi in Sent dopo lo snapshot.
- **9** riguardano nuovi destinatari unici ancora da canonicalizzare/attribuire nel CRM.
- **2** sono duplicati vietati: **Persuadis** e **Marmellata Lab**.
- Un invio `BATMAN → nobody@knows.us` è `REVIEW_REQUIRED` perché manca evidenza sufficiente sul rapporto entità/contatto.
- Il referral **BEYOND BARRIERS** ha superato la SLA delle 17:00 ed è `CRITICAL`.

Contenimento: [Emergency Suppression →](governance/suppression-emergency-2026-08-28.json) · [Audit 17:00 →](audits/2026-08-28-1700.md)

## ⚡ Next Best Actions

| # | Azione | Owner | Stato |
|---:|---|---|---|
| **1** | **HANDLE_REFERRAL — BEYOND BARRIERS** | USER | **CRITICAL · SLA BREACHED** |
| **2** | **RECONCILE_POST_1345_OUTREACH_AND_SUPPRESSION** | AUTOMATION | **CRITICAL QA** |
| 3 | Nexìbo — contatto solo dopo QG + suppression/history check | AUTOMATION | HIGH |
| 4 | Web Genova — risolvere canale ufficiale | AUTOMATION | HIGH |
| 5 | Minimal Studio — application form ufficiale | USER | HIGH |

[Next Best Actions →](views/next-best-actions.json) · [Action Queue →](views/action-queue.json) · [Commercial SLA →](views/commercial-sla.json)

## 📬 Mailbox vs CRM — conteggi verificati

| Metrica | Valore |
|---|---:|
| Partner qualificati canonici Italia/Spagna | **28** |
| Opportunity canoniche totali | **34** |
| First-contact canonici/attribuiti prima del drift | **24** |
| First-contact-style send events reali oggi in Sent | **35** |
| Organizzazioni/destinatari unici first-contacted oggi | **33** |
| Nuovi destinatari post-snapshot da canonicalizzare | **9** |
| Duplicate first-contact violations | **2** |
| Positive reply / referral qualificato | **1** |
| Meeting | **0** |
| Proposte | **0** |
| Contratti vinti | **0** |
| Revenue vinta | **€0** |

**Nota statistica:** il funnel canonico resta basato sulle 24 opportunity già riconciliate. I 9 nuovi destinatari post-snapshot non entrano nei denominatori finché non sono qualificati, deduplicati e attribuiti.

## 🔴 BEYOND BARRIERS

Referral positivo verso due figure Communication & Dissemination.

- Stato: `POSITIVE_REPLY_USER_ACTION_REQUIRED`
- Owner: **USER**
- SLA: **BREACHED at 17:00**
- Automazione risposta: **FORBIDDEN**

[Opportunity →](opportunities/OPP-EU-BEYOND-BARRIERS-WEB.json) · [Referral log →](replies/2026-08-28-beyond-barriers-referral.json)

## 🛡️ Anti-duplicate / Quality Gates

La suppression primaria protegge i first-contact già riconciliati: [Primary Suppression Registry →](governance/suppression-registry.json).

La suppression di emergenza contiene i nuovi destinatari post-snapshot e documenta i duplicate events: [Emergency Suppression →](governance/suppression-emergency-2026-08-28.json).

Qualsiasi nuovo primo contatto deve superare QG-01..QG-12 e controllare **primary suppression + emergency suppression + historical Sent/outreach**.

[Quality Gates →](governance/OUTREACH_QUALITY_GATES.md)

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

- [Lead Health →](views/lead-health.json)
- [Lead Health model →](config/lead-health-model.json)
- [Probability calibration →](config/probability-calibration.json)
- [Commercial SLA →](views/commercial-sla.json)

Il modello probabilistico resta **UNCALIBRATED**. Weighted pipeline rimane `null` finché non esistono valore economico reale e probabilità calibrata difendibile.

## 🗺️ Ricerca Italia / Spagna

| Paese | Territori tracciati | Con lead qualificati | Stato |
|---|---:|---:|---|
| Italia | 20 regioni | **9** | second deep pass required |
| Spagna | 17 comunidades + Ceuta/Melilla | **8** | second deep pass required |

[Regional Coverage →](views/regional-coverage.json) · [Deep Search Log →](research/2026-08-28-regional-deep-search.json)

## 🏪 Local businesses senza sito

Pipeline separata e quality-gated. **Qualified: 0 · Contacted: 0.** Nessun prospect viene promosso senza verifica multi-source dell'assenza di un sito funzionale e business case specifico.

[Local No-Website Index →](local-no-website/master-index.json)

## 💶 Economics

- Pipeline value: **null**
- Weighted pipeline: **null**
- Proposal value: **€0**
- Won revenue: **€0**

Nessun valore economico viene inventato.

[Economics →](views/pipeline-economics.json)

## ✅ QA VDS7

**Audit 17:00:** `FAIL_CORRECTED`.

Correzioni applicate:
1. emergency suppression per i nuovi destinatari post-snapshot;
2. duplicate send events documentati e bloccati da ulteriori first-contact;
3. BEYOND BARRIERS marcato SLA breach CRITICAL;
4. eFarm rimosso dalla READY queue perché l'invio UID 109 è reale;
5. master, NBA e action queue riconciliati con la mailbox;
6. BATMAN / `nobody@knows.us` portato a `REVIEW_REQUIRED`.

Rischi residui: canonicalizzazione/attribution dei 9 nuovi destinatari; storico pre-CRM da backfillare; i due duplicati già inviati non sono reversibili ma sono contenuti.

[Audit 17:00 →](audits/2026-08-28-1700.md) · [QA Standard →](QA_AUDIT_STANDARD.md) · [Master Index →](master-index.json)

## Principio operativo

**Nessun volume commerciale giustifica una regressione di qualità. Prima conversione, ma con deduplica, evidenza, SLA e tracciabilità rigorose.**
