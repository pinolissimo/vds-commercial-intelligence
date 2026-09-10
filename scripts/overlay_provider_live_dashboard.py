#!/usr/bin/env python3
"""Merge provider-verified outbound evidence into Command Center projections.

Provider evidence can arrive in three supported layouts:
1) state/provider-outbound-live.json                     canonical envelope
2) state/provider-outbound-live-pending-*.json           flat pending envelopes
3) state/provider-outbound-live-pending/*.json            per-event pending fragments

All layouts are first-class evidence. The projection layer aggregates them on every
run, deduplicates by provider_uid, lets the newest evidence win for the same UID,
and counts only VERIFIED_EMAIL_SENT events that are not explicitly excluded.
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
    return (
        event.get("state") == "VERIFIED_EMAIL_SENT"
        and event.get("count_as_successful_outbound") is not False
        and isinstance(event.get("provider_uid"), int)
    )


def source_paths():
    paths = [STATE / "provider-outbound-live.json"]
    paths.extend(sorted(STATE.glob("provider-outbound-live-pending-*.json")))
    pending_dir = STATE / "provider-outbound-live-pending"
    if pending_dir.is_dir():
        paths.extend(sorted(pending_dir.glob("*.json")))
    return paths


def payload_events(payload):
    """Normalize both envelope payloads and one-event fragment payloads."""
    if not isinstance(payload, dict):
        return []
    events = payload.get("events")
    if isinstance(events, list):
        return [event for event in events if isinstance(event, dict)]
    if isinstance(payload.get("provider_uid"), int):
        return [payload]
    return []


def event_rank(event, payload_updated_at, source_mtime):
    """Deterministic freshness rank; later provider evidence wins for one UID."""
    for value in (payload_updated_at, event.get("updated_at"), event.get("sent_at")):
        dt = parse_dt(value)
        if dt:
            return (dt.timestamp(), source_mtime)
    return (source_mtime, source_mtime)


def provider_evidence():
    by_uid = {}
    ranks = {}
    newest_at = None
    newest_dt = None
    loaded_sources = 0
    pending_sources = 0

    for path in source_paths():
        payload = load(path, None)
        events = payload_events(payload)
        if not isinstance(payload, dict) or not events:
            continue

        loaded_sources += 1
        if path.name != "provider-outbound-live.json":
            pending_sources += 1

        source_mtime = path.stat().st_mtime if path.exists() else 0.0
        payload_updated_at = payload.get("updated_at")

        candidate_times = [payload_updated_at]
        candidate_times.extend(event.get("sent_at") for event in events)
        for value in candidate_times:
            dt = parse_dt(value)
            if dt and (newest_dt is None or dt > newest_dt):
                newest_dt = dt
                newest_at = value

        for event in events:
            uid = event.get("provider_uid")
            if not isinstance(uid, int):
                continue
            rank = event_rank(event, payload_updated_at, source_mtime)
            if uid not in by_uid or rank >= ranks[uid]:
                by_uid[uid] = dict(event)
                ranks[uid] = rank

    return {
        "events": list(by_uid.values()),
        "updated_at": newest_at,
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

    # Provider evidence is authoritative for the same UID, including a later
    # bounce/duplicate marker that must invalidate a stale success record.
    for event in live.get("events") or []:
        uid = event.get("provider_uid")
        if isinstance(uid, int):
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
        f"{live.get('pending_sources', 0)} pending sources reconciled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
