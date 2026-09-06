#!/usr/bin/env python3
"""Enrich Command Center dashboard with operational funnel semantics.

This is a read-model postprocessor only. It never writes canonical operational
state and never authorizes outreach.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "api" / "v1" / "dashboard.json"
ACQUISITION = ROOT / "views" / "acquisition-performance.json"
ACTIVE = ROOT / "views" / "active-freelance-opportunities.json"

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


def main() -> int:
    dashboard = load(DASHBOARD, {})
    acquisition = load(ACQUISITION, {})
    active = load(ACTIVE, {"opportunities": []})
    runtime = load(ROOT / "config" / "acquisition-runtime-command.json", {})
    if not dashboard:
        raise SystemExit("dashboard.json missing; run build_command_center_api.py first")

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

    dashboard["schema_version"] = "1.2"
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
