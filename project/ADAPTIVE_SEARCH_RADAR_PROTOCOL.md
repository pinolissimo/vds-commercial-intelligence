# VDS Adaptive Search Radar Protocol v1.0

Effective: 2026-09-04

## Purpose

Continuously improve VDS discovery yield across all Spain and Italy by combining broad geographic exploration with adaptive exploitation of the source × territory × query combinations that produce the best downstream results.

## Canonical inputs

Every VDS discovery/ranking task MUST read when available:
- `views/territory-yield-radar.json`
- `views/search-source-performance.json`
- `config/adaptive-search-runtime.json`
- `config/search-territory-frontier.json`
- `config/adaptive-search-policy.json`
- `views/high-frequency-discovery-latest.json`

The GitHub high-frequency discovery workflow refreshes these intelligence views every 15 minutes. They are prioritization inputs, not permission to weaken qualification or dedup gates.

## Geographic coverage invariant

Search scope covers ALL Spain and ALL Italy, including every autonomous community/region and province represented in `config/search-territory-frontier.json`.

No area may be permanently abandoned solely because short-term yield is low. At least 25% of search effort remains exploration/revisit capacity; approximately 75% may be concentrated adaptively on higher-yield areas.

## Territory states

The radar assigns territory modes:
- `HARVEST`: concentrate search/verification effort here now.
- `COOLDOWN`: area has recently been heavily worked; temporarily rotate away.
- `REVISIT`: cooldown expired; actively rescan for fresh demand.
- `EXPLORATION`: continue systematic coverage/sample building.
- `ROTATE_OUT`: marginal yield has fallen; move capacity elsewhere while preserving future revisit.

Workers should prioritize `HARVEST`, then `REVISIT`, then `EXPLORATION`. `COOLDOWN` and `ROTATE_OUT` receive only minimal freshness checks until eligible again.

## Yield model

Territory value is not raw volume. Ranking should increasingly reflect downstream quality:

`raw signals -> verified/open -> high fit -> HOT/HOT+ -> READY -> verified sends -> positive replies/interviews/wins`

Penalize:
- duplicate organizations;
- stale/closed opportunities;
- poor/unsupported routes;
- low-fit noise;
- source errors.

A high-volume territory with poor qualification/conversion must rank below a smaller area with better HOT/READY/reply yield.

## Harvest / rotate / revisit policy

When an area is high-yield, concentrate multiple cycles there to exploit the available reservoir. Do not exhaustively repeat identical queries; expand source families, sectors, cities and query variants within that territory.

After several harvest cycles or when marginal new qualified yield falls, enter cooldown and move exploitation capacity to the next ranked areas. After cooldown, the area becomes `REVISIT` and is checked again for newly published demand.

This creates a cyclic search wave rather than a static city priority list.

## Source ranking

Use `views/search-source-performance.json` and `config/adaptive-search-runtime.json` to prioritize validation/search depth by measured source yield.

High-yield sources receive more query variants and deeper validation. Low-yield sources retain an exploration floor so the system can detect changes in source quality over time.

Do not disable authoritative sources based on small samples.

## High-frequency GitHub reservoir

`views/high-frequency-discovery-latest.json` is a RAW public-signal reservoir refreshed every 15 minutes. Tasks should consume the strongest fresh signals from it before repeating equivalent external discovery work.

The reservoir does not certify a candidate as READY. Tasks must still verify employer identity, freshness, geographic eligibility, route, fit, legal/channel state, global dedup, and any document requirements.

## Geographic enrichment

When researching any promising organization/opportunity, workers should persist the most specific VERIFIED territory metadata available:
- country;
- region/autonomous community;
- province;
- city/cluster when known.

Never guess territory from a brand name. Verified location data improves radar accuracy and downstream allocation.

## Performance feedback

Discovery workers should record source ID/family, territory and query/strategy ID when practical. Downstream tasks should preserve this lineage when candidates become HOT, READY, SENT, REPLIED, INTERVIEW or WON so future radar versions can attribute real commercial conversion back to the source and territory that produced it.

## Safety invariants

Adaptive search NEVER weakens:
- `NO_DUPLICATE_FIRST_CONTACT_GLOBAL`;
- authoritative route requirements;
- freshness/open-state verification;
- truthful skill/fit requirements;
- provider Sent verification;
- legal/channel/geographic blockers.

Optimization changes WHERE and HOW MUCH we search, not the standards required to act.
