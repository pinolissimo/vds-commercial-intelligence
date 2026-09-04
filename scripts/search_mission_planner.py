#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "views/territory-yield-radar.json"
CMD = ROOT / "config/acquisition-runtime-command.json"
PLAY = ROOT / "config/territorial-intent-query-playbook.json"
OUT = ROOT / "views/search-mission-plan.json"

STRATEGIC_PRIOR = {
    "Spain": [
        "Spain|Cataluña|Barcelona",
        "Spain|Comunidad de Madrid|Madrid",
        "Spain|Comunitat Valenciana|Valencia",
        "Spain|País Vasco|Bizkaia",
        "Spain|Andalucía|Málaga",
        "Spain|Andalucía|Sevilla",
        "Spain|Comunitat Valenciana|Alicante",
        "Spain|Aragón|Zaragoza",
        "Spain|Cataluña|Tarragona",
        "Spain|Galicia|A Coruña"
    ],
    "Italy": [
        "Italy|Lombardia|Milano",
        "Italy|Lazio|Roma",
        "Italy|Piemonte|Torino",
        "Italy|Emilia-Romagna|Bologna",
        "Italy|Toscana|Firenze",
        "Italy|Campania|Napoli",
        "Italy|Veneto|Padova",
        "Italy|Veneto|Verona",
        "Italy|Lombardia|Bergamo",
        "Italy|Lombardia|Brescia"
    ]
}


def load(p, d):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return d


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def territory_label(area):
    parts = [area.get("province"), area.get("region")]
    return " ".join(dict.fromkeys([x for x in parts if x and x != "UNRESOLVED"])) or area.get("country", "")


def rotate_pick(pool, slot, count):
    if not pool:
        return []
    start = (slot * max(1, count)) % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(min(count, len(pool)))]


def add_unique(selected, seen, area):
    if area and area.get("area_key") not in seen:
        selected.append(area)
        seen.add(area.get("area_key"))


def main():
    now = dt.datetime.now(dt.timezone.utc)
    radar = load(RADAR, {"areas": []})
    cmd = load(CMD, {})
    play = load(PLAY, {"segments": {}})
    valid_modes = {"HARVEST", "REVISIT", "EXPLORATION"}
    areas = [a for a in radar.get("areas", []) if a.get("mode") in valid_modes and a.get("region") not in {None, "UNRESOLVED"} and a.get("province") not in {None, "UNRESOLVED"}]
    area_by_key = {a.get("area_key"): a for a in areas}
    slot = int(now.timestamp() // 900)

    selected = []
    seen = set()
    # Per country: strongest learned area first, then one strategic-density prior, then one rotating exploration area.
    # This gives urgent commercial density without sacrificing nationwide exploration.
    for country in ("Spain", "Italy"):
        country_areas = [a for a in areas if a.get("country") == country]
        exploit = sorted(
            [a for a in country_areas if a.get("mode") in {"HARVEST", "REVISIT"}],
            key=lambda a: (float(a.get("score", 0)), int((a.get("metrics") or {}).get("hot", 0)), int((a.get("metrics") or {}).get("ready", 0))),
            reverse=True
        )
        if exploit:
            add_unique(selected, seen, exploit[0])

        priors = [area_by_key[k] for k in STRATEGIC_PRIOR.get(country, []) if k in area_by_key and area_by_key[k].get("mode") != "COOLDOWN"]
        if priors:
            strategic = priors[slot % min(len(priors), 6)]
            add_unique(selected, seen, strategic)

        explore = [a for a in country_areas if a.get("mode") == "EXPLORATION" and a.get("area_key") not in seen]
        for a in rotate_pick(explore, slot + (0 if country == "Spain" else 11), 1):
            add_unique(selected, seen, a)

        # If there is no learned exploit yet, use a second strategic metro instead of leaving capacity idle.
        if not exploit and len([a for a in selected if a.get("country") == country]) < 3:
            for a in priors:
                if a.get("area_key") not in seen:
                    add_unique(selected, seen, a)
                    break

    segments = sorted(play.get("segments", {}).items(), key=lambda kv: float(kv[1].get("weight", 1)), reverse=True)
    missions = []
    for ai, area in enumerate(selected):
        country = area.get("country")
        lang = "spain" if country == "Spain" else "italy"
        label = territory_label(area)
        mode = area.get("mode")
        # Four intents per strategic territory to increase route-closure probability.
        for offset in range(4):
            seg_name, seg = segments[(slot + ai + offset) % len(segments)]
            templates = seg.get(lang, [])
            if not templates:
                continue
            template = templates[(slot + ai * 4 + offset) % len(templates)]
            missions.append({
                "mission_id": f"{slot}-{ai}-{offset}",
                "country": country,
                "region": area.get("region"),
                "province": area.get("province"),
                "territory_mode": mode,
                "territory_score": area.get("score"),
                "segment": seg_name,
                "segment_weight": seg.get("weight", 1),
                "query": template.replace("{territory}", label),
                "route_goal": "AUTHORITATIVE_CURRENT_DEMAND_AND_EXACT_APPLICATION_OR_COLLABORATION_ROUTE",
                "dedup_required": True
            })

    output = {
        "schema_version": "1.2",
        "updated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "cycle_minutes": 15,
        "diagnosed_bottleneck": cmd.get("diagnosed_bottleneck"),
        "capacity": cmd.get("capacity", {"exploitation_pct": 70, "exploration_pct": 20, "strategic_reserve_pct": 10}),
        "selected_areas": [{"area_key": a.get("area_key"), "mode": a.get("mode"), "score": a.get("score")} for a in selected],
        "missions": missions,
        "country_counts": {"Spain": sum(1 for a in selected if a.get("country") == "Spain"), "Italy": sum(1 for a in selected if a.get("country") == "Italy")},
        "strategy": "LEARNED_YIELD_PLUS_STRATEGIC_DENSITY_PLUS_NATIONWIDE_ROTATION",
        "instruction": "Execute highest-value missions with fresh web search. When learned yield is sparse, prioritize major digital/business ecosystems while preserving one rotating exploratory territory per country. Verify authoritative demand/route and provider suppression before any downstream execution."
    }
    save(OUT, output)
    print(json.dumps({"selected_areas": len(selected), "missions": len(missions), "countries": output["country_counts"], "bottleneck": output["diagnosed_bottleneck"]}))


if __name__ == "__main__":
    main()
