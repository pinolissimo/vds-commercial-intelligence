#!/usr/bin/env python3
"""Public-web intelligence booster for VDS.

Uses Scrapy for ordinary public pages and Playwright as a JS-rendering fallback.
Explicitly excludes social platforms whose terms prohibit automated scraping.
No login automation, stealth plugins, proxy rotation or access-control bypass.
"""
from __future__ import annotations
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"config/public-web-booster.json"
OUT=ROOT/"views/public-web-booster.json"
SEEDS=ROOT/"views/buyer-intent-priority.json"
TERRITORIAL=ROOT/"views/territorial-public-search-results.json"

def load(path,default):
    try:
        v=json.loads(path.read_text(encoding="utf-8")); return v if isinstance(v,dict) else default
    except Exception: return default

def host(url):
    try:return (urlparse(url).hostname or "").lower()
    except Exception:return ""

def collect_seeds(limit):
    data=load(SEEDS,{})
    territorial=load(TERRITORIAL,{})
    rows=data.get("ranking") or data.get("opportunities") or data.get("items") or []
    urls=[]
    # Fresh territorial search results get first chance at first-party verification.
    for mission in territorial.get("missions") or []:
        for result in mission.get("results") or []:
            u=result.get("url")
            if isinstance(u,str) and u.startswith(("http://","https://")): urls.append(u)
    def walk(v):
        if isinstance(v,str) and v.startswith(("http://","https://")): urls.append(v)
        elif isinstance(v,list):
            for x in v: walk(x)
        elif isinstance(v,dict):
            for x in v.values(): walk(x)
    for row in rows[:300]: walk(row)
    seen=set(); out=[]
    for u in urls:
        h=host(u)
        if not h or h in seen: continue
        seen.add(h); out.append(u)
        if len(out)>=limit: break
    return out

