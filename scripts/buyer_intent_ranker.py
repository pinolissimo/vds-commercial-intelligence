#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "views/high-frequency-discovery-qualified-seeds.json"
POLICY = ROOT / "config/buyer-intent-policy.json"
OUT = ROOT / "views/buyer-intent-priority.json"
METRICS = ROOT / "metrics/buyer-intent-state.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def text_blob(row):
    parts = [
        row.get("title", ""), row.get("organization", ""), row.get("location", ""),
        row.get("description", ""), row.get("snippet", ""), row.get("summary", ""),
        " ".join(row.get("matched_profile_keywords") or []),
        " ".join(row.get("matched_commercial_keywords") or []),
        " ".join(row.get("semantic_role_hits") or []),
        " ".join(row.get("semantic_intent_hits") or []),
        " ".join(row.get("project_scope_hits") or []),
        " ".join(row.get("support_role_hits") or []),
        " ".join(row.get("time_binding_hits") or []),
    ]
    return " ".join(str(x or "") for x in parts).lower()


def hits(blob, terms):
    return sorted({t for t in terms if t.lower() in blob})


def classify_archetype(blob, policy):
    p = policy["positive_intent_terms"]
    agency_hits = hits(blob, p["agency_external_capacity"])
    eu_hits = hits(blob, p["eu_dissemination"])
    sme_hits = hits(blob, p["sme_problem"])

    strong_external_terms = [
        "freelance", "freelancer", "external collaborator", "white label", "white-label",
        "overflow", "subcontractor", "subcontracting", "outsourcing", "external capacity",
        "p.iva", "partita iva", "autónomo", "autonomo", "contractor", "project-based", "project based"
    ]
    agency_context_terms = [
        "agency", "agenzia", "agencia", "studio", "marketing", "communication",
        "comunicazione", "comunicación", "branding", "design studio", "web agency"
    ]
    strong_external = any(x in blob for x in strong_external_terms)
    agency_context = any(x in blob for x in agency_context_terms)

    if eu_hits and any(x in blob for x in [
        "horizon", "prima", "eu project", "european project", "dissemination", "research project"
    ]):
        return "EU_DISSEMINATION_SPECIALIST", eu_hits
    if strong_external and (agency_context or any(x in blob for x in [
        "white label", "white-label", "overflow", "subcontract", "external capacity"
    ])):
        return "AGENCY_EXTERNAL_CAPACITY", agency_hits
    return "SME_WEB_IMPROVEMENT", sme_hits


def engagement_model(blob, row, policy):
    support_hits = sorted(set((row.get("support_role_hits") or []) + hits(blob, policy.get("non_project_support_terms", []))))
    binding_hits = sorted(set((row.get("time_binding_hits") or []) + hits(blob, policy.get("time_binding_terms", []))))
    project_hits = sorted(set((row.get("project_scope_hits") or []) + hits(blob, policy.get("project_delivery_terms", []))))
    maintenance_hits = hits(blob, policy.get("allowed_project_maintenance_terms", []))

    explicit_project_fit = bool(row.get("project_based_fit"))
    scoped_maintenance = bool(maintenance_hits) and not binding_hits
    support_dominant = bool(support_hits) and (bool(binding_hits) or len(support_hits) >= 2 or not project_hits)
    blocked = bool(binding_hits) or (support_dominant and not scoped_maintenance)

    if blocked:
        return {
            "engagement_model": "NON_PROJECT_SUPPORT",
            "project_based_fit": False,
            "support_role_hits": support_hits,
            "time_binding_hits": binding_hits,
            "project_delivery_hits": project_hits,
            "maintenance_project_hits": maintenance_hits,
            "blocker": "NON_PROJECT_SUPPORT_ROLE"
        }
    if explicit_project_fit or project_hits or scoped_maintenance:
        return {
            "engagement_model": "PROJECT_BASED_WEB_DELIVERY",
            "project_based_fit": True,
            "support_role_hits": support_hits,
            "time_binding_hits": binding_hits,
            "project_delivery_hits": project_hits,
            "maintenance_project_hits": maintenance_hits,
            "blocker": None
        }
    return {
        "engagement_model": "PROJECT_MODEL_TO_VERIFY",
        "project_based_fit": False,
        "support_role_hits": support_hits,
        "time_binding_hits": binding_hits,
        "project_delivery_hits": project_hits,
        "maintenance_project_hits": maintenance_hits,
        "blocker": "PROJECT_SCOPE_NOT_VERIFIED"
    }


