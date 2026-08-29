# Automation Orchestration — VDS Job & Client Acquisition

## Principle
The scheduled automations are permanent services of the VDS commercial system. Do not create overlapping replacements when an existing automation already owns that responsibility.

All automations use `pinolissimo/vds-commercial-intelligence` branch `main` as the commercial single source of truth.

## Active commercial automations

### VDS Opportunity Scanner
Cadence: hourly.
Role: recursive discovery + qualification only.

Allowed:
- research;
- verify freshness/identity/need/contact route;
- deduplicate;
- score/classify;
- update CRM/research/dashboard when materially changed.

Forbidden:
- outreach email;
- form submission;
- auto-reply;
- any new first-contact action.

This is the feeder for both `EU_PROJECTS` and `COLLABORATIONS` workstreams.

### VDS Partner Hunt
Cadence: daily.
Role: unified final acquisition/outreach pass across both workstreams.

This is the ONLY scheduled automation permitted to initiate first-contact outreach, and only when all qualification/outreach gates pass.

Before every FIRST_CONTACT it MUST check:
1. canonical company/project record;
2. all related opportunities;
3. contact timeline;
4. campaign/outreach logs;
5. primary suppression registry;
6. emergency suppression registry;
7. Sent mailbox evidence/history.

Hard invariant: **one organization = no duplicate FIRST_CONTACT**, even when a different opportunity, email address, person, job listing or workstream is discovered later.

If an organization has already received a first contact, any later action is a follow-up, referral path, routed-contact continuation or new explicitly approved campaign action — never a silent second first-contact.

### VDS Reply Watch
Cadence: hourly condition watch.
Role: reconcile replies/bounces/referrals and update CRM state.

Forbidden:
- new first contact.

Positive/potentially positive/referral/pricing/proposal/call/next-step replies: never auto-reply; set `POSITIVE_REPLY_USER_ACTION_REQUIRED` or the specific review/action state.

Any reply cancels pending no-response follow-up.

### VDS QA Audit
Cadence: daily at approximately 09:00, 13:00, 17:00 and 21:00.
Role: independent VDS7 quality gate.

Mandatory checks include:
- company/opportunity/contact/campaign deduplication;
- first-contact uniqueness;
- suppression consistency;
- Sent verification for every `SENT` claim;
- state-transition validity;
- source freshness;
- dashboard/master/view reconciliation;
- repository separation;
- no invented facts/economics/probabilities.

Forbidden:
- new commercial outreach.

## Disabled legacy automations
Legacy EU-specific scanner/reply-watcher tasks remain disabled when their scope is already covered by the unified active automations. They must NOT be re-enabled in parallel unless the unified architecture is intentionally changed and overlap/deduplication risk is reviewed first.

This prevents:
- duplicate discovery pipelines;
- conflicting CRM writes;
- double reply handling;
- duplicate first contacts;
- inconsistent dashboards.

## Single-writer responsibility matrix

| Action | Scanner | Partner Hunt | Reply Watch | QA Audit |
|---|---:|---:|---:|---:|
| Discover leads | YES | YES | NO | NO |
| Qualify/verify | YES | YES | event-only | audit-only |
| Create FIRST_CONTACT | **NO** | **YES, gated** | **NO** | **NO** |
| Follow-up | NO | YES, gated | cancel/update | audit-only |
| Auto-reply negative | NO | policy-controlled | policy-controlled | NO |
| Positive reply response | **NO** | **NO AUTO** | **NO AUTO** | **NO** |
| CRM reconciliation | YES | YES | YES | YES |
| QA/dedup enforcement | pre-promotion | pre-send | event correlation | independent audit |

## Absolute duplicate-prevention invariant
No automation, chat or manual workflow may send or classify a message as a new first contact until the global CRM + suppression + Sent-history check has passed.

The deduplication key is the **organization/project commercial identity**, not merely an email address. Changing recipient, role, address, source listing or workstream does not reset first-contact history.

When uncertain, default state is `REVIEW_REQUIRED` / no send.
