#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "views/territory-yield-radar.json"
CROSS = ROOT / "views/cross-signal-opportunities.json"
SEM = ROOT / "views/high-frequency-discovery-qualified-seeds.json"
QUEUE = ROOT / "views/territory-enrichment-queue.json"

MIN_SAMPLE_FOR_LOW_YIELD = 4


def load(p, d):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return d


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unresolved(row):
    return row.get("region") in (None, "UNRESOLVED") or row.get("province") in (None, "UNRESOLVED")


def sample_size(row):
    m = row.get("metrics") or {}
    return int(m.get("signals", 0)) + int(m.get("verified", 0))


def main():
    radar = load(RADAR, {"areas": []})
    changed = 0
    unsampled_reset = 0
    for row in radar.get("areas", []):
        if unresolved(row):
            row["raw_score_before_geo_guard"] = row.get("score", 0)
            row["mode"] = "ENRICHMENT_REQUIRED"
            row["harvest_cycles"] = 0
            row["score"] = min(float(row.get("score", 0)), 17.99)
            changed += 1
            continue
        sample = sample_size(row)
        # Zero/tiny sample is ignorance, not evidence of low yield.
        if sample < MIN_SAMPLE_FOR_LOW_YIELD and row.get("mode") in {"ROTATE_OUT", "COOLDOWN"}:
            row["mode"] = "EXPLORATION"
            row["consecutive_low_yield_cycles"] = 0
            row["harvest_cycles"] = 0
            row["cooldown_until"] = None
            row["sample_status"] = "INSUFFICIENT_SAMPLE"
            unsampled_reset += 1
        else:
            row["sample_status"] = "MEANINGFUL" if sample >= MIN_SAMPLE_FOR_LOW_YIELD else "INSUFFICIENT_SAMPLE"

    mode_priority = {"HARVEST": 6, "REVISIT": 5, "EXPLORATION": 4, "ENRICHMENT_REQUIRED": 3, "ROTATE_OUT": 2, "COOLDOWN": 1}
    radar["areas"].sort(key=lambda r: (mode_priority.get(r.get("mode"), 0), float(r.get("score", 0))), reverse=True)
    for i, row in enumerate(radar.get("areas", []), 1): row["rank"] = i
    radar["top_areas"] = radar.get("areas", [])[:30]
    radar["harvest_now"] = [r for r in radar.get("areas", []) if r.get("mode") == "HARVEST"][:12]
    radar["explore_or_revisit_next"] = [r for r in radar.get("areas", []) if r.get("mode") in {"REVISIT", "EXPLORATION"}][:30]
    radar.setdefault("policy", {})["geo_guard"] = "Country-only/unresolved buckets cannot be HARVEST targets; they represent enrichment demand."
    radar["policy"]["minimum_sample_before_low_yield"] = MIN_SAMPLE_FOR_LOW_YIELD
    radar["policy"]["sampling_rule"] = "No-data or tiny-sample territories remain EXPLORATION; ROTATE_OUT/COOLDOWN requires meaningful observed sample."
    save(RADAR, radar)

    cross = load(CROSS, {"opportunities": []})
    sem = load(SEM, {"semantic_pass": []})
    q = []
    for o in cross.get("opportunities", []):
        t = o.get("territory") or {}
        country = o.get("country") or t.get("country")
        if country in {"ES", "IT", "Spain", "Italy"} and not (t.get("region") and t.get("province")):
            q.append({
                "type": "CROSS_SIGNAL_ORG",
                "canonical_identity_key": o.get("canonical_identity_key"),
                "organization": o.get("organization"),
                "country": country,
                "source_urls": [((o.get("route") or {}).get("source"))] if (o.get("route") or {}).get("source") else [],
                "priority_tier": o.get("priority_tier"),
                "reason": "REGION_PROVINCE_UNRESOLVED"
            })
    for s in sem.get("semantic_pass", []):
        g = s.get("geo_enrichment") or {}
        if g.get("country") in {"Spain", "Italy"} and not (g.get("region") and g.get("province")):
            q.append({
                "type": "SEMANTIC_SEED",
                "signal_key": s.get("signal_key"),
                "organization": s.get("organization"),
                "country": g.get("country"),
                "source_urls": [s.get("opportunity_url") or s.get("source_url")],
                "semantic_score": s.get("semantic_score"),
                "reason": "REGION_PROVINCE_UNRESOLVED"
            })
    tier = {"HOT+": 3, "HOT": 2, "WARM": 1}
    q.sort(key=lambda x: (tier.get(x.get("priority_tier"), 0), float(x.get("semantic_score") or 0)), reverse=True)
    save(QUEUE, {"schema_version": "1.1", "updated_at": radar.get("updated_at"), "count": len(q), "items": q[:500]})
    print(json.dumps({"unresolved_buckets_guarded": changed, "insufficient_sample_resets": unsampled_reset, "enrichment_queue": len(q)}))


if __name__ == "__main__":
    main()
