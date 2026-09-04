#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSS = ROOT / "views/cross-signal-opportunities.json"
HUMAN = ROOT / "views/human-review-high-value.json"
ORG = ROOT / "views/global-organization-index.json"


def load(p, d):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return d


def save(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    stamp = now()
    cross = load(CROSS, {"opportunities":[]})
    human = load(HUMAN, {"items":[],"metrics":{}})
    org = load(ORG, {"contacted":[]})
    states = {x.get("canonical_identity_key"):x for x in org.get("contacted",[]) if x.get("canonical_identity_key")}
    corrected = 0

    for row in cross.get("opportunities", []):
        key = row.get("canonical_identity_key")
        state = states.get(key)
        if not state:
            continue
        corrected += 1
        if state.get("owner_stop") or state.get("status") == "OWNER_STOP_DO_NOT_CONTACT":
            row["contact_status"] = "OWNER_STOP_DO_NOT_CONTACT"
            row["recommended_executor"] = "NONE"
            row["next_best_action"] = "DO_NOT_CONTACT_DUPLICATE"
            row["blockers_missing_gates"] = ["OWNER_STOP_DO_NOT_CONTACT"]
            row["rationale"] = "Global organization history contains an explicit owner stop. No outbound action is permitted unless the owner explicitly reverses it."
        else:
            row["contact_status"] = state.get("status", "CONTACTED")
            row["recommended_executor"] = "NONE_NEW_FIRST_CONTACT"
            row["next_best_action"] = "WAIT_FOR_REPLY"
            row["blockers_missing_gates"] = ["PRIOR_FIRST_CONTACT_OR_OWNER_APPLICATION_RECORDED"]
            ev = state.get("provider_evidence") or state.get("manual_evidence") or "global organization history"
            row["rationale"] = f"Global organization history proves prior professional contact/application ({ev}). Preserve only for reply-driven or otherwise policy-compliant continuation."

    for item in human.get("items", []):
        state = states.get(item.get("canonical_identity_key"))
        if not state:
            continue
        item["dedup_status"] = state.get("status", "CONTACTED")
        item["updated_at"] = stamp
        constraints = item.get("do_not_bypass_constraints") or []
        if state.get("owner_stop") or state.get("status") == "OWNER_STOP_DO_NOT_CONTACT":
            item["recommended_action"] = "NO_ACTION"
            item["owner_decision"] = "REJECT"
            constraints.append("Explicit owner stop: no outbound action unless the owner reverses it.")
        else:
            item["recommended_action"] = "WAIT_FOR_REPLY"
            item["execution_status"] = "CONTACT_ALREADY_EXECUTED"
            if item.get("owner_decision") == "PENDING":
                item["owner_decision"] = "MANUAL_APPLY" if state.get("status") == "CONTACTED_MANUAL_APPLICATION" else "APPROVE_OUTREACH"
            constraints.append("Do not initiate another FIRST_CONTACT; future action must be a compliant continuation.")
        item["do_not_bypass_constraints"] = list(dict.fromkeys(constraints))

    cross["updated_at"] = stamp
    cross["history_reconciled_through"] = org.get("note") or org.get("updated_at")
    human["updated_at"] = stamp
    items = human.get("items", [])
    human["metrics"] = {
        "pending": sum(1 for x in items if x.get("owner_decision") == "PENDING"),
        "approved_outreach": sum(1 for x in items if x.get("owner_decision") == "APPROVE_OUTREACH"),
        "manual_apply": sum(1 for x in items if x.get("owner_decision") == "MANUAL_APPLY"),
        "hold": sum(1 for x in items if x.get("owner_decision") == "HOLD"),
        "rejected": sum(1 for x in items if x.get("owner_decision") == "REJECT"),
        "submitted_by_owner": sum(1 for x in items if x.get("execution_status") in {"CONTACT_ALREADY_EXECUTED","SUBMITTED_BY_OWNER"})
    }
    save(CROSS, cross)
    save(HUMAN, human)
    print(json.dumps({"contacted_states":len(states),"cross_rows_reconciled":corrected,"human_items":len(items)}))

if __name__ == "__main__":
    main()
