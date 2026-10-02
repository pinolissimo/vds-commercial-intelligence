#!/usr/bin/env python3
"""Parallel territorial mission executor with truthful per-worker telemetry.

Six bounded workers execute independent search missions concurrently. Results are
discovery-only and must pass first-party verification and global dedup before any
commercial action. No proxy rotation, stealth, CAPTCHA bypass or login automation.
"""
from __future__ import annotations
import json,time,threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from ddgs import DDGS

ROOT=Path(__file__).resolve().parents[1]
MISSIONS=ROOT/"views/multi-engine-search-missions.json"
LEGACY_HEARTBEAT=ROOT/"state/mission-execution-heartbeat.json"
HEARTBEATS=ROOT/"state/mission-execution-heartbeats.json"
OUT=ROOT/"views/territorial-public-search-results.json"
CURSOR=ROOT/"state/territorial-executor-cursor.json"

WORKERS=6
MISSIONS_PER_RUN=18
MAX_RESULTS=6
FETCH_RESULTS=12
DELAY_SECONDS=0.35

_LOCK=threading.Lock()
_WORKER_STATE={}

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

def domain(url):
    try:return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:return ""

def _write_telemetry(run_id,total_missions):
    with _LOCK:
        workers=[_WORKER_STATE[k] for k in sorted(_WORKER_STATE)]
        payload={
          "schema_version":"2.0","updated_at":now(),"run_id":run_id,
          "executor":"territorial_parallel_executor","provider":"ddgs_multi_engine",
          "execution_is_real":True,"parallel":True,"worker_count":WORKERS,
          "total_missions":total_missions,
          "active_workers":sum(1 for w in workers if w.get("state")=="MISSION_STARTED"),
          "completed_workers":sum(1 for w in workers if w.get("state") in {"MISSION_COMPLETED","MISSION_FAILED","IDLE"}),
          "search_results_are_discovery_only":True,
          "anti_evasion":"NO_PROXY_NO_STEALTH_NO_CAPTCHA_BYPASS",
          "workers":workers
        }
        save(HEARTBEATS,payload)
        if workers:
            latest=max(workers,key=lambda x:x.get("updated_at") or "")
            legacy={"schema_version":"2.0","updated_at":payload["updated_at"],
              "executor":"territorial_parallel_executor","provider":"ddgs_multi_engine",
              "execution_is_real":True,"parallel":True,"worker_count":WORKERS,
              "run_id":run_id,"total_missions":total_missions,**{k:v for k,v in latest.items() if k not in {"worker_id"}}}
            save(LEGACY_HEARTBEAT,legacy)

def update_worker(worker_id,run_id,total_missions,**kw):
    with _LOCK:
        current=dict(_WORKER_STATE.get(worker_id,{}))
        current.update({"worker_id":worker_id,"updated_at":now(),**kw})
        _WORKER_STATE[worker_id]=current
    _write_telemetry(run_id,total_missions)

def choose_variant(m):
    variants=m.get("search_variants") or []
    return next((v for v in variants if v.get("variant") in {"official_site","eu_official","base_precision"}),variants[0] if variants else None)

def execute_mission(worker_id,m,run_id,total_missions):
    chosen=choose_variant(m)
    if not chosen:
        return None
    query=chosen.get("query") or ""
    base={
      "mission_id":m.get("mission_id"),"country":m.get("country"),"region":m.get("region"),
      "locality":m.get("province"),"segment":m.get("segment"),
      "query":query,"variant":chosen.get("variant")
    }
    update_worker(worker_id,run_id,total_missions,state="MISSION_STARTED",**base)
    started=time.time()
    try:
        region="es-es" if m.get("country")=="Spain" else "it-it" if m.get("country")=="Italy" else "us-en"
        # Rotate backend pairs by worker to diversify failure modes.
        pairs=[("brave","bing"),("google","duckduckgo"),("bing","brave"),("duckduckgo","google")]
        selected=pairs[(worker_id-1)%len(pairs)]
        clean=[]; backend_used=None; errors=[]
        ddgs=DDGS(timeout=4)
        for backend in selected:
            try:
                found=list(ddgs.text(query,max_results=FETCH_RESULTS,backend=backend,region=region))
            except Exception as exc:
                errors.append(f"{backend}:{type(exc).__name__}")
                continue
            for x in found:
                if not isinstance(x,dict): continue
                href=x.get("href") or x.get("url") or x.get("link") or ""
                if not isinstance(href,str) or not href.startswith(("http://","https://")): continue
                h=domain(href)
                if not h or h in {"bing.com","google.com","brave.com","duckduckgo.com","yahoo.com"}: continue
                clean.append({"title":x.get("title") or x.get("heading") or "","url":href,"domain":h,
                              "body":x.get("body") or x.get("description") or x.get("snippet") or ""})
                if len(clean)>=MAX_RESULTS: break
            if clean:
                backend_used=backend
                break
        if not clean:
            raise RuntimeError("No usable URL results; "+",".join(errors))
        elapsed=round(time.time()-started,2)
        result={**base,"worker_id":worker_id,"state":"COMPLETED","elapsed_seconds":elapsed,
                "result_count":len(clean),"backend_used":backend_used,"results":clean}
        update_worker(worker_id,run_id,total_missions,state="MISSION_COMPLETED",backend_used=backend_used,
                      result_count=len(clean),elapsed_seconds=elapsed,**base)
        return result
    except Exception as exc:
        elapsed=round(time.time()-started,2)
        result={**base,"worker_id":worker_id,"state":"FAILED","elapsed_seconds":elapsed,
                "result_count":0,"error":f"{type(exc).__name__}: {exc}"[:500]}
        update_worker(worker_id,run_id,total_missions,state="MISSION_FAILED",result_count=0,
                      elapsed_seconds=elapsed,error=result["error"],**base)
        return result
    finally:
        time.sleep(DELAY_SECONDS)

