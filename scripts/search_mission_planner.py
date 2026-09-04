#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "views/territory-yield-radar.json"
CMD = ROOT / "config/acquisition-runtime-command.json"
PLAY = ROOT / "config/territorial-intent-query-playbook.json"
OUT = ROOT / "views/search-mission-plan.json"


def load(p, d):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return d


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def territory_label(area):
    parts = [area.get("province"), area.get("region")]
    return " ".join(dict.fromkeys([x for x in parts if x and x != "UNRESOLVED"])) or area.get("country", "")


def main():
    now = dt.datetime.now(dt.timezone.utc)
    radar = load(RADAR, {"areas": []})
    cmd = load(CMD, {})
    play = load(PLAY, {"segments": {}})
    areas = [a for a in radar.get("areas", []) if a.get("region") not in {None, "UNRESOLVED"} and a.get("province") not in {None, "UNRESOLVED"}]
    harvest = [a for a in areas if a.get("mode") == "HARVEST"]
    revisit = [a for a in areas if a.get("mode") == "REVISIT"]
    explore = [a for a in areas if a.get("mode") == "EXPLORATION"]
    # Prefer actual high-yield areas; if sample is immature, rotate deterministic exploration.
    slot = int(now.timestamp() // 900)
    exploit = (harvest + revisit)[:4]
    pool = explore or areas
    exploration = []
    if pool:
        start = (slot * 4) % len(pool)
        exploration = [pool[(start + i) % len(pool)] for i in range(min(4, len(pool)))]
    selected = []
    seen = set()
    for a in exploit + exploration:
        if a.get("area_key") not in seen:
            selected.append(a); seen.add(a.get("area_key"))

    segments = sorted(play.get("segments", {}).items(), key=lambda kv: float(kv[1].get("weight", 1)), reverse=True)
    missions = []
    for ai, area in enumerate(selected):
        country = area.get("country")
        lang = "spain" if country == "Spain" else "italy"
        label = territory_label(area)
        mode = area.get("mode")
        # 3 queries/area per cycle, rotated across segment/template indexes.
        for offset in range(3):
            seg_name, seg = segments[(slot + ai + offset) % len(segments)]
            templates = seg.get(lang, [])
            if not templates: continue
            template = templates[(slot + ai * 3 + offset) % len(templates)]
            query = template.replace("{territory}", label)
            missions.append({
                "mission_id": f"{slot}-{ai}-{offset}",
                "country": country,
                "region": area.get("region"),
                "province": area.get("province"),
                "territory_mode": mode,
                "territory_score": area.get("score"),
                "segment": seg_name,
                "segment_weight": seg.get("weight", 1),
                "query": query,
                "route_goal": "AUTHORITATIVE_CURRENT_DEMAND_AND_EXACT_APPLICATION_OR_COLLABORATION_ROUTE",
                "dedup_required": True
            })
    output = {
        "schema_version": "1.0",
        "updated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "cycle_minutes": 15,
        "diagnosed_bottleneck": cmd.get("diagnosed_bottleneck"),
        "capacity": cmd.get("capacity", {"exploitation_pct":70,"exploration_pct":20,"strategic_reserve_pct":10}),
        "selected_areas": [{"area_key": a.get("area_key"), "mode": a.get("mode"), "score": a.get("score")} for a in selected],
        "missions": missions,
        "instruction": "Tasks should execute the highest-value independent missions with fresh web search, verify against authoritative sources, merge by canonical organization and stop deep work on weak/duplicate/stale results."
    }
    save(OUT, output)
    print(json.dumps({"selected_areas": len(selected), "missions": len(missions), "bottleneck": output["diagnosed_bottleneck"]}))


if __name__ == "__main__":
    main()
