#!/usr/bin/env python3
"""Merge verified outbound evidence into Command Center projections.

Supported evidence layouts:
1) state/provider-outbound-live.json                     canonical provider envelope
2) state/provider-outbound-live-pending-*.json           flat provider pending envelopes
3) state/provider-outbound-live-pending/*.json           per-event provider fragments
4) state/assistant-outbound-live.json                    assistant/manual Gmail envelope
5) state/assistant-outbound-live-pending-*.json          flat assistant pending envelopes
6) state/assistant-outbound-live-pending/*.json          per-event assistant fragments

Provider and assistant/manual evidence are first-class outbound sources. Events are
merged by a stable identity (provider_uid when present, otherwise external_id or
gmail_message_id), newest evidence wins, and only VERIFIED_EMAIL_SENT events not
explicitly excluded are counted.
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


def event_id(event):
    """Return a stable cross-source identity without conflating Gmail with provider UIDs."""
    uid = event.get("provider_uid")
    if isinstance(uid, int):
        return f"provider:{uid}"
    external = event.get("external_id") or event.get("gmail_message_id")
    if isinstance(external, str) and external.strip():
        source = str(event.get("source") or "external").strip().lower()
        return f"{source}:{external.strip()}"
    return None


def is_success(event):
    return (
        event.get("state") == "VERIFIED_EMAIL_SENT"
        and event.get("count_as_successful_outbound") is not False
        and event_id(event) is not None
    )


def source_paths():
    paths = [
        STATE / "provider-outbound-live.json",
        STATE / "assistant-outbound-live.json",
    ]
    paths.extend(sorted(STATE.glob("provider-outbound-live-pending-*.json")))
    paths.extend(sorted(STATE.glob("assistant-outbound-live-pending-*.json")))
    for dirname in ("provider-outbound-live-pending", "assistant-outbound-live-pending"):
        pending_dir = STATE / dirname
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
    if event_id(payload) is not None:
        return [payload]
    return []


def event_rank(event, payload_updated_at, source_mtime):
    """Deterministic freshness rank; later evidence wins for one event identity."""
    for value in (payload_updated_at, event.get("updated_at"), event.get("sent_at")):
        dt = parse_dt(value)
        if dt:
            return (dt.timestamp(), source_mtime)
    return (source_mtime, source_mtime)


def outbound_evidence():
    by_id = {}
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
        if "pending" in path.name or "pending" in path.parent.name:
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
            identity = event_id(event)
            if identity is None:
                continue
            rank = event_rank(event, payload_updated_at, source_mtime)
            if identity not in by_id or rank >= ranks[identity]:
                by_id[identity] = dict(event)
                ranks[identity] = rank

    return {
        "events": list(by_id.values()),
        "updated_at": newest_at,
        "loaded_sources": loaded_sources,
        "pending_sources": pending_sources,
    }


def main():
    live = outbound_evidence()
    today_api = load(API / "today.json", {})
    dashboard = load(API / "dashboard.json", {})
    outbound = load(API / "outbound.json", {})

    date_str = today_api.get("date")
    if not date_str:
        return 0

    slow_messages = outbound.get("messages") if isinstance(outbound.get("messages"), list) else []
    merged = {}
    for item in slow_messages:
        identity = event_id(item)
        if identity is not None:
            merged[identity] = dict(item)

    # Live evidence is authoritative for the same event identity, including a later
    # bounce/duplicate marker that must invalidate a stale success record.
    for event in live.get("events") or []:
        identity = event_id(event)
        if identity is not None:
            merged[identity] = {**merged.get(identity, {}), **event}

    messages = sorted(
        merged.values(),
        key=lambda x: (parse_dt(x.get("sent_at")) or datetime.min.replace(tzinfo=MADRID)).timestamp(),
    )
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
        "Outbound live overlay: "
        f"{len(today_messages)} successful outbound today, "
        f"{len(first_contacts)} first contacts, "
        f"{live.get('pending_sources', 0)} pending sources reconciled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
