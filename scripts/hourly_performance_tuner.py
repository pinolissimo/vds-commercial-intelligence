#!/usr/bin/env python3
"""Bounded hourly optimizer for VDS commercial discovery.

The governor never weakens dedup, truthful-fit, route, provider or legal/channel gates.
It only reallocates search/research capacity inside conservative bounds and emits a
transparent performance report for the Command Center.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"views/hourly-performance.json"
RUNTIME=ROOT/"config/hourly-optimization-runtime.json"

def load(rel, default):
    try:
        value=json.loads((ROOT/rel).read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else default
    except Exception:
        return default

def save(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def clamp(v,lo,hi): return max(lo,min(hi,v))

def main():
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    buyer=load("views/buyer-intent-priority.json",{})
    active=load("views/active-freelance-opportunities.json",{})
    eu=load("api/v1/eu-project-radar.json",{})
    health=load("api/v1/health.json",{})
    source=load("views/search-source-performance.json",{})
    today=load("api/v1/today.json",{})

    bsum=buyer.get("summary") or buyer.get("counts") or {}
    archetypes=buyer.get("archetypes") or bsum.get("archetypes") or {}
    agency=int(archetypes.get("AGENCY_EXTERNAL_CAPACITY") or 0)
    eu_ready=int((eu.get("summary") or {}).get("ready_contact") or 0)
    eu_qualified=int((eu.get("summary") or {}).get("qualified") or 0)

    opps=active.get("opportunities") or []
    ready=sum(1 for x in opps if str(x.get("status","")).startswith("READY"))
    active_count=len(opps)
    sent=int(today.get("first_contact_count") or 0)
    replies=(today.get("replies") or {})
    positive=int(replies.get("positive") or 0)

    # Base revenue strategy. Adjustments are intentionally bounded to avoid oscillation.
    allocation={"AGENCY_WHITE_LABEL":40,"EU_PROJECT":40,"DIRECT_BUYER_WEB_NEED":20}
    reasons=[]

    if agency < 6:
        allocation["AGENCY_WHITE_LABEL"] += 10
        allocation["EU_PROJECT"] -= 5
        allocation["DIRECT_BUYER_WEB_NEED"] -= 5
        reasons.append("AGENCY_PIPELINE_THIN")

    eu_degraded=(health.get("status")=="DEGRADED" and "CORDIS" in str(health.get("status_reason","")).upper())
    if eu_ready == 0 and eu_qualified < 5:
        allocation["EU_PROJECT"] -= 10
        allocation["AGENCY_WHITE_LABEL"] += 5
        allocation["DIRECT_BUYER_WEB_NEED"] += 5
        reasons.append("EU_CONTACTABLE_SUPPLY_LOW")
    if eu_degraded:
        allocation["EU_PROJECT"] -= 10
        allocation["AGENCY_WHITE_LABEL"] += 10
        reasons.append("EU_SOURCE_DEGRADED")

    if ready < 5 and active_count >= 20:
        allocation["AGENCY_WHITE_LABEL"] += 5
        allocation["DIRECT_BUYER_WEB_NEED"] += 5
        allocation["EU_PROJECT"] -= 10
        reasons.append("READY_CONVERSION_BOTTLENECK")

    # Clamp strategic floors/ceilings, normalize to 100.
    floors={"AGENCY_WHITE_LABEL":30,"EU_PROJECT":20,"DIRECT_BUYER_WEB_NEED":10}
    ceilings={"AGENCY_WHITE_LABEL":60,"EU_PROJECT":50,"DIRECT_BUYER_WEB_NEED":30}
    for k in allocation:
        allocation[k]=clamp(allocation[k],floors[k],ceilings[k])
    total=sum(allocation.values()) or 100
    normalized={k:round(v*100/total) for k,v in allocation.items()}
    drift=100-sum(normalized.values())
    normalized["AGENCY_WHITE_LABEL"]+=drift

    ranking=source.get("ranking") or []
    enabled_top=[
        {"source_id":r.get("source_id"),"quality":r.get("quality_score_0_100"),"multiplier":r.get("priority_multiplier")}
        for r in ranking[:8]
    ]

    report={
      "schema_version":"1.0",
      "updated_at":now,
      "mode":"BOUNDED_CONTINUOUS_IMPROVEMENT",
      "hourly_metrics":{
        "active_opportunities":active_count,
        "ready_opportunities":ready,
        "agency_external_capacity_signals":agency,
        "eu_qualified":eu_qualified,
        "eu_ready_contact":eu_ready,
        "first_contacts_today":sent,
        "positive_replies_today":positive
      },
      "allocation_pct":normalized,
      "adjustment_reasons":reasons or ["BASELINE_HEALTHY"],
      "source_top":enabled_top,
      "guardrails":{
        "dedup_gate":"IMMUTABLE",
        "truthful_fit_gate":"IMMUTABLE",
        "authoritative_route_gate":"IMMUTABLE",
        "provider_verification_gate":"IMMUTABLE",
        "follow_up_owner_approval":"IMMUTABLE",
        "max_hourly_lane_shift_pct":20
      }
    }
    runtime={
      "schema_version":"1.0","updated_at":now,
      "allocation_pct":normalized,
      "reason_codes":report["adjustment_reasons"],
      "rule":"Search capacity may self-adjust hourly; safety/contact gates never self-weaken."
    }
    save(OUT,report); save(RUNTIME,runtime)
    print(json.dumps({"updated_at":now,"allocation_pct":normalized,"reasons":report["adjustment_reasons"]}))
if __name__=="__main__": raise SystemExit(main())
