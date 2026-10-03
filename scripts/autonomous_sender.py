#!/usr/bin/env python3
# Visual Design Studio — 2026
"""Autonomous VDS sender.

No ChatGPT dependency. Sends only queue records explicitly marked APPROVED_TO_SEND
and carrying an allowed eligibility basis. Uses fail-closed dedup and Hostinger API/SMTP transport.
"""
from __future__ import annotations
import json, os, smtplib, ssl, time, hashlib, urllib.parse
from zoneinfo import ZoneInfo
import sync_hostinger_mail as hostinger
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/"outreach/autonomous-send-queue.jsonl"
LEDGER=ROOT/"views/global-contact-ledger.json"
STATE=ROOT/"state/autonomous-sender-state.json"
AUDIT=ROOT/"data/autonomous-sender-runs"
SETTINGS=ROOT/"config/sender-settings.json"
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

def send(host,port,user,password,from_addr,to_addr,subject,text,bcc=None,timeout=25):
    msg=EmailMessage()
    msg["From"]=from_addr
    msg["To"]=to_addr
    if bcc: msg["Bcc"]=bcc
    msg["Subject"]=subject
    msg.set_content(text)
    ctx=ssl.create_default_context()
    p=int(port)
    if p==465:
        with smtplib.SMTP_SSL(host,p,context=ctx,timeout=timeout) as s:
            s.login(user,password); s.send_message(msg)
    else:
        with smtplib.SMTP(host,p,timeout=timeout) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo(); s.login(user,password); s.send_message(msg)

def main():
    settings=load_json(SETTINGS,{})
    provider=str(settings.get("provider") or "SMTP").upper()
    mode=str(settings.get("mode") or "DRY_RUN").upper()

    if mode != "LIVE":
        print(json.dumps({"mode":mode,"provider":provider,"state":"DRY_RUN_NO_SEND"}))
        return 0

    schedule=settings.get("schedule") or {}
    if schedule.get("enabled",True):
        tz=ZoneInfo(str(schedule.get("timezone") or "Europe/Madrid"))
        local=datetime.now(tz)
        hours=schedule.get("allowed_hours") or {}
        start=str(hours.get("start") or "09:00")
        end=str(hours.get("end") or "19:00")
        hhmm=local.strftime("%H:%M")
        if not (start <= hhmm < end):
            print(json.dumps({"mode":mode,"provider":provider,"state":"SEND_WINDOW_CLOSED","local_time":hhmm}))
            return 0

    if provider=="HOSTINGER_API":
        if not hostinger.TOKEN:
            raise SystemExit("Missing HOSTINGER_EMAIL_API_TOKEN")
        mailbox_id=hostinger.get_mailbox()
    else:
        required=["VDS_SMTP_HOST","VDS_SMTP_PORT","VDS_SMTP_USER","VDS_SMTP_PASSWORD","VDS_SMTP_FROM"]
        missing=[k for k in required if not os.getenv(k)]
        if missing:
            raise SystemExit("Missing SMTP configuration: "+",".join(missing))

    queue=load_jsonl(QUEUE)
    safety=settings.get("safety") or {}
    if safety.get("fail_closed_on_missing_ledger",True) and not LEDGER.exists():
        raise SystemExit("Missing global contact ledger")
    ledger=load_json(LEDGER,{})
    state=load_json(STATE,{"sent_idempotency_keys":[]})
    sent_keys=set(state.get("sent_idempotency_keys") or [])
    exact=set((ledger.get("exact_email_index") or {}).keys())
    domains=set((ledger.get("corporate_domain_index") or {}).keys())

    delivery=settings.get("delivery") or {}
    max_batch=max(1,min(int(delivery.get("max_batch") or os.getenv("VDS_AUTONOMOUS_MAX_BATCH","10")),500))
    delay_seconds=max(0.0,float(delivery.get("delay_seconds",os.getenv("VDS_AUTONOMOUS_SEND_DELAY_SECONDS","2"))))
    timeout_seconds=max(5,int(delivery.get("timeout_seconds",25)))
    dedup_enabled=bool(safety.get("dedup_enabled",True))
    idempotency_enabled=bool(safety.get("idempotency_enabled",True))
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
        if idempotency_enabled and key in sent_keys:
            rejected.append({"queue_id":item.get("queue_id"),"reason":"IDEMPOTENT_ALREADY_SENT"})
            continue
        if dedup_enabled and item.get("action_type","FIRST_CONTACT")=="FIRST_CONTACT" and (recipient in exact or domain in domains):
            rejected.append({"queue_id":item.get("queue_id"),"reason":"GLOBAL_DEDUP_BLOCK"})
            continue
        if not item.get("subject") or not item.get("text"):
            rejected.append({"queue_id":item.get("queue_id"),"reason":"MISSING_MESSAGE"})
            continue
        candidates.append((item,key,domain))
        if len(candidates)>=max_batch: break

    if provider!="HOSTINGER_API":
        host=os.environ["VDS_SMTP_HOST"];port=os.environ["VDS_SMTP_PORT"]
        user=os.environ["VDS_SMTP_USER"];password=os.environ["VDS_SMTP_PASSWORD"]
        from_addr=os.environ["VDS_SMTP_FROM"]
    message_cfg=settings.get("message") or {}
    bcc=os.getenv(str(message_cfg.get("owner_bcc_env") or "VDS_OWNER_BCC")) if message_cfg.get("owner_bcc_enabled",True) else None
    results=[]
    for item,key,domain in candidates:
        try:
            if provider=="HOSTINGER_API":
                payload={"to":[item["recipient"]],"subject":item["subject"],"text":item["text"],"displayName":"Giuseppe Allocca — Visual Design Studio"}
                if bcc: payload["bcc"]=[bcc]
                hostinger.api("POST",f"/api/v1/mailboxes/{urllib.parse.quote(mailbox_id,safe='')}/send",body=payload)
            else:
                send(host,port,user,password,from_addr,item["recipient"],item["subject"],item["text"],bcc,timeout_seconds)
            sent_keys.add(key)
            exact.add(item["recipient"].lower()); domains.add(domain)
            results.append({
                "queue_id":item.get("queue_id"),"recipient":item["recipient"].lower(),
                "organization":item.get("organization"),"state":"DELIVERY_ACCEPTED",
                "accepted_at":nowz(),"idempotency_key":key
            })
            time.sleep(delay_seconds)
        except Exception as exc:
            results.append({
                "queue_id":item.get("queue_id"),"recipient":item.get("recipient"),
                "state":"SEND_FAILED","error":f"{type(exc).__name__}: {exc}"[:500]
            })

    payload={
        "schema_version":"1.1","updated_at":nowz(),"provider":provider,"queue_records":len(queue),
        "eligible_candidates":len(candidates),"batch_limit":max_batch,
        "delivery_accepted":sum(1 for x in results if x["state"]=="DELIVERY_ACCEPTED"),
        "smtp_accepted":sum(1 for x in results if x["state"]=="DELIVERY_ACCEPTED"),
        "failed":sum(1 for x in results if x["state"]=="SEND_FAILED"),
        "rejected_count":len(rejected),"results":results,"rejected":rejected[:100],
        "sent_idempotency_keys":sorted(sent_keys),
    }
    save_json(STATE,payload)
    AUDIT.mkdir(parents=True,exist_ok=True)
    save_json(AUDIT/(payload["updated_at"].replace(":","-")+".json"),payload)
    print(json.dumps({k:payload[k] for k in ("queue_records","eligible_candidates","delivery_accepted","smtp_accepted","failed","rejected_count")}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
