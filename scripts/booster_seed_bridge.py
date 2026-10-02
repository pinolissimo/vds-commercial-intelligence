#!/usr/bin/env python3
"""Translate public-web booster findings into conservative buyer-intent seeds.

Booster findings never authorize outreach. They are ranking/qualification inputs only.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"views/public-web-booster.json"
ENRICHED=ROOT/"views/public-web-enriched-routes.json"
OUT=ROOT/"views/public-web-qualified-seeds.json"

def load(path,default):
    try:
        v=json.loads(path.read_text(encoding="utf-8")); return v if isinstance(v,dict) else default
    except Exception:return default

def main():
    src=load(SRC,{})
    enriched=load(ENRICHED,{})
    enrich_index={(x.get("domain"),x.get("source_url")):x for x in (enriched.get("items") or []) if isinstance(x,dict)}
    rows=[]
    for item in src.get("signals") or []:
        url=item.get("url"); domain=item.get("domain")
        if not url or not domain: continue
        terms=item.get("matched_terms") or []
        sample=item.get("text_sample") or ""
        route=enrich_index.get((domain,url),{})
        if route.get("state")=="BLOCKED_DUPLICATE":
            continue
        public_emails=route.get("public_emails") or item.get("emails") or []
        supplier_routes=route.get("supplier_routes") or []
        authoritative_route=(supplier_routes[0] if supplier_routes else url)
        if public_emails:
            route_state="EMAIL_VERIFIED_FIRST_PARTY"
        elif supplier_routes:
            route_state="OFFICIAL_CONTACT_ROUTE"
        else:
            route_state="OFFICIAL_PAGE_TO_VERIFY"
        key="booster:"+hashlib.sha1(url.encode()).hexdigest()[:16]
        rows.append({
          "signal_key":key,
          "organization":domain,
          "title":"Public collaboration / supplier signal",
          "location":"",
          "description":sample,
          "snippet":sample,
          "opportunity_url":url,
          "authoritative_apply_url":authoritative_route,
          "published_at":None,
          "published_age_days":None,
          "source_id":"public_web_booster",
          "source_authority":"EMPLOYER_DIRECT_PUBLIC_PAGE",
          "route_state":route_state,
          "target_geo_bucket":"EU_REMOTE_TO_VERIFY",
          "matched_profile_keywords":["wordpress","frontend","web"] if any(x in terms for x in ["wordpress","frontend","front-end","web developer","sviluppatore web","desarrollador web"]) else [],
          "matched_commercial_keywords":terms,
          "semantic_role_hits":terms,
          "semantic_intent_hits":terms,
          "project_scope_hits":["project-based","external collaboration"] if any(x in terms for x in ["freelance","partita iva","autonomo","autónomo","outsourcing","white label","partner","supplier","provider"]) else [],
          "support_role_hits":[],
          "time_binding_hits":[],
          "project_based_fit":True if any(x in terms for x in ["freelance","partita iva","autonomo","autónomo","outsourcing","white label"]) else False,
          "semantic_score":78 if terms else 55,
          "raw_fit_score":78 if terms else 55,
          "booster_emails":public_emails,
          "decision_makers":route.get("decision_makers") or [],
          "supplier_routes":supplier_routes,
          "contactability_score":route.get("contactability_score"),
          "first_party_evidence_pages":route.get("evidence_pages") or [],
          "booster_render":item.get("render")
        })
    payload={"schema_version":"1.0","updated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"semantic_pass":rows}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"booster_seeds":len(rows)}))
if __name__=="__main__": raise SystemExit(main())
