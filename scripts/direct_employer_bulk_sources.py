#!/usr/bin/env python3
import datetime as dt
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CFG = ROOT / "config/direct-employer-bulk-sources.json"
PROFILE_CFG = ROOT / "config/high-frequency-discovery-sources.json"
LATEST = ROOT / "views/high-frequency-discovery-latest.json"
STATE = ROOT / "metrics/direct-employer-bulk-sources-state.json"
USER_AGENT = "VDS-Commercial-Intelligence/1.3 (+https://www.visualdesignstudio.es/)"


def now():
    return dt.datetime.now(dt.timezone.utc)


def stamp(t=None):
    return (t or now()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=35) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def clean(value):
    text = str(value or "")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def term_present(text, term):
    low = (text or "").lower()
    t = (term or "").lower().strip()
    if not t:
        return False
    if len(t) <= 3 or re.fullmatch(r"[a-z0-9+#.\-]{1,4}", t):
        return re.search(rf"(?<![\w]){re.escape(t)}(?![\w])", low) is not None
    return t in low


def hits(text, terms):
    return sorted({t for t in terms if term_present(text, t)})


def signal_key(source, ext_id, url, title, company):
    source_identity = source.get("dedup_source_id") or source.get("id") or "source"
    raw = f"{source_identity}|{ext_id}|{url}|{title}|{company}".lower().strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def geo_bucket(text, country="", remote=False):
    c = (country or "").upper().strip()
    low = (text or "").lower()
    if c == "ES" or any(x in low for x in ["spain", "españa", "barcelona", "madrid", "valencia", "málaga", "malaga", "bilbao", "sevilla", "zaragoza", "alicante", "catalonia", "cataluña"]):
        return "SPAIN_OR_INCLUDES_SPAIN"
    if c == "IT" or any(x in low for x in ["italy", "italia", "milano", "milan", "roma", "rome", "torino", "turin", "bologna", "firenze", "florence", "napoli", "veneto", "lombardia"]):
        return "ITALY_OR_INCLUDES_ITALY"
    if c in {"PT", "FR", "DE", "NL", "BE", "AT", "IE", "LU", "DK", "SE", "FI", "PL", "CZ", "SK", "SI", "HR", "RO", "BG", "GR", "EE", "LV", "LT", "HU", "CY", "MT"}:
        return "EU_REMOTE_TO_VERIFY" if remote else "EU_GEO_TO_VERIFY"
    if any(x in low for x in ["europe", "european union", "emea", "eu remote", "europe only"]):
        return "EU_REMOTE_TO_VERIFY"
    if any(x in low for x in ["worldwide", "anywhere", "global remote", "work from anywhere"]):
        return "WORLDWIDE_REMOTE"
    return "REMOTE_TO_VERIFY" if remote else "GEO_TO_VERIFY"


def make_row(source, ext_id, title, company, location, country, url, apply_url, published, description, tags, remote, profile, extra=None):
    title = str(title or "")
    company = str(company or "")
    location = str(location or "")
    description = clean(description)
    tags = str(tags or "")
    combined = " ".join([title, company, location, description, tags])
    profile_hits = hits(combined, profile.get("profile_keywords", []))
    if not profile_hits:
        return None
    commercial_hits = hits(combined, profile.get("commercial_keywords", []))
    geo_hits = hits(combined, profile.get("remote_geo_keywords", []))
    bucket = geo_bucket(combined, country=country, remote=remote)
    score = 28 + min(48, len(profile_hits) * 7) + min(14, len(commercial_hits) * 4)
    if bucket in {"SPAIN_OR_INCLUDES_SPAIN", "ITALY_OR_INCLUDES_ITALY", "WORLDWIDE_REMOTE"}:
        score += 10
    elif bucket == "EU_REMOTE_TO_VERIFY":
        score += 7
    if source.get("authority") == "EMPLOYER_DIRECT_ATS_CAREER_INDEX":
        score += 4
    row = {
        "signal_key": signal_key(source, str(ext_id or ""), apply_url or url, title, company),
        "source_id": source["id"],
        "source_kind": source["kind"],
        "source_url": source["url"],
        "source_authority": source.get("authority"),
        "source_dedup_family": source.get("dedup_source_id"),
        "external_id": str(ext_id or ""),
        "title": title,
        "organization": company,
        "location": location,
        "country": country or None,
        "opportunity_url": url or apply_url or "",
        "authoritative_apply_url": apply_url or None,
        "published_at": published,
        "matched_profile_keywords": profile_hits,
        "matched_commercial_keywords": commercial_hits,
        "matched_geo_keywords": geo_hits,
        "target_geo_bucket": bucket,
        "raw_fit_score": min(100, score),
        "route_state": "ATS_APPLY_TO_VERIFY" if apply_url else "TO_VERIFY",
        "verification_state": "EMPLOYER_DIRECT_PUBLIC_SIGNAL" if source.get("authority") == "EMPLOYER_DIRECT_ATS_CAREER_INDEX" else "RAW_PUBLIC_SIGNAL",
        "discovered_at": stamp(),
        "last_seen_at": stamp()
    }
    if extra:
        row.update({k: v for k, v in extra.items() if v not in (None, "", [], {})})
    return row


