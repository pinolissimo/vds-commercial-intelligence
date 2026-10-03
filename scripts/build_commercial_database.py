#!/usr/bin/env python3
"""Build the VDS commercial prospect database projection.

Visual Design Studio — 2026

Read-only over canonical CRM/outreach sources. Writes only disposable projections
under api/v1/. The database is grouped by potential-customer type, country and
region while preserving contact data and anti-duplication state.
"""
from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")

TYPE_ORDER = [
    "WEB_DIGITAL_AGENCY",
    "CREATIVE_BRANDING_AGENCY",
    "MARKETING_COMMUNICATION_AGENCY",
    "SOFTWARE_HOUSE_TECH_COMPANY",
    "EU_PROJECT_RESEARCH_ORGANIZATION",
    "SME_DIRECT_BUYER",
    "ECOMMERCE_RETAIL",
    "PROFESSIONAL_SERVICES",
    "REAL_ESTATE_HOSPITALITY",
    "PUBLIC_SECTOR_PROCUREMENT",
    "NONPROFIT_ASSOCIATION",
    "RECRUITER_INTERMEDIARY",
    "OTHER",
]

TYPE_LABELS = {
    "WEB_DIGITAL_AGENCY": "Web / Digital Agency",
    "CREATIVE_BRANDING_AGENCY": "Creative / Branding Agency",
    "MARKETING_COMMUNICATION_AGENCY": "Marketing / Communication Agency",
    "SOFTWARE_HOUSE_TECH_COMPANY": "Software House / Tech Company",
    "EU_PROJECT_RESEARCH_ORGANIZATION": "EU Project / Research Organization",
    "SME_DIRECT_BUYER": "SME / Direct Buyer",
    "ECOMMERCE_RETAIL": "E-commerce / Retail",
    "PROFESSIONAL_SERVICES": "Professional Services",
    "REAL_ESTATE_HOSPITALITY": "Real Estate / Hospitality",
    "PUBLIC_SECTOR_PROCUREMENT": "Public Sector / Procurement",
    "NONPROFIT_ASSOCIATION": "Nonprofit / Association",
    "RECRUITER_INTERMEDIARY": "Recruiter / Intermediary",
    "OTHER": "Other",
}

REGION_HINTS = {
    "IT-LOM": ("Italy", "Lombardia"), "IT-LAZ": ("Italy", "Lazio"),
    "IT-TOS": ("Italy", "Toscana"), "IT-CAM": ("Italy", "Campania"),
    "IT-PIE": ("Italy", "Piemonte"), "IT-VEN": ("Italy", "Veneto"),
    "IT-EMR": ("Italy", "Emilia-Romagna"), "IT-PUG": ("Italy", "Puglia"),
    "IT-CAL": ("Italy", "Calabria"), "IT-SIC": ("Italy", "Sicilia"),
    "IT-LIG": ("Italy", "Liguria"), "IT-FVG": ("Italy", "Friuli-Venezia Giulia"),
    "IT-TAA": ("Italy", "Trentino-Alto Adige"),
    "ES-CAT": ("Spain", "Cataluña"), "ES-MAD": ("Spain", "Comunidad de Madrid"),
    "ES-MD": ("Spain", "Comunidad de Madrid"), "ES-CV": ("Spain", "Comunitat Valenciana"),
    "ES-AND": ("Spain", "Andalucía"), "ES-GAL": ("Spain", "Galicia"),
    "ES-CYL": ("Spain", "Castilla y León"), "ES-ARA": ("Spain", "Aragón"),
    "ES-MUR": ("Spain", "Región de Murcia"), "ES-AST": ("Spain", "Asturias"),
    "ES-CAN": ("Spain", "Cantabria"),
}

def load(rel, default):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(name, payload):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def blob(company):
    opps = company.get("opportunities") or []
    parts = [
        company.get("organization"), company.get("company_id"), company.get("website"),
        company.get("domain"), company.get("country"), company.get("region"), company.get("territory"),
        " ".join(company.get("workstreams") or []),
        " ".join(company.get("source_urls") or []),
    ]
    for o in opps:
        parts.extend([o.get("title"), o.get("type"), o.get("campaign_id"), o.get("status")])
    return " ".join(str(x or "") for x in parts).lower()

