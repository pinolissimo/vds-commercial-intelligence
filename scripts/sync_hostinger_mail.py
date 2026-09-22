#!/usr/bin/env python3
"""Synchronize Hostinger Mail provider evidence into VDS state.

The job is intentionally provider-facing and fail-closed:
- HOSTINGER_EMAIL_API_TOKEN is required from GitHub Actions Secrets.
- Sent and Inbox are observed directly from Hostinger Mail API.
- Provider UIDs are the stable identities.
- Existing reconciled events are never overwritten by a weaker raw observation.
- The provider heartbeat is refreshed only after both folders were read successfully.

This file writes only provider state. The existing Command Center projection workflow
remains responsible for rebuilding api/v1 and validating invariants.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
BASE = "https://api.mail.hostinger.com"
TOKEN = os.environ.get("HOSTINGER_EMAIL_API_TOKEN", "").strip()
MAILBOX_ADDRESS = os.environ.get("HOSTINGER_MAILBOX", "info@visualdesignstudio.es").strip().lower()
OWNER_BCC = os.environ.get("VDS_OWNER_BCC", "allocca.pino@gmail.com").strip().lower()
MAX_PAGES = 20
PER_PAGE = 100


def load(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except Exception:
        return default


def save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def api(method: str, path: str, *, query=None, body=None):
    if not TOKEN:
        raise RuntimeError("HOSTINGER_EMAIL_API_TOKEN is not configured")
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "VDS-Commercial-Intelligence/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Hostinger API HTTP {exc.code}: {detail}") from exc


def domain_of(address: str | None) -> str:
    value = str(address or "").strip().lower()
    return value.rsplit("@", 1)[-1] if "@" in value else value


def first_address(value) -> str:
    if isinstance(value, list) and value:
        item = value[0]
        if isinstance(item, dict):
            return str(item.get("address") or "").strip().lower()
    if isinstance(value, dict):
        return str(value.get("address") or "").strip().lower()
    return ""


def bcc_contains_owner(message: dict) -> bool:
    for item in message.get("bcc") or []:
        if isinstance(item, dict) and str(item.get("address") or "").strip().lower() == OWNER_BCC:
            return True
    return False


def get_mailbox() -> str:
    me = api("GET", "/api/v1/me")
    mailboxes = ((me.get("data") or {}).get("mailboxes") or [])
    for mailbox in mailboxes:
        if str(mailbox.get("address") or "").strip().lower() == MAILBOX_ADDRESS:
            rid = mailbox.get("resourceId")
            if rid:
                return str(rid)
    if len(mailboxes) == 1 and mailboxes[0].get("resourceId"):
        return str(mailboxes[0]["resourceId"])
    raise RuntimeError(f"Mailbox {MAILBOX_ADDRESS!r} not available to Hostinger token")


def get_folders(mailbox_id: str) -> tuple[str, str]:
    payload = api("GET", f"/api/v1/mailboxes/{urllib.parse.quote(mailbox_id, safe='')}/folders")
    folders = payload.get("data") or []
    sent = inbox = None
    for folder in folders:
        path = folder.get("path")
        special = str(folder.get("specialUse") or "")
        if special == "\\Sent":
            sent = path
        elif special == "\\Inbox":
            inbox = path
    if not sent or not inbox:
        raise RuntimeError("Hostinger Sent/Inbox folders could not be resolved")
    return str(sent), str(inbox)


def list_messages(mailbox_id: str, folder: str, page: int):
    q_mailbox = urllib.parse.quote(mailbox_id, safe="")
    q_folder = urllib.parse.quote(folder, safe="")
    return api(
        "GET",
        f"/api/v1/mailboxes/{q_mailbox}/folders/{q_folder}/messages",
        query={"page": page, "perPage": PER_PAGE, "sort": "-uid"},
    )


def collect_new(mailbox_id: str, folder: str, last_uid: int) -> tuple[list[dict], dict | None]:
    collected: list[dict] = []
    newest = None
    for page in range(1, MAX_PAGES + 1):
        payload = list_messages(mailbox_id, folder, page)
        batch = [m for m in (payload.get("data") or []) if isinstance(m, dict)]
        if page == 1 and batch:
            newest = batch[0]
        if not batch:
            break
        page_uids = []
        for message in batch:
            try:
                uid = int(message.get("uid"))
            except (TypeError, ValueError):
                continue
            page_uids.append(uid)
            if uid > last_uid:
                collected.append(message)
        pagination = payload.get("pagination") or {}
        if last_uid and page_uids and min(page_uids) <= last_uid:
            break
        if page >= int(pagination.get("totalPages") or page):
            break
        if not last_uid:
            # First bootstrap is deliberately bounded. Existing VDS state already
            # carries historical evidence; only the newest provider page is needed.
            break
    collected.sort(key=lambda x: int(x.get("uid") or 0))
    return collected, newest


def outbound_event(message: dict) -> dict:
    recipient = first_address(message.get("to"))
    is_reply = bool(message.get("inReplyTo"))
    event = {
        "provider_uid": int(message["uid"]),
        "sent_at": message.get("date"),
        "canonical_identity_key": f"org:{domain_of(recipient)}",
        "organization": domain_of(recipient),
        "recipient": recipient,
        "subject": message.get("subject") or "",
        "workstream": "OWNER_RESPONSE" if is_reply else "VDS_PROVIDER_SYNC",
        "state": "VERIFIED_EMAIL_SENT",
        "action_type": "REPLY" if is_reply else "FIRST_CONTACT",
        "attachments": len(message.get("attachments") or []),
        "bcc_owner": bcc_contains_owner(message),
        "source": "HOSTINGER_SENT",
    }
    if message.get("messageId"):
        event["external_id"] = message["messageId"]
    if is_reply:
        event["count_as_successful_outbound"] = False
    return event


def inbound_event(message: dict) -> dict:
    sender = first_address(message.get("from"))
    subject = str(message.get("subject") or "")
    sender_l = sender.lower()
    subject_l = subject.lower()
    bounce = (
        "mailer-daemon" in sender_l
        or "postmaster" in sender_l
        or "undelivered mail" in subject_l
        or "delivery status notification" in subject_l
        or "delivery failure" in subject_l
    )
    automated = (
        bounce
        or "no-reply" in sender_l
        or "noreply" in sender_l
        or "do-not-reply" in sender_l
        or "autoreply" in subject_l
        or "automatic reply" in subject_l
        or "risposta automatica" in subject_l
        or "respuesta automática" in subject_l
        or "out of office" in subject_l
    )
    correlated_reply = bool(message.get("inReplyTo")) and not automated
    classification = "BOUNCE" if bounce else "NEUTRAL"
    subtype = "HARD_BOUNCE" if bounce else ("HUMAN_REPLY_UNCLASSIFIED" if correlated_reply else "SYSTEM_OR_UNCORRELATED")
    domain = domain_of(sender)
    return {
        "provider_inbound_uid": int(message["uid"]),
        "received_at": message.get("date"),
        "canonical_identity_key": f"org:{domain}" if domain else "noncommercial:unknown",
        "entity": domain or sender or "Inbox message",
        "sender": sender,
        "subject": subject,
        "message_id": message.get("messageId"),
        "in_reply_to": message.get("inReplyTo"),
        "classification": classification,
        "subtype": subtype,
        "summary": "Human reply detected; semantic classification pending." if correlated_reply else (
            "Provider delivery failure." if bounce else "Provider message observed; not counted as a commercial reply."
        ),
        "count_as_reply": correlated_reply,
        "source": "HOSTINGER_INBOX",
    }


def merge_outbound(messages: list[dict], checked_at: str) -> int:
    path = STATE / "provider-outbound-live.json"
    payload = load(path, {})
    events = [e for e in (payload.get("events") or []) if isinstance(e, dict)]
    by_uid = {e.get("provider_uid"): e for e in events if isinstance(e.get("provider_uid"), int)}
    added = 0
    for message in messages:
        uid = int(message["uid"])
        # Existing reconciled evidence may contain later bounce/duplicate status.
        # Never downgrade it with a raw Sent-folder observation.
        if uid in by_uid:
            continue
        event = outbound_event(message)
        events.append(event)
        by_uid[uid] = event
        added += 1
    events.sort(key=lambda e: int(e.get("provider_uid") or 0))
    payload.update({
        "schema_version": "1.1",
        "provider_of_record": "HOSTINGER_SENT",
        "purpose": payload.get("purpose") or "Authoritative Hostinger Sent evidence for VDS Command Center.",
        "events": events,
        "last_provider_poll_at": checked_at,
    })
    event_dates = [str(e.get("sent_at")) for e in events if e.get("sent_at")]
    if event_dates:
        payload["updated_at"] = max(event_dates)
    save(path, payload)
    return added


def merge_inbound(messages: list[dict], checked_at: str) -> int:
    path = STATE / "provider-inbound-live.json"
    payload = load(path, {})
    events = [e for e in (payload.get("events") or []) if isinstance(e, dict)]
    by_uid = {e.get("provider_inbound_uid"): e for e in events if isinstance(e.get("provider_inbound_uid"), int)}
    added = 0
    for message in messages:
        uid = int(message["uid"])
        if uid in by_uid:
            continue
        event = inbound_event(message)
        events.append(event)
        by_uid[uid] = event
        added += 1
    events.sort(key=lambda e: int(e.get("provider_inbound_uid") or 0))
    payload.update({
        "schema_version": "1.1",
        "provider_of_record": "HOSTINGER_INBOX",
        "purpose": payload.get("purpose") or "Hostinger Inbox evidence for VDS reply reconciliation.",
        "events": events,
        "updated_at": checked_at,
        "latest_checked_uid": max((int(e.get("provider_inbound_uid") or 0) for e in events), default=0),
    })
    save(path, payload)
    return added


def main() -> int:
    if not TOKEN:
        print("::error::HOSTINGER_EMAIL_API_TOKEN is missing from repository secrets", file=sys.stderr)
        return 2

    observation_path = STATE / "provider-observation.json"
    observation = load(observation_path, {})
    last_sent_uid = int(observation.get("latest_sent_uid") or 0)
    last_inbox_uid = int(observation.get("latest_inbox_uid") or observation.get("latest_checked_uid") or 0)

    mailbox_id = get_mailbox()
    sent_folder, inbox_folder = get_folders(mailbox_id)
    sent_new, sent_latest = collect_new(mailbox_id, sent_folder, last_sent_uid)
    inbox_new, inbox_latest = collect_new(mailbox_id, inbox_folder, last_inbox_uid)

    checked_at = now_z()
    added_sent = merge_outbound(sent_new, checked_at)
    added_inbox = merge_inbound(inbox_new, checked_at)

    observation.update({
        "schema_version": "1.1",
        "provider": "HOSTINGER",
        "observed_at": checked_at,
        "mailbox": MAILBOX_ADDRESS,
        "mailbox_resource_id": mailbox_id,
        "sent_observed": True,
        "inbox_observed": True,
        "observation_source": "HOSTINGER_EMAIL_API_AUTOMATIC",
    })
    if sent_latest:
        observation["latest_sent_uid"] = int(sent_latest["uid"])
        observation["latest_sent_at"] = sent_latest.get("date")
    if inbox_latest:
        observation["latest_inbox_uid"] = int(inbox_latest["uid"])
        observation["latest_inbox_at"] = inbox_latest.get("date")
    observation["last_sync"] = {
        "new_sent_events": added_sent,
        "new_inbox_events": added_inbox,
        "checked_at": checked_at,
    }
    save(observation_path, observation)

    print(json.dumps({
        "status": "OK",
        "observed_at": checked_at,
        "mailbox": MAILBOX_ADDRESS,
        "new_sent_events": added_sent,
        "new_inbox_events": added_inbox,
        "latest_sent_uid": observation.get("latest_sent_uid"),
        "latest_inbox_uid": observation.get("latest_inbox_uid"),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
