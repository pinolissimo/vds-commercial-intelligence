#!/usr/bin/env python3
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "views/high-frequency-discovery-latest.json"
STATE = ROOT / "metrics/high-frequency-discovery-state.json"
OUT = ROOT / "views/search-source-performance.json"
RUNTIME = ROOT / "config/adaptive-search-runtime.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    latest = load(LATEST, {"signals": []})
    state = load(STATE, {})
    rows = latest.get("signals", [])
    grouped = defaultdict(list)
    for r in rows:
        grouped[r.get("source_id", "unknown")].append(r)
    errors = Counter(e.get("source_id", "unknown") for e in state.get("errors", []))

    ranked = []
    for source, items in grouped.items():
        n = len(items)
        high70 = sum(int(x.get("raw_fit_score", 0)) >= 70 for x in items)
        high80 = sum(int(x.get("raw_fit_score", 0)) >= 80 for x in items)
        target_geo = sum(x.get("target_geo_bucket") in {"SPAIN_OR_INCLUDES_SPAIN","ITALY_OR_INCLUDES_ITALY","EU_REMOTE_TO_VERIFY","WORLDWIDE_REMOTE"} for x in items)
        commercial = sum(bool(x.get("matched_commercial_keywords")) for x in items)
        official = sum(x.get("verification_state") == "OFFICIAL_PAGE_SIGNAL" for x in items)
        avg_fit = sum(int(x.get("raw_fit_score", 0)) for x in items) / max(1, n)
        sample_conf = min(1.0, math.log1p(n) / math.log(31))
        quality = (
            0.28 * high70 / max(1, n)
            + 0.18 * high80 / max(1, n)
            + 0.22 * target_geo / max(1, n)
            + 0.14 * commercial / max(1, n)
            + 0.08 * official / max(1, n)
            + 0.10 * min(1.0, avg_fit / 85.0)
        )
        quality *= 0.55 + 0.45 * sample_conf
        quality -= min(0.20, errors[source] * 0.04)
        quality = max(0.0, min(1.0, quality))
        multiplier = round(max(0.5, min(2.0, 0.55 + quality * 1.65)), 2)
        ranked.append({
            "source_id": source,
            "signals": n,
            "high_fit_70_plus": high70,
            "high_fit_80_plus": high80,
            "target_geo_signals": target_geo,
            "commercial_intent_signals": commercial,
            "official_signals": official,
            "average_raw_fit": round(avg_fit, 2),
            "recent_errors": errors[source],
            "quality_score_0_100": round(quality * 100, 2),
            "priority_multiplier": multiplier
        })

    ranked.sort(key=lambda x: (x["quality_score_0_100"], x["high_fit_80_plus"], x["signals"]), reverse=True)
    for i, row in enumerate(ranked, 1):
        row["rank"] = i

    output = {
        "schema_version": "1.0",
        "updated_at": now_utc(),
        "principle": "Keep broad public-source coverage, but spend human/LLM verification effort preferentially on sources with high target-geo and high-fit yield. Low-yield sources retain a minimum exploration floor.",
        "ranking": ranked
    }
    runtime = {
        "schema_version": "1.0",
        "updated_at": output["updated_at"],
        "source_priority": {r["source_id"]: r["priority_multiplier"] for r in ranked},
        "top_sources": [r["source_id"] for r in ranked[:5]],
        "low_priority_sources": [r["source_id"] for r in ranked if r["priority_multiplier"] <= 0.75],
        "rule": "Priority multipliers influence downstream validation/research depth, not dedup/safety gates."
    }
    save(OUT, output)
    save(RUNTIME, runtime)
    print(json.dumps({"updated_at": output["updated_at"], "top_sources": runtime["top_sources"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
