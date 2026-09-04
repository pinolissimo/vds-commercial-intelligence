#!/usr/bin/env python3
"""DeepSeek semantic shadow evaluator for VDS acquisition.

This module is intentionally observational. It never edits semantic decisions, READY
state, routes, dedup, reservations, sender state or operational queues. Failure is
fail-open for the production discovery pipeline.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config/deepseek-shadow-policy.json"
SEEDS_PATH = ROOT / "views/high-frequency-discovery-qualified-seeds.json"
CROSS_PATH = ROOT / "views/cross-signal-opportunities.json"
COMPANIES_PATH = ROOT / "api/v1/companies.json"
STATE_PATH = ROOT / "metrics/deepseek-shadow-state.json"
LATEST_PATH = ROOT / "views/deepseek-shadow-latest.json"
API_PATH = ROOT / "api/v1/deepseek-shadow.json"


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stamp(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def norm_org(value):
    text = re.sub(r"\b(s\.?r\.?l\.?|srl|s\.?p\.?a\.?|spa|sl|s\.l\.|ltd|llc|inc|gmbh|group|gruppo)\b", " ", str(value or "").lower())
    return re.sub(r"[^a-z0-9]+", "", text)


def same_org(a, b):
    na, nb = norm_org(a), norm_org(b)
    if not na or not nb:
        return False
    return na == nb or (len(na) >= 6 and len(nb) >= 6 and (na in nb or nb in na))


def baseline_decision(state):
    return {
        "SEMANTIC_PASS": "PROMOTE",
        "SEMANTIC_REVIEW": "REVIEW",
        "SEMANTIC_REJECT": "REJECT",
    }.get(state, "REVIEW")


def candidate_view(row):
    return {
        "signal_key": row.get("signal_key"),
        "baseline_state": row.get("semantic_state"),
        "baseline_score": row.get("semantic_score"),
        "title": row.get("title"),
        "organization": row.get("organization"),
        "location": row.get("location"),
        "country": row.get("country"),
        "published_at": row.get("published_at"),
        "published_age_days": row.get("published_age_days"),
        "employment_type": row.get("employment_type"),
        "remote_state": row.get("remote_published_or_inferred"),
        "target_geo_bucket": row.get("target_geo_bucket"),
        "matched_profile_keywords": row.get("matched_profile_keywords") or [],
        "matched_commercial_keywords": row.get("matched_commercial_keywords") or [],
        "semantic_role_hits": row.get("semantic_role_hits") or [],
        "semantic_negative_hits": row.get("semantic_negative_hits") or [],
        "semantic_stack_mismatch_hits": row.get("semantic_stack_mismatch_hits") or [],
        "semantic_intent_hits": row.get("semantic_intent_hits") or [],
        "route_state": row.get("route_state"),
        "verification_state": row.get("verification_state"),
        "source_authority": row.get("source_authority"),
        "opportunity_url": row.get("opportunity_url"),
    }


def select_candidates(seeds, seen, policy):
    pools = {
        "SEMANTIC_PASS": seeds.get("semantic_pass") or [],
        "SEMANTIC_REVIEW": seeds.get("semantic_review") or [],
        "SEMANTIC_REJECT": seeds.get("semantic_reject_sample") or [],
    }
    selected = []
    chosen = set()
    mix = policy.get("sample_mix") or {}
    for state in ("SEMANTIC_PASS", "SEMANTIC_REVIEW", "SEMANTIC_REJECT"):
        quota = int(mix.get(state, 0))
        for row in pools[state]:
            key = row.get("signal_key")
            if not key or key in seen or key in chosen:
                continue
            selected.append(row)
            chosen.add(key)
            if sum(1 for x in selected if x.get("semantic_state") == state) >= quota:
                break
    cap = int(policy.get("sample_per_run", 24))
    if len(selected) < cap:
        for state in ("SEMANTIC_PASS", "SEMANTIC_REVIEW", "SEMANTIC_REJECT"):
            for row in pools[state]:
                key = row.get("signal_key")
                if not key or key in seen or key in chosen:
                    continue
                selected.append(row)
                chosen.add(key)
                if len(selected) >= cap:
                    break
            if len(selected) >= cap:
                break
    return selected[:cap]


def deepseek_request(rows, policy, api_key):
    system = (
        "You are a shadow evaluator for a freelance web-development acquisition pipeline. "
        "You do not control production. Judge only the supplied evidence. Never invent facts. "
        "The target profile is a freelance web developer strong in WordPress, WooCommerce, custom HTML/CSS/JS, frontend, web performance/Core Web Vitals, website maintenance, UX/UI, technical web support and related IT skills. "
        "Primary markets are Spain and Italy, plus genuinely compatible EU-remote work. "
        "A strong opportunity has current explicit demand, truthful stack fit and plausible freelance/contract/external-collaboration compatibility. "
        "Do not treat generic mentions of partner/collaboration inside unrelated job text as proof of freelance compatibility. "
        "React/Angular/Laravel-heavy core roles without meaningful matching web/WordPress scope should be downgraded. "
        "Return JSON only with key evaluations. Each evaluation must contain signal_key, decision (PROMOTE|REVIEW|REJECT), score 0-100, confidence 0-1, primary_reason, risk_flags (array), inferred_contract_compatibility (HIGH|MEDIUM|LOW|UNKNOWN), and inferred_geo_compatibility (HIGH|MEDIUM|LOW|UNKNOWN)."
    )
    user = {
        "task": "Independently classify these candidates for semantic relevance. This is shadow-mode only; baseline fields are included only for later comparison and should not bias you.",
        "candidates": [candidate_view(r) for r in rows],
    }
    payload = {
        "model": policy.get("model", "deepseek-v4-flash"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False, separators=(",", ":"))},
        ],
        "temperature": float(policy.get("temperature", 0.1)),
        "thinking": {"type": policy.get("thinking", "disabled")},
        "max_tokens": int(policy.get("max_tokens", 6000)),
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    request = urllib.request.Request(
        policy.get("endpoint", "https://api.deepseek.com/chat/completions"),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    timeout = int(policy.get("request_timeout_seconds", 45))
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    content = (((result.get("choices") or [{}])[0].get("message") or {}).get("content")) or "{}"
    parsed = json.loads(content)
    evaluations = parsed.get("evaluations") or []
    return evaluations, result.get("usage") or {}, result.get("model") or policy.get("model")


def price_request(usage, policy, now):
    model = policy.get("model", "deepseek-v4-flash")
    pricing = ((policy.get("pricing_usd_per_million_tokens") or {}).get(model) or {})
    peak_ranges = pricing.get("peak_utc_hours") or []
    peak = any(int(start) <= now.hour < int(end) for start, end in peak_ranges)
    band = "peak" if peak else "off_peak"
    rates = pricing.get(band) or {}
    hit = int(usage.get("prompt_cache_hit_tokens") or 0)
    miss = int(usage.get("prompt_cache_miss_tokens") or max(0, int(usage.get("prompt_tokens") or 0) - hit))
    output = int(usage.get("completion_tokens") or 0)
    cost = (
        hit * float(rates.get("input_cache_hit") or 0)
        + miss * float(rates.get("input_cache_miss") or 0)
        + output * float(rates.get("output") or 0)
    ) / 1_000_000
    return {
        "billing_band": band,
        "prompt_cache_hit_tokens": hit,
        "prompt_cache_miss_tokens": miss,
        "completion_tokens": output,
        "total_tokens": int(usage.get("total_tokens") or hit + miss + output),
        "estimated_cost_usd": round(cost, 8),
    }


def validate_evaluations(raw, selected):
    valid_keys = {x.get("signal_key") for x in selected}
    out = {}
    for item in raw:
        key = item.get("signal_key")
        decision = str(item.get("decision") or "").upper()
        if key not in valid_keys or decision not in {"PROMOTE", "REVIEW", "REJECT"}:
            continue
        try:
            score = max(0.0, min(100.0, float(item.get("score"))))
        except Exception:
            score = 50.0
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence"))))
        except Exception:
            confidence = 0.5
        out[key] = {
            "decision": decision,
            "score": round(score, 1),
            "confidence": round(confidence, 3),
            "primary_reason": str(item.get("primary_reason") or "")[:500],
            "risk_flags": [str(x)[:120] for x in (item.get("risk_flags") or [])[:12]],
            "inferred_contract_compatibility": str(item.get("inferred_contract_compatibility") or "UNKNOWN").upper(),
            "inferred_geo_compatibility": str(item.get("inferred_geo_compatibility") or "UNKNOWN").upper(),
        }
    return out


def reconcile_downstream(evaluations):
    cross = load(CROSS_PATH, {}).get("opportunities") or []
    companies = load(COMPANIES_PATH, {}).get("companies") or []
    for ev in evaluations:
        org = ev.get("organization")
        hot_matches = [x for x in cross if same_org(org, x.get("organization"))]
        ev["observed_hot"] = any(str(x.get("priority_tier") or "").upper() in {"HOT", "HOT+"} for x in hot_matches)
        ev["observed_hot_score"] = max([float((x.get("scores") or {}).get("total") or 0) for x in hot_matches], default=0)
        company_matches = [x for x in companies if same_org(org, x.get("organization"))]
        statuses = []
        for company in company_matches:
            statuses.extend(str(o.get("status") or "") for o in (company.get("opportunities") or []))
        ev["observed_ready_or_contacted"] = any(s.startswith("READY") or "CONTACTED" in s for s in statuses)
        ev["observed_downstream_statuses"] = sorted(set(statuses))[:20]
    return evaluations


def rate(numerator, denominator):
    return round((numerator / denominator) * 100, 2) if denominator else None


def summarize(evaluations, state, policy, latest_request=None):
    total = len(evaluations)
    agreements = sum(1 for e in evaluations if e.get("baseline_decision") == e.get("deepseek_decision"))
    ds_promote = [e for e in evaluations if e.get("deepseek_decision") == "PROMOTE"]
    vds_promote = [e for e in evaluations if e.get("baseline_decision") == "PROMOTE"]
    recovered = [e for e in ds_promote if e.get("baseline_decision") != "PROMOTE"]
    demoted = [e for e in evaluations if e.get("baseline_decision") == "PROMOTE" and e.get("deepseek_decision") != "PROMOTE"]

    def downstream(group, field):
        return sum(1 for e in group if e.get(field))

    cumulative_cost = sum(float(x.get("estimated_cost_usd") or 0) for x in state.get("requests") or [])
    observed_ready = downstream(ds_promote, "observed_ready_or_contacted")
    min_sample = int(policy.get("min_sample_for_pilot_recommendation", 200))
    improvement_needed = float(policy.get("minimum_ready_rate_improvement_pp", 5.0))
    ds_ready_rate = rate(observed_ready, len(ds_promote))
    vds_ready_count = downstream(vds_promote, "observed_ready_or_contacted")
    vds_ready_rate = rate(vds_ready_count, len(vds_promote))
    ready_improvement = None if ds_ready_rate is None or vds_ready_rate is None else round(ds_ready_rate - vds_ready_rate, 2)
    recommendation = "CONTINUE_SHADOW"
    if total >= min_sample and ready_improvement is not None and ready_improvement >= improvement_needed:
        recommendation = "CANDIDATE_FOR_CONTROLLED_PILOT"

    return {
        "schema_version": "1.0",
        "updated_at": stamp(),
        "mode": "SHADOW_ONLY",
        "model": policy.get("model"),
        "production_decisions_mutated": False,
        "production_invariants": policy.get("production_invariants"),
        "sample": {
            "evaluated_total": total,
            "agreement_count": agreements,
            "agreement_pct": rate(agreements, total),
            "deepseek_promote": len(ds_promote),
            "vds_promote": len(vds_promote),
            "deepseek_recovered_from_review_or_reject": len(recovered),
            "deepseek_demoted_from_vds_promote": len(demoted),
        },
        "downstream_observation": {
            "deepseek_promote_hot": downstream(ds_promote, "observed_hot"),
            "deepseek_promote_hot_rate_pct": rate(downstream(ds_promote, "observed_hot"), len(ds_promote)),
            "vds_promote_hot": downstream(vds_promote, "observed_hot"),
            "vds_promote_hot_rate_pct": rate(downstream(vds_promote, "observed_hot"), len(vds_promote)),
            "deepseek_promote_ready_or_contacted": observed_ready,
            "deepseek_promote_ready_or_contacted_rate_pct": ds_ready_rate,
            "vds_promote_ready_or_contacted": vds_ready_count,
            "vds_promote_ready_or_contacted_rate_pct": vds_ready_rate,
            "ready_rate_improvement_pp": ready_improvement,
            "recovered_candidates_observed_hot": downstream(recovered, "observed_hot"),
            "recovered_candidates_observed_ready_or_contacted": downstream(recovered, "observed_ready_or_contacted"),
            "note": "Longitudinal proxy: organization-name reconciliation against current cross-signal HOT/HOT+ and Command Center READY/CONTACTED state. It is observational, not causal proof."
        },
        "economics": {
            "request_count": len(state.get("requests") or []),
            "cumulative_estimated_cost_usd": round(cumulative_cost, 6),
            "cost_per_evaluated_candidate_usd": round(cumulative_cost / total, 8) if total else None,
            "cost_per_deepseek_promote_usd": round(cumulative_cost / len(ds_promote), 8) if ds_promote else None,
            "cost_per_observed_ready_or_contacted_usd": round(cumulative_cost / observed_ready, 8) if observed_ready else None,
            "latest_request": latest_request,
        },
        "recommendation": recommendation,
        "promotion_gate": {
            "minimum_shadow_sample": min_sample,
            "minimum_ready_rate_improvement_pp": improvement_needed,
            "automatic_production_promotion_allowed": False,
        },
        "recent_evaluations": evaluations[-50:],
    }


def write_outputs(summary, state):
    dump(STATE_PATH, state)
    dump(LATEST_PATH, summary)
    dump(API_PATH, summary)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    policy = load(POLICY_PATH, {})
    state = load(STATE_PATH, {"schema_version": "1.0", "created_at": stamp(now), "evaluations": [], "requests": [], "runs": 0})
    state["runs"] = int(state.get("runs", 0)) + 1
    state["updated_at"] = stamp(now)
    state["mode"] = "SHADOW_ONLY"
    state["model"] = policy.get("model", "deepseek-v4-flash")
    state["production_mutation_allowed"] = False

    evaluations = reconcile_downstream(state.get("evaluations") or [])
    state["evaluations"] = evaluations
    seen = {x.get("signal_key") for x in evaluations if x.get("signal_key")}
    seeds = load(SEEDS_PATH, {})
    selected = select_candidates(seeds, seen, policy)
    latest_request = None

    if not policy.get("enabled", True):
        state["last_run_status"] = "DISABLED_BY_POLICY"
    elif not selected:
        state["last_run_status"] = "NO_NEW_UNSEEN_SAMPLE"
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            state["last_run_status"] = "SKIPPED_NO_DEEPSEEK_API_KEY"
        else:
            try:
                raw_eval, usage, model_used = deepseek_request(selected, policy, api_key)
                validated = validate_evaluations(raw_eval, selected)
                pricing = price_request(usage, policy, now)
                request_record = {
                    "at": stamp(now),
                    "model": model_used,
                    "candidate_count": len(selected),
                    "valid_evaluation_count": len(validated),
                    **pricing,
                }
                state.setdefault("requests", []).append(request_record)
                state["requests"] = state["requests"][-500:]
                per_candidate_cost = pricing["estimated_cost_usd"] / max(len(validated), 1)
                for row in selected:
                    key = row.get("signal_key")
                    shadow = validated.get(key)
                    if not shadow:
                        continue
                    evaluations.append({
                        "signal_key": key,
                        "evaluated_at": stamp(now),
                        "organization": row.get("organization"),
                        "title": row.get("title"),
                        "location": row.get("location"),
                        "opportunity_url": row.get("opportunity_url"),
                        "baseline_state": row.get("semantic_state"),
                        "baseline_score": row.get("semantic_score"),
                        "baseline_decision": baseline_decision(row.get("semantic_state")),
                        "deepseek_decision": shadow["decision"],
                        "deepseek_score": shadow["score"],
                        "deepseek_confidence": shadow["confidence"],
                        "deepseek_primary_reason": shadow["primary_reason"],
                        "deepseek_risk_flags": shadow["risk_flags"],
                        "deepseek_contract_compatibility": shadow["inferred_contract_compatibility"],
                        "deepseek_geo_compatibility": shadow["inferred_geo_compatibility"],
                        "estimated_cost_usd": round(per_candidate_cost, 10),
                    })
                max_keep = int(policy.get("max_retained_evaluations", 3000))
                evaluations = reconcile_downstream(evaluations[-max_keep:])
                state["evaluations"] = evaluations
                state["last_run_status"] = "SHADOW_EVALUATION_OK"
                latest_request = request_record
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, KeyError) as exc:
                state["last_run_status"] = "SHADOW_API_ERROR_FAIL_OPEN"
                state["last_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
            except Exception as exc:
                state["last_run_status"] = "SHADOW_INTERNAL_ERROR_FAIL_OPEN"
                state["last_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"

    summary = summarize(state.get("evaluations") or [], state, policy, latest_request)
    summary["last_run_status"] = state.get("last_run_status")
    summary["selected_this_run"] = len(selected)
    summary["source_semantic_updated_at"] = seeds.get("updated_at")
    if state.get("last_error"):
        summary["last_error"] = state.get("last_error")
    write_outputs(summary, state)
    print(json.dumps({
        "status": state.get("last_run_status"),
        "evaluated_total": summary["sample"]["evaluated_total"],
        "agreement_pct": summary["sample"]["agreement_pct"],
        "cost_usd": summary["economics"]["cumulative_estimated_cost_usd"],
        "recommendation": summary["recommendation"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
