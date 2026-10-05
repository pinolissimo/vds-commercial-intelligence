#!/usr/bin/env python3
# Visual Design Studio — 2026
"""Opportunity-first verified first-contact queue builder.

Consumes only first-party verified contact routes matched to opportunity-first
commercial signals. It NEVER sends mail directly: eligible FIRST_CONTACT records
are appended to the canonical autonomous sender queue as APPROVED_TO_SEND.
The autonomous Hostinger sender remains the only provider writer.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / "views/opportunity-first-optimizer.json"
ROUTES = ROOT / "views/public-web-enriched-routes.json"
LEDGER = ROOT / "views/global-contact-ledger.json"
QUEUE = ROOT / "outreach/autonomous-send-queue.jsonl"
OUT = ROOT / "state/opportunity-first-dispatch-latest.json"
AUDIT_DIR = ROOT / "data/opportunity-first-dispatch-runs"

AGGREGATORS = {
    "jobicy.com", "arbeitnow.com", "arbeitnow.co.uk", "arbeitnow.ch",
    "remoteok.com", "remotive.com", "linkedin.com", "indeed.com",
    "upwork.com", "jobs.ashbyhq.com",
}
PLACEHOLDERS = (
    "example.com", "company.com", "your@email", "test@", "noreply@", "no-reply@"
)
ACTIVE_QUEUE_STATUSES = {"APPROVED_TO_SEND", "SENT"}


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_jsonl(path: Path):
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    except FileNotFoundError:
        pass
    return rows


def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def domain_of_url(value):
    try:
        return (urlparse(value or "").hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def email_domain(value):
    value = str(value or "").strip().lower()
    return value.rsplit("@", 1)[-1] if "@" in value else ""


def valid_email(email, domain):
    email = str(email or "").strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return False
    if any(x in email for x in PLACEHOLDERS):
        return False
    return email_domain(email) == domain


def lang_for_domain(domain):
    if domain.endswith(".it"):
        return "it"
    if domain.endswith(".es"):
        return "es"
    return "en"


def message_for(org, strategy, lang):
    site = "https://www.visualdesignstudio.es/"
    if lang == "it":
        subject = "Collaborazione tecnica web — Visual Design Studio"
        body = f"""Buongiorno {org},

sono Giuseppe Allocca, Visual Design Studio, professionista web con base a Barcellona.

Collaboro con agenzie e aziende come supporto tecnico esterno su progetti WordPress, frontend custom, performance/WPO, redesign, landing page e siti ad alte prestazioni. Lavoro anche con un'architettura proprietaria leggera, orientata a velocità, qualità e integrazione semplice nei workflow esistenti.

Esempio diretto di architettura e performance: {site}

Se può essere utile avere capacità tecnica esterna per picchi di lavoro o progetti specifici, posso condividere rapidamente esempi pertinenti.

Un saluto,
Giuseppe Allocca
Visual Design Studio
{site}
"""
    elif lang == "es":
        subject = "Colaboración técnica web — Visual Design Studio"
        body = f"""Hola {org},

soy Giuseppe Allocca, de Visual Design Studio, profesional web con base en Barcelona.

Colaboro con agencias y empresas como apoyo técnico externo en proyectos WordPress, frontend a medida, performance/WPO, rediseños, landing pages y sitios de alto rendimiento. Trabajo también con una arquitectura propia ligera, orientada a velocidad, calidad e integración sencilla con flujos existentes.

Ejemplo directo de arquitectura y rendimiento: {site}

Si os puede resultar útil contar con capacidad técnica externa para picos de trabajo o proyectos concretos, puedo enviar rápidamente algunos ejemplos relevantes.

Un saludo,
Giuseppe Allocca
Visual Design Studio
{site}
"""
    else:
        subject = "External web development capacity — Visual Design Studio"
        body = f"""Hello {org},

I'm Giuseppe Allocca from Visual Design Studio, a web professional based in Barcelona.

I work with agencies and companies as external technical capacity for WordPress, custom frontend, performance/WPO, redesigns, landing pages and high-performance websites. I also work with a lightweight proprietary architecture focused on speed, quality and easy integration with existing delivery workflows.

Architecture and performance example: {site}

If external capacity could be useful for project peaks or specific web work, I can quickly share relevant examples.

