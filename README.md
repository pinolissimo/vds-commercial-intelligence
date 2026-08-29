# VDS Commercial Intelligence — Revenue Command Center

> **Single source of truth:** `pinolissimo/vds-commercial-intelligence` · `main`  
> **North Star:** `qualified conversations → meetings → proposals → contracts → € won`  
> **VDS7:** precisione > volume · evidenza > inferenza · **duplicate FIRST_CONTACT tolerance = 0**

**Data snapshot:** 29 agosto 2026 · 01:58 Europe/Madrid  
**Research:** `RECURSIVE SECOND DEEP PASS + FUNDED EU EARLY-PROJECT SCAN`  
**Scanner outreach:** **0 — research/qualification only**

---

## 🎛️ Executive Dashboard

| 🎯 Success Index | 📈 Probabilità operativa ≥1 nuovo cliente* | 🧲 Opportunity | ✉️ First contact canonici |
|---:|---:|---:|---:|
| **71%** | **79%** | **44** | **24** |
| `███████░░░` | `████████░░` | **20** qualificate non contattate | **55%** pipeline attivata |

| 🔥 Positive signal | 🤝 Meeting | 📄 Proposal | 💶 Revenue won |
|---:|---:|---:|---:|
| **1 referral positivo** | **0** | **0** | **€0** |

> * **79% = operational pipeline proxy, UNCALIBRATED, confidence LOW.** Non è una previsione statistica empirica. Usa esclusivamente i priors operativi già definiti nel CRM e viene mostrata per orientare il lavoro, non per valorizzare economicamente la pipeline. [Indicatori →](views/success-indicators.json) · [Modello →](config/dashboard-success-model.json)

### 🎯 GOAL TODAY

**≥ 1 nuovo cliente / incarico retribuito** — 🟡 **PARTIAL PROGRESS**  
Segnale più forte: **BEYOND BARRIERS → referral positivo a due figure Communication & Dissemination**. Nessun meeting, proposal o win ancora confermato.

---

## 🔻 Funnel commerciale

| Stage | Volume | Conversione / stato | Visuale |
|---|---:|---:|---|
| Opportunity canoniche | **44** | 100% | `██████████` |
| First contact verificati | **24** | **54.5%** delle opportunity | `█████░░░░░` |
| Qualificate non contattate | **20** | **45.5%** della pipeline | `█████░░░░░` |
| Reply thread | **1** | **4.17%** dei contattati | `█░░░░░░░░░` |
| Positive reply / referral | **1** | **4.17%** dei contattati | `█░░░░░░░░░` |
| Meeting | **0** | 0% | `░░░░░░░░░░` |
| Proposal | **0** | 0% | `░░░░░░░░░░` |
| Won | **0** | 0% | `░░░░░░░░░░` |

**Conversion bottleneck attuale:** trasformare **positive referral + lead HOT/HOT+** in conversazioni reali e meeting.

---

## 🇪🇺 EU Projects vs 🤝 Collaborations

| Workstream | Pipeline | Contacted | Ready / research | Positive signal | Stato |
|---|---:|---:|---:|---:|---|
| 🇪🇺 **EU Projects** | **6 canonical commercial opportunities** | **6** | early-funded watchlist attiva | **1** | 🔥 **Referral da gestire** |
| 🤝 **Collaborations / Jobs** | **38 active freelance / outsourcing opportunities** | **18 canonical partner accounts** | **20 qualified not contacted** | **0** | 🟢 **Alta capacità di attivazione** |

### 🇪🇺 Early-funded EU watch
Progetti in riesame con partenza **1 settembre 2026**: **NAVI**, **SENSORAMA**, **HUBS4BUILD**. Nessuna promozione automatica a contattabile finché non è verificata la catena:

`digital WP/task → beneficiary owner → contact/procurement path`

[EU Watchlist →](eu-projects/early-funded-watchlist-2026-08-28.json)

---

## ⚡ Next Best Actions

| # | Azione | Motivo | Priorità |
|---:|---|---|---|
| **1** | **HANDLE_REFERRAL — BEYOND BARRIERS** | positive referral già ricevuto | 🔴 **CRITICAL · SLA BREACHED** |
| **2** | **RECONCILE_MAILBOX / SUPPRESSION** | chiudere criticità QA prima di nuovi invii | 🔴 **CRITICAL QA** |
| **3** | **Grownnectia — Roma** | P.IVA continuativa · WordPress + infra + software | 🔥 **Score 99** |
| **4** | **ReMedia Italia — Roma/Remoto** | very high fit | 🔥 **Score 99** |
| **5** | **Visioni — Palermo** | active P.IVA freelance | 🔥 **Score 99** |

**Next tier:** DNA Agency · Studiart · Hays España · Vaivén Estudio.  
[Full Next Best Actions →](views/next-best-actions.json)

---

## 🆕 Lead ad alto potenziale — ultimo pass

| Lead | Segnale | Stato |
|---|---|---|
| **Grownnectia Srl — Roma** | P.IVA continuativa; hosting/domains/DNS/mail, WordPress via codice, WooCommerce, software | **READY_FOR_DAILY_OUTREACH_REVIEW · 99** |
| **DNA Agency SRLS — Napoli** | Web Developer & WordPress Specialist Freelance/P.IVA; collaborazione stabile e duratura | **READY_FOR_DAILY_OUTREACH_REVIEW · 97** |

