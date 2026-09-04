#!/usr/bin/env python3
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
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
USER_AGENT = "VDS-Commercial-Intelligence/1.1 (+https://www.visualdesignstudio.es/)"


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
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
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/rss+xml, application/xml, text/html;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def strip_html(value):
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value or "", flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def term_present(text_lower, term):
    term_lower = term.lower().strip()
    if len(term_lower) <= 3 or re.fullmatch(r"[a-z0-9+#.\-]{1,4}", term_lower):
        return re.search(rf"(?<![\w]){re.escape(term_lower)}(?![\w])", text_lower) is not None
    return term_lower in text_lower


def keyword_hits(text, keywords):
    low = (text or "").lower()
    return sorted({k for k in keywords if term_present(low, k)})


def normalized_key(source_id, external_id, url, title, company):
    base = f"{source_id}|{external_id or ''}|{url or ''}|{title or ''}|{company or ''}".lower().strip()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]


def geo_bucket(text, remote_source=False):
    low = (text or "").lower()
    spain_terms = ["spain", "españa", "barcelona", "madrid", "valencia", "bilbao", "málaga", "malaga", "sevilla", "zaragoza", "alicante", "catalonia", "cataluña"]
    italy_terms = ["italy", "italia", "milano", "milan", "roma", "rome", "torino", "turin", "bologna", "firenze", "florence", "napoli", "veneto", "lombardia"]
    eu_terms = ["europe", "european union", " eu ", "emea", "europe only", "eu only"]
    worldwide_terms = ["worldwide", "anywhere", "global remote", "work from anywhere"]
    if any(x in low for x in spain_terms):
        return "SPAIN_OR_INCLUDES_SPAIN"
    if any(x in low for x in italy_terms):
        return "ITALY_OR_INCLUDES_ITALY"
    if any(x in low for x in eu_terms):
        return "EU_REMOTE_TO_VERIFY"
    if any(x in low for x in worldwide_terms):
        return "WORLDWIDE_REMOTE"
    return "REMOTE_TO_VERIFY" if remote_source else "GEO_TO_VERIFY"


def build_row(source, ext_id, title, company, location, url, published_at, description, tags, config, remote_source=False):
    combined = " ".join([title or "", company or "", location or "", description or "", tags or ""])
    hits = keyword_hits(combined, config.get("profile_keywords", []))
    if not hits:
        return None
    geo_hits = keyword_hits(combined, config.get("remote_geo_keywords", []))
    commercial_hits = keyword_hits(combined, config.get("commercial_keywords", []))
    geo = geo_bucket(combined, remote_source=remote_source)
    score = 28 + min(48, len(hits) * 7) + min(14, len(commercial_hits) * 4)
    if geo in {"SPAIN_OR_INCLUDES_SPAIN", "ITALY_OR_INCLUDES_ITALY", "WORLDWIDE_REMOTE"}:
        score += 10
    elif geo == "EU_REMOTE_TO_VERIFY":
        score += 7
    return {
        "signal_key": normalized_key(source["id"], str(ext_id or ""), url, title, company),
        "source_id": source["id"],
        "source_kind": source["kind"],
        "source_url": source["url"],
        "source_authority": source.get("authority"),
        "external_id": str(ext_id or ""),
        "title": title or "",
        "organization": company or "",
        "location": location or "",
        "opportunity_url": url or "",
        "published_at": published_at,
        "matched_profile_keywords": hits,
        "matched_commercial_keywords": commercial_hits,
        "matched_geo_keywords": geo_hits,
        "target_geo_bucket": geo,
        "raw_fit_score": min(100, score),
        "route_state": "TO_VERIFY",
        "verification_state": "RAW_PUBLIC_SIGNAL",
    }


def parse_remoteok(source, config):
    raw, _ = fetch_bytes(source["url"])
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    rows = []
    for obj in payload if isinstance(payload, list) else []:
        if not isinstance(obj, dict) or not obj.get("position"):
            continue
        row = build_row(
            source,
            obj.get("id") or obj.get("slug"),
            str(obj.get("position") or ""),
            str(obj.get("company") or ""),
            str(obj.get("location") or ""),
            str(obj.get("url") or obj.get("apply_url") or ""),
            obj.get("date"),
            strip_html(str(obj.get("description") or "")),
            " ".join(str(x) for x in (obj.get("tags") or [])),
            config,
            remote_source=True,
        )
        if row:
            rows.append(row)
    return rows


