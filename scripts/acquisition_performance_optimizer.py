#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "views/high-frequency-discovery-latest.json"
SEM = ROOT / "views/high-frequency-discovery-qualified-seeds.json"
BUYER = ROOT / "views/buyer-intent-priority.json"
SOURCE = ROOT / "views/search-source-performance.json"
TERRITORY = ROOT / "views/territory-yield-radar.json"
CROSS = ROOT / "views/cross-signal-opportunities.json"
READY = ROOT / "views/it-es-partner-apply-ready-queue.json"
OUT = ROOT / "views/acquisition-performance.json"
CMD = ROOT / "config/acquisition-runtime-command.json"

TURBO_ENABLE_SEMANTIC_PASS = 20
TURBO_RELEASE_SEMANTIC_PASS = 8
SOURCE_EXPLORATION_FLOOR = 0.35
LOW_YIELD_MIN_SAMPLE = 40
LOW_YIELD_USEFUL_RATE = 0.03
LOW_YIELD_CAP = 0.45
WEAK_YIELD_MIN_SAMPLE = 20
WEAK_YIELD_USEFUL_RATE = 0.06
WEAK_YIELD_CAP = 0.70


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def choose_turbo(bottleneck, semantic_pass, high_intent_count, previous_turbo=False):
    """Backlog-pressure policy. Buyer intent raises priority but never changes hard gates."""
    if high_intent_count >= 8:
        return True, "HIGH_BUYER_INTENT_BACKLOG"
    if semantic_pass >= TURBO_ENABLE_SEMANTIC_PASS:
        return True, "QUALIFIED_BACKLOG_PRESSURE"
    if previous_turbo and semantic_pass >= TURBO_RELEASE_SEMANTIC_PASS:
        return True, "QUALIFIED_BACKLOG_DRAIN_HYSTERESIS"
    if bottleneck == "DIRECT_QUALIFICATION_ROUTE_CLOSURE" and semantic_pass >= TURBO_RELEASE_SEMANTIC_PASS:
        return True, "DIRECT_QUALIFICATION_ROUTE_CLOSURE"
    return False, "NO_TURBO_PRESSURE"


def adjust_source_multiplier(raw_multiplier, semantic_useful_rate, sample_size):
    semantic_factor = 0.55 + min(1.0, semantic_useful_rate) * 0.9
    candidate = min(1.8, round(float(raw_multiplier) * semantic_factor, 2))
    if sample_size >= LOW_YIELD_MIN_SAMPLE and semantic_useful_rate < LOW_YIELD_USEFUL_RATE:
        candidate = min(candidate, LOW_YIELD_CAP)
    elif sample_size >= WEAK_YIELD_MIN_SAMPLE and semantic_useful_rate < WEAK_YIELD_USEFUL_RATE:
        candidate = min(candidate, WEAK_YIELD_CAP)
    return max(SOURCE_EXPLORATION_FLOOR, round(candidate, 2))


