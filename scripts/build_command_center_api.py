#!/usr/bin/env python3
"""Build disposable JSON read-models for the VDS Command Center.

This script is intentionally read-only with respect to canonical operational data.
It only writes under api/v1/.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")


def load(rel: str, default):
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def write(name: str, payload) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_dt(value: str | None):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def main() -> int:
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(MADRID)
    today = now_local.date()
    generated = now_local.isoformat(timespec="seconds")

    semantic = load("metrics/high-frequency-semantic-gate.json", {})
    opportunities = load("views/active-freelance-opportunities.json", {})
    sent = load("views/global-sent-email-index.json", {})
    success = load("views/success-indicators.json", {})
    missions = load("views/multi-engine-search-missions.json", {})
    mission_plan = load("views/search-mission-plan.json", {})
    seeds = load("views/high-frequency-discovery-qualified-seeds.json", {})
    action_queue = load("views/action-queue.json", {})
    fast_queue = load("views/fast-revenue-queue.json", {})
    direct_pipeline = load("views/direct-commercial-pipeline.json", {})

    opps = opportunities.get("opportunities") or []
    status_counts = Counter(str(o.get("status", "UNKNOWN")) for o in opps)
    type_counts = Counter(str(o.get("type", "UNKNOWN")) for o in opps)

    normalized_opps = []
    for o in opps:
        normalized_opps.append({
            "id": o.get("id"),
            "company_id": o.get("company_id"),
            "type": o.get("type"),
            "priority": o.get("priority"),
            "freshness": o.get("freshness"),
            "status": o.get("status"),
            "sent_uid": o.get("sent_uid"),
        })
    normalized_opps.sort(key=lambda x: (x.get("priority") or 0, x.get("freshness") or 0), reverse=True)

    messages = sent.get("messages") or []
    today_messages = []
    for m in messages:
        dt = parse_dt(m.get("sent_at"))
        if dt and dt.astimezone(MADRID).date() == today:
            item = dict(m)
            item["sent_at_local"] = dt.astimezone(MADRID).isoformat(timespec="seconds")
            today_messages.append(item)
    today_messages.sort(key=lambda x: x.get("sent_at", ""), reverse=True)

    last_run = semantic.get("last_run") or {}
    semantic_rate = None
    if last_run.get("input"):
        semantic_rate = round((last_run.get("pass", 0) / last_run["input"]) * 100, 2)

    manual_count = sum(1 for o in normalized_opps if "MANUAL" in str(o.get("status", "")))
    ready_count = sum(
        1 for o in normalized_opps
        if str(o.get("status", "")).startswith("READY") and "MANUAL" not in str(o.get("status", ""))
    )
    contacted_count = sum(1 for o in normalized_opps if "CONTACTED" in str(o.get("status", "")))

    source_payload = {
        "schema_version": "1.0",
        "generated_at": generated,
        "semantic_gate": {
            "runs": semantic.get("runs", 0),
            "total_input": semantic.get("total_input", 0),
            "total_pass": semantic.get("total_pass", 0),
            "total_review": semantic.get("total_review", 0),
            "total_reject": semantic.get("total_reject", 0),
            "last_run": last_run,
            "last_run_pass_rate_pct": semantic_rate,
        },
        "multi_engine_router": {
            "missions_count": missions.get("missions_count"),
            "query_variants_count": missions.get("query_variants_count"),
            "engine_order": missions.get("engine_order") or missions.get("engines"),
            "generated_at": missions.get("generated_at") or missions.get("updated_at"),
        },
        "mission_plan": {
            "updated_at": mission_plan.get("updated_at"),
            "cycle_minutes": mission_plan.get("cycle_minutes"),
            "diagnosed_bottleneck": mission_plan.get("diagnosed_bottleneck"),
            "selected_territories": mission_plan.get("selected_territories") or mission_plan.get("territories"),
        },
        "qualified_seed_summary": {
            "input": seeds.get("input"),
            "semantic_pass": seeds.get("semantic_pass"),
            "semantic_review": seeds.get("semantic_review"),
            "reject": seeds.get("reject"),
            "updated_at": seeds.get("updated_at") or seeds.get("generated_at"),
        },
    }

    dashboard = {
        "schema_version": "1.0",
        "generated_at": generated,
        "source_of_truth": "pinolissimo/vds-commercial-intelligence@main",
        "production_core": "UNCHANGED_AND_AUTHORITATIVE",
        "headline": {
            "semantic_input_last_run": last_run.get("input", 0),
            "semantic_pass_last_run": last_run.get("pass", 0),
            "semantic_pass_rate_pct": semantic_rate,
            "active_opportunities": len(normalized_opps),
            "ready": ready_count,
            "manual_action": manual_count,
            "contacted_in_active_view": contacted_count,
            "sent_today": len(today_messages),
            "success_index_pct": (success.get("success_index") or {}).get("value_pct"),
            "new_client_probability_proxy_pct": (success.get("new_client_probability_proxy") or {}).get("display_pct"),
        },
        "status_counts": dict(status_counts),
        "type_counts": dict(type_counts),
        "queues": {
            "action_queue_updated_at": action_queue.get("updated_at"),
            "fast_revenue_queue_updated_at": fast_queue.get("updated_at"),
            "direct_pipeline_updated_at": direct_pipeline.get("updated_at"),
        },
        "safety": {
            "duplicate_first_contact_tolerance": 0,
            "global_duplicate_hard_gate": True,
            "sent_verification_required": True,
            "dashboard_can_bypass_gates": False,
        },
    }

    write("dashboard.json", dashboard)
    write("today.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "date": str(today),
        "timezone": "Europe/Madrid",
        "sent_count": len(today_messages),
        "sent": today_messages,
        "semantic_last_run": last_run,
    })
    write("outbound.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "provider_of_record": sent.get("provider_of_record"),
        "messages": messages,
        "today_count": len(today_messages),
    })
    write("opportunities.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "count": len(normalized_opps),
        "status_counts": dict(status_counts),
        "type_counts": dict(type_counts),
        "opportunities": normalized_opps,
    })
    write("sources.json", source_payload)
    write("health.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "status": "OK",
        "production_core": "UNCHANGED",
        "projection_builder": "OK",
        "openai_command_secret_required": True,
        "canonical_inputs": {
            "semantic_gate_updated_at": semantic.get("updated_at"),
            "sent_index_updated_at": sent.get("updated_at"),
            "active_opportunities_updated_at": opportunities.get("updated_at"),
        },
    })

    latest = OUT / "ai-command" / "latest.json"
    if not latest.exists():
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(json.dumps({
            "schema_version": "1.0",
            "generated_at": generated,
            "status": "NO_COMMAND_YET",
            "message": "The AI command channel is installed but has not processed a command yet."
        }, indent=2) + "\n", encoding="utf-8")

    print(f"Command Center API generated at {generated}: {len(normalized_opps)} opportunities, {len(today_messages)} sent today")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
