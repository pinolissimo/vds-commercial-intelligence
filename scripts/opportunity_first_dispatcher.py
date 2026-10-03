#!/usr/bin/env python3
# Visual Design Studio — 2026
"""Opportunity-first first-contact dispatcher.

Consumes only first-party verified contact routes matched to opportunity-first
commercial signals. FIRST_CONTACT only. Fail-closed on dedup ambiguity.
"""
from __future__ import annotations
import json, os, re, smtplib, ssl, time
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
OPP=ROOT/"views/opportunity-first-optimizer.json"
ROUTES=ROOT/"views/public-web-enriched-routes.json"
LEDGER=ROOT/"views/global-contact-ledger.json"
OUT=ROOT/"state/opportunity-first-dispatch-latest.json"
AUDIT_DIR=ROOT/"data/opportunity-first-dispatch-runs"

AGGREGATORS={
 "jobicy.com","arbeitnow.com","arbeitnow.co.uk","arbeitnow.ch","remoteok.com",
 "remotive.com","linkedin.com","indeed.com","upwork.com","jobs.ashbyhq.com"
}
PLACEHOLDERS=("example.com","company.com","your@email","test@","noreply@","no-reply@")

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def domain_of_url(v):
    try:return (urlparse(v or "").hostname or "").lower().removeprefix("www.")
    except Exception:return ""

def email_domain(v):
    return str(v or "").lower().rsplit("@",1)[-1] if "@" in str(v or "") else ""

def valid_email(e,d):
    e=str(e or "").strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",e): return False
    if any(x in e for x in PLACEHOLDERS): return False
    return email_domain(e)==d

def lang_for_domain(d):
    if d.endswith(".it"): return "it"
    if d.endswith(".es"): return "es"
    return "en"

def message_for(org,strategy,lang):
    site="https://www.visualdesignstudio.es/"
    if lang=="it":
        subject="Collaborazione tecnica web — Visual Design Studio"
        body=f"""Buongiorno {org},

sono Giuseppe Allocca, Visual Design Studio, professionista web con base a Barcellona.

Collaboro con agenzie e aziende come supporto tecnico esterno su progetti WordPress, frontend custom, performance/WPO, redesign, landing page e siti ad alta velocità. Il mio approccio è orientato a soluzioni leggere, performanti e facilmente integrabili nei workflow esistenti.

Un esempio diretto dell'architettura e delle performance: {site}

Se può essere utile avere una capacità tecnica esterna per picchi di lavoro o progetti specifici, posso inviare rapidamente alcuni esempi pertinenti.

Un saluto,
Giuseppe Allocca
Visual Design Studio
{site}
"""
    elif lang=="es":
        subject="Colaboración técnica web — Visual Design Studio"
        body=f"""Hola {org},

soy Giuseppe Allocca, de Visual Design Studio, profesional web con base en Barcelona.

Colaboro con agencias y empresas como apoyo técnico externo en proyectos WordPress, frontend a medida, performance/WPO, rediseños, landing pages y sitios de alto rendimiento. Trabajo con una arquitectura ligera y orientada a velocidad, calidad e integración sencilla con flujos existentes.

Ejemplo directo de arquitectura y rendimiento: {site}

Si os puede resultar útil contar con capacidad técnica externa para picos de trabajo o proyectos concretos, puedo enviar rápidamente algunos ejemplos relevantes.

Un saludo,
Giuseppe Allocca
Visual Design Studio
{site}
"""
    else:
        subject="External web development capacity — Visual Design Studio"
        body=f"""Hello {org},

I'm Giuseppe Allocca from Visual Design Studio, a web professional based in Barcelona.

I work with agencies and companies as external technical capacity for WordPress, custom frontend, performance/WPO, redesigns, landing pages and high-performance websites. My approach focuses on lightweight architecture, speed, quality and easy integration with existing delivery workflows.

A direct example of the architecture and performance: {site}

If external capacity could be useful for project peaks or specific web work, I can quickly share a few relevant examples.

Best regards,
Giuseppe Allocca
Visual Design Studio
{site}
"""
    return subject,body

