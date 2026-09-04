# VDS — High-Value Human Review Queue

Updated: 2026-09-04

This report lists commercially strong opportunities that automation could not safely execute but that may deserve a reasoned owner review.

## Operating rule

Only **SOFT-BLOCKED** opportunities belong here. Explicit no-freelance/no-agency/no-external-collaborator statements, opt-outs, legal prohibitions, unresolved identity, guessed contacts and duplicate first contacts are **not** recoverable through this queue.

For every item the report shows why it is attractive, why automation stopped, verified facts vs inference, the verified route/contact, safe alternative angles, checks required before contact and a recommended owner decision.

## Pending review — ranked

### 1. Grownnectia — IT — HOT — 84.0
**Why high value:** recurring P.IVA signal, strong WordPress + infrastructure fit, high continuity/economic potential.  
**Automatic block:** `JOB_PLATFORM_APPLY_REQUIRED`.  
**Verified route:** job-platform application.  
**Human review:** first verify the vacancy on an official employer source and current P.IVA/role terms. If still current, apply manually. Consider a separate B2B capacity approach only if the official company site independently authorizes that kind of professional contact.  
**Do not bypass:** do not replace the platform with a guessed/generic email.  
**Suggested decision:** `MANUAL_APPLY` after freshness verification.

### 2. Global Service Impresa — IT — HOT — 83.5
**Why high value:** explicit freelance-developer demand, strong VDS fit, official route and good recurring potential.  
**Automatic block:** `OFFICIAL_APPLICATION_FORM_REQUIRED`.  
**Verified route:** https://www.globalserviceimpresa.it/lavora-con-noi/  
**Human review:** confirm the form is still open and submit manually with the most relevant Italian CV/portfolio.  
**Do not bypass:** use the official form rather than a generic email for automation convenience.  
**Suggested decision:** `MANUAL_APPLY`.

### 3. Zmot Lab — IT — HOT — 81.6
**Why high value:** fresh P.IVA demand and good web-development overlap.  
**Automatic block:** `OFFICIAL_APPLICATION_FORM_REQUIRED` + `FIT_CAVEAT_SENIOR_REQUIREMENTS`.  
**Verified route:** https://zmotlab.it/lavora-con-noi/sviluppatore-senior/  
**Human review:** compare mandatory senior requirements against Giuseppe's real CV. If the core fit is defensible, apply manually and position VDS on the matching web/frontend/performance strengths without overstating unsupported stack depth.  
**Do not bypass:** no fabricated seniority/technologies and no generic-email substitution without independent authority.  
**Suggested decision:** `MANUAL_APPLY` if mandatory-fit review passes.

### 4. Mindrift — Remote — HOT — 76.7
**Why high value:** current freelance model, remote accessibility and useful web/design fit.  
**Automatic block:** `PLATFORM_APPLY_REQUIRED`.  
**Verified route:** https://mindrift.ai/apply  
**Human review:** check current project availability, compensation/commitment and select the most relevant platform profile.  
**Do not bypass:** do not send an application to support/legal/generic mailboxes.  
**Suggested decision:** `MANUAL_APPLY`.

### 5. UGECE Agency — ES — strategic exception — 70.8
**Why high value:** fit 94/100 and recurring/economic potential 95/100; historical freelance WordPress/technical-SEO usage plus a current official business email.  
**Automatic block:** `CURRENT_OPENING_NOT_PROVEN`; the specific freelance signal is about six months old.  
**Verified contact:** hello@ugeceagency.com via https://ugeceagency.com/  
**Human review:** search latest careers/LinkedIn/company posts for fresh evidence. If no current vacancy exists but the official business route is appropriate, evaluate a low-pressure B2B overflow/availability proposal that does **not** claim UGECE is currently looking for freelancers.  
**Do not bypass:** historical demand must never be presented as current fact.  
**Suggested decision:** `HOLD` pending fresh research, then possible `APPROVE_OUTREACH` if the B2B angle is independently justified.

## Decision states

- `PENDING`
- `APPROVE_OUTREACH`
- `MANUAL_APPLY`
- `HOLD`
- `REJECT`

Canonical protocol: `project/HUMAN_REVIEW_HIGH_VALUE_PROTOCOL.md`  
Machine-readable queue: `views/human-review-high-value.json`
