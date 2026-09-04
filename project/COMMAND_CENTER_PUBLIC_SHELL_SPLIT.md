# VDS Command Center — public shell / private control-plane split

Status: production architecture
Date: 2026-09-04

## Purpose

Keep GitHub Pages available without exposing CRM, contacts, opportunities, command queues, metrics or operational state.

## Repositories

### Public presentation shell

`pinolissimo/vds-campaign-assets`

Published artifact source: `command-center/`.

This repository contains only the static dashboard shell and build-time asset vendoring logic. It MUST NOT receive `api/v1`, `command-center/commands`, CRM ledgers, contacts, replies, operational metrics, provider identifiers, email bodies, OpenAI secrets or any private acquisition state.

### Private production/control repository

`pinolissimo/vds-commercial-intelligence`

This remains the canonical production source of truth for tasks, CRM, projections, command bridge, dedup, sender state, replies, metrics and OpenAI Actions Secret.

The public shell accesses this repository only through the GitHub REST API after the owner supplies a fine-grained token in the browser session. The token is kept in `sessionStorage`; the OpenAI API key is never stored by the public shell and is written only as the private repository Actions Secret `OPENAI_API_KEY` using GitHub's public-key sealed-box flow.

## Invariants

- Production acquisition tasks remain in `vds-commercial-intelligence` and are not migrated to the public repository.
- A Pages/build/UI failure cannot stop discovery, ranking, reply watch or authorized sending.
- Public Pages contains no generated `api/v1` data and no `command-center/commands` state.
- Dashboard commands target the private repository workflow `vds-ai-command.yml` and are consumed through the existing idempotent task bridge.
- No dashboard action may bypass existing quality, route, dedup, suppression, reservation, sending-window or provider-verification gates.

## Deployment

The public shell Pages workflow is `.github/workflows/vds-command-center-pages.yml` in `vds-campaign-assets`. It stages only `command-center/`, downloads pinned fonts/icons/vendor JS at build time, performs static/security smoke tests and deploys the shell.

The private repository does not need GitHub Pages once the public-shell deployment is verified.
