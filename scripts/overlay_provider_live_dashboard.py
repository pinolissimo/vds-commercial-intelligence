#!/usr/bin/env python3
"""Merge low-latency provider outbound events into Command Center API projections.

The canonical slow sent index may lag Hostinger-verified sends. This overlay runs
AFTER build_command_center_api.py and enrich_command_center_funnel.py, merging
state/provider-outbound-live.json by provider_uid. It never invents sends and
never counts failed/bounced audit events as successful outbound.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
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
    if event.get("state") != "VERIFIED_EMAIL_SENT":
        return False
    if event.get("count_as_successful_outbound") is False:
        return False
    return isinstance(event.get("provider_uid"), int)


def main():
    live = load(ROOT / "state" / "provider-outbound-live.json", {})
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

    for event in live.get("events") or []:
        if not is_success(event):
            continue
        uid = event["provider_uid"]
        # Provider-live evidence is the low-latency authority for the same UID.
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

    today_api["sent_count"] = len(today_messages)
    today_api["first_contact_count"] = len(first_contacts)
    today_api["messages_per_active_hour"] = messages_per_hour
    today_api["first_contacts_per_active_hour"] = first_contacts_per_hour
    today_api["sent"] = today_messages
    today_api["provider_live_overlay_updated_at"] = live.get("updated_at")

    dash_today = dashboard.setdefault("today", {})
    dash_today["sent"] = len(today_messages)
    dash_today["first_contacts_sent"] = len(first_contacts)
    dash_today["messages_per_active_hour"] = messages_per_hour
    dash_today["first_contacts_per_active_hour"] = first_contacts_per_hour
    dashboard.setdefault("headline", {})["sent_today"] = len(today_messages)
    dashboard["provider_live_overlay_updated_at"] = live.get("updated_at")

    outbound["messages"] = messages
    outbound["today_count"] = len(today_messages)
    outbound["today_first_contact_count"] = len(first_contacts)
    outbound["messages_per_active_hour"] = messages_per_hour
    outbound["provider_live_overlay_updated_at"] = live.get("updated_at")

    save(API / "today.json", today_api)
    save(API / "dashboard.json", dashboard)
    save(API / "outbound.json", outbound)
    print(f"Provider live overlay: {len(today_messages)} successful outbound today, {len(first_contacts)} first contacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
