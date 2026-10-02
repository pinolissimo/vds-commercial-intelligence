#!/usr/bin/env python3
"""Build and query the VDS global contact dedup ledger.

Sources:
- durable Hostinger provider events
- provider suppression index
- canonical organization index
- optional Gmail sent-contact snapshot

The generated JSON is a read-optimized hard gate for FIRST_CONTACT decisions.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HOSTINGER_LEDGER = ROOT / "data/global-sent-email-ledger.jsonl"
SUPPRESSION = ROOT / "views/provider-contact-suppression-index.json"
ORG_INDEX = ROOT / "views/global-organization-index.json"
GMAIL_SNAPSHOT = ROOT / "data/gmail-sent-contact-snapshot.json"
OUT = ROOT / "views/global-contact-ledger.json"

SHARED_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.it", "yahoo.es",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "icloud.com", "me.com", "proton.me", "protonmail.com",
    "gmx.com", "gmx.net", "mail.com", "inbox.ru",
}

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return out
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


def normalize_email(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    if "<" in value and ">" in value:
        value = value.rsplit("<", 1)[-1].split(">", 1)[0].strip()
    if EMAIL_RE.fullmatch(value):
        return value
    return None


def domain_of(email: str | None) -> str | None:
    email = normalize_email(email)
    if not email:
        return None
    return email.rsplit("@", 1)[1].lower().lstrip("www.")


def canonical_org_key(value: str | None, fallback_domain: str | None = None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    if fallback_domain and fallback_domain not in SHARED_MAIL_DOMAINS:
        return f"org:{fallback_domain}"
    return None


def append_unique(seq: list[Any], value: Any) -> None:
    if value is not None and value not in seq:
        seq.append(value)


def build() -> dict[str, Any]:
    hostinger = load_jsonl(HOSTINGER_LEDGER)
    suppression = load_json(SUPPRESSION, {})
    org_index = load_json(ORG_INDEX, {})
    gmail = load_json(GMAIL_SNAPSHOT, {})

    organizations: dict[str, dict[str, Any]] = {}
    exact: dict[str, dict[str, Any]] = {}
    corporate_domains: dict[str, dict[str, Any]] = {}
    shared_exact: dict[str, dict[str, Any]] = {}

    def ensure_org(key: str, name: str | None = None) -> dict[str, Any]:
        if key not in organizations:
            organizations[key] = {
                "canonical_identity_key": key,
                "organization": name,
                "emails": [],
                "domains": [],
                "sources": [],
                "provider_uids": [],
                "first_contact_at": None,
                "last_contact_at": None,
                "status": "CONTACTED",
            }
        elif name and not organizations[key].get("organization"):
            organizations[key]["organization"] = name
        return organizations[key]

    def ingest(*, email: str | None, org_key: str | None, organization: str | None,
               source: str, at: str | None = None, provider_uid: int | None = None,
               status: str | None = None, evidence: str | None = None) -> None:
        email = normalize_email(email)
        domain = domain_of(email)
        key = canonical_org_key(org_key, domain)

        if email:
            rec = exact.setdefault(email, {
                "email": email,
                "domain": domain,
                "organization_keys": [],
                "sources": [],
                "first_seen_at": None,
                "last_seen_at": None,
                "evidence": [],
            })
            append_unique(rec["organization_keys"], key)
            append_unique(rec["sources"], source)
            append_unique(rec["evidence"], evidence)
            dates = [x for x in [rec.get("first_seen_at"), at] if x]
            rec["first_seen_at"] = min(dates) if dates else None
            dates = [x for x in [rec.get("last_seen_at"), at] if x]
            rec["last_seen_at"] = max(dates) if dates else None

            if domain in SHARED_MAIL_DOMAINS:
                shared_exact[email] = rec

        if key:
            org = ensure_org(key, organization)
            append_unique(org["emails"], email)
            append_unique(org["domains"], domain if domain not in SHARED_MAIL_DOMAINS else None)
            append_unique(org["sources"], source)
            append_unique(org["provider_uids"], provider_uid)
            dates = [x for x in [org.get("first_contact_at"), at] if x]
            org["first_contact_at"] = min(dates) if dates else None
            dates = [x for x in [org.get("last_contact_at"), at] if x]
            org["last_contact_at"] = max(dates) if dates else None
            if status:
                org["status"] = status

        if domain and domain not in SHARED_MAIL_DOMAINS:
            dom = corporate_domains.setdefault(domain, {
                "domain": domain,
                "organization_keys": [],
                "emails": [],
                "sources": [],
                "first_seen_at": None,
                "last_seen_at": None,
            })
            append_unique(dom["organization_keys"], key)
            append_unique(dom["emails"], email)
            append_unique(dom["sources"], source)
            dates = [x for x in [dom.get("first_seen_at"), at] if x]
            dom["first_seen_at"] = min(dates) if dates else None
            dates = [x for x in [dom.get("last_seen_at"), at] if x]
            dom["last_seen_at"] = max(dates) if dates else None

    for event in hostinger:
        if event.get("action_type") not in {"FIRST_CONTACT", "REPLY_CONTINUATION"}:
            continue
        ingest(
            email=event.get("recipient"),
            org_key=event.get("canonical_identity_key"),
            organization=event.get("organization"),
            source="HOSTINGER_SENT",
            at=event.get("sent_at"),
            provider_uid=event.get("provider_uid") if isinstance(event.get("provider_uid"), int) else None,
            status=event.get("state") or "CONTACTED",
            evidence=event.get("provider_evidence") or (
                f"HOSTINGER_SENT_UID_{event.get('provider_uid')}" if event.get("provider_uid") is not None else None
            ),
        )

    for item in (org_index.get("contacted") or []):
        if not isinstance(item, dict):
            continue
        key = canonical_org_key(item.get("canonical_identity_key"))
        domains = [d.lower() for d in (item.get("domains") or []) if isinstance(d, str)]
        fallback = domains[0] if domains else None
        key = key or canonical_org_key(None, fallback)
        emails = [item.get("recipient")] if item.get("recipient") else []
        if not emails and key:
            org = ensure_org(key, item.get("organization"))
            for d in domains:
                if d not in SHARED_MAIL_DOMAINS:
                    append_unique(org["domains"], d)
                    dom = corporate_domains.setdefault(d, {
                        "domain": d, "organization_keys": [], "emails": [], "sources": [],
                        "first_seen_at": None, "last_seen_at": None,
                    })
                    append_unique(dom["organization_keys"], key)
                    append_unique(dom["sources"], "GLOBAL_ORGANIZATION_INDEX")
        for email in emails:
            ingest(
                email=email,
                org_key=key,
                organization=item.get("organization"),
                source="GLOBAL_ORGANIZATION_INDEX",
                at=item.get("first_contact_at"),
                status=item.get("status"),
                evidence=item.get("provider_evidence") or item.get("manual_evidence"),
            )

    for domain in (suppression.get("contacted_domains") or []):
        if not isinstance(domain, str):
            continue
        d = domain.strip().lower().lstrip("www.")
        if not d or d in SHARED_MAIL_DOMAINS:
            continue
        corporate_domains.setdefault(d, {
            "domain": d,
            "organization_keys": [f"org:{d}"],
            "emails": [],
            "sources": ["PROVIDER_SUPPRESSION_INDEX"],
            "first_seen_at": None,
            "last_seen_at": None,
        })

    for email in (suppression.get("exact_free_mail_or_identity_addresses") or []):
        ingest(
            email=email,
            org_key=None,
            organization=None,
            source="PROVIDER_SUPPRESSION_INDEX",
            status="CONTACTED",
            evidence="EXACT_HISTORICAL_IDENTITY",
        )

    for item in (gmail.get("messages") or []):
        if not isinstance(item, dict) or item.get("commercial_relevance") is False:
            continue
        for email in (item.get("recipients") or []):
            ingest(
                email=email,
                org_key=item.get("canonical_identity_key"),
                organization=item.get("organization"),
                source="GMAIL_SENT",
                at=item.get("sent_at"),
                status="CONTACTED",
                evidence=item.get("gmail_message_id"),
            )

    payload = {
        "schema_version": "2.0",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "Single read-optimized FIRST_CONTACT anti-duplication ledger across provider-verified Hostinger history, canonical organization memory and curated Gmail Sent evidence.",
        "policy": {
            "exact_email_match": "HARD_BLOCK",
            "canonical_organization_match": "HARD_BLOCK",
            "corporate_domain_match": "HARD_BLOCK",
            "shared_mail_domain_match": "DO_NOT_BLOCK_BY_DOMAIN; REQUIRE_EXACT_ADDRESS_OR_ORGANIZATION_MATCH",
            "different_role_or_campaign_resets_history": False,
            "follow_up_requires_owner_authorization": True,
        },
        "shared_mail_domains": sorted(SHARED_MAIL_DOMAINS),
        "counts": {
            "exact_emails": len(exact),
            "corporate_domains": len(corporate_domains),
            "organizations": len(organizations),
            "shared_mail_exact_addresses": len(shared_exact),
            "hostinger_events_scanned": len(hostinger),
            "gmail_messages_scanned": len(gmail.get("messages") or []),
        },
        "exact_email_index": dict(sorted(exact.items())),
        "corporate_domain_index": dict(sorted(corporate_domains.items())),
        "organization_index": dict(sorted(organizations.items())),
        "shared_mail_exact_index": dict(sorted(shared_exact.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def check(payload: dict[str, Any], email: str | None, organization_key: str | None) -> dict[str, Any]:
    normalized = normalize_email(email)
    domain = domain_of(normalized)
    key = canonical_org_key(organization_key)

    reasons: list[str] = []
    evidence: list[Any] = []

    if normalized and normalized in payload.get("exact_email_index", {}):
        reasons.append("EXACT_EMAIL_ALREADY_CONTACTED")
        evidence.append(payload["exact_email_index"][normalized])

    if key and key in payload.get("organization_index", {}):
        reasons.append("ORGANIZATION_ALREADY_CONTACTED")
        evidence.append(payload["organization_index"][key])

    if domain and domain not in set(payload.get("shared_mail_domains") or []):
        if domain in payload.get("corporate_domain_index", {}):
            reasons.append("CORPORATE_DOMAIN_ALREADY_CONTACTED")
            evidence.append(payload["corporate_domain_index"][domain])

    decision = "BLOCK_FIRST_CONTACT" if reasons else "CLEAR_FOR_NEXT_GATES"
    return {
        "decision": decision,
        "email": normalized,
        "domain": domain,
        "organization_key": key,
        "reasons": reasons,
        "evidence": evidence,
        "note": "CLEAR only means dedup cleared; route, fit, freshness, legal/channel and send-window gates still apply.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check-email")
    parser.add_argument("--organization-key")
    args = parser.parse_args()

    payload = build() if args.build or not OUT.exists() else load_json(OUT, {})
    if args.check_email or args.organization_key:
        print(json.dumps(check(payload, args.check_email, args.organization_key), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"status": "BUILT", "counts": payload.get("counts"), "path": str(OUT.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