def execute_worker(worker_id,missions,run_id,total_missions):
    out=[]
    for m in missions:
        item=execute_mission(worker_id,m,run_id,total_missions)
        if item: out.append(item)
    update_worker(worker_id,run_id,total_missions,state="IDLE")
    return out

def main():
    src=load(MISSIONS,{})
    missions=src.get("missions") or []
    cursor=load(CURSOR,{})
    start=int(cursor.get("next_index") or 0)%max(1,len(missions))
    take=min(MISSIONS_PER_RUN,len(missions))
    selected=[missions[(start+i)%len(missions)] for i in range(take)] if missions else []
    run_id=f"territorial-par-{int(time.time())}"

    for wid in range(1,WORKERS+1):
        _WORKER_STATE[wid]={"worker_id":wid,"state":"IDLE","updated_at":now()}
    _write_telemetry(run_id,len(selected))

    shards=[[] for _ in range(WORKERS)]
    for i,m in enumerate(selected):
        shards[i%WORKERS].append(m)

    results=[]
    with ThreadPoolExecutor(max_workers=WORKERS,thread_name_prefix="vds-search") as pool:
        future_map={
          pool.submit(execute_worker,wid+1,shards[wid],run_id,len(selected)):wid+1
          for wid in range(WORKERS) if shards[wid]
        }
        for fut in as_completed(future_map):
            wid=future_map[fut]
            try:
                results.extend(fut.result())
            except Exception as exc:
                results.append({"worker_id":wid,"state":"FAILED","result_count":0,
                                "error":f"WorkerCrash:{type(exc).__name__}:{exc}"[:500]})

    # Canonical result merge: one organic URL record per domain+URL, independent of worker.
    merged={}
    for mission in results:
        unique=[]
        for x in mission.get("results") or []:
            key=(x.get("domain"),x.get("url"))
            if not key[0] or not key[1] or key in merged: continue
            merged[key]=True
            unique.append(x)
        mission["results"]=unique
        mission["result_count"]=len(unique)

    results.sort(key=lambda x:(x.get("worker_id",99),x.get("mission_id") or ""))
    next_index=(start+len(selected))%max(1,len(missions)) if missions else 0
    save(CURSOR,{"schema_version":"2.0","updated_at":now(),"next_index":next_index,
                 "mission_count":len(missions),"last_run_id":run_id,"worker_count":WORKERS})
    payload={
      "schema_version":"2.0","updated_at":now(),"run_id":run_id,
      "parallel":True,"worker_count":WORKERS,
      "cursor_start_index":start,"cursor_next_index":next_index,
      "source_plan_updated_at":src.get("source_plan_updated_at"),
      "provider":"ddgs_multi_engine","missions_attempted":len(selected),
      "missions_completed":sum(1 for x in results if x.get("state")=="COMPLETED"),
      "missions_failed":sum(1 for x in results if x.get("state")=="FAILED"),
      "result_count":sum(int(x.get("result_count") or 0) for x in results),
      "unique_domains":len({x.get("domain") for m in results for x in (m.get("results") or []) if x.get("domain")}),
      "policy":"PARALLEL_DISCOVERY_ONLY_FIRST_PARTY_VERIFICATION_REQUIRED",
      "missions":results
    }
    save(OUT,payload)
    print(json.dumps({k:payload[k] for k in ("run_id","worker_count","missions_attempted","missions_completed","missions_failed","result_count","unique_domains")}))
if __name__=="__main__":
    raise SystemExit(main())
