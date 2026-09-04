#!/usr/bin/env python3
"""Interpret one dashboard command and queue it for the simplified VDS flows.

Hard invariants: this script NEVER sends mail; dashboard commands are overlays only;
normal discovery and the two self-contained execution flows remain authoritative.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MADRID = ZoneInfo("Europe/Madrid")
OUT = ROOT / "api" / "v1" / "ai-command"
QUEUE = ROOT / "command-center" / "commands" / "pending.json"
WORKERS = {"LINKEDIN_HUNTER", "UNIFIED_LOOP"}

SYSTEM = """You are VDS Commercial Intelligence Command Router.
Interpret the owner's natural-language command for the simplified VDS acquisition system.
Production architecture: independent GitHub discovery plus exactly two self-contained execution flows:
- LINKEDIN_HUNTER = VDS Job Flow: direct-job discovery, qualification, manual-route preservation and authorized direct-email application execution.
- UNIFIED_LOOP = VDS Revenue Flow: agency/white-label/EU/direct-buyer/commercial discovery, qualification, manual-route preservation and authorized direct-email execution.
The old AGENCY_RADAR and CROSS-SIGNAL intermediate workers are disabled and MUST NOT be targeted.

Never invent an opportunity, recipient, route, sent status, reply, rate, eligibility, freshness or evidence.
Never authorize duplicate FIRST_CONTACT. SEND directives preserve the real hard gates: organization-level dedup/suppression/reservation, current need, truthful fit, authoritative route, legal/channel compatibility, send window and provider verification. Missing nonessential metadata must not become a synthetic blocker. Form/platform-only routes remain manual.