[Grownnectia →](opportunities/OPP-IT-GROWNNECTIA-WP-INFRA-FREELANCE.json) · [DNA Agency →](opportunities/OPP-IT-DNAAGENCY-WP-FREELANCE.json)

---

## 🗺️ Coverage commerciale

| Area | Territori qualificati | Copertura | Account verificati | Visuale |
|---|---:|---:|---:|---|
| 🇮🇹 Italia | **13 / 20** | **65%** | **22** | `███████░░░` |
| 🇪🇸 Spagna | **10 / 19** | **52.6%** | **14** | `█████░░░░░` |

**16 territori** restano a zero e sono ancora oggetto di deep search.  
[Regional Coverage →](views/regional-coverage.json)

---

## 🛡️ Safety / QA — ZERO DUPLICATE FIRST CONTACT

| Controllo | Stato |
|---|---|
| Duplicate FIRST_CONTACT tolerance | **0 — HARD RULE** |
| Global duplicate hard gate | 🟢 **ACTIVE** |
| Check prima dell'invio | company/project + all opportunities + timeline + campaigns + suppression + Sent history |
| Sent verification | 🟢 **MANDATORY** |
| Historical duplicate violations preserved | **2** — Persuadis + Marmellata Lab |
| Nuovo invio quando identità/storia è ambigua | 🔴 **BLOCKED → REVIEW_REQUIRED** |
| Positive / ambiguous reply auto-response | 🔴 **FORBIDDEN** |
| Probability invention tolerance | **0** |

> Le **2 violazioni sono storiche e conservate come evidenza di audit**. Il sistema attuale deve bloccare qualsiasi nuovo doppio FIRST_CONTACT anche se cambia persona, email, annuncio, campagna, territorio o workstream.

### QA aperto
🔴 **RECONCILE_POST_1345_OUTREACH_AND_SUPPRESSION** — criticità ancora da riconciliare.  
🟢 Lo scanner non può inviare outreach.  
🟢 Solo `VDS Partner Hunt` può iniziare un FIRST_CONTACT e solo dopo il global duplicate gate.  
[Automation Governance →](project/AUTOMATIONS.md) · [QA Standard →](QA_AUDIT_STANDARD.md)

---

## 🔴 User Action Required — BEYOND BARRIERS

**Lead Health: 92 / 100 · CRITICAL**  
**State:** `POSITIVE_REPLY_USER_ACTION_REQUIRED`  
**Signal:** referral positivo verso due figure Communication & Dissemination.  
**Automation response:** **FORBIDDEN**.

[Opportunity →](opportunities/OPP-EU-BEYOND-BARRIERS-WEB.json) · [Lead Health →](views/lead-health.json)

---

## 📊 Success & Probability Model

### Success Index — **71%**
Indice operativo, **non una probabilità**. Misura quanto il sistema è vicino a produrre conversione in base a pipeline, attivazione, segnali positivi, profondità del funnel e integrità QA.

| Componente | Punti |
|---|---:|
| Qualified pipeline supply | **25 / 25** |
| Outreach activation | **10.91 / 20** |
| Positive commercial signal | **20 / 20** |
| Funnel depth | **10 / 20** |
| QA integrity | **5 / 15** |
| **Totale** | **70.91 → 71%** |

### Probabilità operativa ≥1 nuovo cliente — **79%***

Formula corrente:

`1 - (1-0.02)^20 × (1-0.04)^23 × (1-0.20)^1 = 79.1%`

Priors CRM usati:

| Stage | Operational prior |
|---|---:|
| READY_TO_CONTACT | **2%** |
| CONTACTED | **4%** |
| POSITIVE_REPLY_USER_ACTION_REQUIRED | **20%** |
| MEETING | **40%** |
| PROPOSAL | **60%** |

⚠️ **UNCALIBRATED · LOW CONFIDENCE.** L'approssimazione assume indipendenza tra opportunity e i tassi osservati sono ancora statisticamente insufficienti. La percentuale diventerà una vera `calibrated_probability_pct` solo quando il CRM avrà campioni/outcome sufficienti. Il `weighted_pipeline_value` resta correttamente **null**.

[Probability Calibration →](config/probability-calibration.json) · [Success Model →](config/dashboard-success-model.json)

---

## 🤖 Automation Layer

| Servizio | Frequenza | Funzione | FIRST_CONTACT |
|---|---|---|---|
| **VDS Opportunity Scanner** | hourly | ricerca + qualificazione | 🔴 **NO** |
| **VDS Partner Hunt** | daily | final review + gated outreach | 🟢 **YES, only after hard gate** |
| **VDS Reply Watch** | hourly | reply/bounce/referral reconciliation | 🔴 **NO** |
| **VDS QA + 3 Daily Reports** | ~09:00 · 14:00 · 20:00 | QA + report | 🔴 **NO** |

Legacy EU-specific overlapping automations restano disattivate per evitare pipeline concorrenti e duplicazioni.

[Project Workspace →](project/README.md) · [Chat Map →](project/CHAT_MAP.md) · [Automation Governance →](project/AUTOMATIONS.md)

---

## Principio operativo

> **Ricerca ampia. Qualificazione severa. Outreach mirato. Zero doppio first-contact. Conversione > attività. Revenue > vanity metrics.**
