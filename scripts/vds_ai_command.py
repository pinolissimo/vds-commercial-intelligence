#!/usr/bin/env python3
"""Interpret one dashboard command through OpenAI and write a structured command record.

Hard invariant: this script NEVER sends mail and NEVER changes the existing
acquisition-task architecture. It writes only additive command/analysis JSON for
the existing task bridge to consume while all current gates remain authoritative.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MADRID = ZoneInfo("Europe/Madrid")
OUT = ROOT / "api" / "v1" / "ai-command"
QUEUE = ROOT / "command-center" / "commands" / "pending.json"

SYSTEM = """You are VDS Commercial Intelligence Command Router.
Interpret the owner's natural-language command for the existing VDS commercial acquisition system.
The current production task architecture is authoritative and must not be weakened, replaced or bypassed.
Never invent an opportunity, recipient, route, sent status, reply, rate, eligibility, freshness or evidence.
Never authorize duplicate FIRST_CONTACT. Any SEND_DIRECTIVE must preserve all existing gates: global organization dedup, suppression, authoritative route, freshness, geography/remote compatibility, fit, legal constraints, provider verification and manual-route preservation.
Quality thresholds must never be lowered merely to increase volume.

Return ONLY one compact JSON object with exactly these keys:
{
  "command_class": "ANALYZE|SEARCH_DIRECTIVE|SEND_DIRECTIVE|PRIORITY_DIRECTIVE|REFRESH|UNKNOWN",
  "intent": "short snake_case intent",
  "summary": "concise Italian explanation",
  "parameters": {},
  "requires_task_bridge": true,
  "requires_existing_gates": true,
  "risk": "LOW|MEDIUM|HIGH",
  "owner_confirmation_required": false,
  "answer": "direct Italian answer when command is analytical; otherwise short operational acknowledgement"
}
Use owner_confirmation_required=true only for commands that would materially alter safety/quality policy or are ambiguous/high-risk. Normal requests to search, prioritize or send already-valid READY items do not need an extra confirmation, but execution remains gated.
"""


def load(rel: str, default):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def extract_output_text(response: dict) -> str:
    for item in response.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") in {"output_text", "text"} and c.get("text"):
                    return c["text"]
    return response.get("output_text", "") or ""


def call_openai(api_key: str, model: str, command: str, context: dict) -> dict:
    payload = {
        "model": model,
        "instructions": SYSTEM,
        "input": "OWNER COMMAND:\n" + command + "\n\nCURRENT READ-ONLY SNAPSHOT:\n" + json.dumps(context, ensure_ascii=False),
        "reasoning": {"effort": "low"},
        "max_output_tokens": 1400,
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


def normalize(parsed: dict) -> dict:
    allowed = {"ANALYZE", "SEARCH_DIRECTIVE", "SEND_DIRECTIVE", "PRIORITY_DIRECTIVE", "REFRESH", "UNKNOWN"}
    cls = str(parsed.get("command_class", "UNKNOWN")).upper()
    if cls not in allowed:
        cls = "UNKNOWN"
    risk = str(parsed.get("risk", "MEDIUM")).upper()
    if risk not in {"LOW", "MEDIUM", "HIGH"}:
        risk = "MEDIUM"
    return {
        "command_class": cls,
        "intent": str(parsed.get("intent") or "unknown")[:120],
        "summary": str(parsed.get("summary") or "")[:1200],
        "parameters": parsed.get("parameters") if isinstance(parsed.get("parameters"), dict) else {},
        "requires_task_bridge": bool(parsed.get("requires_task_bridge", cls not in {"ANALYZE", "UNKNOWN"})),
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
    now = datetime.now(timezone.utc).astimezone(MADRID).isoformat(timespec="seconds")
    command_id = safe_request_id(os.environ.get("VDS_REQUEST_ID", "")) or datetime.now(timezone.utc).strftime("CMD-%Y%m%dT%H%M%SZ")
    record = {
        "schema_version": "1.1",
        "command_id": command_id,
        "created_at": now,
        "source": "VDS_COMMAND_CENTER_GITHUB_PAGES",
        "model": model,
        "owner_command": command,
        **parsed,
        "production_core_modified": False,
        "execution_policy": "EXISTING_TASKS_AND_GATES_REMAIN_AUTHORITATIVE",
        "status": "PENDING_TASK_BRIDGE" if parsed["requires_task_bridge"] and not parsed["owner_confirmation_required"] else ("ANSWERED" if parsed["command_class"] == "ANALYZE" else "REVIEW_REQUIRED"),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "latest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    history = OUT / "history"
    history.mkdir(parents=True, exist_ok=True)
    (history / f"{command_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if record["status"] == "PENDING_TASK_BRIDGE":
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        queue = load("command-center/commands/pending.json", {"schema_version": "1.0", "commands": []})
        commands = queue.get("commands") if isinstance(queue.get("commands"), list) else []
        if not any(item.get("command_id") == command_id for item in commands if isinstance(item, dict)):
            commands.append(record)
        queue = {
            "schema_version": "1.1",
            "updated_at": now,
            "policy": "Existing production tasks consume commands without bypassing existing gates or reducing normal discovery quality.",
            "commands": commands[-50:],
        }
        QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"command_id": command_id, "class": record["command_class"], "status": record["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
