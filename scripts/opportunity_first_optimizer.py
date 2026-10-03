#!/usr/bin/env python3
# Visual Design Studio — 2026
import json, re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"config/opportunity-first-optimizer.json"
BUYER=ROOT/"views/buyer-intent-priority.json"
SEEDS=ROOT/"views/high-frequency-discovery-qualified-seeds.json"
COMPANIES=ROOT/"api/v1/companies.json"
SENT=ROOT/"views/global-sent-email-index.json"
SUCCESS=ROOT/"views/success-indicators.json"
OUT=ROOT/"views/opportunity-first-optimizer.json"
SECOND=ROOT/"views/second-chance-queue.json"
DMQ=ROOT/"views/decision-maker-enrichment-queue.json"
MSG=ROOT/"views/message-strategy.json"
LEARN=ROOT/"views/adaptive-commercial-learning.json"

def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return d
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def nowz():return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def blob(x):
    vals=[x.get("title"),x.get("organization"),x.get("location"),x.get("description"),x.get("snippet"),x.get("summary"),
          " ".join(x.get("buyer_intent_hits") or [])," ".join(x.get("project_delivery_hits") or []),
          " ".join(x.get("semantic_reasons") or [])," ".join(x.get("opportunity_context_hits") or []),
          " ".join(x.get("observable_need_hits") or [])]
    return " ".join(str(v or "") for v in vals).lower()
def hits(t,terms):return sorted({x for x in terms if x.lower() in t})
def customer_type(row,text):
    a=row.get("commercial_archetype")
    if a=="AGENCY_EXTERNAL_CAPACITY": return "WEB_DIGITAL_AGENCY"
    if a=="EU_DISSEMINATION_SPECIALIST": return "EU_PROJECT_RESEARCH_ORGANIZATION"
    if any(k in text for k in ["software house","saas","platform","tech company"]): return "SOFTWARE_HOUSE"
    if any(k in text for k in ["real estate","immobiliare","inmobiliaria","hotel","hospitality"]): return "REAL_ESTATE_HOSPITALITY"
    return "SME_DIRECT_BUYER"
def strategy(row,ctype,policy):
    a=row.get("commercial_archetype")
    if a in policy["message_strategy"]: return policy["message_strategy"][a]
    if ctype=="SOFTWARE_HOUSE": return policy["message_strategy"]["SOFTWARE_HOUSE"]
    if ctype=="REAL_ESTATE_HOSPITALITY": return policy["message_strategy"]["REAL_ESTATE_HOSPITALITY"]
    return policy["message_strategy"]["DEFAULT"]
def main():
    stamp=nowz(); policy=load(POLICY,{})
    buyer=load(BUYER,{"opportunities":[]}); seeds=load(SEEDS,{})
    companies=load(COMPANIES,{"companies":[]}); sent=load(SENT,{"messages":[]}); success=load(SUCCESS,{})
    company_by_name={str(x.get("organization") or "").lower():x for x in companies.get("companies",[])}
    rows=[]; second=[]; dmq=[]; strategies=[]
    for r in buyer.get("opportunities",[]):
        t=blob(r); high=hits(t,policy.get("timing_signals",{}).get("high",[])); med=hits(t,policy.get("timing_signals",{}).get("medium",[]))
        timing=min(25,len(high)*8+len(med)*3)
        multi=len(set((r.get("buyer_intent_hits") or [])+(r.get("project_delivery_hits") or [])))
        correlation=min(20,max(0,multi-1)*3)
        base=float(r.get("buyer_intent_score") or 0)
        combined=min(100,round(base+timing+correlation,1))
        ctype=customer_type(r,t); strat=strategy(r,ctype,policy)
        org=str(r.get("organization") or ""); comp=company_by_name.get(org.lower(),{})
        emails=comp.get("emails") or []; contacts=comp.get("contacts") or []
        has_dm=any((c.get("decision_influence") in {"HIGH","FINAL"} or any(role in str(c.get("role") or "").lower() for role in policy.get("decision_maker_roles",[]))) for c in contacts)
        item=dict(r); item.update({"timing_score":timing,"timing_signals":high+med,"correlation_score":correlation,"opportunity_first_score":combined,"customer_type":ctype,"message_strategy":strat,"known_emails":emails,"decision_maker_known":has_dm})
        rows.append(item)
        strategies.append({"signal_key":r.get("signal_key"),"organization":org,"customer_type":ctype,"strategy":strat,"score":combined})
        if not has_dm and combined>=55:
            dmq.append({"signal_key":r.get("signal_key"),"organization":org,"website":comp.get("website"),"domain":comp.get("domain"),"country":comp.get("country"),"region":comp.get("region"),"priority":combined,"target_roles":policy.get("decision_maker_roles",[])})
        reasons=[]
        if not emails: reasons.append("NO_PUBLIC_EMAIL")
        if not comp.get("region"): reasons.append("REGION_UNRESOLVED")
        if r.get("route_class")=="UNKNOWN": reasons.append("UNKNOWN_ROUTE")
        if r.get("decision_hint")=="VERIFY_PROJECT_SCOPE": reasons.append("PROJECT_SCOPE_NOT_VERIFIED")
        if reasons and combined>=40:
            second.append({"signal_key":r.get("signal_key"),"organization":org,"score":combined,"reasons":reasons,"retry_methods":["official contact/team/privacy pages","company LinkedIn/public profiles","alternate search query","supplier/partner pages","public registries/directories"],"do_not_send_until_hard_gates_pass":True})
    rows.sort(key=lambda x:x["opportunity_first_score"],reverse=True); second.sort(key=lambda x:x["score"],reverse=True); dmq.sort(key=lambda x:x["priority"],reverse=True)
    # Learning: empirical segment yield from provider-verified messages when available.
    by_stream=defaultdict(lambda:{"sent":0})
    for m in sent.get("messages",[]):
        by_stream[str(m.get("workstream") or "UNKNOWN")]["sent"]+=1
    learning={"schema_version":"1.0","updated_at":stamp,"mode":"OBSERVE_AND_REWEIGHT_WITHOUT_BYPASSING_GATES","provider_verified_volume_by_stream":dict(by_stream),"success_indicators":success,"rule":"Increase search/message allocation only from observed downstream outcomes; never weaken dedup or contact validity gates."}
    save(OUT,{"schema_version":"1.0","updated_at":stamp,"count":len(rows),"high_priority_count":sum(1 for x in rows if x["opportunity_first_score"]>=70),"opportunities":rows})
    save(SECOND,{"schema_version":"1.0","updated_at":stamp,"count":len(second),"queue":second})
    save(DMQ,{"schema_version":"1.0","updated_at":stamp,"count":len(dmq),"queue":dmq})
    save(MSG,{"schema_version":"1.0","updated_at":stamp,"count":len(strategies),"strategies":strategies})
    save(LEARN,learning)
    print(json.dumps({"ranked":len(rows),"high_priority":sum(1 for x in rows if x["opportunity_first_score"]>=70),"second_chance":len(second),"decision_maker_enrichment":len(dmq)}))
if __name__=="__main__": main()
