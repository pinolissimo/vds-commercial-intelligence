#!/usr/bin/env python3
import datetime as dt
import email.utils
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "views/high-frequency-discovery-latest.json"
POLICY_PATH = ROOT / "config/semantic-opportunity-policy.json"
OUT_PATH = ROOT / "views/high-frequency-discovery-qualified-seeds.json"
METRICS_PATH = ROOT / "metrics/high-frequency-semantic-gate.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def norm(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def contains(text, term):
    text, term = norm(text), norm(term)
    if not term:
        return False
    if len(term) <= 3 and term.isalnum():
        return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, flags=re.I))
    return term in text


def hits(text, terms):
    return sorted({t for t in terms if contains(text, t)})


def parse_date(value):
    if not value:
        return None
    s = str(value).strip()
    try:
        parsed = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except Exception:
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(s)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except Exception:
        return None


CITY_MAP = {
    "barcelona": ("Spain", "Cataluña", "Barcelona"), "sitges": ("Spain", "Cataluña", "Barcelona"),
    "girona": ("Spain", "Cataluña", "Girona"), "tarragona": ("Spain", "Cataluña", "Tarragona"),
    "lleida": ("Spain", "Cataluña", "Lleida"), "madrid": ("Spain", "Comunidad de Madrid", "Madrid"),
    "valencia": ("Spain", "Comunitat Valenciana", "Valencia"), "alicante": ("Spain", "Comunitat Valenciana", "Alicante"),
    "castellón": ("Spain", "Comunitat Valenciana", "Castellón"), "bilbao": ("Spain", "País Vasco", "Bizkaia"),
    "san sebastián": ("Spain", "País Vasco", "Gipuzkoa"), "vitoria": ("Spain", "País Vasco", "Álava"),
    "sevilla": ("Spain", "Andalucía", "Sevilla"), "málaga": ("Spain", "Andalucía", "Málaga"),
    "malaga": ("Spain", "Andalucía", "Málaga"), "granada": ("Spain", "Andalucía", "Granada"),
    "cádiz": ("Spain", "Andalucía", "Cádiz"), "zaragoza": ("Spain", "Aragón", "Zaragoza"),
    "murcia": ("Spain", "Región de Murcia", "Murcia"), "palma": ("Spain", "Illes Balears", "Illes Balears"),
    "las palmas": ("Spain", "Canarias", "Las Palmas"), "santa cruz de tenerife": ("Spain", "Canarias", "Santa Cruz de Tenerife"),
    "a coruña": ("Spain", "Galicia", "A Coruña"), "vigo": ("Spain", "Galicia", "Pontevedra"),
    "oviedo": ("Spain", "Asturias", "Asturias"), "santander": ("Spain", "Cantabria", "Cantabria"),
    "milano": ("Italy", "Lombardia", "Milano"), "milan": ("Italy", "Lombardia", "Milano"),
    "bergamo": ("Italy", "Lombardia", "Bergamo"), "brescia": ("Italy", "Lombardia", "Brescia"),
    "monza": ("Italy", "Lombardia", "Monza e Brianza"), "torino": ("Italy", "Piemonte", "Torino"),
    "turin": ("Italy", "Piemonte", "Torino"), "bologna": ("Italy", "Emilia-Romagna", "Bologna"),
    "modena": ("Italy", "Emilia-Romagna", "Modena"), "parma": ("Italy", "Emilia-Romagna", "Parma"),
    "roma": ("Italy", "Lazio", "Roma"), "rome": ("Italy", "Lazio", "Roma"),
    "firenze": ("Italy", "Toscana", "Firenze"), "florence": ("Italy", "Toscana", "Firenze"),
    "pisa": ("Italy", "Toscana", "Pisa"), "napoli": ("Italy", "Campania", "Napoli"),
    "naples": ("Italy", "Campania", "Napoli"), "bari": ("Italy", "Puglia", "Bari"),
    "genova": ("Italy", "Liguria", "Genova"), "genoa": ("Italy", "Liguria", "Genova"),
    "palermo": ("Italy", "Sicilia", "Palermo"), "catania": ("Italy", "Sicilia", "Catania"),
    "venezia": ("Italy", "Veneto", "Venezia"), "venice": ("Italy", "Veneto", "Venezia"),
    "padova": ("Italy", "Veneto", "Padova"), "verona": ("Italy", "Veneto", "Verona")
}


def geo_enrich(location, combined):
    text = norm(" ".join([location or "", combined or ""]))
    for key, value in CITY_MAP.items():
        if contains(text, key):
            return {"country": value[0], "region": value[1], "province": value[2], "resolution": "CITY_TEXT"}
    if contains(text, "spain") or contains(text, "españa"):
        return {"country": "Spain", "region": None, "province": None, "resolution": "COUNTRY_TEXT"}
    if contains(text, "italy") or contains(text, "italia"):
        return {"country": "Italy", "region": None, "province": None, "resolution": "COUNTRY_TEXT"}
    if any(contains(text, x) for x in ["europe", "european union", "eu", "emea"]):
        return {"country": "EU_REMOTE", "region": None, "province": None, "resolution": "REMOTE_REGION_TEXT"}
    if any(contains(text, x) for x in ["worldwide", "anywhere"]):
        return {"country": "WORLDWIDE_REMOTE", "region": None, "province": None, "resolution": "WORLDWIDE_TEXT"}
    return {"country": None, "region": None, "province": None, "resolution": "UNRESOLVED"}


