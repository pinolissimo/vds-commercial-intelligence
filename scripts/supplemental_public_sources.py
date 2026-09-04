#!/usr/bin/env python3
import datetime as dt
import hashlib
import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CFG = ROOT / "config/supplemental-public-sources.json"
PROFILE_CFG = ROOT / "config/high-frequency-discovery-sources.json"
LATEST = ROOT / "views/high-frequency-discovery-latest.json"
STATE = ROOT / "metrics/supplemental-public-sources-state.json"
USER_AGENT = "VDS-Commercial-Intelligence/1.2 (+https://www.visualdesignstudio.es/)"


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
    with urllib.request.urlopen(req, timeout=30) as resp:
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


def signal_key(source_id, ext_id, url, title, company):
    raw = f"{source_id}|{ext_id}|{url}|{title}|{company}".lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def geo_bucket(text):
    low = (text or "").lower()
    if any(x in low for x in ["spain", "españa", "barcelona", "madrid", "valencia", "málaga", "malaga", "bilbao"]):
        return "SPAIN_OR_INCLUDES_SPAIN"
    if any(x in low for x in ["italy", "italia", "milano", "milan", "roma", "rome", "torino", "bologna", "firenze", "napoli"]):
        return "ITALY_OR_INCLUDES_ITALY"
    if any(x in low for x in ["europe", "european", "emea", "eu remote"]):
        return "EU_REMOTE_TO_VERIFY"
    if any(x in low for x in ["worldwide", "anywhere", "global remote"]):
        return "WORLDWIDE_REMOTE"
    return "REMOTE_TO_VERIFY"


def make_row(source, ext_id, title, company, location, url, apply_url, published, description, tags, profile):
    combined = " ".join([title, company, location, description, tags])
    profile_hits = hits(combined, profile.get("profile_keywords", []))
    if not profile_hits:
        return None
    commercial_hits = hits(combined, profile.get("commercial_keywords", []))
    geo_hits = hits(combined, profile.get("remote_geo_keywords", []))
    bucket = geo_bucket(combined)
    score = 28 + min(48, len(profile_hits) * 7) + min(14, len(commercial_hits) * 4)
    if bucket in {"SPAIN_OR_INCLUDES_SPAIN", "ITALY_OR_INCLUDES_ITALY", "WORLDWIDE_REMOTE"}:
        score += 10
    elif bucket == "EU_REMOTE_TO_VERIFY":
        score += 7
    return {
        "signal_key": signal_key(source["id"], str(ext_id or ""), url, title, company),
        "source_id": source["id"],
        "source_kind": source["kind"],
        "source_url": source["url"],
        "source_authority": source.get("authority"),
        "external_id": str(ext_id or ""),
        "title": title,
        "organization": company,
        "location": location,
        "opportunity_url": url,
        "authoritative_apply_url": apply_url or None,
        "published_at": published,
        "matched_profile_keywords": profile_hits,
        "matched_commercial_keywords": commercial_hits,
        "matched_geo_keywords": geo_hits,
        "target_geo_bucket": bucket,
        "raw_fit_score": min(100, score),
        "route_state": "ATS_APPLY_TO_VERIFY" if apply_url else "TO_VERIFY",
        "verification_state": "RAW_PUBLIC_SIGNAL",
        "discovered_at": stamp(),
        "last_seen_at": stamp()
    }


def parse_remote_landers(source, profile):
    payload = fetch_json(source["url"])
    out = []
    for j in payload.get("jobs", []) if isinstance(payload, dict) else []:
        row = make_row(
            source,
            j.get("slug"),
            str(j.get("title") or ""),
            str(j.get("company") or ""),
            str(j.get("location") or ""),
            str(j.get("url") or ""),
            str(j.get("applyUrl") or ""),
            j.get("postedDate"),
            "",
            " ".join(str(x) for x in (j.get("subtags") or [])) + " " + str(j.get("type") or "") + " " + str(j.get("category") or ""),
            profile
        )
        if row:
            row["employer_website"] = j.get("companyWebsite")
            out.append(row)
    return out


def parse_jobicy(source, profile):
    payload = fetch_json(source["url"])
    out = []
    for j in payload.get("jobs", []) if isinstance(payload, dict) else []:
        industries = j.get("jobIndustry") or []
        types = j.get("jobType") or []
        tags = " ".join(str(x) for x in industries + types) if isinstance(industries, list) and isinstance(types, list) else ""
        row = make_row(
            source,
            j.get("id") or j.get("jobSlug"),
            str(j.get("jobTitle") or ""),
            str(j.get("companyName") or ""),
            str(j.get("jobGeo") or ""),
            str(j.get("url") or ""),
            "",
            j.get("pubDate"),
            clean(j.get("jobDescription") or j.get("jobExcerpt") or ""),
            tags,
            profile
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
        return (current - t).total_seconds() >= int(source.get("min_poll_minutes", 60)) * 60
    except Exception:
        return True


def main():
    cfg = load(SOURCE_CFG, {"sources": []})
    profile = load(PROFILE_CFG, {})
    latest = load(LATEST, {"schema_version": "1.1", "signals": []})
    state = load(STATE, {"schema_version": "1.0", "sources": {}, "runs": 0})
    current = now()
    existing = {x.get("signal_key"): x for x in latest.get("signals", []) if x.get("signal_key")}
    errors = []
    polled = []
    added = 0

    parsers = {"remote_landers_json": parse_remote_landers, "jobicy_json": parse_jobicy}
    for source in cfg.get("sources", []):
        if not source.get("enabled", True) or not due(source, state, current):
            continue
        parser = parsers.get(source.get("kind"))
        if not parser:
            continue
        try:
            rows = parser(source, profile)
            seen_now = 0
            for row in rows:
                key = row["signal_key"]
                if key in existing:
                    existing[key]["last_seen_at"] = stamp(current)
                    if row.get("authoritative_apply_url"):
                        existing[key]["authoritative_apply_url"] = row["authoritative_apply_url"]
                else:
                    existing[key] = row
                    added += 1
                seen_now += 1
            state.setdefault("sources", {})[source["id"]] = {
                "last_poll_at": stamp(current),
                "last_count": seen_now,
                "last_error": None,
                "min_poll_minutes": source.get("min_poll_minutes")
            }
            polled.append({"source_id": source["id"], "signals": seen_now})
        except Exception as exc:
            errors.append({"source_id": source["id"], "error": f"{type(exc).__name__}: {exc}"[:500]})
            state.setdefault("sources", {})[source["id"]] = {
                "last_poll_at": stamp(current),
                "last_count": 0,
                "last_error": errors[-1]["error"],
                "min_poll_minutes": source.get("min_poll_minutes")
            }

    max_latest = int(profile.get("policy", {}).get("max_latest_signals", 2500))
    signals = list(existing.values())
    signals.sort(key=lambda x: (x.get("published_at") or "", x.get("last_seen_at") or ""), reverse=True)
    latest.update({
        "updated_at": stamp(current),
        "signals": signals[:max_latest],
        "supplemental_last_run": {"polled": polled, "new_signals": added, "errors": errors}
    })
    save(LATEST, latest)
    state.update({"updated_at": stamp(current), "runs": int(state.get("runs", 0)) + 1, "last_run": latest["supplemental_last_run"]})
    save(STATE, state)
    print(json.dumps(latest["supplemental_last_run"], ensure_ascii=False))


if __name__ == "__main__":
    main()
