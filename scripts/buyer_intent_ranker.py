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
        " ".join(row.get("matched_profile_keywords") or []),
        " ".join(row.get("matched_commercial_keywords") or []),
        " ".join(row.get("semantic_role_hits") or []),
        " ".join(row.get("semantic_intent_hits") or []),
    ]
    return " ".join(str(x) for x in parts).lower()


def hits(blob, terms):
    return sorted({t for t in terms if t.lower() in blob})


def classify_archetype(blob, policy):
    p = policy["positive_intent_terms"]
    agency = hits(blob, p["agency_external_capacity"])
    eu = hits(blob, p["eu_dissemination"])
    sme = hits(blob, p["sme_problem"])
    title = blob
    generic_job = any(x in title for x in ["full time", "full-time", "employee", "permanent", "junior developer", "senior developer", "engineer"])
    if agency:
        return "AGENCY_EXTERNAL_CAPACITY", agency
    if eu:
        return "EU_DISSEMINATION_SPECIALIST", eu
    if generic_job:
        return "GENERIC_JOB_APPLICATION", []
    return "SME_WEB_IMPROVEMENT", sme


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
    for row in seeds.get("semantic_pass", []):
        blob = text_blob(row)
        archetype, intent_hits = classify_archetype(blob, policy)
        route = route_class(row)
        base_fit = min(40.0, float(row.get("semantic_score") or row.get("raw_fit_score") or 0) * 0.4)
        archetype_weight = float(policy["archetype_priority"].get(archetype, 0.5))
        intent_score = min(24, len(intent_hits) * 6)
        route_score = int(policy["route_boost"].get(route, policy["route_boost"]["UNKNOWN"]))
        fresh_score = freshness_score(row, policy)
        geo = str(row.get("target_geo_bucket") or "")
        geo_score = 8 if geo in {"SPAIN_OR_INCLUDES_SPAIN", "ITALY_OR_INCLUDES_ITALY", "WORLDWIDE_REMOTE"} else 5 if "EU" in geo else 0
        score = base_fit * archetype_weight + intent_score + route_score + fresh_score + geo_score
        if archetype == "GENERIC_JOB_APPLICATION":
            score -= int(policy.get("job_application_penalty", 18))
        score = max(0, min(100, round(score, 1)))
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
            "buyer_intent_hits": intent_hits,
            "route_class": route,
            "buyer_intent_score": score,
            "buyer_intent_tier": tier(score, policy["buyer_intent_thresholds"]),
            "semantic_score": row.get("semantic_score"),
            "raw_fit_score": row.get("raw_fit_score"),
            "target_geo_bucket": geo,
            "source_id": row.get("source_id"),
            "decision_hint": "PRIORITIZE_QUALIFICATION" if score >= policy["buyer_intent_thresholds"]["HIGH"] else "NORMAL_QUALIFICATION",
            "send_authorized": False,
            "hard_gates_still_required": True
        })
    rows.sort(key=lambda x: (x["buyer_intent_score"], x.get("semantic_score") or 0), reverse=True)
    counts = {}
    archetypes = {}
    for r in rows:
        counts[r["buyer_intent_tier"]] = counts.get(r["buyer_intent_tier"], 0) + 1
        archetypes[r["commercial_archetype"]] = archetypes.get(r["commercial_archetype"], 0) + 1
    output = {
        "schema_version": "1.0",
        "updated_at": now_utc(),
        "objective": policy.get("objective"),
        "north_star_order": policy.get("north_star_order", []),
        "policy": {
            "ranking_only": True,
            "never_authorizes_send": True,
            "all_existing_hard_gates_required": True,
            "generic_job_application_share_cap": policy.get("execution_policy", {}).get("generic_job_application_share_cap", 0.25)
        },
        "counts_by_tier": counts,
        "counts_by_archetype": archetypes,
        "opportunities": rows
    }
    save(OUT, output)
    save(METRICS, {
        "schema_version": "1.0",
        "updated_at": output["updated_at"],
        "input_semantic_pass": len(seeds.get("semantic_pass", [])),
        "ranked": len(rows),
        "very_high": counts.get("VERY_HIGH", 0),
        "high": counts.get("HIGH", 0),
        "medium": counts.get("MEDIUM", 0),
        "low": counts.get("LOW", 0),
        "archetypes": archetypes
    })
    print(json.dumps({"ranked": len(rows), "tiers": counts, "archetypes": archetypes}))


if __name__ == "__main__":
    main()
