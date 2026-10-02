#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"api/v1/geography.json"

CITY={
 ("Spain","Cataluña","Barcelona"):(41.3874,2.1686),
 ("Spain","Aragón","Zaragoza"):(41.6488,-0.8891),
 ("Spain","Comunitat Valenciana","Alicante"):(38.3452,-0.4810),
 ("Spain","Comunitat Valenciana","Castellón"):(39.9864,-0.0513),
 ("Spain","Castilla y León","Valladolid"):(41.6523,-4.7245),
 ("Spain","Madrid","Madrid"):(40.4168,-3.7038),
 ("Spain","Andalucía","Sevilla"):(37.3891,-5.9845),
 ("Spain","Andalucía","Málaga"):(36.7213,-4.4214),
 ("Spain","Castilla y León","Zamora"):(41.5033,-5.7446),
 ("Spain","País Vasco","Bizkaia"):(43.2630,-2.9350),
 ("Spain","País Vasco","Bilbao"):(43.2630,-2.9350),
 ("Spain","Galicia","Lugo"):(43.0121,-7.5559),
 ("Spain","Murcia","Murcia"):(37.9922,-1.1307),
 ("Spain","Asturias","Oviedo"):(43.3619,-5.8494),
 ("Spain","Cantabria","Santander"):(43.4623,-3.8099),
 ("Italy","Lazio","Roma"):(41.9028,12.4964),
 ("Italy","Lazio","Frosinone"):(41.6396,13.3412),
 ("Italy","Lombardia","Milano"):(45.4642,9.1900),
 ("Italy","Piemonte","Torino"):(45.0703,7.6869),
 ("Italy","Veneto","Venezia"):(45.4408,12.3155),
 ("Italy","Emilia-Romagna","Bologna"):(44.4949,11.3426),
 ("Italy","Emilia-Romagna","Piacenza"):(45.0526,9.6930),
 ("Italy","Puglia","Bari"):(41.1171,16.8719),
 ("Italy","Calabria","Reggio Calabria"):(38.1112,15.6473),
 ("Italy","Toscana","Firenze"):(43.7696,11.2558),
 ("Italy","Campania","Napoli"):(40.8518,14.2681),
 ("Italy","Campania","Salerno"):(40.6824,14.7681),
 ("Italy","Liguria","Genova"):(44.4056,8.9463),
 ("Italy","Sicilia","Palermo"):(38.1157,13.3615),
 ("Italy","Basilicata","Potenza"):(40.6404,15.8056),
 ("Italy","Trentino-Alto Adige","Trento"):(46.0748,11.1217),

 ("Spain","Comunidad de Madrid","Madrid"):(40.4168,-3.7038),
 ("Spain","Comunitat Valenciana","Valencia"):(39.4699,-0.3763),
 ("Spain","Cataluña","Tarragona"):(41.1189,1.2445),
 ("Spain","Galicia","A Coruña"):(43.3623,-8.4115),
 ("Spain","Castilla y León","León"):(42.5987,-5.5671),
 ("Spain","Castilla y León","Segovia"):(40.9429,-4.1088),
 ("Spain","Castilla y León","Burgos"):(42.3439,-3.6969),
 ("Spain","Galicia","Pontevedra"):(42.4310,-8.6444),
 ("Spain","Galicia","Ourense"):(42.3358,-7.8639),
 ("Italy","Puglia","Foggia"):(41.4622,15.5446),
 ("Italy","Piemonte","Novara"):(45.4450,8.6222),
 ("Italy","Toscana","Livorno"):(43.5485,10.3106),
 ("Italy","Puglia","Taranto"):(40.4644,17.2470),
 ("Italy","Emilia-Romagna","Modena"):(44.6471,10.9252),
 ("Italy","Lazio","Latina"):(41.4676,12.9037),
 ("Italy","Puglia","Lecce"):(40.3515,18.1750),
 ("Italy","Lombardia","Cremona"):(45.1332,10.0227),
 ("Italy","Puglia","Barletta-Andria-Trani"):(41.2275,16.2951),
 ("Italy","Sicilia","Trapani"):(38.0176,12.5372),
 ("Italy","Calabria","Crotone"):(39.0808,17.1271),
 ("Italy","Calabria","Vibo Valentia"):(38.6762,16.1016),
 ("Italy","Veneto","Treviso"):(45.6669,12.2430),
 ("Italy","Lombardia","Varese"):(45.8206,8.8251),
 ("Italy","Veneto","Padova"):(45.4064,11.8768),
 ("Italy","Veneto","Verona"):(45.4384,10.9916),
 ("Italy","Lombardia","Bergamo"):(45.6983,9.6773),
 ("Italy","Lombardia","Brescia"):(45.5416,10.2118),
}
CODE={
 "ES-CAT-BCN":("Spain","Cataluña","Barcelona"),
 "ES-ARA-ZGZ":("Spain","Aragón","Zaragoza"),
 "ES-CV-VLC":("Spain","Comunitat Valenciana","Valencia"),
 "ES-CV-ALI":("Spain","Comunitat Valenciana","Alicante"),
 "ES-CYL-VA":("Spain","Castilla y León","Valladolid"),
 "ES-MAD-MAD":("Spain","Madrid","Madrid"),
 "ES-MD":("Spain","Madrid","Madrid"),
 "ES-AND":("Spain","Andalucía","Sevilla"),
 "ES-GAL-LU":("Spain","Galicia","Lugo"),
 "ES-MUR":("Spain","Murcia","Murcia"),
 "ES-AST":("Spain","Asturias","Oviedo"),
 "ES-CAN":("Spain","Cantabria","Santander"),
 "IT-LAZ-RM":("Italy","Lazio","Roma"),
 "IT-LAZ":("Italy","Lazio","Roma"),
 "IT-LOM-MI":("Italy","Lombardia","Milano"),
 "IT-PIE-TO":("Italy","Piemonte","Torino"),
 "IT-VEN":("Italy","Veneto","Venezia"),
 "IT-EMR":("Italy","Emilia-Romagna","Bologna"),
 "IT-PUG-BA":("Italy","Puglia","Bari"),
 "IT-CAL":("Italy","Calabria","Reggio Calabria"),
 "IT-TOS-FI":("Italy","Toscana","Firenze"),
 "IT-CAM-NA":("Italy","Campania","Napoli"),
 "IT-CAM-SA":("Italy","Campania","Salerno"),
 "IT-LIG-GE":("Italy","Liguria","Genova"),
 "IT-SIC":("Italy","Sicilia","Palermo"),
 "IT-BAS-PZ":("Italy","Basilicata","Potenza"),
 "IT-TAA-TN":("Italy","Trentino-Alto Adige","Trento"),
}
CITY[("Spain","Comunitat Valenciana","Valencia")]=(39.4699,-0.3763)

