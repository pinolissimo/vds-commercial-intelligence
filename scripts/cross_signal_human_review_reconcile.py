#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSS = ROOT / "views/cross-signal-opportunities.json"
HUMAN = ROOT / "views/human-review-high-value.json"
AGENCY = ROOT / "views/agency-eu-signal-radar.json"
SUPPRESSION = ROOT / "views/provider-contact-suppression-index.json"
GLOBAL_ORG = ROOT / "views/global-organization-index.json"
METRICS = ROOT / "metrics/daily/2026-09-04-cross-signal.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def by_key(rows):
    return {x.get("canonical_identity_key"): x for x in rows if x.get("canonical_identity_key")}


def upsert(rows, row):
    key = row["canonical_identity_key"]
    for i, old in enumerate(rows):
        if old.get("canonical_identity_key") == key:
            merged = dict(old)
            merged.update(row)
            rows[i] = merged
            return
    rows.append(row)


def main():
    now = stamp()
    cross = load(CROSS, {"schema_version":"1.4","opportunities":[]})
    human = load(HUMAN, {"schema_version":"1.0","items":[],"metrics":{}})
    agency = load(AGENCY, {"signals":[]})
    suppression = load(SUPPRESSION, {})
    global_org = load(GLOBAL_ORG, {"contacted":[]})

    suppressed_domains = set(suppression.get("contacted_domains", []))
    contacted = by_key(global_org.get("contacted", []))
    opps = cross.setdefault("opportunities", [])
    humans = human.setdefault("items", [])

    # Hard history corrections from newly reconciled provider/manual state.
    for key in ("org:globalserviceimpresa.it", "org:zmotlab.it", "org:grownnectia.com"):
        for row in opps:
            if row.get("canonical_identity_key") != key:
                continue
            org_state = contacted.get(key, {})
            row["contact_status"] = org_state.get("status", "ALREADY_CONTACTED_PROVIDER_HISTORY")
            row["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            row["next_best_action"] = "WAIT_FOR_REPLY"
            row["blockers_missing_gates"] = ["PRIOR_FIRST_CONTACT_OR_OWNER_APPLICATION_RECORDED"]
            row["rationale"] = "Global provider/manual contact history now proves a prior professional first contact/application. Preserve the opportunity for reply-driven continuation only; no new FIRST_CONTACT through another route."

    # UGECE remains strategically valuable but stale: human review, not automated send.
    for row in opps:
        if row.get("canonical_identity_key") == "org:ugeceagency.com":
            row["recommended_executor"] = "OWNER_HUMAN_REVIEW_ONLY"
            row["next_best_action"] = "HUMAN_REVIEW_HIGH_VALUE"
            row["blockers_missing_gates"] = ["CURRENT_OPENING_NOT_PROVEN"]
            row["rationale"] = "Historical recurring WordPress/technical-SEO freelance demand plus strong current business fit remains strategically valuable, but current external demand is not proven. Preserve for HISTORICAL_RECURRING_SIGNAL human review; never auto-send from stale demand."

    # Promote the newest exact-fit recurring outsourcing signal from Agency+EU radar.
    alpa = next((x for x in agency.get("signals", []) if x.get("canonical_identity_key") == "org:alpacode.it"), None)
    if alpa and "alpacode.it" not in suppressed_domains:
        upsert(opps, {
            "canonical_identity_key":"org:alpacode.it",
            "organization":"Alpacode",
            "domain":"alpacode.it",
            "country":"IT",
            "segment":"AGENCY_WHITE_LABEL",
            "signal_families":["CURRENT_RECURRING_OUTSOURCING","OFFICIAL_COLLABORATION_PAGE","PIVA_SUBCONTRACTING","OFFICIAL_APPLICATION_FORM"],
            "source_lineage_count":1,
            "source_ids":["official_collaboration_page"],
            "query_or_intent":"freelance wordpress outsourcing partita IVA remote Italy",
            "evidence_timestamps":[alpa.get("evidence_timestamp", now)],
            "scores":{"fit":96,"demand":100,"route":40,"freshness":100,"recurring_economic":100,"independent_confirmation":70,"total":87.2},
            "priority_tier":"HOT+",
            "contact_status":"NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX",
            "reservation_status":"NONE_KNOWN",
            "recommended_executor":"OWNER_HUMAN_REVIEW_ONLY",
            "next_best_action":"HUMAN_REVIEW_HIGH_VALUE",
            "blockers_missing_gates":["OFFICIAL_APPLICATION_FORM_REQUIRED"],
            "route":{"type":"OFFICIAL_APPLICATION_FORM","source":"https://alpacode.it/lavora-con-noi/"},
            "rationale":"Current official page explicitly keeps remote collaborations open throughout Italy for WordPress developers, including P.IVA-to-P.IVA subcontracting/outsourcing and continued work after successful delivery. Excellent recurring VDS fit; official form requires human execution."
        })

        upsert(humans, {
            "canonical_identity_key":"org:alpacode.it",
            "organization":"Alpacode",
            "country":"IT",
            "website":"https://alpacode.it/",
            "opportunity_url":"https://alpacode.it/lavora-con-noi/",
            "source_urls":["https://alpacode.it/lavora-con-noi/"],
            "evidence_summary":"Current official collaboration page says collaborations are always open for remote task/project work throughout Italy, explicitly including WordPress developers, P.IVA-to-P.IVA subcontracting/outsourcing and possible continued assignments after successful delivery.",
            "evidence_strength":"PRIMARY_OFFICIAL_CURRENT",
            "signal_date":"2026-09-04 official recheck",
            "score":87.2,
            "priority":"HOT+",
            "why_high_value":"Near-ideal VDS commercial model: WordPress, remote project work, explicit P.IVA outsourcing/subcontracting and recurring delivery potential.",
            "automatic_block_reason":"OFFICIAL_APPLICATION_FORM_REQUIRED",
            "review_class":"MANUAL_ROUTE",
            "safe_alternative_angles":["Submit manually through the official collaboration form, positioning VDS as an external P.IVA WordPress/frontend/performance production partner."],
            "known_public_contacts":[],
            "authoritative_routes":[{"type":"OFFICIAL_APPLICATION_FORM","url":"https://alpacode.it/lavora-con-noi/"}],
            "decision_maker":None,
            "language":"IT",
            "dedup_status":"NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX",
            "do_not_bypass_constraints":["Use the official collaboration form; do not substitute a generic email merely for automation convenience.","Do not claim skills or rates not verified in the VDS profile."],
            "recommended_human_checks":["Confirm the form is still accepting submissions.","Use Italian CV/portfolio and emphasize WordPress, frontend, performance, maintenance, responsive work and dependable overflow capacity.","Review any required rate/availability fields before submission."],
            "recommended_action":"MANUAL_APPLY",
            "owner_decision":"PENDING",
            "created_at":"2026-09-04",
            "updated_at":now,
            "source_task":"VDS Cross-Signal Ranker"
        })

    # Ensure UGECE is represented in the human-review queue as a strategic exception.
    if not any(x.get("canonical_identity_key") == "org:ugeceagency.com" for x in humans):
        humans.append({
            "canonical_identity_key":"org:ugeceagency.com","organization":"UGECE Agency","country":"ES","website":"https://ugeceagency.com/","opportunity_url":"https://es.linkedin.com/company/ugece-agency","source_urls":["https://ugeceagency.com/","https://es.linkedin.com/company/ugece-agency"],"evidence_summary":"Strong recurring freelance WordPress/technical-SEO history and current company route, but current external demand is not independently proven.","evidence_strength":"MIXED_PRIMARY_PLUS_HISTORICAL_SECONDARY","signal_date":"2026-09-04 recheck / historical demand ~6 months old","score":70.8,"priority":"WARM_EXCEPTION_STRATEGIC","why_high_value":"Very high technical fit and recurring/economic potential.","automatic_block_reason":"CURRENT_OPENING_NOT_PROVEN","review_class":"HISTORICAL_RECURRING_SIGNAL","safe_alternative_angles":["Search for fresh external-demand evidence first.","Consider a neutral B2B overflow proposal only after human review, without claiming a current opening."],"known_public_contacts":[{"type":"EMAIL","value":"hello@ugeceagency.com","source":"https://ugeceagency.com/"}],"authoritative_routes":[{"type":"GENERAL_BUSINESS_EMAIL","value":"hello@ugeceagency.com","source":"https://ugeceagency.com/"}],"decision_maker":None,"language":"ES","dedup_status":"NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX","do_not_bypass_constraints":["Do not state a current freelance opening exists unless reverified."],"recommended_human_checks":["Review newest company/careers/LinkedIn posts for renewed freelance demand.","Confirm business email is appropriate for B2B partnership outreach."],"recommended_action":"HOLD_FOR_HUMAN_RESEARCH_OR_B2B_REVIEW","owner_decision":"PENDING","created_at":"2026-09-04","updated_at":now,"source_task":"VDS Cross-Signal Ranker"
        })

    # Reconcile human-review entries that are no longer first-contact candidates.
    for item in humans:
        key = item.get("canonical_identity_key")
        if key in contacted:
            state = contacted[key]
            item["dedup_status"] = state.get("status", "CONTACTED")
            item["recommended_action"] = "WAIT_FOR_REPLY"
            if item.get("owner_decision") == "PENDING":
                item["owner_decision"] = "MANUAL_APPLY" if state.get("status") == "CONTACTED_MANUAL_APPLICATION" else "APPROVE_OUTREACH"
            item["execution_status"] = "CONTACT_ALREADY_EXECUTED"
            item["updated_at"] = now
            item["do_not_bypass_constraints"] = list(dict.fromkeys((item.get("do_not_bypass_constraints") or []) + ["Do not initiate another FIRST_CONTACT; future action must be a compliant continuation."]))

    cross["schema_version"] = "1.4"
    cross["updated_at"] = now
    allowed = cross.setdefault("allowed_next_best_actions", [])
    if "HUMAN_REVIEW_HIGH_VALUE" not in allowed:
        allowed.insert(3, "HUMAN_REVIEW_HIGH_VALUE")
    cross["note"] = "Reconciled current Agency+EU signals, Human Review High Value protocol, and provider/manual history through Hostinger UID 274. Alpacode added as HOT+ human-review/manual-route; Ieros remains executable subject to downstream JIT checks; Global Service Impresa, Zmot Lab and Grownnectia are continuation-only. No external action performed."

    human["updated_at"] = now
    pending = sum(1 for x in humans if x.get("owner_decision") == "PENDING")
    human["metrics"] = {
        "pending": pending,
        "approved_outreach": sum(1 for x in humans if x.get("owner_decision") == "APPROVE_OUTREACH"),
        "manual_apply": sum(1 for x in humans if x.get("owner_decision") == "MANUAL_APPLY"),
        "hold": sum(1 for x in humans if x.get("owner_decision") == "HOLD"),
        "rejected": sum(1 for x in humans if x.get("owner_decision") == "REJECT"),
        "submitted_by_owner": sum(1 for x in humans if x.get("execution_status") == "SUBMITTED_BY_OWNER")
    }

    # Compact daily metrics for this ranker; downstream tasks may enrich later.
    counts = {"HOT+":0,"HOT":0,"WARM":0}
    actions = {}
    for row in opps:
        tier = row.get("priority_tier")
        if tier in counts: counts[tier] += 1
        a = row.get("next_best_action")
        if a: actions[a] = actions.get(a, 0) + 1
    oldm = load(METRICS, {"schema_version":"1.0","runs":0})
    oldm.update({
        "updated_at":now,
        "runs":int(oldm.get("runs",0))+1,
        "evaluated":len(opps),
        "hot_plus":counts["HOT+"],"hot":counts["HOT"],"warm":counts["WARM"],
        "new_first_contact_executable":actions.get("AUTO_EMAIL_NOW",0),
        "queued":actions.get("QUEUE_FOR_SEND_WINDOW",0),
        "manual_high_priority":actions.get("MANUAL_APPLY_HIGH_PRIORITY",0),
        "human_review_high_value":actions.get("HUMAN_REVIEW_HIGH_VALUE",0),
        "research_recipient":actions.get("RESEARCH_RECIPIENT",0),
        "territory_enrichment":actions.get("ENRICH_TERRITORY",0),
        "followup_eligibility":actions.get("FOLLOWUP_1_ELIGIBILITY_REVIEW",0),
        "duplicate_history_blocked":actions.get("DO_NOT_CONTACT_DUPLICATE",0),
        "waiting_reply":actions.get("WAIT_FOR_REPLY",0),
        "stale_or_uncertain":actions.get("HOLD_STALE_OR_UNCERTAIN",0)
    })

    save(CROSS, cross)
    save(HUMAN, human)
    save(METRICS, oldm)
    print(json.dumps({"opportunities":len(opps),"human_review":len(humans),"pending":pending,"actions":actions}, ensure_ascii=False))


if __name__ == "__main__":
    main()