def classify(signal, policy, now):
    title = signal.get("title") or ""
    organization = signal.get("organization") or ""
    location = signal.get("location") or ""
    desc_hits = signal.get("matched_profile_keywords") or []
    combined = " ".join([title, organization, location, " ".join(desc_hits)])

    role_hits = hits(title, policy["target_role_terms"])
    negative_hits = hits(title, policy["negative_title_terms"])
    mismatch_hits = hits(title, policy["stack_mismatch_terms"])
    skill_hits = hits(combined, policy["strong_skill_terms"])
    intent_hits = hits(combined, policy["commercial_intent_terms"])
    geo_exclusions = hits(" ".join([location, title]), policy["hard_geo_exclusion_terms"])
    geo = geo_enrich(location, combined)

    # Discovery should favor recall. Final quality remains enforced downstream.
    score = 10
    score += min(56, len(role_hits) * 28)
    score += min(25, len(skill_hits) * 5)
    score += min(15, len(intent_hits) * 5)
    if geo["country"] in ("Spain", "Italy"):
        score += 20
    elif geo["country"] in ("EU_REMOTE", "WORLDWIDE_REMOTE"):
        score += 15
    elif signal.get("target_geo_bucket") in ("SPAIN", "ITALY", "EU_REMOTE", "WORLDWIDE_REMOTE", "EU_REMOTE_TO_VERIFY", "ITALY_OR_INCLUDES_ITALY", "SPAIN_OR_INCLUDES_SPAIN"):
        score += 10

    reasons = []
    if negative_hits:
        score -= 60
        reasons.append("NEGATIVE_ROLE_TITLE")
    if mismatch_hits:
        score -= 35 if not role_hits else 20
        reasons.append("STACK_MISMATCH_TITLE")
    if geo_exclusions:
        score -= 65
        reasons.append("HARD_GEO_EXCLUSION")

    pub = parse_date(signal.get("published_at"))
    age_days = None
    if pub:
        age_days = max(0, (now - pub).total_seconds() / 86400)
        limits = policy["freshness_days"]
        if age_days > limits["maximum_for_automatic_promotion"]:
            score -= 45
            reasons.append("STALE_OVER_MAX")
        elif age_days > limits["acceptable"]:
            score -= 20
            reasons.append("AGING")
        elif age_days <= limits["preferred"]:
            score += 10

    incidental_only = not role_hits and bool(skill_hits)
    if incidental_only:
        score = min(score, 49)
        reasons.append("INCIDENTAL_BODY_KEYWORDS_ONLY")

    # A real target role with fresh evidence is review-worthy even when geography needs verification.
    if role_hits and not negative_hits and not geo_exclusions and "STALE_OVER_MAX" not in reasons:
        score = max(score, 54)
    # A real target role plus Spain/Italy/EU-remote compatibility should reach promotion when fresh.
    if role_hits and geo["country"] in ("Spain", "Italy", "EU_REMOTE", "WORLDWIDE_REMOTE") and not negative_hits and not geo_exclusions and "STALE_OVER_MAX" not in reasons:
        score = max(score, 74)

    score = max(0, min(100, round(score, 1)))
    thresholds = policy["thresholds"]
    hard_block = any(r in reasons for r in ["NEGATIVE_ROLE_TITLE", "HARD_GEO_EXCLUSION", "STALE_OVER_MAX"])
    if score >= thresholds["promote"] and not hard_block:
        state = "SEMANTIC_PASS"
    elif score >= thresholds["review"] and not hard_block:
        state = "SEMANTIC_REVIEW"
    else:
        state = "SEMANTIC_REJECT"

    out = dict(signal)
    out.update({
        "semantic_state": state,
        "semantic_score": score,
        "semantic_role_hits": role_hits,
        "semantic_negative_hits": negative_hits,
        "semantic_stack_mismatch_hits": mismatch_hits,
        "semantic_intent_hits": intent_hits,
        "geo_enrichment": geo,
        "published_age_days": round(age_days, 1) if age_days is not None else None,
        "semantic_reasons": reasons
    })
    return out


def main():
    raw = load(RAW_PATH, {"signals": []})
    policy = load(POLICY_PATH, {})
    now = utcnow()
    rows = [classify(x, policy, now) for x in raw.get("signals", [])]
    promote = sorted([x for x in rows if x["semantic_state"] == "SEMANTIC_PASS"], key=lambda x: x["semantic_score"], reverse=True)
    review = sorted([x for x in rows if x["semantic_state"] == "SEMANTIC_REVIEW"], key=lambda x: x["semantic_score"], reverse=True)
    reject = sorted([x for x in rows if x["semantic_state"] == "SEMANTIC_REJECT"], key=lambda x: x["semantic_score"], reverse=True)
    stamp = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    dump(OUT_PATH, {
        "schema_version": "1.1",
        "updated_at": stamp,
        "input_signal_count": len(rows),
        "semantic_pass_count": len(promote),
        "semantic_review_count": len(review),
        "semantic_reject_count": len(reject),
        "semantic_pass": promote,
        "semantic_review": review[:300],
        "semantic_reject_sample": reject[:100]
    })
    metrics = load(METRICS_PATH, {"schema_version": "1.1", "runs": 0, "total_input": 0, "total_pass": 0, "total_review": 0, "total_reject": 0})
    metrics.update({
        "updated_at": stamp,
        "runs": int(metrics.get("runs", 0)) + 1,
        "total_input": int(metrics.get("total_input", 0)) + len(rows),
        "total_pass": int(metrics.get("total_pass", 0)) + len(promote),
        "total_review": int(metrics.get("total_review", 0)) + len(review),
        "total_reject": int(metrics.get("total_reject", 0)) + len(reject),
        "last_run": {"input": len(rows), "pass": len(promote), "review": len(review), "reject": len(reject)}
    })
    dump(METRICS_PATH, metrics)
    print(json.dumps(metrics["last_run"]))


if __name__ == "__main__":
    main()