def load(rel,default):
    try:return json.loads((ROOT/rel).read_text(encoding="utf-8"))
    except Exception:return default

def coords(country,region,place,allow_region_fallback=False):
    if (country,region,place) in CITY:return CITY[(country,region,place)]
    if allow_region_fallback:
        for (c,r,p),xy in CITY.items():
            if c==country and r==region:return xy
    return None

def infer_company_geo(company):
    if company.get("country") and company.get("region") and company.get("territory"):
        return (company["country"],company["region"],company["territory"])
    cid=(company.get("company_id") or "").upper()
    for code,val in sorted(CODE.items(),key=lambda x:len(x[0]),reverse=True):
        if code in cid:return val
    return None

def classify_stream(company):
    types={str(x.get("type","")).upper() for x in company.get("opportunities",[])}
    subjects=" ".join([company.get("last_subject") or ""]+[(x.get("title") or "") for x in company.get("opportunities",[])]).lower()
    if any(x in types for x in {"WHITE_LABEL","OUTSOURCING","STRUCTURAL_PARTNERSHIP","ACTIVE_FREELANCE_COLLABORATION","RECURRING_FREELANCE_COLLABORATION"}):
        return "AGENCY_WHITE_LABEL"
    if any(k in subjects for k in ("horizon","prima","dissemination","eu project","progetto europeo")):
        return "EU_PROJECT"
    if any(k in subjects for k in ("performance","wordpress","woocommerce","redesign","website","sito")):
        return "DIRECT_BUYER_WEB_NEED"
    if "ACTIVE_JOB" in types:return "JOB_APPLICATION"
    return "OTHER"

