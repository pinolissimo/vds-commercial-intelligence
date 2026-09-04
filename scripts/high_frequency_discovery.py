#!/usr/bin/env python3
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/high-frequency-discovery-sources.json"
LATEST_PATH = ROOT / "views/high-frequency-discovery-latest.json"
LEDGER_PATH = ROOT / "data/high-frequency-discovery/raw-signals.jsonl"
STATE_PATH = ROOT / "metrics/high-frequency-discovery-state.json"
WATCH_STATE_PATH = ROOT / "metrics/high-frequency-watch-state.json"
USER_AGENT = "VDS-Commercial-Intelligence/1.0 (+https://www.visualdesignstudio.es/)"


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def fetch_bytes(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/rss+xml, application/xml, text/html;q=0.9, */*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def strip_html(value):
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value or "", flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def keyword_hits(text, keywords):
    low = text.lower()
    return sorted({k for k in keywords if k.lower() in low})


def normalized_key(source_id, external_id, url, title, company):
    base = f"{source_id}|{external_id or ''}|{url or ''}|{title or ''}|{company or ''}".lower().strip()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]


def parse_remoteok(source, config):
    raw, _ = fetch_bytes(source["url"])
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    rows = []
    for obj in payload if isinstance(payload, list) else []:
        if not isinstance(obj, dict) or not obj.get("position"):
            continue
        title = str(obj.get("position") or "")
        company = str(obj.get("company") or "")
        location = str(obj.get("location") or "")
        description = strip_html(str(obj.get("description") or ""))
        tags = " ".join(str(x) for x in (obj.get("tags") or []))
        combined = " ".join([title, company, location, description, tags])
        hits = keyword_hits(combined, config["profile_keywords"])
        if not hits:
            continue
        geo_hits = keyword_hits(combined, config["remote_geo_keywords"])
        url = str(obj.get("url") or obj.get("apply_url") or "")
        ext_id = str(obj.get("id") or obj.get("slug") or "")
        rows.append({
            "signal_key": normalized_key(source["id"], ext_id, url, title, company),
            "source_id": source["id"],
            "source_kind": source["kind"],
            "source_url": source["url"],
            "external_id": ext_id,
            "title": title,
            "organization": company,
            "location": location,
            "opportunity_url": url,
            "published_at": obj.get("date"),
            "matched_profile_keywords": hits,
            "matched_geo_keywords": geo_hits,
            "raw_fit_score": min(100, 35 + len(hits) * 8 + min(20, len(geo_hits) * 5)),
            "route_state": "TO_VERIFY",
            "verification_state": "RAW_PUBLIC_SIGNAL"
        })
    return rows


def item_text(item, tag):
    el = item.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def parse_rss(source, config):
    raw, _ = fetch_bytes(source["url"])
    root = ET.fromstring(raw)
    rows = []
    for item in root.findall(".//item"):
        title = item_text(item, "title")
        link = item_text(item, "link")
        description = strip_html(item_text(item, "description"))
        pub = item_text(item, "pubDate")
        creator = ""
        for child in list(item):
            if child.tag.endswith("creator") and child.text:
                creator = child.text.strip()
                break
        combined = " ".join([title, creator, description])
        hits = keyword_hits(combined, config["profile_keywords"])
        if not hits:
            continue
        geo_hits = keyword_hits(combined, config["remote_geo_keywords"])
        rows.append({
            "signal_key": normalized_key(source["id"], "", link, title, creator),
            "source_id": source["id"],
            "source_kind": source["kind"],
            "source_url": source["url"],
            "external_id": "",
            "title": title,
            "organization": creator,
            "location": "",
            "opportunity_url": link,
            "published_at": pub or None,
            "matched_profile_keywords": hits,
            "matched_geo_keywords": geo_hits,
            "raw_fit_score": min(100, 30 + len(hits) * 8 + min(20, len(geo_hits) * 5)),
            "route_state": "TO_VERIFY",
            "verification_state": "RAW_PUBLIC_SIGNAL"
        })
    return rows


def parse_source(source, config):
    if source["kind"] == "remoteok_json":
        return parse_remoteok(source, config)
    if source["kind"] == "rss":
        return parse_rss(source, config)
    raise ValueError(f"Unsupported source kind: {source['kind']}")


def extract_page_title(text):
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    return strip_html(match.group(1))[:240] if match else ""


def scan_watch_pages(config, watch_state):
    now = dt.datetime.now(dt.timezone.utc)
    minute = now.minute
    interval = int(config.get("policy", {}).get("official_watch_pages_interval_minutes", 60))
    if interval >= 60 and minute >= 15:
        return [], watch_state, []
    signals, errors = [], []
    pages = [p for p in config.get("official_watch_pages", []) if p.get("enabled", True) and p.get("url")]
    for page in pages:
        try:
            raw, _ = fetch_bytes(page["url"])
            text = raw.decode("utf-8", errors="replace")
            cleaned = strip_html(text)
            digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
            key = page.get("id") or hashlib.sha256(page["url"].encode("utf-8")).hexdigest()[:20]
            previous = watch_state.get(key, {})
            hits = keyword_hits(cleaned, config["profile_keywords"] + ["freelance", "collaborator", "collaboration", "contractor", "careers", "jobs", "wordpress", "frontend", "website", "dissemination", "communication"])
            changed = previous.get("content_hash") not in (None, digest)
            first_relevant = previous.get("content_hash") is None and bool(hits)
            if (changed or first_relevant) and hits:
                signals.append({
                    "signal_key": normalized_key("official_watch", key, page["url"], extract_page_title(text), page.get("organization", "")),
                    "source_id": "official_watch",
                    "source_kind": "official_page_change" if changed else "official_page_baseline",
                    "source_url": page["url"],
                    "external_id": key,
                    "title": extract_page_title(text) or page.get("name", "Official page"),
                    "organization": page.get("organization", ""),
                    "location": page.get("country", ""),
                    "opportunity_url": page["url"],
                    "published_at": None,
                    "matched_profile_keywords": hits[:30],
                    "matched_geo_keywords": keyword_hits(cleaned, config["remote_geo_keywords"]),
                    "raw_fit_score": min(100, 40 + len(hits) * 4),
                    "route_state": "TO_VERIFY",
                    "verification_state": "OFFICIAL_PAGE_SIGNAL",
                    "watch_category": page.get("category", "official")
                })
            watch_state[key] = {"url": page["url"], "content_hash": digest, "checked_at": now_utc()}
        except Exception as exc:
            errors.append({"source_id": page.get("id", "official_watch"), "error": f"{type(exc).__name__}: {exc}"[:500]})
    return signals, watch_state, errors


def main():
    config = load_json(CONFIG_PATH, {})
    latest = load_json(LATEST_PATH, {"schema_version": "1.0", "signals": []})
    state = load_json(STATE_PATH, {"schema_version": "1.0", "runs": 0, "total_new_signals": 0})
    watch_state = load_json(WATCH_STATE_PATH, {})
    existing = {x.get("signal_key"): x for x in latest.get("signals", []) if x.get("signal_key")}
    enabled = [s for s in config.get("sources", []) if s.get("enabled", True)]
    fetched_at = now_utc()
    all_rows, errors, source_counts = [], [], {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(8, len(enabled)))) as pool:
        futures = {pool.submit(parse_source, source, config): source for source in enabled}
        for future in concurrent.futures.as_completed(futures):
            source = futures[future]
            try:
                rows = future.result()
                all_rows.extend(rows)
                source_counts[source["id"]] = len(rows)
            except Exception as exc:
                errors.append({"source_id": source["id"], "error": f"{type(exc).__name__}: {exc}"[:500]})
                source_counts[source["id"]] = 0

    watch_rows, watch_state, watch_errors = scan_watch_pages(config, watch_state)
    all_rows.extend(watch_rows)
    errors.extend(watch_errors)
    source_counts["official_watch"] = len(watch_rows)

    new_rows = []
    for row in all_rows:
        row["discovered_at"] = fetched_at
        key = row["signal_key"]
        if key not in existing:
            existing[key] = row
            new_rows.append(row)
        else:
            prior = existing[key]
            prior["last_seen_at"] = fetched_at
            prior["matched_profile_keywords"] = sorted(set(prior.get("matched_profile_keywords", [])) | set(row.get("matched_profile_keywords", [])))
            prior["matched_geo_keywords"] = sorted(set(prior.get("matched_geo_keywords", [])) | set(row.get("matched_geo_keywords", [])))
            prior["raw_fit_score"] = max(int(prior.get("raw_fit_score", 0)), int(row.get("raw_fit_score", 0)))

    max_latest = int(config.get("policy", {}).get("max_latest_signals", 1500))
    merged = sorted(existing.values(), key=lambda x: (x.get("discovered_at") or "", x.get("raw_fit_score", 0)), reverse=True)[:max_latest]
    latest_out = {
        "schema_version": "1.0",
        "updated_at": fetched_at,
        "mode": "PUBLIC_HIGH_FREQUENCY_DISCOVERY_ONLY",
        "no_outreach": True,
        "sources_enabled": [s["id"] for s in enabled],
        "new_signals_this_run": len(new_rows),
        "signal_count": len(merged),
        "errors": errors,
        "signals": merged
    }
    state_out = {
        "schema_version": "1.0",
        "updated_at": fetched_at,
        "runs": int(state.get("runs", 0)) + 1,
        "last_run_new_signals": len(new_rows),
        "last_run_matched_signals": len(all_rows),
        "total_new_signals": int(state.get("total_new_signals", 0)) + len(new_rows),
        "source_counts": source_counts,
        "errors": errors
    }

    append_jsonl(LEDGER_PATH, new_rows)
    write_json(LATEST_PATH, latest_out)
    write_json(STATE_PATH, state_out)
    write_json(WATCH_STATE_PATH, watch_state)
    print(json.dumps({"fetched_at": fetched_at, "new_signals": len(new_rows), "matched": len(all_rows), "source_counts": source_counts, "errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
