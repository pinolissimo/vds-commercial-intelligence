# VDS Revenue Flow — 2026-09-13 14:34Z

## Outcome
- Serious candidates evaluated: 31
- Direct-email/route harvest evaluated: 19
- SEND_NOW: 1
- Provider-verified FIRST_CONTACT: 1
- MANUAL_APPLY: 9
- WAIT_RESEARCH: 8
- REJECT: 13
- Fresh provider duplicate checks blocking send: 1 (BlitheDigital UID 193)
- Route failures: 0
- New delivery-state-unknown: 0
- New hard bounce after this run's send: 0 observed in immediate provider check

## Provider-verified send
- Provider UID: 499
- Organization: Jam e la Tempesta S.r.l.
- Recipient: info@jamelatempesta.com
- Subject: Capacità web esterna per i vostri progetti — WordPress / frontend
- Archetype: AGENCY_EXTERNAL_CAPACITY
- Variant: CREDENTIALS_CLASSIC
- Micro CTA: SEND_1_2_RELEVANT_EXAMPLES
- BCC owner: yes
- Attachments: 0
- Evidence: official organization contact page explicitly offers routes for suppliers and collaborators; Hostinger INBOX.Sent verified UID 499 at 2026-09-13T14:33:46Z.

## Selected decisions
### SEND_NOW
- Jam e la Tempesta — official supplier/collaborator route + organization-owned email + no prior Hostinger Sent evidence for recipient/domain checked before send.

### MANUAL_APPLY
- Diamente — freelance collaboration explicitly available, application form is the official route.
- Agencia Reinicia — dedicated freelance collaboration route is form-based.
- Idimad 360 — active WordPress/Prestashop programmer demand, application form.
- Adviva — explicitly collaborates continuously with external freelance/agency WordPress resources, application form.
- Graphalia — freelance/P.IVA remote collaboration, application form.
- WeLabo — professional/P.IVA application, form and CV upload.
- FMD Sysnet — WordPress/HTML-CSS-JS profiles with P.IVA, mandatory form/CV.
- Molecole — PHP/WordPress candidate route is form/CV.
- Nokeon — active web-development vacancy, mandatory form/CV.

### WAIT_RESEARCH
- Visual Blanco — authoritative live site and official email exist; collaborator page requires autónomo + WordPress but appears materially stale, so current-need freshness not strong enough for send.
- Octopus Web — uses freelance collaborators but no verified current external-capacity request.
- Web&Media — collaborators and web production evident, no current buying/capacity signal.
- SciTransfer EU — excellent EU dissemination fit and direct email, but no current external web-capacity signal.
- WIT Berry — EU website/dissemination specialist, no verified external-capacity need.
- Elements Digital — EU communication/dissemination fit, no verified external-capacity need.
- Nerade — WordPress/WooCommerce agency with official email, no current collaboration signal.
- Sabaweb — agency-partnership capable peer provider, but no evidence of buying external capacity now.

### REJECT highlights
- BlitheDigital — provider duplicate: Hostinger Sent UID 193 (2026-09-02).
- Uaoh — current role explicitly in-office/full-time, conflicts with external remote model.
- Emmè Pubblicità — explicitly no remote work.
- Marketalia — current need is Community Manager internship, not VDS fit.
- Studio Graffiti — current open position is commercial consultant, not VDS delivery fit.
- Avante — current freelance opening is content marketing, not core VDS delivery fit.
- Solo-provider/freelancer pages (Javier Félix, Javier Marcilla, Xiomara Pérez, Santiago Márquez, Marco Panichi, Roberto Botturi, Gregores One) — no verified buying signal for external VDS capacity.

## A/B and funnel
- This run: CREDENTIALS_CLASSIC = 1 send; VALUE_MICRO_COMMITMENT = 0 sends.
- No new inbound commercial message appeared after provider INBOX UID 1454 during the run.
- No new qualified positive reply, referral, call/interview, proposal, won or revenue outcome attributable to prior contacts in this run.

## Live-provider overlay
Direct replacement of `state/provider-outbound-live.json` was attempted through the connected GitHub reader, but the connector returned the large file content truncated, making an atomic latest-SHA whole-file replacement unsafe. Per no-resend policy, UID 499 remains provider-authoritative. An idempotent reconciliation event was written to `state/provider-outbound-reconciliation/uid-499.json` for watchdog merge.
