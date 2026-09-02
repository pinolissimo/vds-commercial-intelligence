# VDS Public Document Link Policy

Version: 1.0
Effective: 2026-09-02
Status: OWNER-APPROVED / MANDATORY

## Purpose
Automatic VDS application/outreach emails must not attach CVs, diplomas, certificates, or other application documents. Documents are delivered through verified public GitHub links instead.

## Canonical public document repository
`pinolissimo/Portfolio` (public)

Intended structure:
- `documents/cv/Giuseppe_Allocca_CV_IT.pdf`
- `documents/cv/Giuseppe_Allocca_CV_ES.pdf`
- `documents/cv/Giuseppe_Allocca_CV_EN.pdf`
- `documents/credentials/` for owner-approved diplomas and certifications
- `documents/README.md` as the public document index

## Hard sending rule
1. Automatic VDS emails MUST have no CV/document attachments.
2. When a CV is requested or materially useful, include the verified public GitHub URL for the correct language.
3. Italian opportunity -> Italian CV URL.
4. Spanish opportunity -> Spanish CV URL.
5. English/international opportunity -> English CV URL.
6. A credentials index may be linked when relevant.
7. Before each send, verify that every required public URL is accessible and points to the intended approved document.
8. Missing/private/broken/unverified URL => `DOCUMENT_PUBLIC_LINK_UNAVAILABLE`; do not send that identity until fixed.
9. Never invent a future GitHub path and never send a broken placeholder URL.

## Source documents
Only owner-approved original CV masters may be published. Do not compact, rewrite, re-layout, summarize, ATS-shorten, regenerate, or otherwise alter them without explicit owner authorization.

## Credentials
Only genuine owner-provided or independently verified diplomas/certifications may be published. Never fabricate or infer credentials. Public filenames should be descriptive and professional.

## Google Drive
Google Drive is excluded from this workflow. No download, materialization, deletion, movement, modification, or other document retrieval from Google Drive is permitted without explicit owner authorization for the specific action.

## Dedup and dispatch safeguards
This policy changes document delivery only. All existing organization-level FIRST_CONTACT dedup, Hostinger Sent/Gmail Sent checks, authoritative-route verification, global dispatch lease, JIT dedup and provider verification remain mandatory.

## Historical incident context
This policy supersedes the automatic CV attachment mechanisms that caused document-quality failures and runtime blocking on 2026-09-01/02. Historical evidence remains preserved for audit purposes.
