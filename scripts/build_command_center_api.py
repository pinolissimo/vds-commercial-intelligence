#!/usr/bin/env python3
"""Build disposable JSON read-models for the VDS Command Center.

Hard invariant: this script is READ-ONLY with respect to canonical operational data.
It writes only under api/v1/. Existing discovery, send, dedup and reply tasks are not
modified, called, paused or replaced.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, time, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "api" / "v1"
MADRID = ZoneInfo("Europe/Madrid")


def load(rel: str, default):
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def write(name: str, payload) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_dt(value: str | None):
    if not value or not isinstance(value, str):
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


def first_dt(data: dict):
    for key in ("at", "received_at", "created_at", "detected_at", "updated_at", "last_interaction_at"):
        dt = parse_dt(data.get(key))
        if dt:
            return dt
    return None


def domain_from(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    value = value.strip().lower()
    if "@" in value and not value.startswith("http"):
        return value.rsplit("@", 1)[-1].split(">", 1)[0].strip()
    try:
        parsed = urlparse(value if "://" in value else "https://" + value)
        host = (parsed.hostname or "").lower()
        return host[4:] if host.startswith("www.") else (host or None)
    except ValueError:
        return None


def safe_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def extract_emails(data) -> list[str]:
    found: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in {"email", "emails", "recipient", "sender", "address"}:
                    for candidate in safe_list(value):
                        if isinstance(candidate, str) and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", candidate.strip()):
                            found.add(candidate.strip().lower())
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return sorted(found)


def website_from_urls(urls) -> str | None:
    blocked = ("linkedin.com", "indeed.", "glassdoor.", "upwork.com", "freelancer.", "remoteok.com")
    candidates = []
    for value in safe_list(urls):
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            continue
        host = domain_from(value) or ""
        if any(b in host for b in blocked):
            continue
        candidates.append(value)
    return candidates[0] if candidates else None


def clean_company_id(company_id: str | None) -> str | None:
    if not company_id:
        return None
    text = re.sub(r"^(LEAD|IT|ES|EU|REMOTE)-", "", company_id, flags=re.I)
    # Remove common country/territory prefixes while preserving the recognizable tail.
    tokens = text.split("-")
    noise = {
        "IT", "ES", "EU", "REMOTE", "CAT", "BCN", "MD", "MAD", "LOM", "MI", "LAZ", "RM",
        "PIE", "TO", "TOS", "FI", "CAM", "NA", "VEN", "PD", "TV", "EMR", "SIC", "PA",
        "GAL", "CAN", "AST", "ARA", "CV", "VLC", "PUG", "BA", "CAL", "FVG", "TS", "UMB",
    }
    while len(tokens) > 1 and tokens[0].upper() in noise:
        tokens.pop(0)
    return " ".join(t.capitalize() for t in tokens) or company_id


def infer_country(*values: str | None) -> str | None:
    blob = " ".join(str(v or "") for v in values).upper()
    if re.search(r"(^|[-|_ ])IT([-|_ ]|$)", blob):
        return "Italy"
    if re.search(r"(^|[-|_ ])ES([-|_ ]|$)", blob):
        return "Spain"
    if re.search(r"(^|[-|_ ])EU([-|_ ]|$)", blob):
        return "EU"
    if "REMOTE" in blob:
        return "Remote"
    return None


def classify_reply(data: dict, filename: str) -> str:
    tokens: list[str] = []
    for key in ("classification", "status", "outcome", "commercial_interpretation", "summary", "next_action"):
        value = data.get(key)
        if isinstance(value, list):
            tokens.extend(str(v) for v in value)
        elif value is not None:
            tokens.append(str(value))
    blob = (filename + " " + " ".join(tokens)).upper()
    if "BOUNCE" in blob or "DELIVERY FAILURE" in blob:
        return "BOUNCE"
    if any(k in blob for k in ("NEGATIVE", "NOT INTERESTED", "NO_FURTHER_SOLICITATION", "CLOSED_NEGATIVE")):
        return "NEGATIVE"
    if any(k in blob for k in ("POSITIVE", "REFERRAL", "MEETING", "INTERVIEW", "CALL_REQUEST", "PROPOSAL")):
        return "POSITIVE"
    return "NEUTRAL"


def scan_today_replies(today) -> dict:
    events = []
    for path in sorted((ROOT / "replies").glob("*.json")) if (ROOT / "replies").exists() else []:
        if "reply-watch-delta" in path.name:
            continue  # aggregate/delta files can duplicate atomic events
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        dt = first_dt(data)
        if dt is None:
            match = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
            if match and match.group(1) == str(today):
                dt = datetime.combine(today, time(12, 0), tzinfo=MADRID)
        if not dt or dt.astimezone(MADRID).date() != today:
            continue
        classification = classify_reply(data, path.name)
        events.append({
            "at": dt.astimezone(MADRID).isoformat(timespec="seconds"),
            "entity": data.get("entity") or data.get("project") or data.get("organization") or data.get("company") or path.stem,
            "classification": classification,
            "summary": data.get("summary"),
            "source_file": f"replies/{path.name}",
        })
    counts = Counter(e["classification"] for e in events)
    events.sort(key=lambda x: x["at"], reverse=True)
    return {
        "positive": counts.get("POSITIVE", 0),
        "negative": counts.get("NEGATIVE", 0),
        "neutral": counts.get("NEUTRAL", 0),
        "bounces": counts.get("BOUNCE", 0),
        "total_replies": counts.get("POSITIVE", 0) + counts.get("NEGATIVE", 0) + counts.get("NEUTRAL", 0),
        "events": events,
    }


def build_territory_productivity() -> dict:
    radar = load("metrics/territory-yield-radar-state.json", {})
    rows = []
    country_acc = defaultdict(list)
    for area, meta in (radar.get("areas") or {}).items():
        parts = area.split("|")
        country = parts[0] if len(parts) > 0 else "UNRESOLVED"
        region = parts[1] if len(parts) > 1 else "UNRESOLVED"
        territory = parts[2] if len(parts) > 2 else "UNRESOLVED"
        score = float(meta.get("score") or 0)
        row = {
            "area": area,
            "country": country,
            "region": region,
            "territory": territory,
            "score": round(score, 2),
            "mode": meta.get("mode"),
            "harvest_cycles": meta.get("harvest_cycles", 0),
            "low_yield_cycles": meta.get("consecutive_low_yield_cycles", 0),
            "cooldown_until": meta.get("cooldown_until"),
        }
        rows.append(row)
        if country != "UNRESOLVED":
            country_acc[country].append(row)
    rows.sort(key=lambda x: x["score"], reverse=True)
    max_score = max((r["score"] for r in rows), default=0) or 1
    for row in rows:
        row["heat_pct"] = round((row["score"] / max_score) * 100, 1)

    countries = []
    for country, items in country_acc.items():
        scores = [r["score"] for r in items]
        countries.append({
            "country": country,
            "territories": len(items),
            "average_score": round(sum(scores) / max(len(scores), 1), 2),
            "best_score": round(max(scores), 2),
            "harvest_territories": sum(1 for r in items if r.get("mode") == "HARVEST"),
            "top_territory": max(items, key=lambda r: r["score"])["area"],
        })
    countries.sort(key=lambda x: (x["best_score"], x["average_score"]), reverse=True)
    return {
        "schema_version": "1.0",
        "updated_at": radar.get("updated_at"),
        "metric": "existing territory-yield radar score; higher means more productive according to the acquisition engine's current adaptive model",
        "territories": rows,
        "countries": countries,
    }


def build_company_explorer(messages: list[dict]) -> list[dict]:
    entities: dict[str, dict] = {}
    by_domain: dict[str, str] = {}

    def ensure(key: str, **defaults):
        if key not in entities:
            entities[key] = {
                "key": key,
                "organization": defaults.get("organization"),
                "company_id": defaults.get("company_id"),
                "country": defaults.get("country"),
                "region": None,
                "territory": None,
                "website": defaults.get("website"),
                "domain": defaults.get("domain"),
                "emails": [],
                "contacts": [],
                "opportunities": [],
                "opportunity_count": 0,
                "max_priority": None,
                "max_freshness": None,
                "contacted": False,
                "last_outbound_at": None,
                "last_subject": None,
                "workstreams": [],
                "source_urls": [],
            }
        return entities[key]

    # Provider-verified outbound is the strongest company/contact identity source.
    for m in messages:
        domain = domain_from(m.get("recipient")) or domain_from(m.get("canonical_identity_key"))
        key = m.get("canonical_identity_key") or (f"domain:{domain}" if domain else f"sent:{m.get('provider_uid')}")
        entity = ensure(
            key,
            organization=m.get("organization") or domain,
            domain=domain,
            country=infer_country(m.get("canonical_identity_key"), m.get("workstream")),
        )
        if m.get("organization"):
            entity["organization"] = m["organization"]
        if domain:
            entity["domain"] = domain
            by_domain[domain] = key
        if m.get("recipient") and m["recipient"] not in entity["emails"]:
            entity["emails"].append(m["recipient"])
        entity["contacted"] = True
        entity["last_outbound_at"] = max(filter(None, [entity.get("last_outbound_at"), m.get("sent_at")]), default=None)
        entity["last_subject"] = m.get("subject") or entity.get("last_subject")
        if m.get("workstream") and m["workstream"] not in entity["workstreams"]:
            entity["workstreams"].append(m["workstream"])

    # Rich canonical opportunity files add business context, URLs, routes and scores.
    opp_dir = ROOT / "opportunities"
    if opp_dir.exists():
        for path in opp_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            company_id = data.get("company_id")
            title = data.get("title")
            source_urls = safe_list(data.get("source_urls"))
            website = website_from_urls(source_urls)
            route = data.get("route") if isinstance(data.get("route"), dict) else {}
            route_url = route.get("url")
            web_domain = domain_from(website)
            key = by_domain.get(web_domain) if web_domain else None
            if not key:
                key = f"company:{company_id}" if company_id else f"opportunity:{data.get('id') or path.stem}"
            entity = ensure(
                key,
                organization=data.get("organization") or data.get("company") or data.get("company_name") or clean_company_id(company_id),
                company_id=company_id,
                website=website,
                domain=web_domain,
                country=infer_country(data.get("id"), company_id, data.get("campaign_id")),
            )
            if company_id:
                entity["company_id"] = company_id
            if website and not entity.get("website"):
                entity["website"] = website
            if web_domain and not entity.get("domain"):
                entity["domain"] = web_domain
                by_domain[web_domain] = key
            if not entity.get("country"):
                entity["country"] = infer_country(data.get("id"), company_id, data.get("campaign_id"))
            opp = {
                "id": data.get("id") or path.stem,
                "title": title,
                "status": data.get("status"),
                "type": data.get("type"),
                "campaign_id": data.get("campaign_id"),
                "detected_at": data.get("detected_at"),
                "last_verified_at": data.get("last_verified_at"),
                "priority": ((data.get("scores") or {}).get("revenue_priority") if isinstance(data.get("scores"), dict) else None),
                "fit": ((data.get("scores") or {}).get("vds_fit") if isinstance(data.get("scores"), dict) else None),
                "freshness": ((data.get("freshness") or {}).get("score") if isinstance(data.get("freshness"), dict) else data.get("freshness")),
                "route_type": route.get("type"),
                "route_url": route_url,
            }
            entity["opportunities"].append(opp)
            for u in source_urls:
                if isinstance(u, str) and u not in entity["source_urls"]:
                    entity["source_urls"].append(u)

    # Explicit known people/contacts are attached when organization/domain correlates.
    contact_dir = ROOT / "contacts"
    if contact_dir.exists():
        for path in contact_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            emails = extract_emails(data)
            domain = domain_from(emails[0]) if emails else None
            key = by_domain.get(domain) if domain else None
            if not key:
                org = data.get("organization")
                key = f"contact-org:{re.sub(r'[^a-z0-9]+', '-', str(org).lower()).strip('-')}" if org else f"contact:{data.get('id') or path.stem}"
            entity = ensure(
                key,
                organization=data.get("organization") or data.get("company") or data.get("name"),
                company_id=data.get("company_id"),
                domain=domain,
                country=infer_country(data.get("id"), data.get("company_id")),
            )
            for email in emails:
                if email not in entity["emails"]:
                    entity["emails"].append(email)
            contact = {
                "name": data.get("name"),
                "role": data.get("role"),
                "relationship": data.get("relationship"),
                "decision_influence": data.get("decision_influence"),
                "emails": emails,
                "last_interaction_at": data.get("last_interaction_at"),
                "do_not_contact": data.get("do_not_contact", False),
            }
            entity["contacts"].append(contact)

    rows = []
    for entity in entities.values():
        entity["opportunity_count"] = len(entity["opportunities"])
        priorities = [o.get("priority") for o in entity["opportunities"] if isinstance(o.get("priority"), (int, float))]
        freshness = [o.get("freshness") for o in entity["opportunities"] if isinstance(o.get("freshness"), (int, float))]
        entity["max_priority"] = max(priorities, default=None)
        entity["max_freshness"] = max(freshness, default=None)
        entity["emails"] = sorted(set(entity["emails"]))
        entity["search_text"] = " ".join(str(x or "") for x in (
            entity.get("organization"), entity.get("company_id"), entity.get("country"), entity.get("domain"),
            " ".join(entity.get("emails") or []), " ".join(entity.get("workstreams") or [])
        )).lower()
        rows.append(entity)
    rows.sort(key=lambda x: (x.get("contacted"), x.get("max_priority") or 0, x.get("opportunity_count") or 0), reverse=True)
    return rows


def main() -> int:
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(MADRID)
    today = now_local.date()
    generated = now_local.isoformat(timespec="seconds")

    semantic = load("metrics/high-frequency-semantic-gate.json", {})
    opportunities = load("views/active-freelance-opportunities.json", {})
    sent = load("views/global-sent-email-index.json", {})
    success = load("views/success-indicators.json", {})
    missions = load("views/multi-engine-search-missions.json", {})
    mission_plan = load("views/search-mission-plan.json", {})
    seeds = load("views/high-frequency-discovery-qualified-seeds.json", {})
    action_queue = load("views/action-queue.json", {})
    fast_queue = load("views/fast-revenue-queue.json", {})
    direct_pipeline = load("views/direct-commercial-pipeline.json", {})
    daily_summary = load(f"metrics/daily/{today}-summary.json", {})

    opps = opportunities.get("opportunities") or []
    status_counts = Counter(str(o.get("status", "UNKNOWN")) for o in opps)
    type_counts = Counter(str(o.get("type", "UNKNOWN")) for o in opps)

    normalized_opps = []
    for o in opps:
        normalized_opps.append({
            "id": o.get("id"),
            "company_id": o.get("company_id"),
            "type": o.get("type"),
            "priority": o.get("priority"),
            "freshness": o.get("freshness"),
            "status": o.get("status"),
            "sent_uid": o.get("sent_uid"),
            "country": infer_country(o.get("id"), o.get("company_id")),
        })
    normalized_opps.sort(key=lambda x: (x.get("priority") or 0, x.get("freshness") or 0), reverse=True)

    messages = sent.get("messages") or []
    today_messages = []
    for m in messages:
        dt = parse_dt(m.get("sent_at"))
        if dt and dt.astimezone(MADRID).date() == today:
            item = dict(m)
            item["sent_at_local"] = dt.astimezone(MADRID).isoformat(timespec="seconds")
            today_messages.append(item)
    today_messages.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
    today_first_contacts = [m for m in today_messages if m.get("action_type", "FIRST_CONTACT") == "FIRST_CONTACT"]

    # Throughput is normalized to the active 09:00–19:00 local sending window.
    window_start = datetime.combine(today, time(9, 0), tzinfo=MADRID)
    window_end = datetime.combine(today, time(19, 0), tzinfo=MADRID)
    elapsed_end = min(max(now_local, window_start), window_end)
    elapsed_hours = max((elapsed_end - window_start).total_seconds() / 3600.0, 0.0)
    sent_per_hour = round(len(today_messages) / elapsed_hours, 2) if elapsed_hours > 0 else 0.0
    first_contacts_per_hour = round(len(today_first_contacts) / elapsed_hours, 2) if elapsed_hours > 0 else 0.0

    reply_scan = scan_today_replies(today)
    summary_outcomes = daily_summary.get("outcomes") if isinstance(daily_summary.get("outcomes"), dict) else {}
    # Daily summary is a second source. Use max to avoid double-counting atomic reply files.
    positive_replies = max(reply_scan["positive"], int(summary_outcomes.get("positive_replies") or 0))
    negative_replies = max(reply_scan["negative"], int(summary_outcomes.get("negative_replies") or 0))
    total_replies = max(reply_scan["total_replies"], int(summary_outcomes.get("new_relevant_replies_since_prior_watch") or 0))

    last_run = semantic.get("last_run") or {}
    semantic_rate = None
    if last_run.get("input"):
        semantic_rate = round((last_run.get("pass", 0) / last_run["input"]) * 100, 2)

    manual_count = sum(1 for o in normalized_opps if "MANUAL" in str(o.get("status", "")))
    ready_count = sum(
        1 for o in normalized_opps
        if str(o.get("status", "")).startswith("READY") and "MANUAL" not in str(o.get("status", ""))
    )
    contacted_count = sum(1 for o in normalized_opps if "CONTACTED" in str(o.get("status", "")))

    territory = build_territory_productivity()
    companies = build_company_explorer(messages)

    source_payload = {
        "schema_version": "1.0",
        "generated_at": generated,
        "semantic_gate": {
            "runs": semantic.get("runs", 0),
            "total_input": semantic.get("total_input", 0),
            "total_pass": semantic.get("total_pass", 0),
            "total_review": semantic.get("total_review", 0),
            "total_reject": semantic.get("total_reject", 0),
            "last_run": last_run,
            "last_run_pass_rate_pct": semantic_rate,
        },
        "multi_engine_router": {
            "missions_count": missions.get("missions_count"),
            "query_variants_count": missions.get("query_variants_count"),
            "engine_order": missions.get("engine_order") or missions.get("engines"),
            "generated_at": missions.get("generated_at") or missions.get("updated_at"),
        },
        "mission_plan": {
            "updated_at": mission_plan.get("updated_at"),
            "cycle_minutes": mission_plan.get("cycle_minutes"),
            "diagnosed_bottleneck": mission_plan.get("diagnosed_bottleneck"),
            "selected_territories": mission_plan.get("selected_territories") or mission_plan.get("territories"),
        },
        "qualified_seed_summary": {
            "input": seeds.get("input"),
            "semantic_pass": seeds.get("semantic_pass"),
            "semantic_review": seeds.get("semantic_review"),
            "reject": seeds.get("reject"),
            "updated_at": seeds.get("updated_at") or seeds.get("generated_at"),
        },
    }

    dashboard = {
        "schema_version": "1.1",
        "generated_at": generated,
        "source_of_truth": "pinolissimo/vds-commercial-intelligence@main",
        "production_core": "UNCHANGED_AND_AUTHORITATIVE",
        "today": {
            "date": str(today),
            "sent": len(today_messages),
            "first_contacts_sent": len(today_first_contacts),
            "replies_total": total_replies,
            "replies_positive": positive_replies,
            "replies_negative": negative_replies,
            "replies_neutral": reply_scan["neutral"],
            "hard_bounces": reply_scan["bounces"],
            "messages_per_active_hour": sent_per_hour,
            "first_contacts_per_active_hour": first_contacts_per_hour,
            "active_window_elapsed_hours": round(elapsed_hours, 2),
            "sending_window": "09:00-19:00 Europe/Madrid",
        },
        "headline": {
            "semantic_input_last_run": last_run.get("input", 0),
            "semantic_pass_last_run": last_run.get("pass", 0),
            "semantic_pass_rate_pct": semantic_rate,
            "active_opportunities": len(normalized_opps),
            "ready": ready_count,
            "manual_action": manual_count,
            "contacted_in_active_view": contacted_count,
            "sent_today": len(today_messages),
            "success_index_pct": (success.get("success_index") or {}).get("value_pct"),
            "new_client_probability_proxy_pct": (success.get("new_client_probability_proxy") or {}).get("display_pct"),
            "companies_indexed": len(companies),
        },
        "status_counts": dict(status_counts),
        "type_counts": dict(type_counts),
        "top_territories": territory["territories"][:12],
        "top_countries": territory["countries"],
        "queues": {
            "action_queue_updated_at": action_queue.get("updated_at"),
            "fast_revenue_queue_updated_at": fast_queue.get("updated_at"),
            "direct_pipeline_updated_at": direct_pipeline.get("updated_at"),
        },
        "safety": {
            "duplicate_first_contact_tolerance": 0,
            "global_duplicate_hard_gate": True,
            "sent_verification_required": True,
            "dashboard_can_bypass_gates": False,
            "production_search_is_independent_from_dashboard": True,
        },
    }

    write("dashboard.json", dashboard)
    write("today.json", {
        "schema_version": "1.1",
        "generated_at": generated,
        "date": str(today),
        "timezone": "Europe/Madrid",
        "sent_count": len(today_messages),
        "first_contact_count": len(today_first_contacts),
        "messages_per_active_hour": sent_per_hour,
        "first_contacts_per_active_hour": first_contacts_per_hour,
        "replies": {
            "total": total_replies,
            "positive": positive_replies,
            "negative": negative_replies,
            "neutral": reply_scan["neutral"],
            "hard_bounces": reply_scan["bounces"],
            "events": reply_scan["events"],
        },
        "sent": today_messages,
        "semantic_last_run": last_run,
        "daily_summary_updated_at": daily_summary.get("updated_at"),
    })
    write("outbound.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "provider_of_record": sent.get("provider_of_record"),
        "messages": messages,
        "today_count": len(today_messages),
        "today_first_contact_count": len(today_first_contacts),
        "messages_per_active_hour": sent_per_hour,
    })
    write("opportunities.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "count": len(normalized_opps),
        "status_counts": dict(status_counts),
        "type_counts": dict(type_counts),
        "opportunities": normalized_opps,
    })
    write("companies.json", {
        "schema_version": "1.0",
        "generated_at": generated,
        "count": len(companies),
        "description": "Searchable company/contact projection assembled from canonical opportunity files, explicit contacts and provider-verified outbound. It is a read model, not a replacement CRM database.",
        "companies": companies,
    })
    write("territory-productivity.json", territory)
    write("sources.json", source_payload)
    write("health.json", {
        "schema_version": "1.1",
        "generated_at": generated,
        "status": "OK",
        "production_core": "UNCHANGED",
        "production_search_independent": True,
        "projection_builder": "OK",
        "openai_command_secret_required": True,
        "canonical_inputs": {
            "semantic_gate_updated_at": semantic.get("updated_at"),
            "territory_radar_updated_at": territory.get("updated_at"),
            "sent_index_updated_at": sent.get("updated_at"),
            "active_opportunities_updated_at": opportunities.get("updated_at"),
            "daily_summary_updated_at": daily_summary.get("updated_at"),
        },
    })

    latest = OUT / "ai-command" / "latest.json"
    if not latest.exists():
        latest.parent.mkdir(parents=True, exist_ok=True)
        latest.write_text(json.dumps({
            "schema_version": "1.0",
            "generated_at": generated,
            "status": "NO_COMMAND_YET",
            "message": "The AI command channel is installed but has not processed a command yet."
        }, indent=2) + "\n", encoding="utf-8")

    print(
        f"Command Center API generated at {generated}: "
        f"{len(normalized_opps)} opportunities, {len(companies)} companies, "
        f"{len(today_messages)} sent today, {positive_replies}/{negative_replies} positive/negative replies"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