def parse_remotive(source, config):
    raw, _ = fetch_bytes(source["url"])
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    rows = []
    for obj in payload.get("jobs", []) if isinstance(payload, dict) else []:
        row = build_row(
            source,
            obj.get("id"),
            str(obj.get("title") or ""),
            str(obj.get("company_name") or ""),
            str(obj.get("candidate_required_location") or ""),
            str(obj.get("url") or ""),
            obj.get("publication_date"),
            strip_html(str(obj.get("description") or "")),
            " ".join(str(x) for x in (obj.get("tags") or [])) + " " + str(obj.get("job_type") or ""),
            config,
            remote_source=True,
        )
        if row:
            rows.append(row)
    return rows


def parse_arbeitnow(source, config):
    raw, _ = fetch_bytes(source["url"])
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    rows = []
    for obj in payload.get("data", []) if isinstance(payload, dict) else []:
        remote_source = bool(obj.get("remote")) or "remote" in str(obj.get("title") or "").lower()
        created = obj.get("created_at")
        if isinstance(created, (int, float)):
            try:
                created = dt.datetime.fromtimestamp(created, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")
            except (ValueError, OSError, OverflowError):
                created = str(created)
        row = build_row(
            source,
            obj.get("slug"),
            str(obj.get("title") or ""),
            str(obj.get("company_name") or ""),
            str(obj.get("location") or ""),
            str(obj.get("url") or ""),
            created,
            strip_html(str(obj.get("description") or "")),
            " ".join(str(x) for x in (obj.get("tags") or [])) + " " + " ".join(str(x) for x in (obj.get("job_types") or [])),
            config,
            remote_source=remote_source,
        )
        if row:
            rows.append(row)
    return rows


def parse_himalayas(source, config):
    raw, _ = fetch_bytes(source["url"])
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    rows = []
    for obj in payload.get("jobs", []) if isinstance(payload, dict) else []:
        locations = obj.get("locationRestrictions") or obj.get("locations") or obj.get("location") or []
        if isinstance(locations, list):
            location = ", ".join(str(x) for x in locations)
        else:
            location = str(locations or "")
        tags_obj = obj.get("techStack") or obj.get("skills") or obj.get("categories") or []
        tags = " ".join(str(x) for x in tags_obj) if isinstance(tags_obj, list) else str(tags_obj or "")
        company = str(obj.get("companyName") or (obj.get("company") or {}).get("name") if isinstance(obj.get("company"), dict) else obj.get("company") or "")
        url = str(obj.get("url") or obj.get("applicationUrl") or obj.get("applyUrl") or obj.get("jobUrl") or "")
        row = build_row(
            source,
            obj.get("id") or obj.get("slug"),
            str(obj.get("title") or ""),
            company,
            location,
            url,
            obj.get("publishedAt") or obj.get("createdAt") or obj.get("updatedAt"),
            strip_html(str(obj.get("description") or obj.get("descriptionHtml") or "")),
            tags + " " + str(obj.get("employmentType") or ""),
            config,
            remote_source=True,
        )
        if row:
            rows.append(row)
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
        row = build_row(source, "", title, creator, "", link, pub or None, description, "", config, remote_source=True)
        if row:
            rows.append(row)
    return rows


def parse_source(source, config):
    parsers = {
        "remoteok_json": parse_remoteok,
        "remotive_json": parse_remotive,
        "arbeitnow_json": parse_arbeitnow,
        "himalayas_json": parse_himalayas,
        "rss": parse_rss,
    }
    parser = parsers.get(source.get("kind"))
    if not parser:
        raise ValueError(f"Unsupported source kind: {source.get('kind')}")
    return parser(source, config)


def extract_page_title(text):
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    return strip_html(match.group(1))[:240] if match else ""


def scan_watch_pages(config, watch_state):
    now = dt.datetime.now(dt.timezone.utc)
    interval = int(config.get("policy", {}).get("official_watch_pages_interval_minutes", 60))
    if interval >= 60 and now.minute >= 15:
        return [], watch_state, []
    signals, errors = [], []
    pages = [p for p in config.get("official_watch_pages", []) if p.get("enabled", True) and p.get("url")]
    watch_terms = config.get("profile_keywords", []) + config.get("commercial_keywords", []) + ["careers", "jobs", "dissemination", "communication", "website"]
    for page in pages:
        try:
            raw, _ = fetch_bytes(page["url"])
            text = raw.decode("utf-8", errors="replace")
            cleaned = strip_html(text)
            digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
            key = page.get("id") or hashlib.sha256(page["url"].encode("utf-8")).hexdigest()[:20]
            previous = watch_state.get(key, {})
            hits = keyword_hits(cleaned, watch_terms)
            changed = previous.get("content_hash") not in (None, digest)
            first_relevant = previous.get("content_hash") is None and bool(hits)
            if (changed or first_relevant) and hits:
                row = build_row(
                    {"id": "official_watch", "kind": "official_page_change", "url": page["url"], "authority": "OFFICIAL_PAGE"},
                    key,
                    extract_page_title(text) or page.get("name", "Official page"),
                    page.get("organization", ""),
                    page.get("country", ""),
                    page["url"],
                    None,
                    cleaned[:12000],
                    " ".join(hits[:40]),
                    config,
                    remote_source=False,
                )
                if row:
                    row["verification_state"] = "OFFICIAL_PAGE_SIGNAL"
                    row["watch_category"] = page.get("category", "official")
                    signals.append(row)
            watch_state[key] = {"url": page["url"], "content_hash": digest, "checked_at": now_utc()}
        except Exception as exc:
            errors.append({"source_id": page.get("id", "official_watch"), "error": f"{type(exc).__name__}: {exc}"[:500]})
    return signals, watch_state, errors


def main():
    config = load_json(CONFIG_PATH, {})
    latest = load_json(LATEST_PATH, {"schema_version": "1.1", "signals": []})
    state = load_json(STATE_PATH, {"schema_version": "1.1", "runs": 0, "total_new_signals": 0})
    watch_state = load_json(WATCH_STATE_PATH, {})
    existing = {x.get("signal_key"): x for x in latest.get("signals", []) if x.get("signal_key")}
    enabled = [s for s in config.get("sources", []) if s.get("enabled", True)]
    fetched_at = now_utc()
    all_rows, errors, source_counts = [], [], {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(10, len(enabled)))) as pool:
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
            prior["matched_commercial_keywords"] = sorted(set(prior.get("matched_commercial_keywords", [])) | set(row.get("matched_commercial_keywords", [])))
            prior["matched_geo_keywords"] = sorted(set(prior.get("matched_geo_keywords", [])) | set(row.get("matched_geo_keywords", [])))
            prior["raw_fit_score"] = max(int(prior.get("raw_fit_score", 0)), int(row.get("raw_fit_score", 0)))

    max_latest = int(config.get("policy", {}).get("max_latest_signals", 2500))
    merged = sorted(existing.values(), key=lambda x: (int(x.get("raw_fit_score", 0)), x.get("discovered_at") or ""), reverse=True)[:max_latest]
    latest_out = {
        "schema_version": "1.1",
        "updated_at": fetched_at,
        "mode": "PUBLIC_HIGH_FREQUENCY_DISCOVERY_ONLY",
        "no_outreach": True,
        "sources_enabled": [s["id"] for s in enabled],
        "new_signals_this_run": len(new_rows),
        "signal_count": len(merged),
        "errors": errors,
        "signals": merged,
    }
    state_out = {
        "schema_version": "1.1",
        "updated_at": fetched_at,
        "runs": int(state.get("runs", 0)) + 1,
        "last_run_new_signals": len(new_rows),
        "last_run_matched_signals": len(all_rows),
        "total_new_signals": int(state.get("total_new_signals", 0)) + len(new_rows),
        "source_counts": source_counts,
        "errors": errors,
    }

    append_jsonl(LEDGER_PATH, new_rows)
    write_json(LATEST_PATH, latest_out)
    write_json(STATE_PATH, state_out)
    write_json(WATCH_STATE_PATH, watch_state)
    print(json.dumps({"fetched_at": fetched_at, "new_signals": len(new_rows), "matched": len(all_rows), "source_counts": source_counts, "errors": errors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
