#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/multi-engine-search-router.json"
MISSIONS = ROOT / "views/search-mission-plan.json"
OUT = ROOT / "views/multi-engine-search-missions.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def iso_date(days_ago):
    return (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=days_ago)).isoformat()


def noise(cfg):
    return " ".join(cfg.get("negative_noise", []))


def ats_scope(cfg):
    domains = cfg.get("official_job_domains", [])
    return "(" + " OR ".join(f"site:{d}" for d in domains) + ")" if domains else ""


def variants(mission, cfg):
    q = mission.get("query", "").strip()
    segment = mission.get("segment", "")
    country = mission.get("country", "")
    region = mission.get("region", "")
    province = mission.get("province", "")
    geo = " ".join(x for x in [province, region, country] if x)
    n = noise(cfg)
    out = []

    def add(kind, query, priority):
        query = " ".join(query.split())
        if query and all(x["query"] != query for x in out):
            out.append({"variant": kind, "query": query, "priority": priority})

    add("base_precision", f"{q} {n}", 100)
    add("fresh_1d", f"{q} after:{iso_date(1)} {n}", 98)
    add("fresh_7d", f"{q} after:{iso_date(7)} {n}", 96)
    add("fresh_30d", f"{q} after:{iso_date(30)} {n}", 90)

    if segment == "DIRECT_JOB":
        add("ats_scoped", f"{ats_scope(cfg)} ({q}) {geo} after:{iso_date(30)}", 99)
        add("linkedin_indexed", f"site:linkedin.com/jobs/view ({q}) {geo} after:{iso_date(30)}", 94)
        add("official_careers", f"({q}) (careers OR jobs OR \"lavora con noi\" OR \"trabaja con nosotros\") {geo} {n}", 97)
    elif segment == "AGENCY_WHITE_LABEL":
        add("official_site", f"({q}) (inurl:careers OR inurl:jobs OR inurl:lavora-con-noi OR inurl:trabaja-con-nosotros OR inurl:collabora) {n}", 99)
        add("exact_route_terms", f"({q}) (\"invia CV\" OR \"envía tu CV\" OR \"send CV\" OR \"collaboratori freelance\" OR \"colaboradores freelance\") {n}", 98)
    elif segment == "DIRECT_BUYER_WEB_NEED":
        add("official_site", f"({q}) (site:.it OR site:.es OR site:.eu) {n}", 96)
        add("procurement_pdf", f"({q}) filetype:pdf (RFP OR RFQ OR bando OR gara OR licitación OR presupuesto) after:{iso_date(30)}", 92)
    elif segment == "WPO_MAINTENANCE":
        add("exact_route_terms", f"({q}) (freelance OR autonomo OR autónomo OR contractor OR collaborazione OR colaboración) {n}", 98)
        add("official_site", f"({q}) (site:.it OR site:.es OR site:.eu) {n}", 94)
    elif segment == "EU_PROJECT":
        add("eu_official", f"({q}) (site:europa.eu OR site:ec.europa.eu OR site:cordis.europa.eu) after:{iso_date(60)}", 100)
        add("pdf_evidence", f"({q}) filetype:pdf (communication OR dissemination OR website OR digital platform) after:{iso_date(90)}", 97)
        add("partner_site", f"({q}) (kickoff OR consortium OR partner OR work package OR dissemination) {n}", 94)

    limit = int(cfg.get("policy", {}).get("max_variants_per_mission", 7))
    return sorted(out, key=lambda x: x["priority"], reverse=True)[:limit]


def main():
    cfg = load(CFG, {})
    plan = load(MISSIONS, {})
    missions = plan.get("missions", [])
    max_missions = int(cfg.get("policy", {}).get("max_missions", 20))
    routed = []
    for mission in missions[:max_missions]:
        routed.append({
            "mission_id": mission.get("mission_id"),
            "country": mission.get("country"),
            "region": mission.get("region"),
            "province": mission.get("province"),
            "segment": mission.get("segment"),
            "territory_mode": mission.get("territory_mode"),
            "territory_score": mission.get("territory_score"),
            "engine_order": cfg.get("engine_order", []),
            "search_variants": variants(mission, cfg),
            "verification_rule": "SEARCH_RESULT_IS_DISCOVERY_ONLY_VERIFY_CURRENT_AUTHORITATIVE_SOURCE_BEFORE_PROMOTION"
        })

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    out = {
        "schema_version": "1.0",
        "updated_at": now,
        "source_plan_updated_at": plan.get("updated_at"),
        "engine_order": cfg.get("engine_order", []),
        "quality_gates_unchanged": True,
        "missions_count": len(routed),
        "query_variants_count": sum(len(x["search_variants"]) for x in routed),
        "missions": routed,
        "instruction": "Discovery tasks should fan out the highest-priority query variants across independent search engines/search backends when available, merge by canonical organization, then verify freshness, fit and route on authoritative sources. Never send from search snippets."
    }
    save(OUT, out)
    print(json.dumps({"missions": out["missions_count"], "variants": out["query_variants_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
