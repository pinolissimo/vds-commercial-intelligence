#!/usr/bin/env python3
"""Set Command Center health from authoritative outbound and inbound evidence.

Projection timestamps alone must never make stale commercial data look live. Outbound
and reply reconciliation are evaluated independently so one healthy lane cannot mask a
stale lane. A current provider overlay is authoritative even when slower canonical
indexes have not yet caught up.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")
INBOUND_MAX_AGE_HOURS = 1.5


def load(name: str) -> dict:
    path = API / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def save(name: str, payload: dict) -> None:
    (API / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_dt(value):
    if not isinstance(value, str) or not value:
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


def same_madrid_day(value, now_utc: datetime) -> bool:
    dt = parse_dt(value)
    return bool(dt and dt.astimezone(MADRID).date() == now_utc.astimezone(MADRID).date())


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

    provider_updated = (
        today.get("provider_live_overlay_updated_at")
        or dashboard.get("provider_live_overlay_updated_at")
        or (dashboard.get("provider_live_overlay") or {}).get("updated_at")
    )
    provider_fresh = same_madrid_day(provider_updated, now_utc)

    canonical = health.get("canonical_inputs") or {}
    sent_index_updated = canonical.get("sent_index_updated_at")
    sent_index_age = age_hours(sent_index_updated, now_utc)
    sent_index_fresh = sent_index_age is not None and sent_index_age <= 36.0
    outbound_fresh = provider_fresh or sent_index_fresh

    inbound_updated = (
        today.get("provider_inbound_overlay_updated_at")
        or dashboard.get("provider_inbound_overlay_updated_at")
    )
    inbound_age = age_hours(inbound_updated, now_utc)
    inbound_fresh = (
        inbound_age is not None
        and inbound_age <= INBOUND_MAX_AGE_HOURS
        and same_madrid_day(inbound_updated, now_utc)
    )

    health["schema_version"] = "1.3"
    health["provider_live_overlay_updated_at"] = provider_updated
    health["provider_live_fresh"] = provider_fresh
    health["provider_live_sources"] = today.get("provider_live_sources", dashboard.get("provider_live_sources", 0))
    health["provider_live_pending_sources"] = today.get("provider_live_pending_sources", dashboard.get("provider_live_pending_sources", 0))
    health["sent_index_fresh"] = sent_index_fresh
    health["sent_index_age_hours"] = round(sent_index_age, 2) if sent_index_age is not None else None
    health["outbound_source_fresh"] = outbound_fresh

    health["provider_inbound_overlay_updated_at"] = inbound_updated
    health["provider_inbound_fresh"] = inbound_fresh
    health["provider_inbound_age_hours"] = round(inbound_age, 2) if inbound_age is not None else None
    health["provider_inbound_sources"] = today.get("provider_inbound_sources", dashboard.get("provider_inbound_sources", 0))
    health["provider_inbound_pending_sources"] = today.get("provider_inbound_pending_sources", dashboard.get("provider_inbound_pending_sources", 0))
    health["reply_source_fresh"] = inbound_fresh

    if outbound_fresh and inbound_fresh:
        health["status"] = "OK"
        health["status_reason"] = "PROVIDER_OUTBOUND_AND_INBOUND_CURRENT"
    elif not outbound_fresh and not inbound_fresh:
        health["status"] = "DEGRADED"
        health["status_reason"] = "OUTBOUND_AND_INBOUND_SOURCES_STALE_OR_MISSING"
    elif not outbound_fresh:
        health["status"] = "DEGRADED"
        health["status_reason"] = "OUTBOUND_SOURCE_STALE_OR_MISSING"
    else:
        health["status"] = "DEGRADED"
        health["status_reason"] = "INBOUND_REPLY_SOURCE_STALE_OR_MISSING"

    source_health = {
        "provider_live_fresh": provider_fresh,
        "provider_live_overlay_updated_at": provider_updated,
        "canonical_sent_index_fresh": sent_index_fresh,
        "outbound_source_fresh": outbound_fresh,
        "provider_inbound_fresh": inbound_fresh,
        "provider_inbound_overlay_updated_at": inbound_updated,
        "reply_source_fresh": inbound_fresh,
    }
    today["source_health"] = source_health
    dashboard["source_health"] = dict(source_health)

    save("health.json", health)
    save("today.json", today)
    save("dashboard.json", dashboard)
    print(json.dumps({
        "status": health["status"],
        "reason": health["status_reason"],
        "provider_live_fresh": provider_fresh,
        "sent_index_fresh": sent_index_fresh,
        "provider_inbound_fresh": inbound_fresh,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
