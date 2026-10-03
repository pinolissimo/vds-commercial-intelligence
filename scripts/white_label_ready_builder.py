#!/usr/bin/env python3
# Visual Design Studio — 2026
from __future__ import annotations
import json,re
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
ROUTES=ROOT/"views/public-web-enriched-routes.json"
BOOST=ROOT/"views/public-web-booster.json"
LEDGER=ROOT/"views/global-contact-ledger.json"
OUT=ROOT/"views/white-label-ready-to-send.json"
PLACEHOLDERS=("example.com","company.com","your@email","test@","noreply@","no-reply@")
AGENCY_TERMS=("white label","white-label","outsourcing","partner","wordpress","woocommerce","web development","sviluppo web","desarrollo web","frontend","ecommerce","agency","agenzia","agencia")

def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d
def domain_of_email(e):
    return str(e or "").lower().rsplit("@",1)[-1] if "@" in str(e or "") else ""
def valid(e,d):
    e=str(e or "").strip().lower()
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",e)) and domain_of_email(e)==d and not any(x in e for x in PLACEHOLDERS)
def main():
    routes=load(ROUTES,{"items":[]}); boost=load(BOOST,{"signals":[]}); ledger=load(LEDGER,{})
    exact=set((ledger.get("exact_email_index") or {}).keys())
    domains=set((ledger.get("corporate_domain_index") or {}).keys())
    signal_by_domain={}
    for s in boost.get("signals") or []:
        d=str(s.get("domain") or "").lower().removeprefix("www.")
        text=(" ".join(s.get("matched_terms") or [])+" "+str(s.get("text_sample") or "")).lower()
        score=sum(1 for t in AGENCY_TERMS if t in text)
        if score:
            cur=signal_by_domain.get(d)
            if not cur or score>cur["agency_score"]: signal_by_domain[d]={"agency_score":score,"signal":s}
    ready=[]; seen=set()

    # Fast lane: same-domain public email + agency/web signal on the same
    # first-party page is sufficient for READY_TO_SEND preparation.
    for d, pack in signal_by_domain.items():
        if not d or d in seen or d in domains: continue
        sig=pack["signal"]
        emails=[str(e).lower() for e in (sig.get("emails") or []) if valid(e,d) and str(e).lower() not in exact]
        if not emails: continue
        if pack["agency_score"] < 2: continue
        matched=[str(x).lower() for x in (sig.get("matched_terms") or [])]
        strong=any(x in matched for x in ("white label","white-label","outsourcing","wordpress","woocommerce","web development","sviluppo web","desarrollo web"))
        if not strong and not sig.get("route_hint"): continue
        priority=min(100,55+pack["agency_score"]*7+(10 if sig.get("route_hint") else 0))
        ready.append({
          "organization":d,
          "domain":d,
          "email":emails[0],
          "priority":priority,
          "agency_signal_score":pack["agency_score"],
          "source_url":sig.get("url"),
          "supplier_routes":[sig.get("url")] if sig.get("route_hint") else [],
          "evidence_pages":[sig.get("url")] if sig.get("url") else [],
          "state":"READY_TO_SEND",
          "dedup_verified":True,
          "evidence_mode":"FIRST_PARTY_SAME_PAGE_SIGNAL_AND_EMAIL",
          "message_strategy":"TECHNICAL_WHITE_LABEL_PARTNER"
        }); seen.add(d)

    # Deep lane: richer route/decision-maker evidence from the dedicated enricher.
    for r in routes.get("items") or []:
        d=str(r.get("domain") or "").lower().removeprefix("www.")
        if not d or d in seen or d in domains: continue
        sig=signal_by_domain.get(d)
        if not sig: continue
        emails=[str(e).lower() for e in (r.get("public_emails") or []) if valid(e,d) and str(e).lower() not in exact]
        if not emails: continue
        if int(r.get("contactability_score") or 0)<55: continue
        routes_ok=r.get("supplier_routes") or []
        source=r.get("source_url")
        priority=min(100,int(r.get("contactability_score") or 0)+sig["agency_score"]*4)
        ready.append({
          "organization":d,
          "domain":d,
          "email":emails[0],
          "priority":priority,
          "agency_signal_score":sig["agency_score"],
          "source_url":source,
          "supplier_routes":routes_ok[:5],
          "evidence_pages":(r.get("evidence_pages") or [])[:8],
          "state":"READY_TO_SEND",
          "dedup_verified":True,
          "message_strategy":"TECHNICAL_WHITE_LABEL_PARTNER"
        }); seen.add(d)
    ready.sort(key=lambda x:x["priority"],reverse=True)
    payload={
      "schema_version":"1.0",
      "updated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
      "count":len(ready),
      "target":100,
      "status":"TARGET_REACHED" if len(ready)>=100 else "BUILDING",
      "items":ready[:300]
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ready_to_send":len(ready),"target":100,"status":payload["status"]}))
if __name__=="__main__": raise SystemExit(main())
