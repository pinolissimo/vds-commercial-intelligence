# VDS Attachment Safety Protocol

Version: 1.0
Owner rule: ABSOLUTE / FAIL-CLOSED
Effective: 2026-09-04

## Purpose
No VDS professional outbound message may contain an attachment unless that exact file has passed technical integrity validation, has been shown to Giuseppe Allocca in ChatGPT for visual/content inspection, and has received explicit owner approval for that exact immutable file.

## Absolute rule
**ONLY VERIFIED, HEALTHY, OWNER-APPROVED, BYTE-IDENTICAL FILES MAY BE SENT AS ATTACHMENTS.**

This applies to every format without exception: PDF, DOC/DOCX, XLS/XLSX, PPT/PPTX, JPG/JPEG, PNG, WEBP, SVG, TXT, CSV, ZIP and any other attachment type.

## Mandatory state machine
`CANDIDATE_FILE -> TECHNICAL_VALIDATION -> CHAT_PREVIEW -> OWNER_APPROVAL -> IMMUTABLE_APPROVED -> PRE_SEND_HASH_CHECK -> SEND_EXACT_BYTES -> SENT_ATTACHMENT_VERIFICATION`

If any state is missing, uncertain or fails: **DO NOT ATTACH / DO NOT SEND THE FILE.**

## 1. Technical validation before owner review
The exact candidate file must be validated using format-appropriate checks before it is shown for approval.

Minimum universal checks:
- file exists and size is non-zero;
- MIME/type and extension are coherent;
- magic/signature bytes are valid where the format defines them;
- compute SHA-256 of the exact bytes;
- parse/open the file with an appropriate independent reader/library;
- no parser error, truncation, malformed container, CRC/container failure or missing mandatory structure;
- render/extract enough content to confirm the file is viewable and not blank/corrupt.

Format-specific examples:
- PDF: parser opens all pages; page count > 0; render representative/all pages where practical; no broken xref/page-tree error.
- JPG/PNG/WEBP/images: decoder fully loads and verifies dimensions; image can be rendered; no truncated-image error.
- DOCX/XLSX/PPTX: ZIP/OpenXML container validates; required package parts exist; application-level parser can open; render/inspect relevant content where practical.
- ZIP/archive: container integrity/CRC test passes and contained file list is readable.

A file that merely has a filename or valid Base64 is NOT considered validated.

## 2. Mandatory chat preview
Before any external send, ChatGPT must show the exact validated attachment to Giuseppe Allocca in chat in a form that allows meaningful inspection.

Examples:
- image/photo: display the exact image;
- PDF/document: provide the exact file and, when useful, rendered page previews or a readable extraction;
- spreadsheet/slides: provide the exact file plus a meaningful preview of sheets/slides.

The assistant must explicitly identify the proposed attachment filename and SHA-256 when asking for approval.

## 3. Explicit owner approval
Only Giuseppe Allocca can authorize attachment use. Approval must refer to the exact presented file, e.g. `APPROVO QUESTO ALLEGATO` or equivalent unambiguous wording.

No inferred approval. No approval from an earlier version. No approval of “the screenshot” in general. The approval binds to the exact filename + SHA-256 bytes recorded in `governance/approved-attachments.json`.

## 4. Immutability after approval
After approval, the file is immutable.

Forbidden after approval:
- conversion;
- recompression;
- image resize;
- metadata rewrite;
- PDF regeneration;
- DOCX/PDF export;
- Base64 roundtrip that does not provably preserve exact bytes;
- renaming if the transport implementation can alter content or MIME packaging;
- any structural edit, optimization or transformation.

If any modification is required, it becomes a NEW candidate file and must restart from TECHNICAL_VALIDATION and OWNER_APPROVAL.

## 5. Pre-send identity check
Immediately before sending:
- re-read the approved file from the same immutable source;
- recompute SHA-256 and size;
- require exact equality with the owner-approved registry entry;
- require approval status `APPROVED` and not revoked/consumed incorrectly;
- ensure Hostinger attachment payload is generated from those exact approved bytes.

Hash or size mismatch = HARD BLOCK.

## 6. Send rule for automations
Active automations MAY NOT create, convert, tailor, regenerate, compress or attach files autonomously.

An automation may attach a file only when `governance/approved-attachments.json` contains a current explicit owner approval with:
- exact SHA-256;
- exact size;
- exact filename;
- approved source/path/reference;
- intended recipient or approved scope;
- approval timestamp;
- status `APPROVED`.

If that registry evidence is absent, sender must use attachment-free email or a previously verified public link if policy permits. It must never substitute a newly generated attachment.

## 7. Post-send verification
A successful provider API response alone is insufficient.

After send:
- verify message exists in Hostinger Sent;
- verify attachment filename, content type and non-zero size;
- when provider tooling allows retrieving the sent attachment bytes, retrieve them and compare SHA-256 to the approved SHA-256;
- if provider does not expose enough bytes to prove identity, record that limitation and never claim byte-level post-send validation. Pre-send byte identity remains mandatory.

Any ambiguous/corrupt sent attachment state => `ATTACHMENT_DELIVERY_STATE_UNKNOWN`; NEVER blindly send a correction or replacement. Owner must decide the next action.

## 8. No automatic repair/retry
If an attachment fails before or after send, the system MUST NOT send a second email, correction, replacement or follow-up automatically. It must stop and report the failure to Giuseppe.

## 9. Audit fields
Every approved attachment event should record:
- filename;
- format/MIME;
- byte size;
- SHA-256;
- validation methods/results;
- preview evidence/reference;
- owner approval wording/timestamp;
- intended recipient/scope;
- immutable source reference;
- pre-send revalidation result;
- provider UID;
- post-send attachment metadata/hash if obtainable.

## North-star invariant
**If we cannot prove the file is healthy before send and prove that the bytes being sent are exactly the bytes Giuseppe approved, the file is not sent.**