def main():
    raw = load(RAW, {"signals": []})
    sem = load(SEM, {"semantic_pass": [], "semantic_review": [], "semantic_reject_sample": []})
    buyer = load(BUYER, {"opportunities": [], "counts_by_tier": {}, "counts_by_archetype": {}, "counts_by_engagement_model": {}})
    source = load(SOURCE, {"ranking": []})
    territory = load(TERRITORY, {"areas": []})
    previous_runtime = load(CMD, {})

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
        final_multiplier = adjust_source_multiplier(raw_multiplier, semantic_useful_rate, r)
        source_rows.append({
            "source_id": sid,
            "raw_signals": r,
            "semantic_pass": p,
            "semantic_review": rv,
            "semantic_pass_rate": round(semantic_pass_rate, 4),
            "semantic_useful_rate": round(semantic_useful_rate, 4),
            "raw_priority_multiplier": raw_multiplier,
            "recommended_multiplier": final_multiplier,
            "budget_class": (
                "CONSTRAINED_NOISY" if r >= LOW_YIELD_MIN_SAMPLE and semantic_useful_rate < LOW_YIELD_USEFUL_RATE
                else "REDUCED_WEAK" if r >= WEAK_YIELD_MIN_SAMPLE and semantic_useful_rate < WEAK_YIELD_USEFUL_RATE
                else "NORMAL_OR_PROMOTED"
            ),
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
    support_rejects = int(sem.get("rejected_non_project_support_count", 0))

    buyer_counts = buyer.get("counts_by_tier", {}) or {}
    very_high_intent = int(buyer_counts.get("VERY_HIGH", 0))
    high_intent = int(buyer_counts.get("HIGH", 0))
    high_intent_count = very_high_intent + high_intent
    buyer_archetypes = buyer.get("counts_by_archetype", {}) or {}
    engagement_models = buyer.get("counts_by_engagement_model", {}) or {}
    project_high_intent = int(buyer.get("project_based_high_intent", 0))
    prioritized_buyer_sample = [
        x for x in (buyer.get("opportunities") or [])
        if x.get("project_based_fit") is True and x.get("engagement_model") == "PROJECT_BASED_WEB_DELIVERY"
    ][:20]

    if project_high_intent >= 8:
        bottleneck = "HIGH_INTENT_PROJECT_ROUTE_AND_CONVERSION_CLOSURE"
    elif semantic_input and semantic_pass / max(1, semantic_input) < 0.15:
        bottleneck = "RAW_SOURCE_PRECISION"
    elif semantic_pass >= 10:
        bottleneck = "DIRECT_QUALIFICATION_ROUTE_CLOSURE"
    else:
        bottleneck = "BALANCED_OR_INSUFFICIENT_SAMPLE"

    resolved_areas = [a for a in territory.get("areas", []) if a.get("region") not in {None, "UNRESOLVED"} and a.get("province") not in {None, "UNRESOLVED"}]
    unresolved = [a for a in territory.get("areas", []) if a.get("region") == "UNRESOLVED" or a.get("province") == "UNRESOLVED"]
    harvest = [a for a in resolved_areas if a.get("mode") == "HARVEST"][:12]
    explore = [a for a in resolved_areas if a.get("mode") in {"REVISIT", "EXPLORATION"}][:20]

    previous_turbo = bool((previous_runtime.get("turbo") or {}).get("enabled"))
    turbo, turbo_reason = choose_turbo(bottleneck, semantic_pass, project_high_intent, previous_turbo)
    if project_high_intent >= 8:
        capacity = {"high_buyer_intent_project_pct": 70, "qualified_project_backlog_pct": 15, "exploration_pct": 15}
    elif turbo:
        capacity = {"high_buyer_intent_project_pct": 50, "qualified_project_backlog_pct": 35, "exploration_pct": 15}
    else:
        capacity = {"high_buyer_intent_project_pct": 45, "qualified_project_backlog_pct": 35, "exploration_pct": 20}

    output = {
        "schema_version": "1.5",
        "updated_at": sem.get("updated_at") or raw.get("updated_at"),
        "north_star": "WON_REVENUE_THEN_PROPOSAL_CALL_QUALIFIED_REPLY_FIRST_CONTACT",
        "north_star_order": [
            "WON_REVENUE", "PROPOSAL", "CALL_INTERVIEW",
            "QUALIFIED_POSITIVE_REPLY_REFERRAL", "MICRO_COMMITMENT_REPLY",
            "PROVIDER_VERIFIED_FIRST_CONTACT"
        ],
        "required_engagement_model": "PROJECT_BASED_WEB_DELIVERY",
        "excluded_engagements": [
            "HELPDESK", "TICKETING", "TECHNICAL_SUPPORT", "PHONE_SUPPORT", "REMOTE_ASSISTANCE",
            "SLA_SUPPORT", "ON_CALL_SUPPORT", "SHIFT_SUPPORT", "MANAGED_SERVICES_SUPPORT", "HOURLY_SUPPORT_RETAINER"
        ],
        "funnel_snapshot": {
            "raw": len(raw.get("signals", [])),
            "semantic_input": semantic_input,
            "semantic_pass": semantic_pass,
            "semantic_review": semantic_review,
            "semantic_reject": semantic_reject,
            "rejected_non_project_support": support_rejects,
            "buyer_intent_very_high": very_high_intent,
            "buyer_intent_high": high_intent,
            "buyer_intent_high_total": high_intent_count,
            "project_based_high_intent": project_high_intent,
            "buyer_archetypes": buyer_archetypes,
            "engagement_models": engagement_models,
            "legacy_cross_signal_hot_plus_advisory": hot_plus,
            "legacy_cross_signal_hot_advisory": hot,
            "legacy_cross_signal_manual_advisory": manual,
            "legacy_cross_signal_duplicate_or_waiting_advisory": duplicates,
            "legacy_cross_signal_executable_advisory": executable,
            "legacy_ready_queue_advisory": ready_count
        },
        "diagnosed_bottleneck": bottleneck,
        "adaptive_mode": "BUYER_INTENT_TURBO" if project_high_intent >= 8 else "MIDDLE_FUNNEL_TURBO" if turbo else "NORMAL_ADAPTIVE",
        "turbo_reason": turbo_reason,
        "capacity": capacity,
        "buyer_intent_priority_sample": prioritized_buyer_sample,
        "source_ranking": source_rows,
        "territory": {
            "resolved_area_count": len(resolved_areas),
            "unresolved_bucket_count": len(unresolved),
            "harvest_now": harvest,
            "explore_or_revisit": explore,
            "rule": "Unresolved country-only buckets are enrichment demand, never HARVEST targets."
        },
        "recommended_actions": [
            "Pursue project-based website delivery only: sites, redesigns, landing pages, ecommerce, portals, WordPress/custom frontend, performance, migrations and EU project websites",
            "Hard reject helpdesk, ticketing, technical/telephone/remote support, SLA/on-call/shift coverage and hourly support retainers",
            "Allow maintenance only when it is scoped evolutionary website work without support-availability obligations",
            "Prioritize VERY_HIGH/HIGH project-based buyer-intent opportunities before generic vacancy backlog",
            "Prefer agency external-capacity buyers, then EU dissemination buyers, then SMEs with observable web problems",
            "Use problem plus proof plus micro-commitment messaging; do not default to generic call requests",
            "Measure progression to qualified reply, call, proposal and won revenue, not email volume alone",
            "Resolve authoritative route and provider/organization dedup immediately before every send",
            "Preserve application-only routes and all legal/channel constraints",
            "DeepSeek remains shadow-only and cannot authorize or veto deterministic execution"
        ]
    }
    save(OUT, output)

    runtime = {
        "schema_version": "1.6",
        "updated_at": output["updated_at"],
        "mode": output["adaptive_mode"],
        "worker_contract": "SELF_CONTAINED_VDS_REVENUE_FLOW",
        "commercial_strategy": {
            "primary_objective": "CONVERT_PROJECT_BASED_WEB_BUYER_INTENT_TO_REVENUE",
            "priority_order": ["AGENCY_EXTERNAL_CAPACITY", "EU_DISSEMINATION_SPECIALIST", "SME_WEB_IMPROVEMENT"],
            "required_engagement_model": "PROJECT_BASED_WEB_DELIVERY",
            "generic_job_application_share_cap": 0.15,
            "message_default": "PROBLEM_PROOF_MICRO_COMMITMENT",
            "vds_engine_positioning": "BENEFIT_LEVEL_ONLY",
            "target_high_intent_first_contacts_7d": 120,
            "target_first_contacts_per_business_day": 20,
            "soft_daily_first_contact_ceiling": 25,
            "target_calls_7d": 5,
            "target_proposals_7d": 3,
            "target_wins_7d": 1
        },
        "engagement_exclusion_policy": {
            "hard_reject_non_project_support": True,
            "excluded": [
                "help desk", "ticketing", "technical support", "telephone support", "phone support",
                "remote assistance", "remote support", "L1/L2 support", "SLA coverage", "on-call",
                "shifts", "managed services support", "desktop/endpoint/user support", "hourly support retainers"
            ],
            "maintenance_rule": "Allow only scoped evolutionary website maintenance/optimization with deliverables and no phone/ticket/SLA/on-call obligation.",
            "mixed_role_rule": "If support availability is a material recurring duty, REJECT even when web development is also mentioned. Accept only when project deliverables clearly dominate and support is incidental handover."
        },
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
            "buyer_intent_ranker_is_priority_advice_not_send_authorization": True,
            "legacy_cross_signal_and_ready_are_advisory_only": True
        },
        "operational_outcomes": ["SEND_NOW", "MANUAL_APPLY", "WAIT_RESEARCH", "REJECT"],
        "capacity": capacity,
        "diagnosed_bottleneck": bottleneck,
        "source_priority": {r["source_id"]: r["recommended_multiplier"] for r in source_rows},
        "top_sources": [r["source_id"] for r in source_rows[:6]],
        "buyer_intent": {
            "very_high": very_high_intent,
            "high": high_intent,
            "high_total": high_intent_count,
            "project_based_high_intent": project_high_intent,
            "archetypes": buyer_archetypes,
            "engagement_models": engagement_models,
            "priority_view": "views/buyer-intent-priority.json"
        },
        "source_budget_policy": {
            "objective": "Spend verification effort on measured project-based semantic and commercial yield while preserving exploration.",
            "exploration_floor_multiplier": SOURCE_EXPLORATION_FLOOR,
            "never_disable_source_from_semantic_yield_alone": True
        },
        "qualified_backlog_policy": {
            "priority": "HIGH_PROJECT_BUYER_INTENT_THEN_UNRESOLVED_SEMANTIC_PASS",
            "semantic_pass_snapshot_proxy": semantic_pass,
            "project_based_high_intent_snapshot": project_high_intent,
            "target_serious_candidate_decisions_per_run": 120,
            "target_high_intent_decisions_first": True,
            "continue_after_individual_blocker": True,
            "send_all_valid_send_now": True,
            "no_batch_minimum": True
        },
        "harvest_areas": [r["area_key"] for r in harvest],
        "explore_or_revisit_areas": [r["area_key"] for r in explore[:12]],
        "turbo": {
            "enabled": turbo,
            "reason": turbo_reason,
            "quality_gates_unchanged": True,
            "target_serious_candidate_decisions_per_run": 120,
            "same_run_qualification_and_send": True,
            "send_all_valid_send_now": True,
            "no_batch_minimum": True,
            "prefer_direct_authoritative_email_routes": True,
            "prefer_fresh_24h_then_7d": True,
            "prefer_high_buyer_intent": True,
            "require_project_based_fit": True,
            "manual_route_preservation": True,
            "never_promote_from_deepseek_shadow": True,
            "minimum_exploration_pct": 25
        },
        "route_policy": {
            "job_or_application_lane": "Require the exact authoritative application/collaboration route; never replace an official form/platform with a generic email. Job-style opportunities are commercially relevant only when the engagement can truthfully be proposed as project-based freelance/P.IVA web delivery.",
            "b2b_agency_commercial_lane": "An official public company partnership/contact/hello email may be used as the authoritative B2B commercial route only for a genuine agency/white-label/external-capacity website-project proposal when no application-only route is bypassed and all hard gates pass."
        },
        "instruction": (
            "SELF_CONTAINED_REVENUE_FLOW: run self-healing preflight first. "
            "VDS ONLY WANTS PROJECT-BASED WEBSITE DEVELOPMENT WORK. Pursue websites, redesigns, landing pages, ecommerce, portals, WordPress/custom frontend, performance/WPO, migrations, scoped evolutionary web work and EU project/dissemination websites. "
            "HARD REJECT help desk, ticketing, technical support, telephone/phone support, remote assistance, user/desktop/endpoint support, managed-services support, SLA/on-call/shift coverage and hourly support retainers. Do not pursue roles that bind Giuseppe to recurring support hours. "
            "Maintenance is eligible only when it is a scoped website evolution/optimization project with deliverables and no ticket/phone/SLA/on-call availability obligation. If a mixed role contains material recurring support duties, REJECT it even if it also mentions WordPress or web development. "
            "Every prospect must use exactly one commercial archetype: AGENCY_EXTERNAL_CAPACITY, EU_DISSEMINATION_SPECIALIST, or SME_WEB_IMPROVEMENT. Engagement model is separate from archetype. "
            "Prioritize project-based buyer intent over raw vacancy volume: AGENCY_EXTERNAL_CAPACITY first, EU_DISSEMINATION_SPECIALIST second, SME_WEB_IMPROVEMENT third. "
            "Use the buyer-intent ranker only for ordering; it never authorizes sending. "
            "Use PROBLEM + PROOF + MICRO-COMMITMENT messaging by default and mention VDS Engine only through buyer outcomes. "
            "Measure and optimize for qualified reply, call, proposal and won revenue. "
            "Process at least 120 serious candidates when supply/runtime permits, continue after blockers, and send every currently valid SEND_NOW identity with no batch minimum. Target 20 qualified first contacts per business day, with a soft ceiling of 25 to protect sender reputation; never lower dedup, route, truthful-fit or legal/channel gates to hit volume. "
            "Preserve organization-level dedup, authoritative-route integrity, current need, truthful fit, legal/channel gates, provider verification and the live-send window. DeepSeek remains shadow-only."
        )
    }
    save(CMD, runtime)
    print(json.dumps({
        "bottleneck": bottleneck,
        "mode": runtime["mode"],
        "turbo_reason": turbo_reason,
        "semantic_pass": semantic_pass,
        "rejected_non_project_support": support_rejects,
        "project_based_high_intent": project_high_intent,
        "buyer_archetypes": buyer_archetypes,
        "capacity": capacity,
        "self_contained": True,
        "preflight_required": True
    }))


if __name__ == "__main__":
    main()
