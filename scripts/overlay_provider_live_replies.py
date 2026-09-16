#!/usr/bin/env python3
"""Merge low-latency Hostinger Inbox evidence into Command Center reply KPIs.

This postprocessor is deliberately independent from outbound reconciliation. It counts
only human commercial replies explicitly marked count_as_reply=true. Autoresponders,
calendar/system events and audit-only messages remain visible in provider state but
cannot inflate dashboard reply metrics.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
API = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")


def load(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except Exception:
        return default


def save(path: Path, payload) -> None:
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


def source_paths():
    paths = [STATE / "provider-inbound-live.json"]
    paths.extend(sorted(STATE.glob("provider-inbound-live-pending-*.json")))
    pending_dir = STATE / "provider-inbound-live-pending"
    if pending_dir.is_dir():
        paths.extend(sorted(pending_dir.glob("*.json")))
    return paths


def payload_events(payload):
    if not isinstance(payload, dict):
        return []
    events = payload.get("events")
    return [e for e in events if isinstance(e, dict)] if isinstance(events, list) else []


def normalized_classification(event):
    raw = str(event.get("classification") or "NEUTRAL").upper()
    if raw in {"POSITIVE", "QUALIFIED_POSITIVE_REPLY", "MICRO_COMMITMENT_REPLY", "CALL_REQUEST", "MEETING", "PROPOSAL"}:
        return "POSITIVE"
    if raw in {"NEGATIVE", "REJECTION", "OPT_OUT", "NOT_INTERESTED"}:
        return "NEGATIVE"
    if raw in {"BOUNCE", "HARD_BOUNCE", "DELIVERY_FAILURE"}:
        return "BOUNCE"
    return "NEUTRAL"


def event_key(event):
    uid = event.get("provider_inbound_uid")
    if uid is not None:
        return f"provider-inbound:{uid}"
    message_id = event.get("message_id")
    if isinstance(message_id, str) and message_id.strip():
        return f"message:{message_id.strip()}"
    dt = parse_dt(event.get("received_at") or event.get("at"))
    minute = dt.astimezone(MADRID).strftime("%Y-%m-%dT%H:%M") if dt else "unknown"
    entity = str(event.get("canonical_identity_key") or event.get("entity") or "unknown").strip().lower()
    return f"fallback:{entity}:{minute}"


def live_evidence():
    by_key = {}
    newest_checked = None
    newest_dt = None
    loaded_sources = 0
    pending_sources = 0

    for path in source_paths():
        payload = load(path, None)
        events = payload_events(payload)
        if not isinstance(payload, dict):
            continue
        loaded_sources += 1
        if "pending" in path.name or "pending" in path.parent.name:
            pending_sources += 1

        checked = payload.get("updated_at") or payload.get("checked_at")
        checked_dt = parse_dt(checked)
        if checked_dt and (newest_dt is None or checked_dt > newest_dt):
            newest_dt = checked_dt
            newest_checked = checked

        for event in events:
            by_key[event_key(event)] = dict(event)

    return {
        "events": list(by_key.values()),
        "updated_at": newest_checked,
        "loaded_sources": loaded_sources,
        "pending_sources": pending_sources,
    }


def main() -> int:
    today_api = load(API / "today.json", {})
    dashboard = load(API / "dashboard.json", {})
    date_str = today_api.get("date") or (dashboard.get("today") or {}).get("date")
    if not date_str:
        raise SystemExit("today date missing from Command Center projection")

    existing = ((today_api.get("replies") or {}).get("events") or [])
    merged = {}
    for event in existing:
        if isinstance(event, dict):
            merged[event_key(event)] = dict(event)

    live = live_evidence()
    for event in live["events"]:
        # Audit-only provider events stay in state/provider-inbound-live.json but do not
        # enter commercial reply projections.
        if event.get("count_as_reply") is False:
            continue
        dt = parse_dt(event.get("received_at") or event.get("at"))
        if not dt or str(dt.astimezone(MADRID).date()) != date_str:
            continue
        row = {
            "at": dt.astimezone(MADRID).isoformat(timespec="seconds"),
            "entity": event.get("entity") or event.get("canonical_identity_key") or event.get("sender") or "Risposta",
            "classification": normalized_classification(event),
            "subtype": event.get("subtype"),
            "summary": event.get("summary"),
            "sender": event.get("sender"),
            "subject": event.get("subject"),
            "provider_inbound_uid": event.get("provider_inbound_uid"),
            "canonical_identity_key": event.get("canonical_identity_key"),
            "source": "HOSTINGER_INBOX",
        }
        merged[event_key(row)] = row

    events = []
    for event in merged.values():
        dt = parse_dt(event.get("at") or event.get("received_at"))
        if dt and str(dt.astimezone(MADRID).date()) == date_str:
            event = dict(event)
            event["classification"] = normalized_classification(event)
            events.append(event)
    events.sort(key=lambda e: e.get("at", ""), reverse=True)

    counts = Counter(e.get("classification") for e in events)
    replies = {
        "total": counts.get("POSITIVE", 0) + counts.get("NEGATIVE", 0) + counts.get("NEUTRAL", 0),
        "positive": counts.get("POSITIVE", 0),
        "negative": counts.get("NEGATIVE", 0),
        "neutral": counts.get("NEUTRAL", 0),
        "hard_bounces": counts.get("BOUNCE", 0),
        "events": events,
    }

    today_api["replies"] = replies
    today_api["provider_inbound_overlay_updated_at"] = live.get("updated_at")
    today_api["provider_inbound_sources"] = live.get("loaded_sources", 0)
    today_api["provider_inbound_pending_sources"] = live.get("pending_sources", 0)

    dash_today = dashboard.setdefault("today", {})
    dash_today["replies_total"] = replies["total"]
    dash_today["replies_positive"] = replies["positive"]
    dash_today["replies_negative"] = replies["negative"]
    dash_today["replies_neutral"] = replies["neutral"]
    dash_today["hard_bounces"] = replies["hard_bounces"]
    dashboard["provider_inbound_overlay_updated_at"] = live.get("updated_at")
    dashboard["provider_inbound_sources"] = live.get("loaded_sources", 0)
    dashboard["provider_inbound_pending_sources"] = live.get("pending_sources", 0)

    save(API / "today.json", today_api)
    save(API / "dashboard.json", dashboard)
    print(json.dumps({
        "replies_total": replies["total"],
        "positive": replies["positive"],
        "negative": replies["negative"],
        "neutral": replies["neutral"],
        "provider_inbound_overlay_updated_at": live.get("updated_at"),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
