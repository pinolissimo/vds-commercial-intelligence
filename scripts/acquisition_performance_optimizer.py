#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "views/high-frequency-discovery-latest.json"
SEM = ROOT / "views/high-frequency-discovery-qualified-seeds.json"
SOURCE = ROOT / "views/search-source-performance.json"
TERRITORY = ROOT / "views/territory-yield-radar.json"
CROSS = ROOT / "views/cross-signal-opportunities.json"
READY = ROOT / "views/it-es-partner-apply-ready-queue.json"
OUT = ROOT / "views/acquisition-performance.json"
CMD = ROOT / "config/acquisition-runtime-command.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    raw = load(RAW, {"signals": []})
    sem = load(SEM, {"semantic_pass": [], "semantic_review": [], "semantic_reject_sample": []})
    source = load(SOURCE, {"ranking": []})
    territory = load(TERRITORY, {"areas": []})

    # Legacy cross-signal/READY products remain analytics-only. They are not
    # prerequisites for the self-contained Revenue Flow and may be stale or absent.
    cross = load(CROSS, {"opportunities": []})
    ready = load(READY, {"queue": []})

    raw_by = Counter(x.get("source_id") or "unknown" for x in raw.get("signals", []))
    pass_by = Counter(x.get("source_id") or "unknown" for x in sem.get("semantic_pass", []))
    review_by = Counter(x.get("source_id") or "unknown" for x in sem.get("semantic_review", []))

    source_rows = []
    raw_rank = {x.get("source_id"): x for x in source.get("ranking", [])}
    for sid in sorted(set(raw_by) | set(raw_rank)):
        r = raw_by[sid]
        p = pass_by[sid]
        rv = review_by[sid]
        semantic_pass_rate = p / max(1, r)
        semantic_useful_rate = (p + 0.35 * rv) / max(1, r)
        raw_multiplier = float((raw_rank.get(sid) or {}).get("priority_multiplier", 1.0))
        semantic_factor = 0.55 + min(1.0, semantic_useful_rate) * 0.9
        final_multiplier = max(0.5, min(1.8, round(raw_multiplier * semantic_factor, 2)))
        source_rows.append({
            "source_id": sid,
            "raw_signals": r,
            "semantic_pass": p,
            "semantic_review": rv,
            "semantic_pass_rate": round(semantic_pass_rate, 4),
            "semantic_useful_rate": round(semantic_useful_rate, 4),
            "raw_priority_multiplier": raw_multiplier,
            "recommended_multiplier": final_multiplier
        })
    source_rows.sort(key=lambda x: (x["recommended_multiplier"], x["semantic_pass"], x["raw_signals"]), reverse=True)
    for i, row in enumerate(source_rows, 1):
        row["rank"] = i

    opps = cross.get("opportunities", []) if isinstance(cross.get("opportunities", []), list) else []
    hot_plus = sum(1 for o in opps if o.get("priority_tier") == "HOT+")
    hot = sum(1 for o in opps if o.get("priority_tier") == "HOT")
    executable = sum(1 for o in opps if o.get("next_best_action") in {"AUTO_EMAIL_NOW", "QUEUE_FOR_SEND_WINDOW"})
    manual = sum(1 for o in opps if o.get("next_best_action") == "MANUAL_APPLY_HIGH_PRIORITY")
    duplicates = sum(1 for o in opps if o.get("next_best_action") in {"DO_NOT_CONTACT_DUPLICATE", "WAIT_FOR_REPLY"})
    ready_count = len(ready.get("queue", []))

    semantic_input = int(sem.get("input_signal_count", 0))
    semantic_pass = int(sem.get("semantic_pass_count", len(sem.get("semantic_pass", []))))
    semantic_review = int(sem.get("semantic_review_count", len(sem.get("semantic_review", []))))
    semantic_reject = int(sem.get("semantic_reject_count", 0))

    # Runtime mode is driven by current discovery/semantic throughput only.
    # Legacy cross-signal/READY state is informational and MUST NOT block or gate
    # the self-contained worker.
    if semantic_input and semantic_pass / max(1, semantic_input) < 0.15:
        bottleneck = "RAW_SOURCE_PRECISION"
    elif semantic_pass >= 10:
        bottleneck = "DIRECT_QUALIFICATION_ROUTE_CLOSURE"
    else:
        bottleneck = "BALANCED_OR_INSUFFICIENT_SAMPLE"

    resolved_areas = [a for a in territory.get("areas", []) if a.get("region") not in {None, "UNRESOLVED"} and a.get("province") not in {None, "UNRESOLVED"}]
    unresolved = [a for a in territory.get("areas", []) if a.get("region") == "UNRESOLVED" or a.get("province") == "UNRESOLVED"]
    harvest = [a for a in resolved_areas if a.get("mode") == "HARVEST"][:12]
    explore = [a for a in resolved_areas if a.get("mode") in {"REVISIT", "EXPLORATION"}][:20]

    turbo = bottleneck == "DIRECT_QUALIFICATION_ROUTE_CLOSURE"
    capacity = {"exploitation_pct": 85, "exploration_pct": 10, "strategic_reserve_pct": 5} if turbo else {"exploitation_pct": 70, "exploration_pct": 20, "strategic_reserve_pct": 10}

    output = {
        "schema_version": "1.2",
        "updated_at": sem.get("updated_at") or raw.get("updated_at"),
        "north_star": "PROVIDER_VERIFIED_FIRST_CONTACTS_AND_POSITIVE_OUTCOMES",
        "funnel_snapshot": {
            "raw": len(raw.get("signals", [])),
            "semantic_input": semantic_input,
            "semantic_pass": semantic_pass,
            "semantic_review": semantic_review,
            "semantic_reject": semantic_reject,
            "legacy_cross_signal_hot_plus_advisory": hot_plus,
            "legacy_cross_signal_hot_advisory": hot,
            "legacy_cross_signal_manual_advisory": manual,
            "legacy_cross_signal_duplicate_or_waiting_advisory": duplicates,
            "legacy_cross_signal_executable_advisory": executable,
            "legacy_ready_queue_advisory": ready_count
        },
        "diagnosed_bottleneck": bottleneck,
        "adaptive_mode": "MIDDLE_FUNNEL_TURBO" if turbo else "NORMAL_ADAPTIVE",
        "source_ranking": source_rows,
        "territory": {
            "resolved_area_count": len(resolved_areas),
            "unresolved_bucket_count": len(unresolved),
            "harvest_now": harvest,
            "explore_or_revisit": explore,
            "rule": "Unresolved country-only buckets are enrichment demand, never HARVEST targets."
        },
        "recommended_actions": [
            "Consume fresh high-frequency discovery and unresolved strong backlog directly",
            "Resolve only canonical identity, freshness, truthful fit, authoritative route, dedup and channel compatibility",
            "Use provider suppression/global sent/global organization/reservations before every provider call",
            "Preserve manual application routes instead of substituting generic email",
            "Never require cross-signal, Agency Radar or a separate READY builder as an operational prerequisite"
        ]
    }
    save(OUT, output)

    runtime = {
        "schema_version": "1.3",
        "updated_at": output["updated_at"],
        "mode": "MIDDLE_FUNNEL_TURBO" if turbo else "NORMAL_ADAPTIVE",
        "worker_contract": "SELF_CONTAINED_VDS_REVENUE_FLOW",
        "revenue_flow_preflight": {
            "required": True,
            "protocol": "project/REVENUE_FLOW_SELF_HEALING_PROTOCOL.md",
            "executable": "scripts/revenue_flow_preflight.py",
            "default_mode": "--repair",
            "run_before_candidate_processing": True,
            "derived_cache_drift_is_repairable_not_global_blocker": True,
            "large_github_content_omission_is_not_empty_snapshot": True,
            "provider_calls_require_post_repair_unambiguous_state": True
        },
        "dependency_policy": {
            "agency_radar_required": False,
            "cross_signal_required": False,
            "separate_ready_builder_required": False,
            "legacy_cross_signal_and_ready_are_advisory_only": True
        },
        "operational_outcomes": ["SEND_NOW", "MANUAL_APPLY", "WAIT_RESEARCH", "REJECT"],
        "capacity": capacity,
        "diagnosed_bottleneck": bottleneck,
        "source_priority": {r["source_id"]: r["recommended_multiplier"] for r in source_rows},
        "top_sources": [r["source_id"] for r in source_rows[:6]],
        "harvest_areas": [r["area_key"] for r in harvest],
        "explore_or_revisit_areas": [r["area_key"] for r in explore[:12]],
        "turbo": {
            "enabled": turbo,
            "quality_gates_unchanged": True,
            "target_serious_candidate_decisions_per_run": 40,
            "same_run_qualification_and_send": True,
            "send_all_valid_send_now": True,
            "no_batch_minimum": True,
            "prefer_direct_authoritative_email_routes": True,
            "prefer_fresh_24h_then_7d": True,
            "manual_route_preservation": True,
            "never_promote_from_deepseek_shadow": True
        },
        "route_policy": {
            "job_or_application_lane": "Require the exact authoritative application/collaboration route; never replace an official form/platform with a generic email.",
            "b2b_agency_commercial_lane": "An official public company partnership/contact/hello email may be used as the authoritative B2B commercial route only for a genuine agency/white-label/external-capacity proposal, when no application-only route is being bypassed and all legal, identity, fit, freshness and dedup gates pass."
        },
        "instruction": "SELF_CONTAINED_REVENUE_FLOW: run the mandatory self-healing preflight first. Consume fresh discovery plus unresolved strong backlog directly; qualify, decide and route in the same run. Do not require Agency Radar, cross-signal state or a separate READY queue. Process at least 40 serious candidates when supply/runtime permits. Preserve absolute organization-level dedup, authoritative-route integrity, current need, truthful fit, legal/channel gates, provider verification and the live-send window. DeepSeek remains shadow-only."
    }
    save(CMD, runtime)
    print(json.dumps({
        "bottleneck": bottleneck,
        "mode": runtime["mode"],
        "sources": [r["source_id"] for r in source_rows[:6]],
        "semantic_pass": semantic_pass,
        "legacy_hot_plus_advisory": hot_plus,
        "legacy_hot_advisory": hot,
        "capacity": capacity,
        "self_contained": True,
        "preflight_required": True
    }))


if __name__ == "__main__":
    main()
