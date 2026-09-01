# VDS Candidate CV Master Set

Canonical CV source set for professional applications and collaboration outreach.

## HARD OWNER POLICY — APPROVED ORIGINALS ONLY

- The ONLY CV PDFs that may be attached automatically are the three original user-approved master PDFs referenced by `assets/cv/document-qa-manifest.json`: Spanish, Italian and English.
- Spanish opportunities: use the approved Spanish master.
- Italian opportunities: use the approved Italian master.
- International/English-language opportunities: use the approved English master.
- The approved original master PDFs are IMMUTABLE source-of-truth attachments.
- NEVER compress, summarize, compact, shorten, rewrite, re-layout, regenerate, one-page, ATS-shorten, create a `mini`, create a `dispatch-safe` derivative, or otherwise alter an approved CV automatically.
- NEVER create or send a candidate-specific CV variant unless Giuseppe Allocca explicitly authorizes that exact variant in chat before it is used.
- If an opportunity materially requires a different CV and no explicit owner authorization exists, mark `CV_VARIANT_APPROVAL_REQUIRED` and do not send that identity automatically.
- Technical convenience, attachment-size optimization, provider limits, layout preference, ATS optimization or perceived relevance NEVER constitute authorization to alter the CV.
- A clean outgoing filename may be used, but the attached PDF bytes must be byte-for-byte identical to the approved master assigned in the canonical manifest.
- Official application/outreach email is sent from `info@visualdesignstudio.es`; the private Gmail address is BCC'd according to the established VDS outreach workflow.

## Incident record — 2026-09-01 first live batch

During the first live dispatcher batch, unauthorized one-page compact/mini derivatives were generated and attached to multiple outbound applications. Those derivatives were not user-approved and must NEVER be reused as application assets. The incident evidence is retained only for auditability; it does not grant approval to the derivative files.

## Current master baseline

Updated: 2026-09-01

Profile: Giuseppe Allocca — Web Developer / Technical IT Specialist / WordPress / IoT, founder of Visual Design Studio ES, Barcelona/Sitges.

Canonical public profile links:
- LinkedIn: https://www.linkedin.com/in/giuseppe-allocca-itechnician/
- Visual Design Studio: https://www.visualdesignstudio.es

## Available approved source files

The current approved source set supplied by Giuseppe Allocca consists of:

- `Giuseppe_Allocca_CV_Generico_ES(1).pdf` — Spanish approved master
- `Giuseppe_Allocca_CV_Generico_IT(1).pdf` — Italian approved master
- `Giuseppe_Allocca_Master_CV_EN(1).pdf` — English approved master

Their editable DOCX source files may be retained for future owner-approved editing, but DOCX files are not sent unless an opportunity explicitly requires DOC/DOCX and the owner authorizes it.

Binary source files are retained as the authoritative user-supplied CV assets outside this text manifest when the GitHub connector cannot upload binary content directly.

## Canonical Document QA

Machine-readable document QA evidence: `assets/cv/document-qa-manifest.json`.

The manifest records for each approved original PDF:
- exact ChatGPT Library file id;
- exact byte size;
- SHA-256 hash;
- page count and PDF preflight result;
- visual render QA result;
- organization assignment where relevant.

Before a LIVE Hostinger send the dispatcher must materialize the exact assigned approved Library file, verify size + SHA-256, base64-encode those exact bytes and attach them as `application/pdf`. After sending it must verify the message in Hostinger Sent and confirm the expected PDF attachment exists with non-zero size.

Any derivative file, recompression, regeneration, materialization error, byte/hash mismatch, empty attachment or Sent attachment mismatch is `FAIL_CLOSED_DOCUMENT_QA` and blocks that identity. It must never trigger a blind resend.

Audit establishing the original master PASS baseline: `audits/2026-09-01-2059-document-qa.md`.
