#!/usr/bin/env python3
import json
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel, default):
    p = ROOT / rel
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(rel, data):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def nowz():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def tier_score(tier):
    return 90.0 if str(tier).startswith("HOT+") else 80.0 if str(tier).startswith("HOT") else 65.0

def main():
    stamp = nowz()
    cross = load("views/cross-signal-opportunities.json", {"schema_version":"1.4","opportunities":[]})
    hr = load("views/human-review-high-value.json", {"schema_version":"1.0","items":[],"metrics":{}})
    orgidx = load("views/global-organization-index.json", {"contacted":[]})
    sentidx = load("views/global-sent-email-index.json", {"messages":[]})
    suppression = load("views/provider-contact-suppression-index.json", {"contacted_domains":[]})
    jobs = load("views/linkedin-job-applications.json", {"evaluated":[]})
    radar = load("views/agency-eu-signal-radar.json", {"signals":[]})
    sem = load("views/high-frequency-discovery-qualified-seeds.json", {})
    perf = load("views/acquisition-performance.json", {})

    opps = {x.get("canonical_identity_key"): x for x in cross.get("opportunities", []) if x.get("canonical_identity_key")}
    hr_items = {x.get("canonical_identity_key"): x for x in hr.get("items", []) if x.get("canonical_identity_key")}
    contacted = {x.get("canonical_identity_key"):x for x in orgidx.get("contacted", []) if x.get("canonical_identity_key")}
    suppressed_domains = set(suppression.get("contacted_domains", []))

    provider_contacted = {}
    highest_sent_uid = 0
    for msg in sentidx.get("messages", []):
        try:
            highest_sent_uid = max(highest_sent_uid, int(msg.get("provider_uid") or 0))
        except Exception:
            pass
        key = msg.get("canonical_identity_key")
        if not key:
            continue
        action = msg.get("action_type")
        if action in {None, "FIRST_CONTACT"}:
            provider_contacted[key] = {
                "canonical_identity_key": key,
                "organization": msg.get("organization"),
                "status": "CONTACTED",
                "provider_evidence": f"HOSTINGER_SENT_UID_{msg.get('provider_uid')}_{msg.get('sent_at')}",
                "first_contact_at": msg.get("sent_at"),
                "recipient": msg.get("recipient"),
                "source": "GLOBAL_SENT_EMAIL_INDEX",
            }

    for key, state in provider_contacted.items():
        if key not in contacted:
            contacted[key] = state

    material = []

    for key, state in contacted.items():
        if key not in opps:
            continue
        o = opps[key]
        if state.get("owner_stop") or state.get("status") == "OWNER_STOP_DO_NOT_CONTACT":
            new_action = "DO_NOT_CONTACT_DUPLICATE"
            o["contact_status"] = "OWNER_STOP_DO_NOT_CONTACT"
            o["blockers_missing_gates"] = ["OWNER_STOP_DO_NOT_CONTACT"]
            o["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            o["rationale"] = "Explicit owner stop/global history blocks every outbound action unless the owner explicitly reverses it."
        else:
            new_action = "WAIT_FOR_REPLY"
            o["contact_status"] = state.get("status", "CONTACTED")
            o["blockers_missing_gates"] = ["PRIOR_FIRST_CONTACT_OR_OWNER_APPLICATION_RECORDED"]
            o["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            ev = state.get("provider_evidence")
            suffix = f" ({ev})" if ev else ""
            o["rationale"] = "Global organization/provider history proves prior professional contact/application. Preserve only for reply-driven or otherwise policy-compliant continuation." + suffix
        if o.get("next_best_action") != new_action:
            material.append(f"{key}:{o.get('next_best_action')}->{new_action}")
        o["next_best_action"] = new_action

    for key, o in list(opps.items()):
        domain = o.get("domain")
        if domain in suppressed_domains and key not in contacted and o.get("next_best_action") in {"AUTO_EMAIL_NOW","QUEUE_FOR_SEND_WINDOW","MANUAL_APPLY_HIGH_PRIORITY","HUMAN_REVIEW_HIGH_VALUE","RESEARCH_RECIPIENT"}:
            o["contact_status"] = "ALREADY_CONTACTED_PROVIDER_HISTORY"
            o["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            o["next_best_action"] = "DO_NOT_CONTACT_DUPLICATE"
            o["blockers_missing_gates"] = ["PROVIDER_HISTORY_DOMAIN_MATCH"]
            material.append(f"{key}:provider-history-block")

    for key, item in list(hr_items.items()):
        if key not in contacted:
            continue
        state = contacted[key]
        if state.get("owner_stop") or state.get("status") == "OWNER_STOP_DO_NOT_CONTACT":
            item["dedup_status"] = "OWNER_STOP_DO_NOT_CONTACT"
            item["owner_decision"] = "REJECT"
            item["execution_status"] = "OWNER_STOP_DO_NOT_CONTACT"
            item["recommended_action"] = "NO_ACTION"
        else:
            item["dedup_status"] = state.get("status", "CONTACTED")
            item["execution_status"] = "CONTACT_ALREADY_EXECUTED"
            item["recommended_action"] = "WAIT_FOR_REPLY"
            if item.get("owner_decision") == "PENDING":
                item["owner_decision"] = "APPROVE_OUTREACH"
            item["do_not_bypass_constraints"] = list(dict.fromkeys((item.get("do_not_bypass_constraints") or []) + ["Do not initiate another FIRST_CONTACT; future action must be a compliant continuation."]))
        item["updated_at"] = stamp
        material.append(f"{key}:HUMAN_REVIEW_RECONCILED_WITH_PROVIDER_HISTORY")

    for s in radar.get("signals", []):
        key = s.get("canonical_identity_key")
        if not key:
            continue
        if key in contacted:
            if key in opps:
                opps[key]["next_best_action"] = "WAIT_FOR_REPLY"
                opps[key]["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            continue
        domain = s.get("domain")
        if domain in suppressed_domains:
            if key in opps:
                opps[key]["next_best_action"] = "DO_NOT_CONTACT_DUPLICATE"
                opps[key]["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            continue
        tier = s.get("priority_tier", "WARM")
        hot = str(tier).startswith("HOT")
        next_action = s.get("recommended_next_action")
        if hot and next_action == "MANUAL_ROUTE_REQUIRED":
            hr_score = float(hr_items.get(key, {}).get("score", tier_score(tier)))
            o = opps.get(key, {})
            o.update({"canonical_identity_key":key,"organization":s.get("organization"),"domain":domain,"country":s.get("country"),"territory":{"country":s.get("country"),"region":s.get("region"),"province":s.get("province"),"city":s.get("city")},"segment":s.get("segment"),"scores":{"total":hr_score},"priority_tier":"HOT+" if hr_score>=85 else "HOT","contact_status":s.get("global_contact_state","NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX"),"recommended_executor":"OWNER_HUMAN_REVIEW_ONLY","next_best_action":"HUMAN_REVIEW_HIGH_VALUE","blockers_missing_gates":s.get("missing_gates",[]),"route":s.get("route"),"source_ids":[s.get("source_id")] if s.get("source_id") else [],"query_or_intent":s.get("query_or_intent"),"evidence_timestamps":[s.get("evidence_timestamp")] if s.get("evidence_timestamp") else [],"rationale":s.get("closure_note") or s.get("demand")})
            if key not in opps:
                material.append(f"{key}:NEW_HUMAN_REVIEW")
            opps[key] = o
        elif key in opps and next_action == "HOLD_STALE_OR_UNCERTAIN":
            if key in hr_items and hr_items[key].get("owner_decision") == "PENDING":
                opps[key]["next_best_action"] = "HUMAN_REVIEW_HIGH_VALUE"
                opps[key]["recommended_executor"] = "OWNER_HUMAN_REVIEW_ONLY"
            else:
                opps[key]["next_best_action"] = "HOLD_STALE_OR_UNCERTAIN"
                opps[key]["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"

    removed = list(hr.get("removed_or_closed", []))
    removed_keys = {x.get("canonical_identity_key") for x in removed}
    for j in jobs.get("evaluated", []):
        key = j.get("canonical_identity_key")
        if not key:
            continue
        state = j.get("state")
        if state == "VERIFIED_EMAIL_SENT":
            o = opps.get(key, {})
            o.update({"canonical_identity_key":key,"organization":j.get("organization"),"country":j.get("country"),"segment":"DIRECT_JOB","scores":{"total":float(j.get("fit_score",80))},"priority_tier":"HOT+" if float(j.get("fit_score",80))>=85 else "HOT","contact_status":"CONTACTED","recommended_executor":"NONE_NEW_FIRST_CONTACT","next_best_action":"WAIT_FOR_REPLY","blockers_missing_gates":["PRIOR_FIRST_CONTACT_OR_OWNER_APPLICATION_RECORDED"],"route":{"type":j.get("route"),"recipient":j.get("recipient"),"source":j.get("opportunity_url")},"rationale":f"Provider-verified job first contact UID {j.get('provider_uid')}; continuation-only."})
            opps[key] = o
        elif state == "STALE":
            o = opps.get(key, {})
            o.update({"canonical_identity_key":key,"organization":j.get("organization"),"country":j.get("country"),"segment":"DIRECT_JOB","scores":{"total":float(j.get("fit_score",0))},"priority_tier":"HOT" if float(j.get("fit_score",0))>=75 else "HOLD","contact_status":"NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX","recommended_executor":"VDS LinkedIn Job Hunter","next_best_action":"HOLD_STALE_OR_UNCERTAIN","blockers_missing_gates":[j.get("reason","STALE")],"route":{"type":"CLOSED","source":j.get("opportunity_url")},"rationale":"Latest authoritative job-state recheck shows the opening is stale/closed; no application action is allowed."})
            opps[key] = o
            if key in hr_items and hr_items[key].get("owner_decision") == "PENDING":
                hr_items.pop(key, None)
                if key not in removed_keys:
                    removed.append({"canonical_identity_key":key,"organization":j.get("organization"),"reason":j.get("reason","STALE"),"state":"STALE_CLOSED_CURRENT_OPENING","updated_at":stamp})
                    removed_keys.add(key)
                material.append(f"{key}:HUMAN_REVIEW->STALE")
        elif state == "HUMAN_REVIEW_HIGH_VALUE":
            if key in contacted:
                continue
            o = opps.get(key, {})
            score = float(j.get("fit_score", hr_items.get(key,{}).get("score",75)))
            o.update({"canonical_identity_key":key,"organization":j.get("organization"),"country":j.get("country"),"segment":"DIRECT_JOB","scores":{"total":score},"priority_tier":"HOT+" if score>=85 else "HOT","contact_status":"NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX","recommended_executor":"OWNER_HUMAN_REVIEW_ONLY","next_best_action":"HUMAN_REVIEW_HIGH_VALUE","blockers_missing_gates":[j.get("route","MANUAL_OR_SOFT_BLOCK")],"route":{"type":j.get("route"),"source":j.get("opportunity_url")},"rationale":hr_items.get(key,{}).get("why_high_value") or "High-value soft-blocked job preserved for owner review."})
            opps[key] = o

    for key, item in hr_items.items():
        if key in contacted or item.get("owner_decision") != "PENDING" or item.get("execution_status") in {"CONTACT_ALREADY_EXECUTED","OWNER_STOP_DO_NOT_CONTACT"}:
            continue
        score_value = float(item.get("score",0) or 0)
        if score_value < 75 and not str(item.get("priority","")).startswith("STRATEGIC_EXCEPTION"):
            continue
        if key not in opps:
            routes = item.get("authoritative_routes") or []
            route = routes[0] if routes else {"type":item.get("review_class","HUMAN_REVIEW")}
            opps[key] = {"canonical_identity_key":key,"organization":item.get("organization"),"country":item.get("country"),"segment":"AGENCY_WHITE_LABEL" if item.get("review_class") in {"PARTNER_ANGLE","B2B_ALTERNATIVE"} else "DIRECT_JOB","scores":{"total":score_value},"priority_tier":"HOT+" if score_value>=85 else "HOT","contact_status":item.get("dedup_status","NO_MATCH_IN_PROVIDER_SUPPRESSION_INDEX"),"recommended_executor":"OWNER_HUMAN_REVIEW_ONLY","next_best_action":"HUMAN_REVIEW_HIGH_VALUE","blockers_missing_gates":[item.get("automatic_block_reason","SOFT_BLOCK_REQUIRES_HUMAN_REVIEW")],"route":route,"source_ids":[item.get("source_task")] if item.get("source_task") else [],"evidence_timestamps":[item.get("updated_at") or item.get("signal_date")],"rationale":item.get("why_high_value") or item.get("evidence_summary")}
            material.append(f"{key}:HUMAN_REVIEW_MERGED_INTO_CROSS_SIGNAL")

    def score(x):
        try: return float((x.get("scores") or {}).get("total",0))
        except Exception: return 0.0

    cross["opportunities"] = sorted(opps.values(), key=score, reverse=True)
    cross["schema_version"] = "1.7"
    cross["updated_at"] = stamp
    provider_checkpoint = max(int(suppression.get("scan",{}).get("highest_uid_seen",0) or 0), highest_sent_uid)
    cross["history_reconciled_through"] = f"Hostinger/provider evidence through UID {provider_checkpoint}"
    cross["note"] = "Runtime reconciliation merges current Agency/EU, LinkedIn/job, Human Review, global-sent and provider-history evidence; no external action performed."

    hr["items"] = sorted(hr_items.values(), key=lambda x: float(x.get("score",0) or 0), reverse=True)
    hr["removed_or_closed"] = removed
    hr["schema_version"] = "1.2"
    hr["updated_at"] = stamp
    pending = sum(1 for x in hr["items"] if x.get("owner_decision") == "PENDING")
    approved = sum(1 for x in hr["items"] if x.get("owner_decision") == "APPROVE_OUTREACH")
    manual = sum(1 for x in hr["items"] if x.get("owner_decision") == "MANUAL_APPLY")
    hr["metrics"] = {"pending":pending,"approved_outreach":approved,"manual_apply":manual,"hold":sum(1 for x in hr["items"] if x.get("owner_decision")=="HOLD"),"rejected":len(removed),"contact_already_executed":sum(1 for x in hr["items"] if x.get("execution_status")=="CONTACT_ALREADY_EXECUTED")}

    day = dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).date().isoformat()
    mpath = f"metrics/daily/{day}-cross-signal.json"
    metrics = load(mpath, {"schema_version":"1.3","date":day,"timezone":"Europe/Madrid","counted_run_ids":[],"cumulative_processing":{"runs":0}})
    run_id = "cross-signal-runtime-" + stamp[:16].replace("-","").replace(":","").replace("T","T") + "Z"
    ids = metrics.setdefault("counted_run_ids", [])
    if run_id not in ids:
        ids.append(run_id)
        cp = metrics.setdefault("cumulative_processing", {})
        cp["runs"] = int(cp.get("runs",0)) + 1
        cp["organization_evaluations"] = int(cp.get("organization_evaluations",0)) + len(cross["opportunities"])
        cp["fresh_semantic_passes_reviewed"] = int(cp.get("fresh_semantic_passes_reviewed",0)) + int(sem.get("semantic_pass_count",0))

    actions = {}
    for x in cross["opportunities"]:
        a=x.get("next_best_action","UNKNOWN"); actions[a]=actions.get(a,0)+1
    hotp=sum(1 for x in cross["opportunities"] if x.get("priority_tier")=="HOT+")
    hot=sum(1 for x in cross["opportunities"] if x.get("priority_tier")=="HOT")
    warm=sum(1 for x in cross["opportunities"] if x.get("priority_tier")=="WARM")
    executable = actions.get("AUTO_EMAIL_NOW",0)+actions.get("QUEUE_FOR_SEND_WINDOW",0)
    metrics.update({"schema_version":"1.4","updated_at":stamp,"last_snapshot":{"organizations":len(cross["opportunities"]),"hot_plus":hotp,"hot":hot,"warm":warm,"new_first_contact_executable":executable,"human_review_high_value":actions.get("HUMAN_REVIEW_HIGH_VALUE",0),"waiting_reply":actions.get("WAIT_FOR_REPLY",0),"duplicate_or_history_blocked":actions.get("DO_NOT_CONTACT_DUPLICATE",0),"stale_or_uncertain":actions.get("HOLD_STALE_OR_UNCERTAIN",0),"provider_history_reconciled_through_uid":provider_checkpoint},"current_action_distribution":actions,"fresh_semantic_state":{"input":sem.get("input_signal_count",0),"pass":sem.get("semantic_pass_count",0),"review":sem.get("semantic_review_count",0),"reject":sem.get("semantic_reject_count",0)},"diagnosed_bottleneck":perf.get("diagnosed_bottleneck"),"material_changes":material[-30:],"note":"State counts only. Cross-Signal performed analysis/ranking/state-write only; no external action."})
    metrics["runs"] = int(metrics.get("cumulative_processing",{}).get("runs",0))
    metrics["evaluated"] = len(cross["opportunities"])
    metrics["hot_plus"] = hotp
    metrics["hot"] = hot
    metrics["warm"] = warm
    metrics["new_first_contact_executable"] = executable
    metrics["queued"] = actions.get("QUEUE_FOR_SEND_WINDOW",0)
    metrics["manual_high_priority"] = actions.get("MANUAL_APPLY_HIGH_PRIORITY",0)
    metrics["human_review_high_value"] = actions.get("HUMAN_REVIEW_HIGH_VALUE",0)
    metrics["research_recipient"] = actions.get("RESEARCH_RECIPIENT",0)
    metrics["territory_enrichment"] = actions.get("ENRICH_TERRITORY",0)
    metrics["followup_eligibility"] = actions.get("FOLLOWUP_1_ELIGIBILITY_REVIEW",0)
    metrics["duplicate_history_blocked"] = actions.get("DO_NOT_CONTACT_DUPLICATE",0)
    metrics["waiting_reply"] = actions.get("WAIT_FOR_REPLY",0)
    metrics["stale_or_uncertain"] = actions.get("HOLD_STALE_OR_UNCERTAIN",0)

    save("views/cross-signal-opportunities.json", cross)
    save("views/human-review-high-value.json", hr)
    save(mpath, metrics)
    print(json.dumps({"updated_at":stamp,"opportunities":len(cross["opportunities"]),"human_review_pending":pending,"provider_checkpoint":provider_checkpoint,"material_changes":material,"actions":actions}, ensure_ascii=False))

if __name__ == "__main__":
    main()
