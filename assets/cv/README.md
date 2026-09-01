# VDS Candidate CV Master Set

Canonical CV source set for professional applications and collaboration outreach.

## Policy

- Select the CV language according to the recipient, opportunity and market.
- Spanish opportunities: use the Spanish master as the default.
- Italian opportunities: use the Italian master as the default.
- International/English-language opportunities: use the English master as the default.
- Tailoring to a specific opportunity is encouraged when it materially improves relevance.
- Tailoring must remain strictly truthful: never add qualifications, experience or certifications not supported by the master CV or verified source material.
- A QA-passed master PDF MAY be reused directly when candidate-specific tailoring is not materially necessary; do not generate a new PDF merely to satisfy process ceremony.
- Prefer an opportunity-specific PDF when tailoring materially improves relevance; any newly generated PDF becomes a new byte-level artifact and must pass document QA before sending.
- Official application/outreach email is sent from `info@visualdesignstudio.es`; the private Gmail address is BCC'd according to the established VDS outreach workflow.

## Current master baseline

Updated: 2026-08-31

Profile: Giuseppe Allocca — Web Developer / Technical IT Specialist / WordPress / IoT, founder of Visual Design Studio ES, Barcelona/Sitges.

Canonical public profile links:
- LinkedIn: https://www.linkedin.com/in/giuseppe-allocca-itechnician/
- Visual Design Studio: https://www.visualdesignstudio.es

## Available source files

The current source set supplied by Giuseppe Allocca consists of:

- `Giuseppe_Allocca_CV_Generico_ES.docx` + PDF — Spanish master
- `Giuseppe_Allocca_CV_Generico_IT.docx` + PDF — Italian master
- `Giuseppe_Allocca_Master_CV_EN.docx` + PDF — English master

Binary source files are retained as the authoritative user-supplied CV assets outside this text manifest when the GitHub connector cannot upload binary content directly.

## Canonical Document QA

Machine-readable document QA evidence: `assets/cv/document-qa-manifest.json`.

The manifest records for each QA-passed PDF:
- exact ChatGPT Library file id;
- exact byte size;
- SHA-256 hash;
- page count and PDF preflight result;
- visual render QA result;
- candidate/organization assignment for the current READY queue.

Before a LIVE Hostinger send the dispatcher must materialize the exact assigned Library file, verify size + SHA-256, base64-encode those exact bytes and attach them as `application/pdf`. After sending it must verify the message in Hostinger Sent and confirm the expected PDF attachment exists with non-zero size.

A materialization error, byte/hash mismatch, empty attachment or Sent attachment mismatch is `FAIL_CLOSED_DOCUMENT_QA` for that identity and must never trigger a blind resend.

Audit establishing the initial PASS baseline: `audits/2026-09-01-2059-document-qa.md`.
