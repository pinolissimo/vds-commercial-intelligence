# VDS Source Coverage

> Derived view. Canonical commercial state remains in company/project/opportunity/contact/campaign records. This file tracks research coverage and source performance only.

## Source Intelligence status

- Multi-source protocol: **ACTIVE**
- Independence/lineage deduplication: **REQUIRED**
- Cross-source qualification gate: **REQUIRED**
- Source Confidence Score: **OPERATING INDEX, NOT PROBABILITY**
- Territory × source-family matrix: **ACTIVE FOR ITALY + SPAIN**

## Source families

| Family | Purpose | Default priority | Coverage target |
|---|---|---:|---:|
| Official company/career/partner | identity + current need + route | VERY HIGH | all actionable leads |
| Specialist jobs | discovery + freshness | HIGH | all territories |
| Freelance/contract marketplaces | recurring freelance/contract work | HIGH | all realistic territories |
| Professional networks | discovery + corroboration + buyer path | HIGH | all territories |
| Agency/outsourcing/white-label | recurring commercial collaboration | VERY HIGH | all territories |
| Procurement/tenders | paid external delivery | VERY HIGH | all territories |
| EU project registries | grant/project identity + timing | VERY HIGH | EU track |
| Programme portals | funded-project discovery | HIGH | EU track |
| Chambers/clusters | local company ecosystems | MEDIUM | under-covered territories |
| Incubators/accelerators | growth/funding signals | MEDIUM | innovation hubs |
| University/research directories | beneficiary + decision path | HIGH | EU track |
| News/social | early signals + freshness | MEDIUM | corroboration |
| Local business directories | local discovery | LOW | gap filling |
| Search routers | route discovery only | LOW | never final evidence |

## Quality rules

A territory is not `LOW_OPPORTUNITY` merely because few leads were found. If source-family coverage is incomplete it remains `UNDER_SEARCHED`.

A lead is not stronger merely because the same listing appears on multiple mirrors. Evidence is counted by independent information lineage.

Preferred promotion pattern:
`primary/institutional identity + independent need/freshness corroboration + verified contact/application/buyer route`.

## Seed source registry

Machine-readable registry: [`config/source-registry.json`](../config/source-registry.json)
Protocol: [`project/SOURCE_INTELLIGENCE_PROTOCOL.md`](../project/SOURCE_INTELLIGENCE_PROTOCOL.md)

Initial high-value sources include CORDIS, EU Funding & Tenders, TED, Acquisti in Rete/MEPA, Plataforma de Contratación del Sector Público, LinkedIn, InfoJobs España, Tecnoempleo, Workana and Malt. The registry is designed to expand only when a source contributes a distinct discovery or evidence function.

## Yield learning

For every source/family the engine will accumulate material counters only:
`discoveries → qualified → contacted → replies → positive replies → meetings → proposals → wins`.

Search allocation should exploit proven high-yield combinations while preserving exploration of under-tested territories and source families.

## QA requirements

QA must fail or warn when:
- a lead was promoted using mirrored evidence presented as independent;
- a `QUALIFIED` lead lacks sufficient source basis;
- freshness is stale or missing;
- a territory is marked complete without source-family coverage evidence;
- a contact route is inferred but represented as verified;
- source counters cannot be reconciled to canonical CRM events;
- a source score is used to bypass duplicate prevention or outreach gates.