def route_class(row):
    state = str(row.get("route_state") or "").upper()
    authority = str(row.get("source_authority") or "").upper()
    apply_url = str(row.get("authoritative_apply_url") or "")
    if "EMAIL_VERIFIED" in state:
        return "DIRECT_EMAIL_VERIFIED"
    if "EMAIL" in state:
        return "DIRECT_EMAIL_TO_VERIFY"
    if any(x in state for x in ["ATS", "FORM", "PLATFORM"]) or any(x in apply_url.lower() for x in ["greenhouse", "lever.co", "workable", "smartrecruiters", "ashbyhq"]):
        return "ATS_OR_FORM"
    if "EMPLOYER_DIRECT" in authority or apply_url:
        return "OFFICIAL_CONTACT_ROUTE"
    return "UNKNOWN"


def freshness_score(row, policy):
    age = row.get("published_age_days")
    if age is None:
        return 0
    try:
        age = float(age)
    except Exception:
        return 0
    f = policy["freshness"]
    if age <= 7:
        return f["days_0_7"]
    if age <= 21:
        return f["days_8_21"]
    if age <= 45:
        return f["days_22_45"]
    return f["older"]


def tier(score, thresholds):
    if score >= thresholds["VERY_HIGH"]:
        return "VERY_HIGH"
    if score >= thresholds["HIGH"]:
        return "HIGH"
    if score >= thresholds["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def main():
    seeds = load(SEEDS, {"semantic_pass": []})
    policy = load(POLICY, {})
    rows = []
    rejected_support = 0
    project_high_intent = 0

    for row in seeds.get("semantic_pass", []):
        blob = text_blob(row)
        archetype, intent_hits = classify_archetype(blob, policy)
        engagement = engagement_model(blob, row, policy)
        route = route_class(row)
        base_fit = min(40.0, float(row.get("semantic_score") or row.get("raw_fit_score") or 0) * 0.4)
        archetype_weight = float(policy["archetype_priority"].get(archetype, 0.8))
        intent_score = min(24, len(intent_hits) * 6)
        route_score = int(policy["route_boost"].get(route, policy["route_boost"]["UNKNOWN"]))
        fresh_score = freshness_score(row, policy)
        geo = str(row.get("target_geo_bucket") or "")
        geo_score = 8 if geo in {"SPAIN_OR_INCLUDES_SPAIN", "ITALY_OR_INCLUDES_ITALY", "WORLDWIDE_REMOTE"} else 5 if "EU" in geo else 0
        project_score = min(18, len(engagement["project_delivery_hits"]) * 3)
        score = base_fit * archetype_weight + intent_score + route_score + fresh_score + geo_score + project_score

        generic_job_terms = ["full time", "full-time", "employee", "permanent", "employment", "salary", "vacancy", "job"]
        generic_job = any(x in blob for x in generic_job_terms) and not any(x in blob for x in [
            "freelance", "freelancer", "contractor", "p.iva", "partita iva", "autónomo", "autonomo", "project-based", "project based"
        ])
        if generic_job:
            score -= int(policy.get("generic_job_penalty", 20))

        if engagement["engagement_model"] == "NON_PROJECT_SUPPORT":
            score = 0
            rejected_support += 1
            decision_hint = "REJECT_NON_PROJECT_SUPPORT"
        elif not engagement["project_based_fit"]:
            score = min(score, 39)
            decision_hint = "VERIFY_PROJECT_SCOPE"
        else:
            decision_hint = "PRIORITIZE_QUALIFICATION"

        score = max(0, min(100, round(score, 1)))
        intent_tier = tier(score, policy["buyer_intent_thresholds"])
        if engagement["project_based_fit"] and intent_tier in {"HIGH", "VERY_HIGH"}:
            project_high_intent += 1

        rows.append({
            "signal_key": row.get("signal_key"),
            "organization": row.get("organization"),
            "title": row.get("title"),
            "location": row.get("location"),
            "opportunity_url": row.get("opportunity_url"),
            "authoritative_apply_url": row.get("authoritative_apply_url"),
            "published_at": row.get("published_at"),
            "published_age_days": row.get("published_age_days"),
            "commercial_archetype": archetype,
            "engagement_model": engagement["engagement_model"],
            "project_based_fit": engagement["project_based_fit"],
            "project_delivery_hits": engagement["project_delivery_hits"],
            "support_role_hits": engagement["support_role_hits"],
            "time_binding_hits": engagement["time_binding_hits"],
            "engagement_blocker": engagement["blocker"],
            "buyer_intent_hits": intent_hits,
            "route_class": route,
            "buyer_intent_score": score,
            "buyer_intent_tier": intent_tier,
            "semantic_score": row.get("semantic_score"),
            "raw_fit_score": row.get("raw_fit_score"),
            "target_geo_bucket": geo,
            "source_id": row.get("source_id"),
            "decision_hint": decision_hint,
            "send_authorized": False,
            "hard_gates_still_required": True
        })

    rows.sort(key=lambda x: (x["project_based_fit"], x["buyer_intent_score"], x.get("semantic_score") or 0), reverse=True)
    counts = {}
    archetypes = {}
    engagements = {}
    for r in rows:
        counts[r["buyer_intent_tier"]] = counts.get(r["buyer_intent_tier"], 0) + 1
        archetypes[r["commercial_archetype"]] = archetypes.get(r["commercial_archetype"], 0) + 1
        engagements[r["engagement_model"]] = engagements.get(r["engagement_model"], 0) + 1

    output = {
        "schema_version": "1.2",
        "updated_at": now_utc(),
        "objective": policy.get("objective"),
        "north_star_order": policy.get("north_star_order", []),
        "policy": {
            "ranking_only": True,
            "never_authorizes_send": True,
            "all_existing_hard_gates_required": True,
            "required_engagement_model": "PROJECT_BASED_WEB_DELIVERY",
            "support_ticketing_phone_remote_support_excluded": True,
            "project_scoped_evolutionary_web_maintenance_allowed": True,
            "commercial_archetypes_exactly": [
                "AGENCY_EXTERNAL_CAPACITY", "SME_WEB_IMPROVEMENT", "EU_DISSEMINATION_SPECIALIST"
            ]
        },
        "counts_by_tier": counts,
        "counts_by_archetype": archetypes,
        "counts_by_engagement_model": engagements,
        "rejected_non_project_support": rejected_support,
        "project_based_high_intent": project_high_intent,
        "opportunities": rows
    }
    save(OUT, output)
    save(METRICS, {
        "schema_version": "1.2",
        "updated_at": output["updated_at"],
        "input_semantic_pass": len(seeds.get("semantic_pass", [])),
        "ranked": len(rows),
        "very_high": counts.get("VERY_HIGH", 0),
        "high": counts.get("HIGH", 0),
        "medium": counts.get("MEDIUM", 0),
        "low": counts.get("LOW", 0),
        "archetypes": archetypes,
        "engagement_models": engagements,
        "rejected_non_project_support": rejected_support,
        "project_based_high_intent": project_high_intent
    })
    print(json.dumps({
        "ranked": len(rows), "tiers": counts, "archetypes": archetypes,
        "engagement_models": engagements, "rejected_non_project_support": rejected_support,
        "project_based_high_intent": project_high_intent
    }))


if __name__ == "__main__":
    main()
