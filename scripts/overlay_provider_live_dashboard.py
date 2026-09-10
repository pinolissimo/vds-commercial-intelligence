#!/usr/bin/env python3
"""Merge provider-verified outbound events into Command Center projections.

Sources of truth are:
- state/provider-outbound-live.json (canonical provider ledger)
- state/provider-outbound-live-pending-*.json (append-only safety fragments)

Pending fragments exist because some connector writes cannot safely replace a large
canonical JSON file. They are therefore first-class provider evidence, not temporary
noise. This overlay always aggregates canonical + pending evidence, deduplicates by
provider_uid, and lets the newest provider evidence win for the same UID.

It never invents sends and never counts failed/bounced/duplicate-policy attempts as
successful outbound.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
API = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")
PENDING_GLOB = "provider-outbound-live-pending-*.json"


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def save(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def is_success(event):
    if event.get("state") != "VERIFIED_EMAIL_SENT":
        return False
    if event.get("count_as_successful_outbound") is False:
        return False
    return isinstance(event.get("provider_uid"), int)


def event_rank(event, source_mtime=0.0):
    """Return a deterministic freshness rank for conflicting evidence."""
    for key in ("updated_at", "sent_at"):
        dt = parse_dt(event.get(key))
        if dt:
            return (dt.timestamp(), source_mtime)
    return (source_mtime, source_mtime)


def provider_evidence():
    """Aggregate canonical provider ledger and all pending safety fragments."""
    sources = [STATE / "provider-outbound-live.json", *sorted(STATE.glob(PENDING_GLOB))]
    by_uid = {}
    ranks = {}
    newest_updated_at = None
    newest_updated_dt = None
    loaded_sources = 0
    pending_sources = 0

    for path in sources:
        payload = load(path, None)
        if not isinstance(payload, dict):
            continue
        loaded_sources += 1
        if path.name.startswith("provider-outbound-live-pending-"):
            pending_sources += 1
        source_mtime = path.stat().st_mtime if path.exists() else 0.0

        updated_at = payload.get("updated_at")
        updated_dt = parse_dt(updated_at)
        if updated_dt and (newest_updated_dt is None or updated_dt > newest_updated_dt):
            newest_updated_dt = updated_dt
            newest_updated_at = updated_at

        for event in payload.get("events") or []:
            if not isinstance(event, dict):
                continue
            uid = event.get("provider_uid")
            if not isinstance(uid, int):
                continue
            rank = event_rank({**event, "updated_at": updated_at}, source_mtime)
            if uid not in by_uid or rank >= ranks[uid]:
                by_uid[uid] = dict(event)
                ranks[uid] = rank

    return {
        "events": list(by_uid.values()),
        "updated_at": newest_updated_at,
        "loaded_sources": loaded_sources,
        "pending_sources": pending_sources,
    }


def main():
    live = provider_evidence()
    today_api = load(API / "today.json", {})
    dashboard = load(API / "dashboard.json", {})
    outbound = load(API / "outbound.json", {})

    date_str = today_api.get("date")
    if not date_str:
        return 0

    slow_messages = outbound.get("messages") if isinstance(outbound.get("messages"), list) else []
    merged = {}
    for item in slow_messages:
        uid = item.get("provider_uid")
        if isinstance(uid, int):
            merged[uid] = dict(item)

    # Provider evidence is authoritative for an existing UID. Keep unsuccessful
    # evidence too so a newer bounce/duplicate marker can prevent stale success
    # records from surviving in the merged outbound ledger.
    for event in live.get("events") or []:
        uid = event.get("provider_uid")
        if not isinstance(uid, int):
            continue
        merged[uid] = {**merged.get(uid, {}), **event}

    messages = sorted(merged.values(), key=lambda x: x.get("provider_uid", 0))
    today_messages = []
    for item in messages:
        if not is_success(item):
            continue
        dt = parse_dt(item.get("sent_at"))
        if not dt or str(dt.astimezone(MADRID).date()) != date_str:
            continue
        row = dict(item)
        row["sent_at_local"] = dt.astimezone(MADRID).isoformat(timespec="seconds")
        today_messages.append(row)

    today_messages.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
    first_contacts = [m for m in today_messages if m.get("action_type", "FIRST_CONTACT") == "FIRST_CONTACT"]

    # Preserve builder-computed elapsed-hour denominator when available.
    elapsed = ((dashboard.get("today") or {}).get("active_window_elapsed_hours") or 0)
    messages_per_hour = round(len(today_messages) / elapsed, 2) if elapsed else 0.0
    first_contacts_per_hour = round(len(first_contacts) / elapsed, 2) if elapsed else 0.0
    overlay_updated_at = live.get("updated_at")

    today_api["sent_count"] = len(today_messages)
    today_api["first_contact_count"] = len(first_contacts)
    today_api["messages_per_active_hour"] = messages_per_hour
    today_api["first_contacts_per_active_hour"] = first_contacts_per_hour
    today_api["sent"] = today_messages
    today_api["provider_live_overlay_updated_at"] = overlay_updated_at
    today_api["provider_live_sources"] = live.get("loaded_sources", 0)
    today_api["provider_live_pending_sources"] = live.get("pending_sources", 0)

    dash_today = dashboard.setdefault("today", {})
    dash_today["sent"] = len(today_messages)
    dash_today["first_contacts_sent"] = len(first_contacts)
    dash_today["messages_per_active_hour"] = messages_per_hour
    dash_today["first_contacts_per_active_hour"] = first_contacts_per_hour
    dashboard.setdefault("headline", {})["sent_today"] = len(today_messages)
    dashboard["provider_live_overlay_updated_at"] = overlay_updated_at
    dashboard["provider_live_sources"] = live.get("loaded_sources", 0)
    dashboard["provider_live_pending_sources"] = live.get("pending_sources", 0)

    outbound["messages"] = messages
    outbound["today_count"] = len(today_messages)
    outbound["today_first_contact_count"] = len(first_contacts)
    outbound["messages_per_active_hour"] = messages_per_hour
    outbound["provider_live_overlay_updated_at"] = overlay_updated_at
    outbound["provider_live_sources"] = live.get("loaded_sources", 0)
    outbound["provider_live_pending_sources"] = live.get("pending_sources", 0)

    save(API / "today.json", today_api)
    save(API / "dashboard.json", dashboard)
    save(API / "outbound.json", outbound)
    print(
        "Provider live overlay: "
        f"{len(today_messages)} successful outbound today, "
        f"{len(first_contacts)} first contacts, "
        f"{live.get('pending_sources', 0)} pending fragments reconciled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
