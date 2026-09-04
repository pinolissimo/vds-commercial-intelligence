#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel, default):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def save(rel, data):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def nowz():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    stamp = nowz()
    cross = load("views/cross-signal-opportunities.json", {"schema_version": "1.4", "opportunities": []})
    hr = load("views/human-review-high-value.json", {"schema_version": "1.0", "items": [], "metrics": {}})
    radar = load("views/agency-eu-signal-radar.json", {"signals": []})
    suppression = load("views/provider-contact-suppression-index.json", {"contacted_domains": []})
    sentidx = load("views/global-sent-email-index.json", {"messages": []})
    metrics = load("metrics/daily/2026-09-04-cross-signal.json", {})

    opps = {x.get("canonical_identity_key"): x for x in cross.get("opportunities", []) if x.get("canonical_identity_key")}
    hr_items = {x.get("canonical_identity_key"): x for x in hr.get("items", []) if x.get("canonical_identity_key")}
    suppressed = set(suppression.get("contacted_domains", []))
    contacted = set()
    highest_uid = 0
    for msg in sentidx.get("messages", []):
        try:
            highest_uid = max(highest_uid, int(msg.get("provider_uid") or 0))
        except Exception:
            pass
        if msg.get("action_type") in {None, "FIRST_CONTACT"} and msg.get("canonical_identity_key"):
            contacted.add(msg["canonical_identity_key"])

    material = []
    for s in radar.get("signals", []):
        key = s.get("canonical_identity_key")
        if not key:
            continue
        score = float(s.get("score") or 0)
        tier = str(s.get("priority_tier") or "")
        action = s.get("recommended_next_action")
        domain = s.get("domain")
        if score < 75 and not tier.startswith("HOT"):
            continue
        if action != "MANUAL_ROUTE_REQUIRED":
            continue
        if key in contacted or (domain and domain in suppressed):
            continue

        route = s.get("route") or {}
        route_type = route.get("type") or "MANUAL_ROUTE"
        cross_item = opps.get(key, {})
        cross_item.update({
            "canonical_identity_key": key,
            "organization": s.get("organization"),
            "domain": domain,
            "country": s.get("country"),
            "territory": {
                "country": s.get("country"),
                "region": s.get("region"),
                "province": s.get("province"),
                "city": s.get("city"),
            },
            "segment": s.get("segment"),
            "scores": {"total": score},
            "priority_tier": "HOT+" if score >= 85 else "HOT",
            "contact_status": s.get("global_contact_state") or "NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX",
            "recommended_executor": "OWNER_HUMAN_REVIEW_ONLY",
            "next_best_action": "HUMAN_REVIEW_HIGH_VALUE",
            "blockers_missing_gates": s.get("missing_gates") or ["MANUAL_ROUTE_REQUIRED"],
            "route": route,
            "source_ids": [s.get("source_id")] if s.get("source_id") else [],
            "query_or_intent": s.get("query_or_intent"),
            "evidence_timestamps": [s.get("evidence_timestamp")] if s.get("evidence_timestamp") else [],
            "rationale": s.get("closure_note") or s.get("demand") or "High-value soft-blocked opportunity preserved for owner review.",
        })
        opps[key] = cross_item

        if key not in hr_items:
            urls = list(dict.fromkeys([u for u in (s.get("source_urls") or []) if u]))
            route_url = route.get("source") or route.get("url")
            if route_url and route_url not in urls:
                urls.append(route_url)
            facts = []
            if s.get("demand"):
                facts.append(s.get("demand"))
            if s.get("freshness"):
                facts.append("Freshness: " + str(s.get("freshness")))
            if route_type:
                facts.append("Authoritative route: " + str(route_type))
            hr_items[key] = {
                "schema_version": "1.1",
                "created_at": stamp,
                "updated_at": stamp,
                "canonical_identity_key": key,
                "organization": s.get("organization"),
                "country": s.get("country"),
                "territory": {
                    "country": s.get("country"),
                    "region": s.get("region"),
                    "province": s.get("province"),
                    "city": s.get("city"),
                },
                "website": (s.get("source_urls") or [None])[-1] if s.get("source_urls") else None,
                "opportunity_url": route_url,
                "source_urls": urls,
                "evidence_summary": s.get("demand") or "Current high-value agency/collaboration signal verified by Agency + EU radar.",
                "evidence_strength": s.get("confidence") or "RADAR_VERIFIED_CURRENT",
                "signal_date": s.get("evidence_timestamp") or stamp,
                "score": score,
                "priority": "HOT+" if score >= 85 else "HOT",
                "why_high_value": s.get("demand") or "Strong current VDS fit and commercial potential.",
                "automatic_block_reason": "; ".join(s.get("missing_gates") or ["MANUAL_ROUTE_REQUIRED"]),
                "review_class": "MANUAL_ROUTE",
                "verified_facts": facts,
                "inferences": ["No generic email, contract term, rate, availability or unsupported capability is inferred beyond the verified evidence."],
                "safe_alternative_angles": ["Use only the authoritative manual application/collaboration route with truthful VDS positioning."],
                "known_public_contacts": [],
                "authoritative_routes": [{"type": route_type, "url": route_url}] if route_url else [],
                "decision_maker": None,
                "language": "IT" if s.get("country") == "IT" else "ES" if s.get("country") == "ES" else "EN",
                "dedup_status": s.get("global_contact_state") or f"NO_MATCH_IN_PROVIDER_SUPPRESSION_OR_GLOBAL_SENT_INDEX_THROUGH_UID_{highest_uid}",
                "do_not_bypass_constraints": [
                    "Do not substitute a generic company email for the authoritative form/platform route.",
                    "Do not claim submission unless the manual action is actually completed.",
                    "Do not invent unsupported skills, rates, availability or contract facts.",
                    "Use only owner-approved attachments if a file upload is mandatory.",
                ],
                "recommended_human_checks": [
                    "Confirm the authoritative route is still accepting applications/collaboration proposals.",
                    "Verify all mandatory fields against the truthful VDS profile before submission.",
                    "Use the strongest relevant portfolio/CV evidence without bypassing the declared route.",
                ],
                "recommended_action": "MANUAL_APPLY",
                "owner_decision": "PENDING",
                "source_task": "VDS Agency + EU Signal Radar",
                "state": "PENDING_CANONICAL_QUEUE_MERGE",
            }
            material.append(f"{key}:RADAR_HOT_TO_HUMAN_REVIEW")

    ordered = sorted(opps.values(), key=lambda x: float((x.get("scores") or {}).get("total") or 0), reverse=True)
    cross["opportunities"] = ordered
    cross["updated_at"] = stamp
    hr["items"] = sorted(hr_items.values(), key=lambda x: float(x.get("score") or 0), reverse=True)
    hr["updated_at"] = stamp

    actions = {}
    for o in ordered:
        a = o.get("next_best_action") or "UNKNOWN"
        actions[a] = actions.get(a, 0) + 1
    hp = sum(1 for o in ordered if str(o.get("priority_tier", "")).startswith("HOT+"))
    hot = sum(1 for o in ordered if str(o.get("priority_tier", "")) == "HOT")
    warm = sum(1 for o in ordered if str(o.get("priority_tier", "")) == "WARM")
    pending_hr = sum(1 for x in hr.get("items", []) if x.get("owner_decision") == "PENDING")

    metrics["updated_at"] = stamp
    metrics["evaluated"] = len(ordered)
    metrics["hot_plus"] = hp
    metrics["hot"] = hot
    metrics["warm"] = warm
    metrics["new_first_contact_executable"] = actions.get("AUTO_EMAIL_NOW", 0)
    metrics["queued"] = actions.get("QUEUE_FOR_SEND_WINDOW", 0)
    metrics["manual_high_priority"] = actions.get("MANUAL_APPLY_HIGH_PRIORITY", 0)
    metrics["human_review_high_value"] = pending_hr
    metrics["research_recipient"] = actions.get("RESEARCH_RECIPIENT", 0)
    metrics["territory_enrichment"] = actions.get("ENRICH_TERRITORY", 0)
    metrics["followup_eligibility"] = actions.get("FOLLOWUP_1_ELIGIBILITY_REVIEW", 0)
    metrics["duplicate_history_blocked"] = actions.get("DO_NOT_CONTACT_DUPLICATE", 0)
    metrics["waiting_reply"] = actions.get("WAIT_FOR_REPLY", 0)
    metrics["stale_or_uncertain"] = actions.get("HOLD_STALE_OR_UNCERTAIN", 0)
    metrics["current_action_distribution"] = actions
    metrics.setdefault("material_changes", [])
    metrics["material_changes"] = list(dict.fromkeys(metrics["material_changes"] + material))
    if "last_snapshot" in metrics:
        metrics["last_snapshot"].update({
            "organizations": len(ordered),
            "hot_plus": hp,
            "hot": hot,
            "warm": warm,
            "new_first_contact_executable": actions.get("AUTO_EMAIL_NOW", 0),
            "human_review_high_value": pending_hr,
            "waiting_reply": actions.get("WAIT_FOR_REPLY", 0),
            "duplicate_or_history_blocked": actions.get("DO_NOT_CONTACT_DUPLICATE", 0),
            "stale_or_uncertain": actions.get("HOLD_STALE_OR_UNCERTAIN", 0),
            "provider_history_reconciled_through_uid": max(highest_uid, int((suppression.get("scan") or {}).get("highest_uid_seen") or 0)),
        })

    save("views/cross-signal-opportunities.json", cross)
    save("views/human-review-high-value.json", hr)
    save("metrics/daily/2026-09-04-cross-signal.json", metrics)
    print(json.dumps({"material": material, "organizations": len(ordered), "pending_hr": pending_hr, "actions": actions}))


if __name__ == "__main__":
    main()