def main():
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    companies=load("api/v1/companies.json",{}).get("companies",[])
    territory=load("views/territory-yield-radar.json",{})
    mission_plan=load("views/search-mission-plan.json",{})
    missions=mission_plan.get("missions",[])
    execution=load("state/mission-execution-heartbeat.json",{})
    execution_results=load("views/territorial-public-search-results.json",{})
    points=[]
    for c in companies:
        if not c.get("contacted"):continue
        g=infer_company_geo(c)
        if not g:continue
        xy=coords(*g)
        if not xy:continue
        points.append({
          "kind":"CONTACTED","lat":xy[0],"lon":xy[1],
          "country":g[0],"region":g[1],"locality":g[2],
          "organization":c.get("organization"),"domain":c.get("domain"),
          "last_outbound_at":c.get("last_outbound_at"),"stream":classify_stream(c),
          "company_key":c.get("key")
        })
    territories=[]
    raw_areas=territory.get("areas") or territory.get("ranking") or []
    if isinstance(raw_areas,dict):
        area_rows=[]
        for key,val in raw_areas.items():
            if not isinstance(val,dict): continue
            row=dict(val)
            parts=str(key).split("|")
            if len(parts)>=3:
                row.setdefault("country",parts[0]); row.setdefault("region",parts[1]); row.setdefault("province",parts[2])
            area_rows.append(row)
    else:
        area_rows=[x for x in raw_areas if isinstance(x,dict)]
    for a in area_rows:
        country=a.get("country");region=a.get("region");place=a.get("province") or a.get("territory")
        xy=coords(country,region,place) if country and region and place else None
        if xy:
            territories.append({"country":country,"region":region,"locality":place,"lat":xy[0],"lon":xy[1],"mode":a.get("mode"),"score":a.get("score"),"metrics":a.get("metrics") or {}})
    scans=[]
    for i,m in enumerate(missions[:30]):
        xy=coords(m.get("country"),m.get("region"),m.get("province"))
        if not xy:continue
        scans.append({"order":i+1,"lat":xy[0],"lon":xy[1],"country":m.get("country"),"region":m.get("region"),"locality":m.get("province"),"segment":m.get("segment"),"query":m.get("query"),"mode":m.get("territory_mode"),"score":m.get("territory_score")})
    streams={}
    for c in companies:
        s=classify_stream(c); d=streams.setdefault(s,{"indexed":0,"contacted":0,"latest_contact":None})
        d["indexed"]+=1
        if c.get("contacted"):
            d["contacted"]+=1
            if c.get("last_outbound_at") and (not d["latest_contact"] or c["last_outbound_at"]>d["latest_contact"]):d["latest_contact"]=c["last_outbound_at"]
    stream_meta={
      "AGENCY_WHITE_LABEL":{"label":"Agenzie / white-label","priority":"VERY_HIGH","objective":"Capacità esterna, overflow, freelance, partner"},
      "EU_PROJECT":{"label":"Progetti UE","priority":"HIGH","objective":"Siti e dissemination per nuovi progetti"},
      "DIRECT_BUYER_WEB_NEED":{"label":"Buyer web diretti","priority":"HIGH","objective":"Redesign, WordPress, performance, ecommerce"},
      "JOB_APPLICATION":{"label":"Job / candidature","priority":"MEDIUM","objective":"Ruoli compatibili con proposta freelance"},
      "OTHER":{"label":"Altri segnali","priority":"LOW","objective":"Esplorazione e classificazione"}
    }
    stream_rows=[]
    for key,meta in stream_meta.items():
        d=streams.get(key,{"indexed":0,"contacted":0,"latest_contact":None})
        stream_rows.append({"stream":key,**meta,**d})
    actual_focus=None
    if execution.get("locality") and execution.get("state") in {"MISSION_STARTED","MISSION_COMPLETED","MISSION_FAILED","RUN_COMPLETED"}:
        xy=coords(execution.get("country"),execution.get("region"),execution.get("locality"))
        if xy:
            actual_focus={
              "lat":xy[0],"lon":xy[1],"country":execution.get("country"),"region":execution.get("region"),
              "locality":execution.get("locality"),"segment":execution.get("segment"),"query":execution.get("query"),
              "mission_id":execution.get("mission_id"),"state":execution.get("state"),"provider":execution.get("provider"),
              "updated_at":execution.get("updated_at"),"result_count":execution.get("result_count"),
              "execution_is_real":bool(execution.get("execution_is_real"))
            }
    payload={"schema_version":"1.2","generated_at":now,"plan_updated_at":mission_plan.get("updated_at"),"cycle_seconds":300,
      "contacted_points":points,"territories":territories,"scan_path":scans,
      "current_focus":actual_focus or (scans[0] if scans else None),
      "actual_execution_focus":actual_focus,
      "execution_summary":{
        "heartbeat_state":execution.get("state"),"heartbeat_updated_at":execution.get("updated_at"),
        "provider":execution.get("provider"),"execution_is_real":execution.get("execution_is_real",False),
        "last_run_id":execution_results.get("run_id"),"missions_attempted":execution_results.get("missions_attempted"),
        "missions_completed":execution_results.get("missions_completed"),"missions_failed":execution_results.get("missions_failed"),
        "result_count":execution_results.get("result_count")
      },
      "commercial_streams":stream_rows,
      "summary":{"mapped_contacted":len(points),"mapped_territories":len(territories),"scan_points":len(scans)}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload["summary"]))
if __name__=="__main__":raise SystemExit(main())