def send_mail(host,port,user,password,from_addr,to_addr,subject,body,bcc=None):
    msg=EmailMessage()
    msg["From"]=from_addr
    msg["To"]=to_addr
    if bcc: msg["Bcc"]=bcc
    msg["Subject"]=subject
    msg.set_content(body)
    ctx=ssl.create_default_context()
    if int(port)==465:
        with smtplib.SMTP_SSL(host,int(port),context=ctx,timeout=20) as s:
            s.login(user,password); s.send_message(msg)
    else:
        with smtplib.SMTP(host,int(port),timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo(); s.login(user,password); s.send_message(msg)

def main():
    now=datetime.now(timezone.utc)
    stamp=now.replace(microsecond=0).isoformat().replace("+00:00","Z")
    opp=load(OPP,{"opportunities":[]})
    routes=load(ROUTES,{"items":[]})
    ledger=load(LEDGER,{})
    exact=set((ledger.get("exact_email_index") or {}).keys())
    domains=set((ledger.get("corporate_domain_index") or {}).keys())

    # Map only official/non-aggregator opportunity domains.
    by_domain={}
    for o in opp.get("opportunities") or []:
        if float(o.get("opportunity_first_score") or 0)<70: continue
        for u in (o.get("authoritative_apply_url"),o.get("opportunity_url")):
            d=domain_of_url(u)
            if not d or d in AGGREGATORS: continue
            by_domain.setdefault(d,[]).append(o)

    candidates=[]
    seen_domains=set()
    for r in routes.get("items") or []:
        d=str(r.get("domain") or "").lower().removeprefix("www.")
        if not d or d in AGGREGATORS or d in seen_domains: continue
        if r.get("state")!="CONTACTABLE_EVIDENCE": continue
        if int(r.get("contactability_score") or 0)<65: continue
        matches=by_domain.get(d) or []
        if not matches: continue
        best=max(matches,key=lambda x:float(x.get("opportunity_first_score") or 0))
        emails=[e for e in (r.get("public_emails") or []) if valid_email(e,d)]
        if not emails: continue
        emails=[e for e in emails if e not in exact]
        if d in domains or not emails: continue
        candidates.append({"organization":best.get("organization") or d,"domain":d,"email":emails[0],
                           "score":best.get("opportunity_first_score"),"strategy":best.get("message_strategy"),
                           "source_url":r.get("source_url"),"signal_key":best.get("signal_key")})
        seen_domains.add(d)

    candidates.sort(key=lambda x:float(x.get("score") or 0),reverse=True)
    max_batch=int(os.getenv("VDS_DISPATCH_MAX_BATCH","5"))
    dry_run=os.getenv("VDS_DISPATCH_DRY_RUN","0")=="1"
    required=["VDS_SMTP_HOST","VDS_SMTP_PORT","VDS_SMTP_USER","VDS_SMTP_PASSWORD","VDS_SMTP_FROM"]
    missing=[k for k in required if not os.getenv(k)]
    results=[]
    if missing and not dry_run:
        save(OUT,{"schema_version":"1.0","updated_at":stamp,"status":"BLOCKED_MISSING_SMTP","missing":missing,"candidate_count":len(candidates)})
        print(json.dumps({"status":"BLOCKED_MISSING_SMTP","missing":missing,"candidates":len(candidates)}))
        return 2

    host=os.getenv("VDS_SMTP_HOST");port=os.getenv("VDS_SMTP_PORT","587");user=os.getenv("VDS_SMTP_USER")
    password=os.getenv("VDS_SMTP_PASSWORD");from_addr=os.getenv("VDS_SMTP_FROM") or user
    bcc=os.getenv("VDS_OWNER_BCC")
    for c in candidates[:max_batch]:
        e=c["email"]; d=c["domain"]
        # Recheck in-memory immediately before provider call.
        if e in exact or d in domains:
            results.append({**c,"state":"BLOCKED_DUPLICATE_PRE_SEND"});continue
        subject,body=message_for(c["organization"],c.get("strategy"),lang_for_domain(d))
        if dry_run:
            results.append({**c,"state":"DRY_RUN_READY","subject":subject});continue
        try:
            send_mail(host,port,user,password,from_addr,e,subject,body,bcc)
            # Immediate local reservation/suppression prevents same-run duplicates.
            exact.add(e);domains.add(d)
            results.append({**c,"state":"SMTP_ACCEPTED","subject":subject,"sent_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")})
            time.sleep(1.0)
        except Exception as exc:
            results.append({**c,"state":"SEND_FAILED","error":f"{type(exc).__name__}: {exc}"[:500]})

    payload={"schema_version":"1.0","updated_at":stamp,"status":"COMPLETED","dry_run":dry_run,
             "candidate_count":len(candidates),"batch_limit":max_batch,
             "smtp_accepted":sum(1 for x in results if x.get("state")=="SMTP_ACCEPTED"),
             "blocked_duplicate":sum(1 for x in results if str(x.get("state","")).startswith("BLOCKED_DUPLICATE")),
             "failed":sum(1 for x in results if x.get("state")=="SEND_FAILED"),"results":results}
    save(OUT,payload)
    AUDIT_DIR.mkdir(parents=True,exist_ok=True)
    save(AUDIT_DIR/(stamp.replace(":","-")+".json"),payload)
    print(json.dumps({k:payload[k] for k in ("status","candidate_count","batch_limit","smtp_accepted","blocked_duplicate","failed")}))
    return 0

if __name__=="__main__": raise SystemExit(main())