def parse_jobopportunities(source, profile):
    payload = fetch_json(source["url"])
    out = []
    for j in payload.get("data", []) if isinstance(payload, dict) else []:
        country = str(j.get("country") or "")
        location = str(j.get("location") or "")
        if not location:
            location = ", ".join(x for x in [str(j.get("city") or ""), country] if x)
        remote_value = str(j.get("remote") or "").lower()
        remote = remote_value in {"remote", "hybrid", "true", "1"}
        apply_url = str(j.get("apply_url") or "")
        tags = " ".join([
            str(j.get("category") or ""),
            str(j.get("employment_type") or ""),
            str(j.get("seniority") or ""),
            str(j.get("source") or ""),
            str(j.get("source_type") or "")
        ])
        row = make_row(
            source,
            j.get("id") or j.get("slug"),
            j.get("title"),
            j.get("company"),
            location,
            country,
            apply_url,
            apply_url,
            j.get("posted_at"),
            j.get("description") or "",
            tags,
            remote,
            profile,
            extra={
                "last_verified_at": j.get("last_verified_at"),
                "upstream_source": j.get("source"),
                "upstream_source_type": j.get("source_type"),
                "remote_published_or_inferred": j.get("remote"),
                "remote_inferred": j.get("remote_inferred"),
                "employment_type": j.get("employment_type"),
                "field_sources": j.get("field_sources")
            }
        )
        if row:
            out.append(row)
    return out


def parse_remotejobs_org(source, profile):
    payload = fetch_json(source["url"])
    out = []
    for j in payload.get("data", []) if isinstance(payload, dict) else []:
        company_obj = j.get("company") or {}
        company = company_obj.get("name") if isinstance(company_obj, dict) else str(company_obj or "")
        website = company_obj.get("website") if isinstance(company_obj, dict) else None
        location = str(j.get("location") or "")
        row = make_row(
            source,
            j.get("id"),
            j.get("title"),
            company,
            location,
            "",
            j.get("url"),
            j.get("apply_url"),
            j.get("posted_at"),
            j.get("description") or "",
            " ".join([str((j.get("category") or {}).get("name") if isinstance(j.get("category"), dict) else j.get("category") or ""), str(j.get("type") or "")]),
            True,
            profile,
            extra={"employer_website": website, "job_type": j.get("type"), "original_language": j.get("original_language")}
        )
        if row:
            out.append(row)
    return out


def parse_nomado24(source, profile):
    payload = fetch_json(source["url"])
    out = []
    for j in payload.get("data", []) if isinstance(payload, dict) else []:
        location = str(j.get("location") or "")
        remote = bool(j.get("remote")) or str(j.get("workArrangement") or "").lower() in {"remote", "hybrid"}
        tags_obj = j.get("tags") or []
        tags = " ".join(str(x) for x in tags_obj) if isinstance(tags_obj, list) else str(tags_obj or "")
        row = make_row(
            source,
            j.get("id") or j.get("slug"),
            j.get("title"),
            j.get("companyName") or j.get("company"),
            location,
            str(j.get("country") or ""),
            j.get("url"),
            j.get("url"),
            j.get("publishedAt"),
            j.get("description") or "",
            tags + " " + str(j.get("workArrangement") or ""),
            remote,
            profile,
            extra={"language": j.get("language"), "work_arrangement": j.get("workArrangement"), "upstream_source": j.get("source")}
        )
        if row:
            out.append(row)
    return out