Best regards,
Giuseppe Allocca
Visual Design Studio
{site}
"""
    return subject, body


def queue_id_for(domain, email, signal_key):
    raw = f"{domain}|{email.lower()}|{signal_key or ''}"
    return "opp-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def main():
    now = datetime.now(timezone.utc)
    stamp = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    opp = load(OPP, {"opportunities": []})
    routes = load(ROUTES, {"items": []})
    ledger = load(LEDGER, {})
    queue = load_jsonl(QUEUE)

    exact = set((ledger.get("exact_email_index") or {}).keys())
    domains = set((ledger.get("corporate_domain_index") or {}).keys())

    queued_exact = set()
    queued_domains = set()
    queued_ids = set()
    for item in queue:
        qid = str(item.get("queue_id") or "")
        if qid:
            queued_ids.add(qid)
        if str(item.get("status") or "") not in ACTIVE_QUEUE_STATUSES:
            continue
        recipient = str(item.get("recipient") or "").strip().lower()
        if recipient and "@" in recipient:
            queued_exact.add(recipient)
            queued_domains.add(email_domain(recipient))

    # Match only official, non-aggregator domains with strong opportunity score.
    by_domain = {}
    for opportunity in opp.get("opportunities") or []:
        if float(opportunity.get("opportunity_first_score") or 0) < 70:
            continue
        for url in (opportunity.get("authoritative_apply_url"), opportunity.get("opportunity_url")):
            domain = domain_of_url(url)
            if not domain or domain in AGGREGATORS:
                continue
            by_domain.setdefault(domain, []).append(opportunity)

    candidates = []
    seen_domains = set()
    for route in routes.get("items") or []:
        domain = str(route.get("domain") or "").lower().removeprefix("www.")
        if not domain or domain in AGGREGATORS or domain in seen_domains:
            continue
        if route.get("state") != "CONTACTABLE_EVIDENCE":
            continue
        if int(route.get("contactability_score") or 0) < 65:
            continue
        matches = by_domain.get(domain) or []
        if not matches:
            continue
        best = max(matches, key=lambda x: float(x.get("opportunity_first_score") or 0))
        emails = [e.strip().lower() for e in (route.get("public_emails") or []) if valid_email(e, domain)]
        emails = [e for e in emails if e not in exact and e not in queued_exact]
        if domain in domains or domain in queued_domains or not emails:
            continue
        candidate = {
            "organization": best.get("organization") or domain,
            "domain": domain,
            "email": emails[0],
            "score": best.get("opportunity_first_score"),
            "strategy": best.get("message_strategy"),
            "source_url": route.get("source_url"),
            "signal_key": best.get("signal_key"),
        }
        candidates.append(candidate)
        seen_domains.add(domain)

    candidates.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
    max_batch = max(1, min(int(os.getenv("VDS_DISPATCH_MAX_BATCH", "10")), 100))

    results = []
    queued_count = 0
    for candidate in candidates[:max_batch]:
        email = candidate["email"]
        domain = candidate["domain"]
        qid = queue_id_for(domain, email, candidate.get("signal_key"))

        # JIT local guard immediately before queue mutation.
        if email in exact or domain in domains or email in queued_exact or domain in queued_domains or qid in queued_ids:
            results.append({**candidate, "state": "BLOCKED_DUPLICATE_PRE_QUEUE"})
            continue

        subject, body = message_for(candidate["organization"], candidate.get("strategy"), lang_for_domain(domain))
        record = {
            "schema_version": "1.1",
            "queue_id": qid,
            "status": "APPROVED_TO_SEND",
            "action_type": "FIRST_CONTACT",
            "eligibility_basis": "AUTONOMOUS_FIRST_CONTACT",
            "organization": candidate["organization"],
            "recipient": email,
            "subject": subject,
            "text": body,
            "approved_at": stamp,
            "metadata": {
                "prepared_at": stamp,
                "source": "opportunity-first-queue-builder",
                "priority": candidate.get("score"),
                "source_url": candidate.get("source_url"),
                "signal_key": candidate.get("signal_key"),
                "message_strategy": candidate.get("strategy"),
                "approved_via": "AUTOMATED_FIRST_CONTACT_POLICY",
                "approval_basis": "FIRST_PARTY_VERIFIED_ROUTE_PLUS_GLOBAL_DEDUP",
            },
        }
        queue.append(record)
        queued_count += 1
        queued_exact.add(email)
        queued_domains.add(domain)
        queued_ids.add(qid)
        results.append({**candidate, "state": "APPROVED_TO_SEND", "queue_id": qid, "subject": subject})

    if queued_count:
        save_jsonl(QUEUE, queue)

    payload = {
        "schema_version": "2.0",
        "updated_at": stamp,
        "status": "COMPLETED",
        "mode": "QUEUE_ONLY_SINGLE_PROVIDER_WRITER",
        "candidate_count": len(candidates),
        "batch_limit": max_batch,
        "queued_approved": queued_count,
        "blocked_duplicate": sum(1 for x in results if str(x.get("state", "")).startswith("BLOCKED_DUPLICATE")),
        "queue_records_total": len(queue),
        "results": results,
    }
    save(OUT, payload)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    save(AUDIT_DIR / (stamp.replace(":", "-") + ".json"), payload)
    print(json.dumps({k: payload[k] for k in (
        "status", "mode", "candidate_count", "batch_limit", "queued_approved", "blocked_duplicate", "queue_records_total"
    )}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
