#!/usr/bin/env python3
"""Compute Command Center health from reconciliation, not commercial activity.

An old last-event timestamp is valid when no new event occurred. Health therefore
tracks whether projections were reconciled successfully; last_event_at is telemetry
only. This prevents a legitimate zero from becoming an unknown value in the UI.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")
RECONCILIATION_MAX_AGE_HOURS = 1.5


def load(name: str) -> dict:
    try:
        value = json.loads((API / name).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def save(name: str, payload: dict) -> None:
    (API / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_dt(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=MADRID)
    except ValueError:
        return None


def age_hours(value, now_utc: datetime):
    dt = parse_dt(value)
    if not dt:
        return None
    return max(0.0, (now_utc - dt.astimezone(timezone.utc)).total_seconds() / 3600.0)


def main() -> int:
    health = load("health.json")
    today = load("today.json")
    dashboard = load("dashboard.json")
    now_utc = datetime.now(timezone.utc)
    reconciled_at = now_utc.isoformat(timespec="seconds").replace("+00:00", "Z")

    outbound_last_event_at = (
        today.get("provider_live_overlay_updated_at")
        or dashboard.get("provider_live_overlay_updated_at")
        or (dashboard.get("provider_live_overlay") or {}).get("updated_at")
    )
    inbound_last_event_at = (
        today.get("provider_inbound_overlay_updated_at")
        or dashboard.get("provider_inbound_overlay_updated_at")
    )

    outbound_sources = today.get("provider_live_sources", dashboard.get("provider_live_sources", 0)) or 0
    inbound_sources = today.get("provider_inbound_sources", dashboard.get("provider_inbound_sources", 0)) or 0

    # The projection pipeline has just completed both reconcilers before this script.
    # Source presence establishes that the lane is observable. Event age never does.
    outbound_reconciled = outbound_sources > 0
    inbound_reconciled = inbound_sources > 0

    health["schema_version"] = "2.0"
    health["reconciled_at"] = reconciled_at
    health["reconciliation_max_age_hours"] = RECONCILIATION_MAX_AGE_HOURS
    health["provider_live_overlay_updated_at"] = outbound_last_event_at  # compatibility
    health["provider_inbound_overlay_updated_at"] = inbound_last_event_at  # compatibility
    health["outbound_last_event_at"] = outbound_last_event_at
    health["inbound_last_event_at"] = inbound_last_event_at
    health["provider_live_sources"] = outbound_sources
    health["provider_live_pending_sources"] = today.get("provider_live_pending_sources", dashboard.get("provider_live_pending_sources", 0))
    health["provider_inbound_sources"] = inbound_sources
    health["provider_inbound_pending_sources"] = today.get("provider_inbound_pending_sources", dashboard.get("provider_inbound_pending_sources", 0))
    health["outbound_reconciled"] = outbound_reconciled
    health["inbound_reconciled"] = inbound_reconciled
    health["outbound_source_fresh"] = outbound_reconciled
    health["reply_source_fresh"] = inbound_reconciled
    health["provider_live_fresh"] = outbound_reconciled  # compatibility: means lane observable/reconciled
    health["provider_inbound_fresh"] = inbound_reconciled

    if outbound_reconciled and inbound_reconciled:
        health["status"] = "OK"
        health["status_reason"] = "OUTBOUND_AND_INBOUND_RECONCILED"
    elif not outbound_reconciled and not inbound_reconciled:
        health["status"] = "DEGRADED"
        health["status_reason"] = "OUTBOUND_AND_INBOUND_RECONCILIATION_UNAVAILABLE"
    elif not outbound_reconciled:
        health["status"] = "DEGRADED"
        health["status_reason"] = "OUTBOUND_RECONCILIATION_UNAVAILABLE"
    else:
        health["status"] = "DEGRADED"
        health["status_reason"] = "INBOUND_RECONCILIATION_UNAVAILABLE"

    source_health = {
        "schema_version": "2.0",
        "reconciled_at": reconciled_at,
        "outbound_last_event_at": outbound_last_event_at,
        "inbound_last_event_at": inbound_last_event_at,
        "outbound_reconciled": outbound_reconciled,
        "inbound_reconciled": inbound_reconciled,
        "outbound_source_fresh": outbound_reconciled,
        "reply_source_fresh": inbound_reconciled,
    }
    today["source_health"] = dict(source_health)
    dashboard["source_health"] = dict(source_health)

    save("health.json", health)
    save("today.json", today)
    save("dashboard.json", dashboard)
    print(json.dumps({"status": health["status"], "reason": health["status_reason"], **source_health}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
