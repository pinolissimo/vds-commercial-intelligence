#!/usr/bin/env python3
# Visual Design Studio — 2026
"""Bridge qualified commercial routes into the autonomous sender queue.

FIRST_CONTACT policy:
- qualified first-party commercial routes may be auto-approved;
- global email/domain dedup remains fail-closed;
- only FIRST_CONTACT records owned by this bridge are auto-promoted;
- follow-ups/replies remain outside this automatic approval path.
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
READY=ROOT/"views/white-label-ready-to-send.json"
QUEUE=ROOT/"outreach/autonomous-send-queue.jsonl"
LEDGER=ROOT/"views/global-contact-ledger.json"
SITE="https://www.visualdesignstudio.es/"
AUTO_BASIS="AUTONOMOUS_FIRST_CONTACT"
AUTO_SOURCE="white-label-ready-to-send"

def load_json(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def load_queue():
    rows=[]
    try:
        for line in QUEUE.read_text(encoding="utf-8").splitlines():
            if line.strip(): rows.append(json.loads(line))
    except FileNotFoundError: pass
    return rows

def domain_of_email(email):
    return str(email or "").strip().lower().rsplit("@",1)[-1] if "@" in str(email or "") else ""

def message(org,domain):
    if domain.endswith(".it"):
        return ("Collaborazione tecnica web — Visual Design Studio",
f"""Buongiorno {org},

sono Giuseppe Allocca, Visual Design Studio, professionista web con base a Barcellona.

Collaboro con agenzie come supporto tecnico esterno su WordPress, frontend custom, performance/WPO, redesign e siti ad alte prestazioni. Lavoro con un'architettura proprietaria leggera e facilmente integrabile nei workflow esistenti.

Esempio diretto di architettura e performance: {SITE}

Se può essere utile avere capacità tecnica esterna per picchi di lavoro o progetti specifici, posso condividere rapidamente esempi pertinenti.

Un saluto,
Giuseppe Allocca
Visual Design Studio
{SITE}
""")
    if domain.endswith(".es"):
        return ("Colaboración técnica web — Visual Design Studio",
f"""Hola {org},

soy Giuseppe Allocca, de Visual Design Studio, profesional web con base en Barcelona.

Colaboro con agencias como apoyo técnico externo en WordPress, frontend a medida, performance/WPO, rediseños y sitios de alto rendimiento. Trabajo con una arquitectura propia ligera y fácil de integrar en flujos existentes.

Ejemplo directo de arquitectura y rendimiento: {SITE}

Si os puede resultar útil contar con capacidad técnica externa para picos de trabajo o proyectos concretos, puedo compartir rápidamente ejemplos relevantes.

Un saludo,
Giuseppe Allocca
Visual Design Studio
{SITE}
""")
    return ("External web development capacity — Visual Design Studio",
f"""Hello {org},

I'm Giuseppe Allocca from Visual Design Studio, a web professional based in Barcelona.

I work with agencies as external technical capacity for WordPress, custom frontend, performance/WPO, redesigns and high-performance websites, using a lightweight proprietary architecture that integrates cleanly with existing delivery workflows.

Architecture and performance example: {SITE}

If external capacity could be useful for project peaks or specific web work, I can quickly share relevant examples.

Best regards,
Giuseppe Allocca
Visual Design Studio
{SITE}
""")

def main():
    ready=load_json(READY,{"items":[]})
    ledger=load_json(LEDGER,{})
    exact=set((ledger.get("exact_email_index") or {}).keys())
    domains=set((ledger.get("corporate_domain_index") or {}).keys())
    rows=load_queue()
    stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

    ready_by_email={}
    for item in ready.get("items") or []:
        email=str(item.get("email") or "").strip().lower()
        domain=str(item.get("domain") or "").strip().lower()
        if not email or not domain: continue
        if item.get("state")!="READY_TO_SEND" or not item.get("dedup_verified"): continue
        if email in exact or domain in domains: continue
        ready_by_email[email]=item

    promoted=0
    suppressed=0
    for row in rows:
        if row.get("action_type")!="FIRST_CONTACT" or row.get("status")!="DRAFT":
            continue
        metadata=row.get("metadata") or {}
        if metadata.get("source")!=AUTO_SOURCE:
            continue
        email=str(row.get("recipient") or "").strip().lower()
        domain=domain_of_email(email)
        if email in exact or domain in domains:
            row["status"]="CANCELLED"
            row["metadata"]={**metadata,"suppressed_at":stamp,"suppression_reason":"GLOBAL_DEDUP_BLOCK"}
            suppressed+=1
            continue
        if email not in ready_by_email:
            continue
        row["status"]="APPROVED_TO_SEND"
        row["eligibility_basis"]=AUTO_BASIS
        row["approved_at"]=stamp
        row["metadata"]={**metadata,"approved_via":"AUTOMATED_FIRST_CONTACT_POLICY","approved_at":stamp}
        promoted+=1

    existing={(str(x.get("recipient") or "").lower(),str(x.get("action_type") or "")) for x in rows}
    added=0
    for email,item in ready_by_email.items():
        domain=str(item.get("domain") or "").strip().lower()
        if (email,"FIRST_CONTACT") in existing: continue
        org=str(item.get("organization") or domain)
        subject,text=message(org,domain)
        key=hashlib.sha256((domain+"|"+email).encode()).hexdigest()[:16]
        rows.append({
          "schema_version":"1.1","queue_id":"commercial-"+key,
          "status":"APPROVED_TO_SEND","action_type":"FIRST_CONTACT",
          "eligibility_basis":AUTO_BASIS,
          "organization":org,"recipient":email,"subject":subject,"text":text,
          "approved_at":stamp,"metadata":{"prepared_at":stamp,"source":AUTO_SOURCE,
          "priority":item.get("priority"),"source_url":item.get("source_url"),
          "message_strategy":item.get("message_strategy"),
          "approved_via":"AUTOMATED_FIRST_CONTACT_POLICY","approved_at":stamp}
        })
        existing.add((email,"FIRST_CONTACT")); added+=1

    QUEUE.parent.mkdir(parents=True,exist_ok=True)
    QUEUE.write_text("\n".join(json.dumps(x,ensure_ascii=False,separators=(",",":")) for x in rows)+"\n",encoding="utf-8")
    print(json.dumps({
        "ready":len(ready_by_email),
        "queue_records":len(rows),
        "auto_approved_added":added,
        "legacy_drafts_promoted":promoted,
        "duplicates_suppressed":suppressed
    }))
    return 0

if __name__=="__main__": raise SystemExit(main())
