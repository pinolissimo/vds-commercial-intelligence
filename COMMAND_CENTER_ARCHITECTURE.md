# VDS Commercial Intelligence — Command Center Architecture

## Non-negotiable production invariant

The existing acquisition/reply task architecture remains authoritative and unchanged. The Command Center is an additive control/read layer around it. No dashboard failure, AI failure, Pages failure, command failure or analytics failure may stop, weaken, bypass or replace current discovery, semantic gates, authoritative route verification, deduplication, suppression, provider verification, manual-route preservation or reply monitoring.

## Architecture

```text
EXISTING PRODUCTION TASKS (UNCHANGED)
          |
          v
Canonical repository JSON / metrics / views
          |
          +------------------------------+
          |                              |
          v                              v
Command Center Projection Builder   Existing execution workers
          |
          v
api/v1/*.json  (private read models)
          |
          v
GitHub Pages — VDS Command Center
          |
          +--> authenticated read / filter / analytics
          |
          +--> secure command dispatch (GitHub workflow_dispatch)
                    |
                    v
             VDS AI Command Action
             OpenAI API via GitHub Secret
                    |
                    v
         structured command queue / analysis
                    |
                    v
     idempotent task bridge / existing gates
```

## Security model

- `OPENAI_API_KEY` is a GitHub Actions repository secret. It is never committed and never exposed to GitHub Pages.
- On first authenticated dashboard access, the UI checks only whether the secret exists; GitHub never returns its value.
- If the secret is absent, the dashboard asks the owner for the OpenAI API key once, fetches the repository Actions public key, encrypts the key locally with the official LibSodium sealed-box mechanism (`crypto_box_seal`), and uploads only the encrypted value to the GitHub repository-secret endpoint.
- The OpenAI key is never written to `localStorage`, `sessionStorage`, repository JSON, query strings, workflow inputs or the static Pages artifact. The input is cleared after setup and plaintext byte buffers are zeroed best-effort.
- LibSodium, Chart.js, DM Sans and Material Symbols are downloaded at build time and served locally by GitHub Pages; no runtime CDN is required.
- Private CRM JSON is not copied into Pages. The dashboard reads it from the private repository through the authenticated GitHub API.
- The fine-grained GitHub token is limited to this repository and kept only in `sessionStorage`. Minimum intended repository permissions: `Contents: read`, `Actions: read/write`, `Secrets: read/write`.
- Commands requesting outbound execution are requests, not bypasses. They remain subject to the existing global organization dedup, suppression, route, freshness, geography, truthful fit, sending-window and provider-verification gates.
- AI output is never authoritative evidence of opportunity validity.

## Read model

The projection builder reads existing canonical files and emits disposable dashboard projections under `api/v1/`. These files are caches/read models and are never used as replacements for canonical data. They remain private repository data and are fetched by the dashboard only after GitHub authentication.

Primary projections:

- `api/v1/dashboard.json`
- `api/v1/today.json`
- `api/v1/opportunities.json`
- `api/v1/outbound.json`
- `api/v1/health.json`
- `api/v1/sources.json`
- `api/v1/ai-command/latest.json`

## Command bridge

Canonical bridge contract: `project/COMMAND_CENTER_TASK_BRIDGE_PROTOCOL.md`.

The AI router assigns explicit `target_workers` among:

- `AGENCY_RADAR`
- `LINKEDIN_HUNTER`
- `UNIFIED_LOOP`

Workers read `command-center/commands/pending.json` during their existing normal run and append idempotent receipts to `command-center/commands/processed.json`. Receipt identity is `(command_id, worker_id)`. Command TTL is normally 24 hours. A bridge read/write failure is non-fatal and MUST NOT stop the worker's normal acquisition cycle.

## Command classes

- `ANALYZE`: answer/diagnose using current repository snapshot; no production mutation.
- `SEARCH_DIRECTIVE`: queue an operator research/focus instruction for the existing task bridge.
- `SEND_DIRECTIVE`: queue a request to send already-valid opportunities; same current execution gates are mandatory.
- `PRIORITY_DIRECTIVE`: queue a prioritization instruction without lowering quality thresholds.
- `REFRESH`: refresh/focus the relevant existing workers without creating a replacement scheduler.
- `UNKNOWN`: no execution.

## Migration policy

There is no production migration in V1. If the execution engine is ever moved into the webapp architecture, it must first run in shadow mode and demonstrate behavioral parity on critical gates and no measurable reduction in discovery quality or downstream conversion.
