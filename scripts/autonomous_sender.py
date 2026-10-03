#!/usr/bin/env python3
# Visual Design Studio — 2026
"""Autonomous VDS sender.

No ChatGPT dependency. Sends only queue records explicitly marked APPROVED_TO_SEND
and carrying an allowed eligibility basis. Uses fail-closed dedup and Hostinger SMTP.
"""
from __future__ import annotations
import json, os, smtplib, ssl, time, hashlib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/"outreach/autonomous-send-queue.jsonl"
LEDGER=ROOT/"views/global-contact-ledger.json"
STATE=ROOT/"state/autonomous-sender-state.json"
AUDIT=ROOT/"data/autonomous-sender-runs"
ALLOWED_BASES={
    "CONSENT",
    "REQUESTED_CONTACT",
    "EXISTING_BUSINESS_RELATIONSHIP",
    "AUTHORITATIVE_APPLICATION_ROUTE",
    "OWNER_APPROVED_ONE_TO_ONE",
}

def nowz():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def load_json(path, default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def load_jsonl(path):
    rows=[]
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line: continue
            v=json.loads(line)
            if isinstance(v,dict): rows.append(v)
    except FileNotFoundError:
        pass
    return rows

def save_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def email_domain(email):
    return str(email or "").strip().lower().rsplit("@",1)[-1] if "@" in str(email or "") else ""

def idem_key(item):
    raw="|".join([
        str(item.get("queue_id") or ""),
        str(item.get("recipient") or "").lower(),
        str(item.get("subject") or ""),
        str(item.get("approved_at") or ""),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def send(host,port,user,password,from_addr,to_addr,subject,text,bcc=None):
    msg=EmailMessage()
    msg["From"]=from_addr
    msg["To"]=to_addr
    if bcc: msg["Bcc"]=bcc
    msg["Subject"]=subject
    msg.set_content(text)
    ctx=ssl.create_default_context()
    p=int(port)
    if p==465:
        with smtplib.SMTP_SSL(host,p,context=ctx,timeout=25) as s:
            s.login(user,password); s.send_message(msg)
    else:
        with smtplib.SMTP(host,p,timeout=25) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo(); s.login(user,password); s.send_message(msg)

def main():
    required=["VDS_SMTP_HOST","VDS_SMTP_PORT","VDS_SMTP_USER","VDS_SMTP_PASSWORD","VDS_SMTP_FROM"]
    missing=[k for k in required if not os.getenv(k)]
    if missing:
        raise SystemExit("Missing SMTP configuration: "+",".join(missing))

    queue=load_jsonl(QUEUE)
    ledger=load_json(LEDGER,{})
    state=load_json(STATE,{"sent_idempotency_keys":[]})
    sent_keys=set(state.get("sent_idempotency_keys") or [])
    exact=set((ledger.get("exact_email_index") or {}).keys())
    domains=set((ledger.get("corporate_domain_index") or {}).keys())

    max_batch=max(1,min(int(os.getenv("VDS_AUTONOMOUS_MAX_BATCH","10")),25))
    candidates=[]
    rejected=[]
    for item in queue:
        if item.get("status")!="APPROVED_TO_SEND":
            continue
        basis=str(item.get("eligibility_basis") or "")
        if basis not in ALLOWED_BASES:
            rejected.append({"queue_id":item.get("queue_id"),"reason":"ELIGIBILITY_BASIS_NOT_ALLOWED"})
            continue
        recipient=str(item.get("recipient") or "").strip().lower()
        domain=email_domain(recipient)
        if not recipient or "@" not in recipient:
            rejected.append({"queue_id":item.get("queue_id"),"reason":"INVALID_RECIPIENT"})
            continue
        key=idem_key(item)
        if key in sent_keys:
            rejected.append({"queue_id":item.get("queue_id"),"reason":"IDEMPOTENT_ALREADY_SENT"})
            continue
        if item.get("action_type","FIRST_CONTACT")=="FIRST_CONTACT" and (recipient in exact or domain in domains):
            rejected.append({"queue_id":item.get("queue_id"),"reason":"GLOBAL_DEDUP_BLOCK"})
            continue
        if not item.get("subject") or not item.get("text"):
            rejected.append({"queue_id":item.get("queue_id"),"reason":"MISSING_MESSAGE"})
            continue
        candidates.append((item,key,domain))
        if len(candidates)>=max_batch: break

    host=os.environ["VDS_SMTP_HOST"];port=os.environ["VDS_SMTP_PORT"]
    user=os.environ["VDS_SMTP_USER"];password=os.environ["VDS_SMTP_PASSWORD"]
    from_addr=os.environ["VDS_SMTP_FROM"];bcc=os.getenv("VDS_OWNER_BCC")
    results=[]
    for item,key,domain in candidates:
        try:
            send(host,port,user,password,from_addr,item["recipient"],item["subject"],item["text"],bcc)
            sent_keys.add(key)
            exact.add(item["recipient"].lower()); domains.add(domain)
            results.append({
                "queue_id":item.get("queue_id"),"recipient":item["recipient"].lower(),
                "organization":item.get("organization"),"state":"SMTP_ACCEPTED",
                "accepted_at":nowz(),"idempotency_key":key
            })
            time.sleep(float(os.getenv("VDS_AUTONOMOUS_SEND_DELAY_SECONDS","2")))
        except Exception as exc:
            results.append({
                "queue_id":item.get("queue_id"),"recipient":item.get("recipient"),
                "state":"SEND_FAILED","error":f"{type(exc).__name__}: {exc}"[:500]
            })

    payload={
        "schema_version":"1.0","updated_at":nowz(),"queue_records":len(queue),
        "eligible_candidates":len(candidates),"batch_limit":max_batch,
        "smtp_accepted":sum(1 for x in results if x["state"]=="SMTP_ACCEPTED"),
        "failed":sum(1 for x in results if x["state"]=="SEND_FAILED"),
        "rejected_count":len(rejected),"results":results,"rejected":rejected[:100],
        "sent_idempotency_keys":sorted(sent_keys),
    }
    save_json(STATE,payload)
    AUDIT.mkdir(parents=True,exist_ok=True)
    save_json(AUDIT/(payload["updated_at"].replace(":","-")+".json"),payload)
    print(json.dumps({k:payload[k] for k in ("queue_records","eligible_candidates","smtp_accepted","failed","rejected_count")}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
