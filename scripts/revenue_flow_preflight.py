#!/usr/bin/env python3
"""VDS Revenue Flow deterministic preflight and cache self-healing.

This tool NEVER sends email and NEVER invents provider events. It validates the
commercial sent-history invariants and can repair derived caches only from the
durable append-only global sent ledger.

Usage:
    python scripts/revenue_flow_preflight.py --check
    python scripts/revenue_flow_preflight.py --repair
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


LEDGER = Path("data/global-sent-email-ledger.jsonl")
SUPPRESSION = Path("views/provider-contact-suppression-index.json")
SENT_INDEX = Path("views/global-sent-email-index.json")
ORG_INDEX = Path("views/global-organization-index.json")
RESERVATIONS = Path("governance/global-contact-reservations.json")
DISCOVERY = Path("views/high-frequency-discovery-latest.json")
PROVIDER_OUTBOUND = Path("state/provider-outbound-live.json")
PROVIDER_OBSERVATION = Path("state/provider-observation.json")
PROVIDER_SYNC_STATUS = Path("state/provider-sync-status.json")
PROVIDER_FRESHNESS_SECONDS = 15 * 60


class PreflightError(RuntimeError):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreflightError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PreflightError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightError(f"expected JSON object in {path}")
    return value


def load_ledger(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise PreflightError(f"missing durable ledger: {path}") from exc
    for line_no, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PreflightError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
        if not isinstance(obj, dict):
            raise PreflightError(f"expected object at {path}:{line_no}")
        events.append(obj)
    return events


def durable_first_contacts(events: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen_uids = set()
    for event in events:
        if event.get("event_type") != "VERIFIED_EMAIL_SENT":
            continue
        if event.get("action_type") != "FIRST_CONTACT":
            continue
        uid = event.get("provider_uid")
        if not isinstance(uid, int):
            raise PreflightError(f"FIRST_CONTACT missing integer provider_uid: {event!r}")
        if uid in seen_uids:
            raise PreflightError(f"duplicate durable provider_uid {uid}")
        seen_uids.add(uid)
        out.append(event)
    out.sort(key=lambda x: x["provider_uid"])
    return out


def canonical_domain(event: Dict[str, Any]) -> str | None:
    key = event.get("canonical_identity_key")
    if isinstance(key, str) and key.startswith("org:") and len(key) > 4:
        return key[4:].strip().lower()
    recipient = event.get("recipient")
    if isinstance(recipient, str) and "@" in recipient:
        domain = recipient.rsplit("@", 1)[1].strip().lower()
        return domain or None
    return None


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def cache_uid_set(sent_index: Dict[str, Any]) -> set[int]:
    values: set[int] = set()
    for item in sent_index.get("messages", []):
        if isinstance(item, dict) and isinstance(item.get("provider_uid"), int):
            values.add(item["provider_uid"])
    return values


def org_identity_set(org_index: Dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for item in org_index.get("contacted", []):
        if isinstance(item, dict) and isinstance(item.get("canonical_identity_key"), str):
            values.add(item["canonical_identity_key"])
    return values


def reconcile(
    contacts: List[Dict[str, Any]],
    suppression: Dict[str, Any],
    sent_index: Dict[str, Any],
    org_index: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, List[Any]]]:
    changes: Dict[str, List[Any]] = {
        "suppression_domains_added": [],
        "sent_uids_added": [],
        "organization_keys_added": [],
    }

    durable_max_uid = max((e["provider_uid"] for e in contacts), default=0)

    domains = suppression.setdefault("contacted_domains", [])
    if not isinstance(domains, list):
        raise PreflightError("provider suppression contacted_domains must be a list")
    domain_set = {str(x).lower() for x in domains}
    for event in contacts:
        domain = canonical_domain(event)
        if domain and domain not in domain_set:
            domains.append(domain)
            domain_set.add(domain)
            changes["suppression_domains_added"].append(domain)
    domains.sort()

    scan = suppression.setdefault("scan", {})
    if not isinstance(scan, dict):
        raise PreflightError("provider suppression scan must be an object")
    if durable_max_uid > int(scan.get("highest_uid_seen") or 0):
        scan["highest_uid_seen"] = durable_max_uid

    messages = sent_index.setdefault("messages", [])
    if not isinstance(messages, list):
        raise PreflightError("global sent index messages must be a list")
    sent_uids = cache_uid_set(sent_index)
    for event in contacts:
        uid = event["provider_uid"]
        if uid in sent_uids:
            continue
        record = {
            "provider_uid": uid,
            "sent_at": event.get("sent_at"),
            "canonical_identity_key": event.get("canonical_identity_key"),
            "organization": event.get("organization"),
            "recipient": event.get("recipient"),
            "subject": event.get("subject"),
            "workstream": event.get("workstream"),
            "state": event.get("state", "VERIFIED_EMAIL_SENT"),
            "action_type": event.get("action_type", "FIRST_CONTACT"),
            "attachments": event.get("attachments", 0),
            "bcc_owner": event.get("bcc_owner"),
        }
        messages.append({k: v for k, v in record.items() if v is not None})
        sent_uids.add(uid)
        changes["sent_uids_added"].append(uid)
    messages.sort(key=lambda x: (x.get("provider_uid") is None, x.get("provider_uid") or 0))

    contacted = org_index.setdefault("contacted", [])
    if not isinstance(contacted, list):
        raise PreflightError("global organization contacted must be a list")
    org_keys = org_identity_set(org_index)
    for event in contacts:
        key = event.get("canonical_identity_key")
        if not isinstance(key, str) or not key:
            raise PreflightError(f"durable FIRST_CONTACT UID {event['provider_uid']} missing canonical_identity_key")
        if key in org_keys:
            continue
        domain = canonical_domain(event)
        record = {
            "canonical_identity_key": key,
            "organization": event.get("organization") or domain or key,
            "domains": [domain] if domain else [],
            "status": "CONTACTED",
            "first_contact_workstream": event.get("workstream"),
            "recipient": event.get("recipient"),
            "provider_evidence": f"HOSTINGER_SENT_UID_{event['provider_uid']}_{event.get('sent_at', 'UNKNOWN')}",
            "first_contact_at": event.get("sent_at"),
            "next_state": "WAIT_FOR_REPLY",
            "dedup_instruction": "Block new unsolicited FIRST_CONTACT to this organization; future action only as a policy-compliant continuation.",
        }
        contacted.append(record)
        org_keys.add(key)
        changes["organization_keys_added"].append(key)

    return suppression, sent_index, org_index, changes


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PreflightError("missing provider observation timestamp")
    raw = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise PreflightError(f"invalid provider timestamp: {value!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def provider_snapshot_health(
    outbound: Dict[str, Any],
    observation: Dict[str, Any],
    sync_status: Dict[str, Any],
    *,
    now: datetime | None = None,
    max_age_seconds: int = PROVIDER_FRESHNESS_SECONDS,
) -> Dict[str, Any]:
    """Validate the automatic Hostinger Sent mirror before it is used for dedup.

    The mirror is never an independent authority: it is acceptable only when the
    Hostinger sync reports VALID auth, both Sent/Inbox were observed, the provider
    UID watermarks agree, and the heartbeat is recent. Any ambiguity fails closed.
    """
    if sync_status.get("status") != "OK" or sync_status.get("auth_status") != "VALID":
        raise PreflightError("Hostinger provider sync is not authenticated and healthy")
    if not observation.get("sent_observed") or not observation.get("inbox_observed"):
        raise PreflightError("Hostinger provider observation is incomplete")

    obs_uid = int(observation.get("latest_sent_uid") or 0)
    sync_uid = int(sync_status.get("latest_sent_uid") or 0)
    events = [e for e in outbound.get("events", []) if isinstance(e, dict)]
    mirror_uid = max((int(e.get("provider_uid") or 0) for e in events), default=0)
    if not obs_uid or obs_uid != sync_uid or mirror_uid < obs_uid:
        raise PreflightError(
            f"Hostinger Sent mirror watermark mismatch: observation={obs_uid}, "
            f"sync={sync_uid}, mirror={mirror_uid}"
        )

    checked = _parse_time(observation.get("observed_at"))
    sync_checked = _parse_time(sync_status.get("checked_at"))
    reference = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = max((reference - checked).total_seconds(), (reference - sync_checked).total_seconds())
    if age < -60 or age > max_age_seconds:
        raise PreflightError(f"Hostinger Sent mirror is stale or clock-skewed: age={age:.0f}s")

    return {
        "status": "HEALTHY",
        "auth_status": "VALID",
        "latest_sent_uid": obs_uid,
        "mirror_max_uid": mirror_uid,
        "age_seconds": int(max(age, 0)),
        "max_age_seconds": max_age_seconds,
        "source": "HOSTINGER_EMAIL_API_AUTOMATIC",
    }


def provider_sent_matches(
    outbound: Dict[str, Any],
    *,
    recipient: str,
    canonical_organization_key: str | None = None,
    corporate_domain: str | None = None,
) -> Dict[str, Any]:
    """Return exact-recipient and organization/domain evidence from verified Sent."""
    recipient_l = str(recipient or "").strip().lower()
    domain_l = str(corporate_domain or "").strip().lower()
    org_key_l = str(canonical_organization_key or "").strip().lower()
    exact, organization = [], []
    for event in outbound.get("events", []):
        if not isinstance(event, dict) or event.get("state") != "VERIFIED_EMAIL_SENT":
            continue
        event_recipient = str(event.get("recipient") or "").strip().lower()
        event_key = str(event.get("canonical_identity_key") or "").strip().lower()
        event_domain = canonical_domain(event) or ""
        if recipient_l and event_recipient == recipient_l:
            exact.append(event)
        if (org_key_l and event_key == org_key_l) or (domain_l and event_domain == domain_l):
            organization.append(event)
    return {
        "exact_recipient_match": bool(exact),
        "organization_or_domain_match": bool(organization),
        "exact_provider_uids": sorted({int(e["provider_uid"]) for e in exact if isinstance(e.get("provider_uid"), int)}),
        "organization_provider_uids": sorted({int(e["provider_uid"]) for e in organization if isinstance(e.get("provider_uid"), int)}),
    }


def discovery_health(path: Path) -> Dict[str, Any]:
    try:
        byte_size = path.stat().st_size
    except FileNotFoundError as exc:
        raise PreflightError(f"missing discovery snapshot: {path}") from exc
    if byte_size == 0:
        raise PreflightError(f"discovery snapshot is truly empty: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreflightError(f"invalid discovery snapshot JSON: {exc}") from exc

    signal_count = None
    if isinstance(payload, dict):
        for key in ("signals", "items", "candidates", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                signal_count = len(value)
                break
        if signal_count is None:
            summary = payload.get("summary")
            if isinstance(summary, dict):
                for key in ("signals", "signal_count", "total_signals", "total"):
                    value = summary.get(key)
                    if isinstance(value, int):
                        signal_count = value
                        break
    return {"byte_size": byte_size, "signal_count": signal_count, "json_valid": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="validate only; do not write")
    mode.add_argument("--repair", action="store_true", help="repair deterministic cache drift from durable ledger")
    parser.add_argument("--repo-root", default=".", help="repository root (default: current directory)")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    ledger_events = load_ledger(root / LEDGER)
    contacts = durable_first_contacts(ledger_events)
    suppression = load_json(root / SUPPRESSION)
    sent_index = load_json(root / SENT_INDEX)
    org_index = load_json(root / ORG_INDEX)
    reservations = load_json(root / RESERVATIONS)
    discovery = discovery_health(root / DISCOVERY)
    provider_outbound = load_json(root / PROVIDER_OUTBOUND)
    provider_observation = load_json(root / PROVIDER_OBSERVATION)
    provider_sync_status = load_json(root / PROVIDER_SYNC_STATUS)
    provider_snapshot = provider_snapshot_health(
        provider_outbound, provider_observation, provider_sync_status
    )

    suppression, sent_index, org_index, changes = reconcile(contacts, suppression, sent_index, org_index)

    drift = any(changes.values())
    if args.repair and drift:
        atomic_write_json(root / SUPPRESSION, suppression)
        atomic_write_json(root / SENT_INDEX, sent_index)
        atomic_write_json(root / ORG_INDEX, org_index)

    durable_max_uid = max((e["provider_uid"] for e in contacts), default=0)
    report = {
        "status": "REPAIRED" if args.repair and drift else ("DRIFT_DETECTED" if drift else "HEALTHY"),
        "durable_first_contacts": len(contacts),
        "durable_max_provider_uid": durable_max_uid,
        "changes": changes,
        "reservations_file_valid": isinstance(reservations, dict),
        "discovery": discovery,
        "provider_snapshot": provider_snapshot,
        "invariant": "derived caches cover every durable provider-verified FIRST_CONTACT",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.check and drift:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PreflightError as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(3)