def classify(company):
    text = blob(company)
    opp_types = {str(x.get("type") or "").upper() for x in company.get("opportunities") or []}
    campaign = " ".join(str(x.get("campaign_id") or "") for x in company.get("opportunities") or []).upper()

    if any(x in text for x in ["horizon", "prima", "european project", "eu project", "dissemination", "research project"]):
        return "EU_PROJECT_RESEARCH_ORGANIZATION"
    if any(x in opp_types for x in {"WHITE_LABEL", "OUTSOURCING", "STRUCTURAL_PARTNERSHIP", "ACTIVE_FREELANCE_COLLABORATION"}) or "AGENCY-OUTSOURCING" in campaign:
        if any(x in text for x in ["branding", "creative agency", "design studio"]):
            return "CREATIVE_BRANDING_AGENCY"
        if any(x in text for x in ["marketing", "communication", "comunicazione", "comunicación", "social media"]):
            return "MARKETING_COMMUNICATION_AGENCY"
        return "WEB_DIGITAL_AGENCY"
    if any(x in text for x in ["web agency", "digital agency", "agenzia web", "agencia web", "wordpress agency"]):
        return "WEB_DIGITAL_AGENCY"
    if any(x in text for x in ["creative agency", "branding agency", "design studio"]):
        return "CREATIVE_BRANDING_AGENCY"
    if any(x in text for x in ["marketing agency", "communication agency", "agenzia di comunicazione", "agencia de comunicación"]):
        return "MARKETING_COMMUNICATION_AGENCY"
    if any(x in text for x in ["software house", "software company", "tech company", "saas", "platform"]):
        return "SOFTWARE_HOUSE_TECH_COMPANY"
    if any(x in text for x in ["public procurement", "tender", "municipality", "comune", "ayuntamiento", "provincia", "regione"]):
        return "PUBLIC_SECTOR_PROCUREMENT"
    if any(x in text for x in ["real estate", "immobiliare", "inmobiliaria", "hotel", "hospitality", "resort"]):
        return "REAL_ESTATE_HOSPITALITY"
    if any(x in text for x in ["ecommerce", "e-commerce", "woocommerce", "retail", "shop"]):
        return "ECOMMERCE_RETAIL"
    if any(x in text for x in ["association", "associazione", "asociación", "foundation", "fondazione", "fundación", "ngo", "nonprofit"]):
        return "NONPROFIT_ASSOCIATION"
    if any(x in text for x in ["recruit", "talent", "staffing", "headhunter"]):
        return "RECRUITER_INTERMEDIARY"
    if any(x in text for x in ["consulting", "consultancy", "studio professionale", "law firm", "advisory"]):
        return "PROFESSIONAL_SERVICES"
    if company.get("opportunity_count", 0):
        return "SME_DIRECT_BUYER"
    return "OTHER"

def infer_geo(company):
    country = company.get("country") or "Unknown"
    region = company.get("region")
    cid = str(company.get("company_id") or company.get("key") or "").upper()
    opp_ids = " ".join(str(x.get("id") or "") for x in company.get("opportunities") or []).upper()
    geo_blob = cid + " " + opp_ids
    if not region:
        for prefix, value in sorted(REGION_HINTS.items(), key=lambda x: len(x[0]), reverse=True):
            if prefix in geo_blob:
                country, region = value
                break
    if country in {"Unknown", "EU", "Remote"}:
        if re.search(r"(^|[-_ ])IT([-_ ]|$)", geo_blob) or str(company.get("domain") or "").lower().endswith(".it"):
            country = "Italy"
        elif re.search(r"(^|[-_ ])ES([-_ ]|$)", geo_blob) or str(company.get("domain") or "").lower().endswith(".es"):
            country = "Spain"
        elif re.search(r"(^|[-_ ])DE([-_ ]|$)", geo_blob) or str(company.get("domain") or "").lower().endswith(".de"):
            country = "Germany"
        elif re.search(r"(^|[-_ ])FR([-_ ]|$)", geo_blob) or str(company.get("domain") or "").lower().endswith(".fr"):
            country = "France"
        elif re.search(r"(^|[-_ ])AT([-_ ]|$)", geo_blob) or str(company.get("domain") or "").lower().endswith(".at"):
            country = "Austria"
    return country or "Unknown", region or "Unresolved"

def dedup_state(company, ledger):
    exact = ledger.get("exact_email_index") or {}
    domains = ledger.get("corporate_domain_index") or {}
    orgs = ledger.get("organization_index") or {}
    shared = set(ledger.get("shared_mail_domains") or [])

    reasons = []
    for email in company.get("emails") or []:
        e = str(email).strip().lower()
        if e in exact:
            reasons.append("EXACT_EMAIL_ALREADY_CONTACTED")
        if "@" in e:
            d = e.rsplit("@",1)[1].lower().lstrip("www.")
            if d not in shared and d in domains:
                reasons.append("CORPORATE_DOMAIN_ALREADY_CONTACTED")
    domain = str(company.get("domain") or "").lower().lstrip("www.")
    if domain and domain not in shared and domain in domains:
        reasons.append("CORPORATE_DOMAIN_ALREADY_CONTACTED")
    keys = [company.get("key"), company.get("company_id")]
    for key in keys:
        if key and str(key).lower() in orgs:
            reasons.append("ORGANIZATION_ALREADY_CONTACTED")
    if company.get("contacted") and not reasons:
        reasons.append("CONTACTED_STATE_FROM_COMPANY_PROJECTION")
    reasons = sorted(set(reasons))
    return {
        "first_contact_allowed": not reasons,
        "decision": "HARD_BLOCK_DUPLICATE" if reasons else "CLEAR_FOR_NEXT_GATES",
        "reasons": reasons,
    }

