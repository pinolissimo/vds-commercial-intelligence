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
api/v1/*.json  (read models only)
          |
          v
GitHub Pages — VDS Command Center
          |
          +--> read / filter / analytics
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
       existing task bridge / existing gates
```

## Security model

- `OPENAI_API_KEY` is a GitHub Actions repository secret. It is never committed and never exposed to GitHub Pages.
- The public/static dashboard never receives the OpenAI API key.
- Direct dashboard command dispatch uses a user-supplied fine-grained GitHub token with only `Actions: write` for this repository. The token is kept in memory for the current page session only; the Command page loads no third-party JavaScript.
- Commands requesting outbound execution are requests, not bypasses. They remain subject to the existing global organization dedup, suppression, route, freshness, geography, fit and provider-verification gates.
- AI output is never authoritative evidence of opportunity validity.

## Read model

The projection builder reads existing canonical files and emits disposable dashboard projections under `api/v1/`. These files are caches/read models and are never used as replacements for canonical data.

Primary projections:

- `api/v1/dashboard.json`
- `api/v1/today.json`
- `api/v1/opportunities.json`
- `api/v1/outbound.json`
- `api/v1/health.json`
- `api/v1/sources.json`
- `api/v1/ai-command/latest.json`

## Command classes

- `ANALYZE`: answer/diagnose using current repository snapshot; no production mutation.
- `SEARCH_DIRECTIVE`: queue an operator research/focus instruction for the existing task bridge.
- `SEND_DIRECTIVE`: queue a request to send already-valid opportunities; same current execution gates are mandatory.
- `PRIORITY_DIRECTIVE`: queue a prioritization instruction without lowering quality thresholds.
- `REFRESH`: refresh projections / optionally dispatch existing discovery workflow.
- `UNKNOWN`: no execution.

## Migration policy

There is no production migration in V1. If the execution engine is ever moved into the webapp architecture, it must first run in shadow mode and demonstrate behavioral parity on critical gates and no measurable reduction in discovery quality or downstream conversion.