def authoritative_emails(text, mailto_hrefs=None):
    """Extract public routes and drop truncated local-part suffix artifacts."""
    candidates=set(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",text or "",re.I))
    for href in mailto_hrefs or []:
        raw=str(href or "").split(":",1)[-1].split("?",1)[0].strip()
        candidates.update(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",raw,re.I))
    normalized=sorted({e.lower() for e in candidates})
    clean=[]
    for email in normalized:
        local,domain=email.rsplit("@",1)
        if any(
            other_domain==domain and other_local!=local and other_local.endswith(local)
            for other in normalized
            for other_local,other_domain in [other.rsplit("@",1)]
        ):
            continue
        clean.append(email)
    return clean[:10]

def main():
    cfg=load(CFG,{})
    blocked=set(cfg.get("blocked_domains") or [])
    seeds=[u for u in collect_seeds(int(cfg.get("max_domains_per_run",30))) if host(u) not in blocked]
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    # The actual crawler is generated as a tiny Scrapy process so the booster remains isolated
    # from the revenue engine. Playwright is imported only as a fallback.
    results=[]
    signal_terms=[x.lower() for x in cfg.get("signal_terms",[])]
    path_terms=[x.lower() for x in cfg.get("interesting_path_terms",[])]
    max_pages=int(cfg.get("max_pages_per_domain",8))

    try:
        import scrapy
        from scrapy.crawler import CrawlerProcess
        from scrapy.spiders import Spider
    except Exception as exc:
        OUT.write_text(json.dumps({"schema_version":"1.0","updated_at":now,"status":"DEPENDENCY_MISSING","error":str(exc),"signals":[]},indent=2)+"\n")
        return 0

    class BoosterSpider(Spider):
        name="vds_public_booster"
        custom_settings={
          "ROBOTSTXT_OBEY":bool(cfg.get("respect_robots_txt",True)),
          "DOWNLOAD_DELAY":float(cfg.get("request_delay_seconds",2.0)),
          "CONCURRENT_REQUESTS_PER_DOMAIN":1,
          "LOG_LEVEL":"ERROR",
          "USER_AGENT":"VDS-Commercial-Research/1.0 (+https://www.visualdesignstudio.es/)"
        }
        start_urls=seeds
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw); self.counts={}
        def parse(self,response):
            h=host(response.url); self.counts[h]=self.counts.get(h,0)+1
            if self.counts[h] > max_pages: return
            ctype=(response.headers.get("Content-Type") or b"").decode(errors="ignore").lower()
            if "html" not in ctype and "xhtml" not in ctype: return
            text=" ".join(response.css("body *::text").getall())
            compact=re.sub(r"\s+"," ",text).strip()
            matched=sorted({t for t in signal_terms if t in compact.lower()})
            emails=authoritative_emails(compact,response.css('a[href^="mailto:"]::attr(href)').getall())
            min_terms=int(cfg.get("min_signal_terms",2))
            path_l=response.url.lower()
            route_hint=any(t in path_l for t in path_terms)
            score=len(matched)*4 + min(len(emails),2)*3 + (5 if route_hint else 0)
            if len(matched)>=min_terms or (matched and emails):
                results.append({"url":response.url,"domain":h,"matched_terms":matched,"emails":emails,"text_sample":compact[:900],"render":"SCRAPY","signal_score":score,"route_hint":route_hint})
            if self.counts[h]>=max_pages:return
            for href in response.css("a::attr(href)").getall():
                absolute=response.urljoin(href); ah=host(absolute)
                if ah!=h:return_or_none=None
                if ah==h and any(t in absolute.lower() for t in path_terms):
                    yield response.follow(href,self.parse)

    process=CrawlerProcess()
    process.crawl(BoosterSpider)
    process.start()

    # Playwright fallback only for seed domains with no useful Scrapy result.
    if cfg.get("dynamic_browser_fallback",True):
        hit_domains={r["domain"] for r in results}
        missing=[u for u in seeds if host(u) not in hit_domains][:8]
        if missing:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser=p.chromium.launch(headless=True)
                    for u in missing:
                        try:
                            page=browser.new_page()
                            page.goto(u,wait_until="domcontentloaded",timeout=20000)
                            compact=re.sub(r"\s+"," ",page.locator("body").inner_text(timeout=5000)).strip()
                            matched=sorted({t for t in signal_terms if t in compact.lower()})
                            mailto_hrefs=page.locator('a[href^="mailto:"]').evaluate_all("(els) => els.map((e) => e.getAttribute('href') || '')")
                            emails=authoritative_emails(compact,mailto_hrefs)
                            route_hint=any(t in u.lower() for t in path_terms); score=len(matched)*4+min(len(emails),2)*3+(5 if route_hint else 0)
                            if len(matched)>=int(cfg.get("min_signal_terms",2)) or (matched and emails): results.append({"url":u,"domain":host(u),"matched_terms":matched,"emails":emails,"text_sample":compact[:900],"render":"PLAYWRIGHT","signal_score":score,"route_hint":route_hint})
                            page.close()
                        except Exception: pass
                    browser.close()
            except Exception: pass

    dedup={}
    for r in results:
        key=(r["domain"],r["url"])
        if key not in dedup or int(r.get("signal_score",0))>int(dedup[key].get("signal_score",0)): dedup[key]=r
    ranked=sorted(dedup.values(),key=lambda x:(int(x.get("signal_score",0)),bool(x.get("route_hint")),len(x.get("emails") or [])),reverse=True)
    ranked=ranked[:int(cfg.get("max_signal_records",120))]
    payload={
      "schema_version":"1.0","updated_at":now,"status":"OK",
      "policy":"PUBLIC_WEB_ONLY_NO_EVASION",
      "domains_attempted":len({host(u) for u in seeds}),
      "signals":ranked
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"OK","domains":payload["domains_attempted"],"signals":len(payload["signals"])}))
    return 0
if __name__=="__main__": raise SystemExit(main())
