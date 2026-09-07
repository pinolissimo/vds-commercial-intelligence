#!/usr/bin/env python3
"""Enrich Command Center dashboard with operational funnel semantics.

This is a read-model postprocessor only. It never authorizes outreach.
It also merges the low-latency provider outbound reconciliation overlay so
provider-verified Hostinger sends appear in the Command Center immediately,
even when the slower global sent index has not yet been reconciled.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api" / "v1"
DASHBOARD = API / "dashboard.json"
TODAY = API / "today.json"
OUTBOUND = API / "outbound.json"
ACQUISITION = ROOT / "views" / "acquisition-performance.json"
ACTIVE = ROOT / "views" / "active-freelance-opportunities.json"
LIVE_PROVIDER = ROOT / "state" / "provider-outbound-live.json"
MADRID = ZoneInfo("Europe/Madrid")

EXECUTABLE_STATUSES = {
    "SEND_NOW",
    "READY_TO_CONTACT",
    "EXECUTABLE_READY",
    "AUTO_EMAIL_NOW",
    "QUEUE_FOR_SEND_WINDOW",
}
LEGACY_ADVISORY_STATUSES = {"READY_FOR_DAILY_OUTREACH_REVIEW"}


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_dt(value):
    if not value or not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MADRID)
        return dt
    except ValueError:
        return None


def classify_status(status: str) -> str:
    s = str(status or "UNKNOWN").upper()
    if s in LEGACY_ADVISORY_STATUSES:
        return "LEGACY_ADVISORY"
    if s in EXECUTABLE_STATUSES:
        return "EXECUTABLE"
    if "MANUAL" in s:
        return "MANUAL_APPLY"
    if "CONTACTED" in s or s in {"SENT", "VERIFIED_EMAIL_SENT"}:
        return "CONTACTED"
    if any(token in s for token in ("WAIT", "RESEARCH", "REVERIFY", "REVIEW_REQUIRED", "HOLD")):
        return "WAIT_RESEARCH"
    if any(token in s for token in ("REJECT", "STALE", "DUPLICATE", "SUPPRESSED", "BLOCKED")):
        return "REJECT"
    return "OTHER"


def merge_live_provider_outbound(dashboard: dict) -> dict:
    """Merge verified live Hostinger events into dashboard/today/outbound read models.

    Failed/bounced attempts remain in the live audit overlay but are excluded from
    successful sent counters. Provider UID is the idempotency key.
    """
    today_model = load(TODAY, {})
    outbound_model = load(OUTBOUND, {})
    live = load(LIVE_PROVIDER, {"events": []})

    base_messages = outbound_model.get("messages") if isinstance(outbound_model.get("messages"), list) else []
    by_uid = {}
    for message in base_messages:
        uid = message.get("provider_uid")
        if uid is not None:
            by_uid[str(uid)] = dict(message)

    for event in live.get("events") or []:
        if not isinstance(event, dict):
            continue
        if event.get("state") != "VERIFIED_EMAIL_SENT":
            continue
        uid = event.get("provider_uid")
        if uid is None:
            continue
        by_uid[str(uid)] = dict(event)

    messages = list(by_uid.values())
    messages.sort(key=lambda m: (m.get("sent_at") or "", int(m.get("provider_uid") or 0)), reverse=True)

    now_local = datetime.now(timezone.utc).astimezone(MADRID)
    local_date = now_local.date()
    today_messages = []
    for message in messages:
        dt = parse_dt(message.get("sent_at"))
        if dt and dt.astimezone(MADRID).date() == local_date:
            item = dict(message)
            item["sent_at_local"] = dt.astimezone(MADRID).isoformat(timespec="seconds")
            today_messages.append(item)
    today_messages.sort(key=lambda m: m.get("sent_at", ""), reverse=True)
    first_contacts = [m for m in today_messages if m.get("action_type", "FIRST_CONTACT") == "FIRST_CONTACT"]

    window_start = datetime.combine(local_date, time(9, 0), tzinfo=MADRID)
    window_end = datetime.combine(local_date, time(19, 0), tzinfo=MADRID)
    elapsed_end = min(max(now_local, window_start), window_end)
    elapsed_hours = max((elapsed_end - window_start).total_seconds() / 3600.0, 0.0)
    sent_rate = round(len(today_messages) / elapsed_hours, 2) if elapsed_hours > 0 else 0.0
    first_rate = round(len(first_contacts) / elapsed_hours, 2) if elapsed_hours > 0 else 0.0

    today_model["sent_count"] = len(today_messages)
    today_model["first_contact_count"] = len(first_contacts)
    today_model["messages_per_active_hour"] = sent_rate
    today_model["first_contacts_per_active_hour"] = first_rate
    today_model["sent"] = today_messages
    today_model["provider_live_overlay_updated_at"] = live.get("updated_at")
    save(TODAY, today_model)

    outbound_model["provider_of_record"] = "HOSTINGER_SENT"
    outbound_model["messages"] = messages
    outbound_model["today_count"] = len(today_messages)
    outbound_model["today_first_contact_count"] = len(first_contacts)
    outbound_model["messages_per_active_hour"] = sent_rate
    outbound_model["provider_live_overlay_updated_at"] = live.get("updated_at")
    save(OUTBOUND, outbound_model)

    today_dash = dashboard.setdefault("today", {})
    today_dash["sent"] = len(today_messages)
    today_dash["first_contacts_sent"] = len(first_contacts)
    today_dash["messages_per_active_hour"] = sent_rate
    today_dash["first_contacts_per_active_hour"] = first_rate
    dashboard.setdefault("headline", {})["sent_today"] = len(today_messages)
    dashboard["provider_live_overlay"] = {
        "updated_at": live.get("updated_at"),
        "successful_events_merged": sum(1 for e in (live.get("events") or []) if isinstance(e, dict) and e.get("state") == "VERIFIED_EMAIL_SENT"),
        "failed_or_bounced_events_excluded": sum(1 for e in (live.get("events") or []) if isinstance(e, dict) and e.get("state") != "VERIFIED_EMAIL_SENT"),
        "provider_of_record": "HOSTINGER_SENT",
    }
    return dashboard


def main() -> int:
    dashboard = load(DASHBOARD, {})
    acquisition = load(ACQUISITION, {})
    active = load(ACTIVE, {"opportunities": []})
    runtime = load(ROOT / "config" / "acquisition-runtime-command.json", {})
    if not dashboard:
        raise SystemExit("dashboard.json missing; run build_command_center_api.py first")

    dashboard = merge_live_provider_outbound(dashboard)

    opps = active.get("opportunities") if isinstance(active.get("opportunities"), list) else []
    classes = Counter(classify_status(o.get("status")) for o in opps)
    status_counts = Counter(str(o.get("status") or "UNKNOWN") for o in opps)

    funnel = acquisition.get("funnel_snapshot") if isinstance(acquisition.get("funnel_snapshot"), dict) else {}
    raw = int(funnel.get("raw") or 0)
    semantic_input = int(funnel.get("semantic_input") or 0)
    semantic_pass = int(funnel.get("semantic_pass") or 0)
    semantic_review = int(funnel.get("semantic_review") or 0)
    semantic_reject = int(funnel.get("semantic_reject") or 0)

    executable = classes["EXECUTABLE"]
    manual_apply = classes["MANUAL_APPLY"]
    wait_research = classes["WAIT_RESEARCH"]
    legacy_advisory = classes["LEGACY_ADVISORY"]
    contacted = classes["CONTACTED"]
    sent_today = int((dashboard.get("today") or {}).get("first_contacts_sent") or 0)

    operational_funnel = {
        "schema_version": "1.0",
        "definition": "Operational read model. Legacy READY_FOR_DAILY_OUTREACH_REVIEW is advisory and excluded. Executable-candidate statuses still require the live JIT safety preflight before any provider call.",
        "stages": {
            "raw_signals": raw,
            "semantic_input": semantic_input,
            "semantic_pass": semantic_pass,
            "company_verified": None,
            "route_found": None,
            "dedup_ok": None,
            "executable_ready_now": executable,
            "manual_apply_now": manual_apply,
            "wait_research_now": wait_research,
            "contacted_in_active_view": contacted,
            "provider_verified_first_contacts_today": sent_today,
        },
        "instrumentation": {
            "company_verified": "NOT_CANONICALLY_METERED_YET",
            "route_found": "NOT_CANONICALLY_METERED_YET",
            "dedup_ok": "NOT_CANONICALLY_METERED_YET",
            "rule": "Never fabricate intermediate counts. Null means the canonical state does not yet expose a reliable stage counter.",
        },
        "attrition": {
            "semantic_reject": semantic_reject,
            "semantic_review": semantic_review,
            "semantic_pass_to_executable_gap_proxy": max(0, semantic_pass - executable),
            "legacy_ready_advisory_excluded": legacy_advisory,
        },
        "status_classes": dict(classes),
        "status_counts": dict(status_counts),
        "pressure": {
            "qualified_backlog_proxy": semantic_pass,
            "executable_ready_now": executable,
            "conversion_pressure_ratio": round(semantic_pass / max(1, executable), 2),
            "turbo_enabled": bool(((runtime.get("turbo") or {}).get("enabled"))),
            "turbo_reason": ((runtime.get("turbo") or {}).get("reason")),
        },
    }

    headline = dashboard.setdefault("headline", {})
    previous_ready = headline.get("ready")
    headline["ready_legacy_compat_previous_value"] = previous_ready
    headline["ready"] = executable
    headline["executable_ready_now"] = executable
    headline["legacy_ready_advisory"] = legacy_advisory
    headline["semantic_pass_backlog_proxy"] = semantic_pass

    dashboard["schema_version"] = "1.3"
    dashboard["operational_funnel"] = operational_funnel
    dashboard["readiness_semantics"] = {
        "headline_ready_means": "EXECUTABLE_CANDIDATE_STATUS_ONLY; LIVE_JIT_GATES_REMAIN_AUTHORITATIVE",
        "requires_live_jit_preflight_before_provider_call": True,
        "legacy_advisory_is_excluded": True,
        "legacy_advisory_statuses": sorted(LEGACY_ADVISORY_STATUSES),
        "executable_statuses": sorted(EXECUTABLE_STATUSES),
    }
    save(DASHBOARD, dashboard)
    print(json.dumps({
        "executable_ready_now": executable,
        "legacy_ready_advisory": legacy_advisory,
        "semantic_pass": semantic_pass,
        "sent_today": sent_today,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
