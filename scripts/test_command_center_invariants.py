#!/usr/bin/env python3
# Visual Design Studio — 2026
"""Fail-closed Command Center deployment invariants."""
from pathlib import Path
import json,re,sys

ROOT=Path(__file__).resolve().parents[1]
PAGES=ROOT/".pages"
SRC=ROOT/"outreach/autonomous-send-queue.jsonl"
PUB=PAGES/"outreach/autonomous-send-queue.jsonl"

def rows(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

errors=[]
for p in [SRC,PUB,PAGES/"index.html",PAGES/"assets/app.js",PAGES/"assets/approval-queue.js",PAGES/"assets/eu-radar.js"]:
    if not p.exists() or not p.stat().st_size: errors.append(f"missing/empty: {p}")

if not errors:
    src,pub=rows(SRC),rows(PUB)
    src_by={str(x.get("queue_id")):x for x in src}
    pub_by={str(x.get("queue_id")):x for x in pub}
    for qid,item in src_by.items():
        if qid not in pub_by: errors.append(f"published queue missing {qid}")
        elif pub_by[qid] != item: errors.append(f"published queue differs for {qid}")
    drafts=[x for x in src if x.get("status")=="DRAFT" and x.get("action_type")=="FIRST_CONTACT"]
    for x in drafts:
        if x.get("queue_id") not in pub_by: errors.append(f"approval draft not published: {x.get('queue_id')}")
    app=(PAGES/"assets/app.js").read_text(encoding="utf-8")
    radar=(PAGES/"assets/eu-radar.js").read_text(encoding="utf-8")
    for required in ["dashboard.json","today.json","health.json","companies.json","opportunities.json","sources.json","territory-productivity.json","geography.json","eu-project-radar.json","acquisition-performance.json"]:
        p=PAGES/"api/v1"/required
        if not p.exists() or not p.stat().st_size: errors.append(f"missing public projection: {required}")
    for js in (PAGES/"assets").glob("*.js"):
        body=js.read_text(encoding="utf-8",errors="ignore")
        if "/contents/api/v1/" in body: errors.append(f"legacy Contents polling in {js.name}")
    approval=(PAGES/"assets/approval-queue.js").read_text(encoding="utf-8")
    index=(PAGES/"index.html").read_text(encoding="utf-8")
    if "/contents/api/v1/" in app or "/contents/api/v1/" in radar: errors.append("authenticated API polling regression")
    if "QA_PATH='outreach/autonomous-send-queue.jsonl'" not in approval: errors.append("approval queue path contract missing")
    read_block=approval.split("async function qaRead(){",1)[1].split("async function qaWrite",1)[0] if "async function qaRead(){" in approval and "async function qaWrite" in approval else ""
    if "api.github.com" in read_block or "QA_GH" in read_block: errors.append("approval queue read must be API-free")
    if "APPROVED_TO_SEND" not in approval or "OWNER_APPROVED_ONE_TO_ONE" not in approval: errors.append("approval transition contract missing")
    if 'id="approvalRows"' not in index: errors.append("approval UI missing")
    if "frame-ancestors" in index: errors.append("invalid meta CSP frame-ancestors regression")
    if 'style="' in radar: errors.append("EU radar inline style CSP regression")

if errors:
    print("COMMAND CENTER INVARIANTS FAILED",file=sys.stderr)
    for e in errors: print(" - "+e,file=sys.stderr)
    raise SystemExit(1)
print(json.dumps({"status":"PASS","source_records":len(rows(SRC)),"published_records":len(rows(PUB))},indent=2))