def due(source, state, current):
    last = (state.get("sources", {}).get(source["id"], {}) or {}).get("last_poll_at")
    if not last:
        return True
    try:
        t = dt.datetime.fromisoformat(last.replace("Z", "+00:00"))
        return (current - t).total_seconds() >= int(source.get("min_poll_minutes", 15)) * 60
    except Exception:
        return True


def main():
    cfg = load(SOURCE_CFG, {"sources": [], "policy": {}})
    profile = load(PROFILE_CFG, {})
    latest = load(LATEST, {"schema_version": "1.1", "signals": []})
    state = load(STATE, {"schema_version": "1.0", "sources": {}, "runs": 0})
    current = now()
    existing = {x.get("signal_key"): x for x in latest.get("signals", []) if x.get("signal_key")}
    errors = []
    polled = []
    added = 0
    matched = 0
    parsers = {
        "jobopportunities_json": parse_jobopportunities,
        "remotejobs_org_json": parse_remotejobs_org,
        "nomado24_json": parse_nomado24
    }
    host_last_request = {}
    host_delays = cfg.get("policy", {}).get("host_rate_limit_seconds", {})

    for source in cfg.get("sources", []):
        if not source.get("enabled", True) or not due(source, state, current):
            continue
        parser = parsers.get(source.get("kind"))
        if not parser:
            continue
        host = urllib.parse.urlparse(source["url"]).netloc
        delay = float(host_delays.get(host, 0.0))
        prior_request = host_last_request.get(host)
        if prior_request and delay > 0:
            elapsed = time.monotonic() - prior_request
            if elapsed < delay:
                time.sleep(delay - elapsed)
        try:
            rows = parser(source, profile)
            host_last_request[host] = time.monotonic()
            seen_now = 0
            for row in rows:
                key = row["signal_key"]
                if key in existing:
                    prior = existing[key]
                    prior["last_seen_at"] = stamp(current)
                    prior["raw_fit_score"] = max(int(prior.get("raw_fit_score", 0)), int(row.get("raw_fit_score", 0)))
                    prior["matched_profile_keywords"] = sorted(set(prior.get("matched_profile_keywords", [])) | set(row.get("matched_profile_keywords", [])))
                    prior["matched_commercial_keywords"] = sorted(set(prior.get("matched_commercial_keywords", [])) | set(row.get("matched_commercial_keywords", [])))
                    if row.get("authoritative_apply_url"):
                        prior["authoritative_apply_url"] = row["authoritative_apply_url"]
                    prior.setdefault("discovery_query_sources", [])
                    if source["id"] not in prior["discovery_query_sources"]:
                        prior["discovery_query_sources"].append(source["id"])
                else:
                    row["discovery_query_sources"] = [source["id"]]
                    existing[key] = row
                    added += 1
                seen_now += 1
            matched += seen_now
            state.setdefault("sources", {})[source["id"]] = {
                "last_poll_at": stamp(current),
                "last_count": seen_now,
                "last_error": None,
                "min_poll_minutes": source.get("min_poll_minutes")
            }
            polled.append({"source_id": source["id"], "signals": seen_now})
        except Exception as exc:
            host_last_request[host] = time.monotonic()
            err = {"source_id": source["id"], "error": f"{type(exc).__name__}: {exc}"[:500]}
            errors.append(err)
            state.setdefault("sources", {})[source["id"]] = {
                "last_poll_at": stamp(current),
                "last_count": 0,
                "last_error": err["error"],
                "min_poll_minutes": source.get("min_poll_minutes")
            }

    max_latest = int(cfg.get("policy", {}).get("max_latest_signals", profile.get("policy", {}).get("max_latest_signals", 5000)))
    signals = list(existing.values())
    signals.sort(key=lambda x: (int(x.get("raw_fit_score", 0)), x.get("published_at") or "", x.get("last_seen_at") or ""), reverse=True)
    run_summary = {"polled": polled, "new_signals": added, "matched_signals": matched, "errors": errors}
    latest.update({
        "updated_at": stamp(current),
        "signals": signals[:max_latest],
        "direct_employer_bulk_last_run": run_summary
    })
    save(LATEST, latest)
    state.update({
        "updated_at": stamp(current),
        "runs": int(state.get("runs", 0)) + 1,
        "last_run": run_summary
    })
    save(STATE, state)
    print(json.dumps(run_summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
