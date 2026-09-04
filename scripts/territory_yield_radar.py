#!/usr/bin/env python3
import datetime as dt
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "config/search-territory-frontier.json"
POLICY = ROOT / "config/adaptive-search-policy.json"
DISCOVERY = ROOT / "views/high-frequency-discovery-latest.json"
CROSS = ROOT / "views/cross-signal-opportunities.json"
SENT = ROOT / "views/global-sent-email-index.json"
OUT = ROOT / "views/territory-yield-radar.json"
STATE = ROOT / "metrics/territory-yield-radar-state.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def parse_time(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def territory_catalog(frontier):
    catalog = []
    aliases = {}
    for country_key, country_name in (("spain", "Spain"), ("italy", "Italy")):
        data = frontier.get(country_key, {})
        for region, provinces in data.get("regions", {}).items():
            for province in provinces:
                key = f"{country_name}|{region}|{province}"
                catalog.append({"key": key, "country": country_name, "region": region, "province": province})
                aliases.setdefault(norm(province), []).append(key)
                aliases.setdefault(norm(region), []).append(key)
        for cluster in data.get("high_density_clusters", []):
            aliases.setdefault(norm(cluster), [])
    return catalog, aliases


def infer_territory(text, catalog):
    low = f" {norm(text)} "
    # Province first: most specific.
    matches = []
    for item in catalog:
        p = norm(item["province"])
        r = norm(item["region"])
        if p and re.search(rf"(?<!\w){re.escape(p)}(?!\w)", low):
            matches.append((3, item))
        elif r and re.search(rf"(?<!\w){re.escape(r)}(?!\w)", low):
            matches.append((2, item))
    if matches:
        matches.sort(key=lambda x: (x[0], len(x[1]["province"])), reverse=True)
        return matches[0][1]
    if any(x in low for x in (" spain ", " españa ", " espana ")):
        return {"key": "Spain|UNRESOLVED|UNRESOLVED", "country": "Spain", "region": "UNRESOLVED", "province": "UNRESOLVED"}
    if any(x in low for x in (" italy ", " italia ")):
        return {"key": "Italy|UNRESOLVED|UNRESOLVED", "country": "Italy", "region": "UNRESOLVED", "province": "UNRESOLVED"}
    return None


def get_explicit_territory(record):
    t = record.get("territory") or {}
    if isinstance(t, dict) and (t.get("province") or t.get("region")):
        country = t.get("country") or record.get("country") or "UNRESOLVED"
        if country == "ES": country = "Spain"
        if country == "IT": country = "Italy"
        region = t.get("region") or "UNRESOLVED"
        province = t.get("province") or "UNRESOLVED"
        return {"key": f"{country}|{region}|{province}", "country": country, "region": region, "province": province}
    return None