Return ONLY one compact JSON object with exactly these keys:
{
  "command_class": "ANALYZE|SEARCH_DIRECTIVE|SEND_DIRECTIVE|PRIORITY_DIRECTIVE|REFRESH|UNKNOWN",
  "intent": "short_snake_case_intent",
  "summary": "concise Italian explanation",
  "parameters": {},
  "target_workers": ["LINKEDIN_HUNTER|UNIFIED_LOOP"],
  "requires_task_bridge": true,
  "requires_existing_gates": true,
  "risk": "LOW|MEDIUM|HIGH",
  "owner_confirmation_required": false,
  "answer": "direct Italian answer when analytical; otherwise short operational acknowledgement"
}
Routing: direct job/vacancy/application -> LINKEDIN_HUNTER. Agency/white-label/EU-project/WPO/direct-buyer/commercial -> UNIFIED_LOOP. Broad acquisition priority/refresh -> both. Never route a send to a worker outside its existing send authority.
Use owner_confirmation_required=true only for a genuinely ambiguous/high-risk request that would alter hard safety policy. Normal search, priority, refresh, or sending of already-valid candidates does not require another confirmation, but all hard gates remain mandatory.
"""


def load(rel: str, default):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def extract_output_text(response: dict) -> str:
    for item in response.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    return content["text"]
    return response.get("output_text", "") or ""


def call_openai(api_key: str, model: str, command: str, context: dict) -> dict:
    payload = {
        "model": model,
        "instructions": SYSTEM,
        "input": "OWNER COMMAND:\n" + command + "\n\nCURRENT READ-ONLY SNAPSHOT:\n" + json.dumps(context, ensure_ascii=False),
        "reasoning": {"effort": "low"},
        "max_output_tokens": 1600,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {body[:800]}") from exc
    text = extract_output_text(data).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI returned non-JSON command output: {text[:800]}") from exc


def fallback_targets(command_class: str, intent: str, parameters: dict) -> list[str]:
    haystack = " ".join([intent, json.dumps(parameters, ensure_ascii=False)]).lower()
    jobish = any(k in haystack for k in ("job", "vacancy", "linkedin", "ats", "candidatur", "direct_job", "application"))
    if command_class in {"SEND_DIRECTIVE", "SEARCH_DIRECTIVE"}:
        return ["LINKEDIN_HUNTER"] if jobish else ["UNIFIED_LOOP"]
    if command_class in {"PRIORITY_DIRECTIVE", "REFRESH"}:
        return ["LINKEDIN_HUNTER", "UNIFIED_LOOP"]
    return []


def normalize(parsed: dict) -> dict:
    allowed = {"ANALYZE", "SEARCH_DIRECTIVE", "SEND_DIRECTIVE", "PRIORITY_DIRECTIVE", "REFRESH", "UNKNOWN"}
    cls = str(parsed.get("command_class", "UNKNOWN")).upper()
    if cls not in allowed:
        cls = "UNKNOWN"
    risk = str(parsed.get("risk", "MEDIUM")).upper()
    if risk not in {"LOW", "MEDIUM", "HIGH"}:
        risk = "MEDIUM"
    params = parsed.get("parameters") if isinstance(parsed.get("parameters"), dict) else {}
    intent = str(parsed.get("intent") or "unknown")[:120]
    raw_targets = parsed.get("target_workers") if isinstance(parsed.get("target_workers"), list) else []
    targets: list[str] = []
    for value in raw_targets:
        worker = str(value).upper().strip()
        if worker in WORKERS and worker not in targets:
            targets.append(worker)
    requires_bridge = bool(parsed.get("requires_task_bridge", cls not in {"ANALYZE", "UNKNOWN"}))
    if requires_bridge and not targets:
        targets = fallback_targets(cls, intent, params)
    if cls in {"ANALYZE", "UNKNOWN"}:
        targets = []
        requires_bridge = False
    return {
        "command_class": cls,
        "intent": intent,
        "summary": str(parsed.get("summary") or "")[:1200],
        "parameters": params,
        "target_workers": targets,
        "requires_task_bridge": requires_bridge,
        "requires_existing_gates": True,
        "risk": risk,
        "owner_confirmation_required": bool(parsed.get("owner_confirmation_required", False)),
        "answer": str(parsed.get("answer") or "")[:4000],
    }


def safe_request_id(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    if not re.fullmatch(r"[A-Za-z0-9._:-]{8,120}", value):
        raise RuntimeError("Invalid VDS_REQUEST_ID")
    return value


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("usage: vds_ai_command.py '<command>'", file=sys.stderr)
        return 2
    command = sys.argv[1].strip()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY GitHub Actions secret is missing")
    model = os.environ.get("OPENAI_MODEL", "gpt-5.6-terra").strip() or "gpt-5.6-terra"

    context = {
        "dashboard": load("api/v1/dashboard.json", {}),
        "today": load("api/v1/today.json", {}),
        "sources": load("api/v1/sources.json", {}),
        "health": load("api/v1/health.json", {}),
    }
    parsed = normalize(call_openai(api_key, model, command, context))
    now_utc = datetime.now(timezone.utc)
    now = now_utc.astimezone(MADRID).isoformat(timespec="seconds")
    expires_at = (now_utc + timedelta(hours=24)).astimezone(MADRID).isoformat(timespec="seconds")
    command_id = safe_request_id(os.environ.get("VDS_REQUEST_ID", "")) or now_utc.strftime("CMD-%Y%m%dT%H%M%SZ")
    record = {
        "schema_version": "1.3",
        "command_id": command_id,
        "created_at": now,
        "expires_at": expires_at,
        "source": "VDS_COMMAND_CENTER_GITHUB_PAGES",
        "model": model,
        "owner_command": command,
        **parsed,
        "production_core_modified": False,
        "normal_cycle_must_continue": True,
        "execution_policy": "SIMPLIFIED_TWO_FLOW_ARCHITECTURE_WITH_HARD_GATES",
        "status": "PENDING_TASK_BRIDGE" if parsed["requires_task_bridge"] and parsed["target_workers"] and not parsed["owner_confirmation_required"] else ("ANSWERED" if parsed["command_class"] == "ANALYZE" else "REVIEW_REQUIRED"),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "latest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    history = OUT / "history"
    history.mkdir(parents=True, exist_ok=True)
    (history / f"{command_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if record["status"] == "PENDING_TASK_BRIDGE":
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        queue = load("command-center/commands/pending.json", {"schema_version": "1.3", "commands": []})
        commands = queue.get("commands") if isinstance(queue.get("commands"), list) else []
        if not any(item.get("command_id") == command_id for item in commands if isinstance(item, dict)):
            commands.append(record)
        queue = {
            "schema_version": "1.3",
            "updated_at": now,
            "policy": "Dashboard commands route only to the two active self-contained flows. Discovery and normal execution continue even if the bridge is unavailable.",
            "commands": commands[-60:],
        }
        QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"command_id": command_id, "class": record["command_class"], "status": record["status"], "target_workers": record["target_workers"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