def main():
    generated = datetime.now(MADRID).isoformat(timespec="seconds")
    companies = load("api/v1/companies.json", {}).get("companies") or []
    ledger = load("views/global-contact-ledger.json", {})

    rows = []
    by_type = defaultdict(list)
    by_country = defaultdict(list)
    by_region = defaultdict(list)

    for c in companies:
        ctype = classify(c)
        country, region = infer_geo(c)
        anti_dup = dedup_state(c, ledger)
        row = {
            "id": c.get("company_id") or c.get("key"),
            "organization": c.get("organization"),
            "customer_type": ctype,
            "customer_type_label": TYPE_LABELS.get(ctype, ctype),
            "country": country,
            "region": region,
            "territory": c.get("territory"),
            "website": c.get("website"),
            "domain": c.get("domain"),
            "emails": sorted(set(c.get("emails") or [])),
            "contacts": c.get("contacts") or [],
            "opportunities": c.get("opportunities") or [],
            "opportunity_count": c.get("opportunity_count") or 0,
            "max_priority": c.get("max_priority"),
            "max_freshness": c.get("max_freshness"),
            "contacted": bool(c.get("contacted")),
            "last_outbound_at": c.get("last_outbound_at"),
            "last_subject": c.get("last_subject"),
            "workstreams": c.get("workstreams") or [],
            "source_urls": c.get("source_urls") or [],
            "anti_duplication": anti_dup,
        }
        rows.append(row)
        by_type[ctype].append(row["id"])
        by_country[country].append(row["id"])
        by_region[f"{country}|{region}"].append(row["id"])

    rows.sort(key=lambda x: (
        TYPE_ORDER.index(x["customer_type"]) if x["customer_type"] in TYPE_ORDER else 999,
        x["country"], x["region"], -(x.get("max_priority") or 0), str(x.get("organization") or "")
    ))

    summary_types = []
    for key in TYPE_ORDER:
        ids = by_type.get(key, [])
        subset = [r for r in rows if r["customer_type"] == key]
        summary_types.append({
            "type": key,
            "label": TYPE_LABELS[key],
            "count": len(ids),
            "contacted": sum(1 for r in subset if r["contacted"]),
            "clear_for_first_contact": sum(1 for r in subset if r["anti_duplication"]["first_contact_allowed"]),
        })

    payload = {
        "schema_version": "1.0",
        "generated_at": generated,
        "purpose": "Commercial prospect database organized by potential-customer type, country and region, including contacts, opportunities and anti-duplication state.",
        "anti_duplication_policy": {
            "rule": "NO_DUPLICATION",
            "first_contact_must_pass_global_ledger": True,
            "exact_email": "HARD_BLOCK",
            "corporate_domain": "HARD_BLOCK",
            "canonical_organization": "HARD_BLOCK",
            "volume_can_never_bypass_dedup": True,
        },
        "count": len(rows),
        "summary_by_type": summary_types,
        "summary_by_country": [
            {"country": k, "count": len(v)} for k,v in sorted(by_country.items(), key=lambda x:(-len(x[1]),x[0]))
        ],
        "summary_by_region": [
            {"country": k.split("|",1)[0], "region": k.split("|",1)[1], "count": len(v)}
            for k,v in sorted(by_region.items(), key=lambda x:(x[0].split("|",1)[0],-len(x[1]),x[0]))
        ],
        "indexes": {
            "by_customer_type": dict(sorted(by_type.items())),
            "by_country": dict(sorted(by_country.items())),
            "by_country_region": dict(sorted(by_region.items())),
        },
        "companies": rows,
    }
    write_json("commercial-database.json", payload)

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([
        "organization","customer_type","country","region","territory","website","domain",
        "emails","contact_names","opportunity_count","max_priority","contacted",
        "first_contact_allowed","dedup_decision","dedup_reasons","last_outbound_at"
    ])
    for r in rows:
        names = [str(x.get("name") or "") for x in r["contacts"] if isinstance(x, dict) and x.get("name")]
        w.writerow([
            r["organization"], r["customer_type"], r["country"], r["region"], r["territory"],
            r["website"], r["domain"], "; ".join(r["emails"]), "; ".join(names),
            r["opportunity_count"], r["max_priority"], r["contacted"],
            r["anti_duplication"]["first_contact_allowed"], r["anti_duplication"]["decision"],
            "; ".join(r["anti_duplication"]["reasons"]), r["last_outbound_at"]
        ])
    (OUT / "commercial-database.csv").write_text(out.getvalue(), encoding="utf-8")

    print(json.dumps({
        "companies": len(rows),
        "types": {x["type"]: x["count"] for x in summary_types if x["count"]},
        "countries": {x["country"]: x["count"] for x in payload["summary_by_country"]},
        "duplicates_blocked": sum(1 for r in rows if not r["anti_duplication"]["first_contact_allowed"]),
        "clear_for_next_gates": sum(1 for r in rows if r["anti_duplication"]["first_contact_allowed"]),
    }, ensure_ascii=False))

if __name__ == "__main__":
    raise SystemExit(main())
