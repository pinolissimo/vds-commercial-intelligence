#!/usr/bin/env python3
"""Execute a bounded set of territorial search missions with truthful live telemetry.

Uses DDGS (open-source client) without proxy rotation, stealth, CAPTCHA bypass or
login automation. Search results are discovery-only and require first-party
verification before any commercial action.
"""
from __future__ import annotations
import json,time,traceback
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from ddgs import DDGS

ROOT=Path(__file__).resolve().parents[1]
MISSIONS=ROOT/"views/multi-engine-search-missions.json"
HEARTBEAT=ROOT/"state/mission-execution-heartbeat.json"
OUT=ROOT/"views/territorial-public-search-results.json"
CURSOR=ROOT/"state/territorial-executor-cursor.json"

MAX_MISSIONS=8
MAX_RESULTS=8
DELAY_SECONDS=2.0

def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def load(path,default):
    try:
        v=json.loads(path.read_text(encoding="utf-8"))
        return v if isinstance(v,dict) else default
    except Exception:
        return default

def save(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def write_hb(**kw):
    payload={
      "schema_version":"1.0",
      "updated_at":now(),
      "executor":"territorial_mission_executor",
      "provider":"duckduckgo_via_ddgs",
      "execution_is_real":True,
      "search_results_are_discovery_only":True,
      "anti_evasion":"NO_PROXY_NO_STEALTH_NO_CAPTCHA_BYPASS",
      **kw
    }
    save(HEARTBEAT,payload)

def domain(url):
    try:return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:return ""

def main():
    src=load(MISSIONS,{})
    missions=src.get("missions") or []
    cursor=load(CURSOR,{})
    start=int(cursor.get("next_index") or 0) % max(1,len(missions))
    selected=[missions[(start+i)%len(missions)] for i in range(min(MAX_MISSIONS,len(missions)))] if missions else []
    run_id=f"territorial-{int(time.time())}"
    results=[]
    write_hb(state="RUN_STARTED",run_id=run_id,total_missions=len(selected),completed_missions=0)
    ddgs=DDGS()
    for idx,m in enumerate(selected,1):
        variants=m.get("search_variants") or []
        chosen=next((v for v in variants if v.get("variant") in {"official_site","eu_official","base_precision"}),variants[0] if variants else None)
        if not chosen: continue
        query=chosen.get("query") or ""
        hb_base={
          "run_id":run_id,"mission_id":m.get("mission_id"),"mission_index":idx,
          "total_missions":len(selected),"country":m.get("country"),"region":m.get("region"),
          "locality":m.get("province"),"segment":m.get("segment"),
          "query":query,"variant":chosen.get("variant")
        }
        write_hb(state="MISSION_STARTED",completed_missions=idx-1,**hb_base)
        started=time.time()
        try:
            found=list(ddgs.text(query,max_results=MAX_RESULTS,backend="auto"))
            clean=[]
            for x in found:
                href=x.get("href") or x.get("url") or ""
                clean.append({
                  "title":x.get("title") or "",
                  "url":href,
                  "domain":domain(href),
                  "body":x.get("body") or x.get("description") or ""
                })
            elapsed=round(time.time()-started,2)
            results.append({**hb_base,"state":"COMPLETED","elapsed_seconds":elapsed,"result_count":len(clean),"results":clean})
            write_hb(state="MISSION_COMPLETED",completed_missions=idx,result_count=len(clean),elapsed_seconds=elapsed,**hb_base)
        except Exception as exc:
            elapsed=round(time.time()-started,2)
            results.append({**hb_base,"state":"FAILED","elapsed_seconds":elapsed,"result_count":0,"error":f"{type(exc).__name__}: {exc}"[:500]})
            write_hb(state="MISSION_FAILED",completed_missions=idx,error=f"{type(exc).__name__}: {exc}"[:500],elapsed_seconds=elapsed,**hb_base)
        time.sleep(DELAY_SECONDS)
    next_index=(start+len(selected))%max(1,len(missions)) if missions else 0
    save(CURSOR,{"schema_version":"1.0","updated_at":now(),"next_index":next_index,"mission_count":len(missions),"last_run_id":run_id})
    last=results[-1] if results else {}
    payload={
      "schema_version":"1.1","updated_at":now(),"run_id":run_id,
      "cursor_start_index":start,"cursor_next_index":next_index,
      "source_plan_updated_at":src.get("source_plan_updated_at"),
      "provider":"duckduckgo_via_ddgs","missions_attempted":len(selected),
      "missions_completed":sum(1 for x in results if x.get("state")=="COMPLETED"),
      "missions_failed":sum(1 for x in results if x.get("state")=="FAILED"),
      "result_count":sum(int(x.get("result_count") or 0) for x in results),
      "policy":"DISCOVERY_ONLY_FIRST_PARTY_VERIFICATION_REQUIRED",
      "missions":results
    }
    save(OUT,payload)
    write_hb(
      state="RUN_COMPLETED",run_id=run_id,total_missions=len(selected),
      completed_missions=payload["missions_completed"],result_count=payload["result_count"],
      mission_id=last.get("mission_id"),country=last.get("country"),region=last.get("region"),
      locality=last.get("locality"),segment=last.get("segment"),query=last.get("query"),
      variant=last.get("variant"),last_mission_state=last.get("state"),
      cursor_next_index=next_index
    )
    print(json.dumps({k:payload[k] for k in ("run_id","missions_attempted","missions_completed","missions_failed","result_count")}))
if __name__=="__main__":
    raise SystemExit(main())