def score_area(m, prior):
    scans = max(1, m["signals"])
    verified_rate = m["verified"] / scans
    high_fit_rate = m["high_fit"] / scans
    hot_rate = m["hot"] / scans
    ready_rate = m["ready"] / scans
    send_rate = m["sends"] / max(1, m["ready"])
    reply_rate = m["positive_replies"] / max(1, m["sends"])
    noise_rate = (m["stale"] + m["duplicates"] + m["rejected"]) / scans

    # Quality-sensitive score. Responses are rare, so use Bayesian smoothing.
    reply_smoothed = (m["positive_replies"] + 0.5) / (m["sends"] + 5.0)
    volume_confidence = min(1.0, math.log1p(m["signals"]) / math.log(21))
    base = (
        18 * verified_rate
        + 18 * high_fit_rate
        + 22 * hot_rate
        + 18 * ready_rate
        + 10 * send_rate
        + 12 * reply_smoothed
        - 12 * min(1.0, noise_rate)
    )
    confidence_adjusted = base * (0.55 + 0.45 * volume_confidence)
    # Preserve useful historical signal without freezing the ranking.
    previous_score = float(prior.get("score", 0))
    score = 0.72 * confidence_adjusted + 0.28 * previous_score
    return round(max(0.0, min(100.0, score)), 2)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    frontier = load(FRONTIER, {})
    policy = load(POLICY, {})
    discovery = load(DISCOVERY, {"signals": []})
    cross = load(CROSS, {"opportunities": []})
    sent = load(SENT, {"messages": []})
    old_state = load(STATE, {"areas": {}})
    catalog, _ = territory_catalog(frontier)

    metrics = defaultdict(lambda: Counter({
        "signals": 0, "verified": 0, "high_fit": 0, "hot": 0, "ready": 0,
        "sends": 0, "positive_replies": 0, "duplicates": 0, "stale": 0, "rejected": 0
    }))
    org_area = {}

    for s in discovery.get("signals", []):
        text = " ".join(str(s.get(k) or "") for k in ("location", "title", "organization", "matched_geo_keywords"))
        t = infer_territory(text, catalog)
        if not t:
            continue
        m = metrics[t["key"]]
        m["signals"] += 1
        if s.get("verification_state") in {"OFFICIAL_PAGE_SIGNAL", "VERIFIED_JOB", "VERIFIED"}:
            m["verified"] += 1
        if int(s.get("raw_fit_score", 0)) >= 70:
            m["high_fit"] += 1

    opportunities = cross.get("opportunities", [])
    for o in opportunities if isinstance(opportunities, list) else []:
        t = get_explicit_territory(o)
        if not t:
            country = o.get("country")
            if country in {"ES", "Spain"}:
                t = {"key": "Spain|UNRESOLVED|UNRESOLVED", "country": "Spain", "region": "UNRESOLVED", "province": "UNRESOLVED"}
            elif country in {"IT", "Italy"}:
                t = {"key": "Italy|UNRESOLVED|UNRESOLVED", "country": "Italy", "region": "UNRESOLVED", "province": "UNRESOLVED"}
        if not t:
            continue
        key = t["key"]
        org_key = o.get("canonical_identity_key")
        if org_key:
            org_area[org_key] = t
        m = metrics[key]
        m["verified"] += 1
        total = float((o.get("scores") or {}).get("total", 0))
        if total >= 75:
            m["high_fit"] += 1
        tier = o.get("priority_tier")
        if tier in {"HOT", "HOT+"}:
            m["hot"] += 1
        action = o.get("next_best_action")
        if action in {"AUTO_EMAIL_NOW", "QUEUE_FOR_SEND_WINDOW"}:
            m["ready"] += 1
        if action == "DO_NOT_CONTACT_DUPLICATE":
            m["duplicates"] += 1
        if action == "HOLD_STALE_OR_UNCERTAIN":
            m["stale"] += 1

    # Join sent mail to known opportunity territory when possible.
    for msg in sent.get("messages", []):
        org_key = msg.get("canonical_identity_key")
        t = org_area.get(org_key)
        if t:
            metrics[t["key"]]["sends"] += 1

    old_areas = old_state.get("areas", {})
    rows = []
    low_yield_threshold = 18.0
    strong_threshold = 45.0
    cooldown_hours = 18
    max_harvest_cycles = 4

    all_keys = {x["key"] for x in catalog} | set(metrics.keys())
    for key in all_keys:
        parts = key.split("|", 2)
        country, region, province = parts if len(parts) == 3 else (parts[0], "UNRESOLVED", "UNRESOLVED")
        m = metrics[key]
        prior = old_areas.get(key, {})
        score = score_area(m, prior)
        consecutive_low = int(prior.get("consecutive_low_yield_cycles", 0))
        harvest_cycles = int(prior.get("harvest_cycles", 0))
        cooldown_until = parse_time(prior.get("cooldown_until"))
        mode = prior.get("mode", "EXPLORATION")

        if score >= strong_threshold and m["hot"] + m["ready"] > 0:
            consecutive_low = 0
            harvest_cycles += 1
            if harvest_cycles >= max_harvest_cycles:
                mode = "COOLDOWN"
                cooldown_until = now + dt.timedelta(hours=cooldown_hours)
                harvest_cycles = 0
            else:
                mode = "HARVEST"
        elif score < low_yield_threshold:
            consecutive_low += 1
            harvest_cycles = 0
            if consecutive_low >= 3:
                mode = "ROTATE_OUT"
                cooldown_until = now + dt.timedelta(hours=cooldown_hours)
            else:
                mode = "EXPLORATION"
        else:
            consecutive_low = max(0, consecutive_low - 1)
            harvest_cycles = 0
            mode = "EXPLORATION"

        if cooldown_until and now >= cooldown_until:
            mode = "REVISIT"
            cooldown_until = None

        rows.append({
            "area_key": key,
            "country": country,
            "region": region,
            "province": province,
            "score": score,
            "mode": mode,
            "harvest_cycles": harvest_cycles,
            "consecutive_low_yield_cycles": consecutive_low,
            "cooldown_until": cooldown_until.isoformat().replace("+00:00", "Z") if cooldown_until else None,
            "metrics": dict(m),
        })

    mode_priority = {"HARVEST": 5, "REVISIT": 4, "EXPLORATION": 3, "ROTATE_OUT": 2, "COOLDOWN": 1}
    rows.sort(key=lambda r: (mode_priority.get(r["mode"], 0), r["score"], r["metrics"].get("hot", 0), r["metrics"].get("signals", 0)), reverse=True)
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx

    harvest = [r for r in rows if r["mode"] == "HARVEST"][:12]
    revisit = [r for r in rows if r["mode"] in {"REVISIT", "EXPLORATION"}][:20]
    output = {
        "schema_version": "1.0",
        "updated_at": now_utc(),
        "strategy": "ADAPTIVE_TERRITORY_HARVEST_ROTATE_REVISIT",
        "policy": {
            "exploration_budget_pct": int(frontier.get("policy", {}).get("exploration_budget_pct", 25)),
            "adaptive_exploitation_budget_pct": int(frontier.get("policy", {}).get("adaptive_exploitation_budget_pct", 75)),
            "harvest_score_threshold": strong_threshold,
            "low_yield_score_threshold": low_yield_threshold,
            "harvest_cycles_before_cooldown": max_harvest_cycles,
            "cooldown_hours": cooldown_hours,
            "principle": "Exploit high-yield areas until marginal yield falls or harvest cycle cap is reached; rotate to other areas; revisit cooled areas cyclically. Never permanently abandon Spain/Italy coverage."
        },
        "top_areas": rows[:30],
        "harvest_now": harvest,
        "explore_or_revisit_next": revisit,
        "areas": rows,
    }
    state = {
        "schema_version": "1.0",
        "updated_at": output["updated_at"],
        "areas": {r["area_key"]: {k: r[k] for k in ("score", "mode", "harvest_cycles", "consecutive_low_yield_cycles", "cooldown_until")} for r in rows},
    }
    save(OUT, output)
    save(STATE, state)
    print(json.dumps({"updated_at": output["updated_at"], "top": [{"rank": r["rank"], "area": r["area_key"], "score": r["score"], "mode": r["mode"]} for r in rows[:10]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
