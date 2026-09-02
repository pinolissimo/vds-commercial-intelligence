# VDS Candidate CV Master Set

Canonical CV source set for professional applications and collaboration outreach.

## HARD OWNER POLICY — APPROVED ORIGINALS ONLY

The approved original CV masters remain immutable source documents. Automatic VDS applications no longer attach CV/document PDFs: they use verified public GitHub links only.

Language mapping:
- Spanish opportunities → approved Spanish CV link.
- Italian opportunities → approved Italian CV link.
- English/international opportunities → approved English CV link.

Never compact, rewrite, summarize, regenerate, re-layout or create a mini/dispatch-safe derivative automatically. Candidate-specific variants require explicit owner authorization.

## Canonical public CV links

- Spanish: https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_CV_Generico_ES.pdf
- Italian: https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_CV_Generico_IT.pdf
- English: https://github.com/pinolissimo/Portfolio/blob/main/documents/Giuseppe_Allocca_Master_CV_EN.pdf
- Public manifest: https://github.com/pinolissimo/Portfolio/blob/main/documents/public-document-manifest.json

## Automatic delivery contract

Before a LIVE automatic send the dispatcher must:
1. resolve the required language;
2. read `assets/cv/document-qa-manifest.json` and the canonical public manifest;
3. verify the mapped public GitHub PDF still exists and matches expected filename/byte size;
4. include the verified public URL when the opportunity requests or materially benefits from a CV;
5. send with `attachments=[]`;
6. verify the message in official Hostinger Sent and confirm the attachments array is empty.

If the public link is broken or missing, this is a repairable dependency failure, not a reason to strand the opportunity indefinitely. Repair canonical link state and retry on the next safe dispatcher cycle.

Google Drive remains forbidden for automated retrieval without explicit owner permission.

## Incident record — 2026-09-01

Unauthorized compact/mini PDF derivatives were used in the first live batch. Those files are permanently disallowed. This incident is retained only for auditability.

## Canonical QA

Machine-readable evidence and public-link mapping: `assets/cv/document-qa-manifest.json`.
