#!/usr/bin/env python3
"""Enrich first-party booster signals into decision-maker/contact-route candidates.

Evidence rules:
- only public first-party pages
- no guessed emails
- no social scraping
- names/roles must appear in first-party page text
- email must be explicitly published on the same first-party domain or a mailto link
- supplier/collaboration route must be an explicit first-party URL/page
"""
from __future__ import annotations
import json,re,html
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse,urljoin
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"views/public-web-booster.json"
OUT=ROOT/"views/public-web-enriched-routes.json"
LEDGER=ROOT/"views/global-contact-ledger.json"

ROLE_PATTERNS=[
 r"(?:Head|Director|Lead|Manager|Responsabile|Direttore|Director|Responsable)\s+(?:of\s+)?(?:Digital|Web|Technology|Tech|Development|Marketing|Communication|Communications|Innovation|IT)",
 r"(?:Founder|Co-Founder|CEO|CTO|COO|Owner|Managing Director|Amministratore|Titolare|Fundador|Directora|Director)"
]
ROUTE_TERMS=("partner","supplier","provider","vendor","procurement","freelance","collabor","outsourc","white-label","white label","lavora","trabaja","contact")
EMAIL_RE=re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",re.I)
TAG_RE=re.compile(r"<[^>]+>")

def load(path,default):
    try:
        v=json.loads(path.read_text(encoding="utf-8")); return v if isinstance(v,dict) else default
    except Exception:return default

def domain(url):
    try:return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:return ""

def fetch(url,timeout=12):
    req=Request(url,headers={"User-Agent":"VDS-Commercial-Research/1.0 (+https://www.visualdesignstudio.es/)"})
    with urlopen(req,timeout=timeout) as r:
        ctype=(r.headers.get("Content-Type") or "").lower()
        if "html" not in ctype:return None
        return r.read(1200000).decode("utf-8","ignore")

def textify(raw):
    raw=re.sub(r"(?is)<script.*?</script>|<style.*?</style>"," ",raw)
    return re.sub(r"\s+"," ",html.unescape(TAG_RE.sub(" ",raw))).strip()

def extract_links(raw,base,root_domain):
    links=[]
    for m in re.finditer(r'''(?is)href\s*=\s*["']([^"']+)["']''',raw):
        href=html.unescape(m.group(1).strip())
        if href.startswith(("javascript:","#")):continue
        u=urljoin(base,href)
        if domain(u)!=root_domain:continue
        score=sum(1 for t in ROUTE_TERMS if t in u.lower())
        if score:links.append((score,u))
    return [u for _,u in sorted(set(links),reverse=True)[:10]]

def extract_people(text):
    people=[]
    for pat in ROLE_PATTERNS:
        for m in re.finditer(pat,text,re.I):
            start=max(0,m.start()-90);end=min(len(text),m.end()+90)
            snippet=text[start:end]
            name=None
            # Conservative nearby proper-name extraction, 2-4 title-cased tokens.
            candidates=re.findall(r"\b([A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’-]+(?:\s+[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’-]+){1,3})\b",snippet)
            for cand in candidates:
                if not any(x.lower() in cand.lower() for x in ["Visual Design","Managing Director","Marketing Manager","Web Developer"]):
                    name=cand; break
            people.append({"name":name,"role":m.group(0),"evidence":snippet.strip()})
    dedup=[];seen=set()
    for p in people:
        k=((p.get("name") or "").lower(),p["role"].lower())
        if k in seen:continue
        seen.add(k);dedup.append(p)
    return dedup[:8]

def main():
    src=load(SRC,{})
    ledger=load(LEDGER,{})
    exact=ledger.get("exact_email_index") or {}
    domains=ledger.get("corporate_domain_index") or {}
    rows=[]
    for sig in src.get("signals") or []:
        url=sig.get("url"); d=(sig.get("domain") or domain(url)).removeprefix("www.")
        if not url or not d:continue
        pages=[url]
        raw0=None
        try:raw0=fetch(url)
        except Exception:pass
        if raw0:
            pages += [x for x in extract_links(raw0,url,d) if x not in pages][:6]
        emails=set(sig.get("emails") or [])
        routes=[]
        people=[]
        evidence_pages=[]
        for purl in pages[:7]:
            try:raw=raw0 if purl==url and raw0 else fetch(purl)
            except Exception:continue
            if not raw:continue
            txt=textify(raw)
            evidence_pages.append(purl)
            for e in EMAIL_RE.findall(txt):
                if e.lower().endswith("@"+d): emails.add(e.lower())
            for mm in re.finditer(r'''(?is)href\s*=\s*["']mailto:([^?"']+)''',raw):
                e=mm.group(1).strip().lower()
                if e.endswith("@"+d):emails.add(e)
            if any(t in purl.lower() or t in txt.lower()[:6000] for t in ROUTE_TERMS):
                routes.append(purl)
            people.extend(extract_people(txt))
        emails=sorted(emails)
        route_candidates=sorted(set(routes))
        dm=[p for p in people if p.get("role")][:8]
        exact_block=[e for e in emails if e in exact]
        domain_block=d in domains
        confidence=0
        if emails:confidence+=35
        if route_candidates:confidence+=30
        if dm:confidence+=20
        if sig.get("route_hint"):confidence+=10
        if int(sig.get("signal_score") or 0)>=15:confidence+=5
        rows.append({
          "domain":d,"source_url":url,"signal_score":sig.get("signal_score",0),
          "decision_makers":dm,"public_emails":emails,
          "supplier_routes":route_candidates[:8],"evidence_pages":sorted(set(evidence_pages)),
          "dedup":{"exact_email_blocks":exact_block,"domain_already_contacted":domain_block},
          "contactability_score":min(100,confidence),
          "state":"BLOCKED_DUPLICATE" if domain_block or exact_block else ("CONTACTABLE_EVIDENCE" if emails and route_candidates else "ENRICHMENT_PARTIAL"),
          "send_authorized":False
        })
    rows.sort(key=lambda x:(x["state"]=="CONTACTABLE_EVIDENCE",x["contactability_score"],x["signal_score"]),reverse=True)
    payload={"schema_version":"1.0","updated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
      "policy":"FIRST_PARTY_EVIDENCE_ONLY_NO_EMAIL_GUESSING","count":len(rows),
      "contactable":sum(1 for x in rows if x["state"]=="CONTACTABLE_EVIDENCE"),
      "blocked_duplicate":sum(1 for x in rows if x["state"]=="BLOCKED_DUPLICATE"),
      "items":rows}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"count":payload["count"],"contactable":payload["contactable"],"blocked_duplicate":payload["blocked_duplicate"]}))
if __name__=="__main__": raise SystemExit(main())
