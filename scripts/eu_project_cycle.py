#!/usr/bin/env python3
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import re
import smtplib
import ssl
import urllib.error
import urllib.request
import zipfile
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/eu-project-outreach-policy.json"
RADAR = ROOT / "api/v1/eu-project-radar.json"
STATE = ROOT / "state/eu-project-outreach-state.json"
QUEUE = ROOT / "outreach/eu-project-contact-queue.jsonl"
COMPANIES = ROOT / "api/v1/companies.json"
USER_AGENT = "VDS-EU-Project-Outreach/1.0 (+https://www.visualdesignstudio.es/)"


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def parse_date(value: str):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return dt.datetime.strptime(value[:19], fmt).date()
        except ValueError:
            pass
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def pick(row: dict, *names, default=""):
    lookup = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in row.items()}
    for name in names:
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        if key in lookup and lookup[key] not in (None, ""):
            return str(lookup[key]).strip()
    return default


def score_project(project: dict, policy: dict, today: dt.date) -> int:
    score = 0
    start = parse_date(project.get("start_date", ""))
    end = parse_date(project.get("end_date", ""))
    if start:
        delta = (start - today).days
        if -60 <= delta <= 60:
            score += 5
        elif -180 <= delta <= 120:
            score += 4
        elif -365 <= delta <= 180:
            score += 2
    if end and end >= today + dt.timedelta(days=365):
        score += 2
    try:
        budget = float(re.sub(r"[^0-9.]", "", project.get("budget", "") or "0"))
    except ValueError:
        budget = 0
    if budget >= 5_000_000:
        score += 3
    elif budget >= 1_000_000:
        score += 2
    text = " ".join([project.get("title", ""), project.get("objective", ""), project.get("topics", "")]).lower()
    hits = sum(1 for term in policy.get("communication_terms", []) if term.lower() in text)
    score += min(3, hits)
    if project.get("project_url"):
        score -= 1
    return max(0, score)


def download_cordis(policy: dict, state: dict):
    url = policy["cordis_bulk_url"]
    headers = {"User-Agent": USER_AGENT, "Accept": "application/zip, application/octet-stream"}
    if state.get("cordis_etag"):
        headers["If-None-Match"] = state["cordis_etag"]
    if state.get("cordis_last_modified"):
        headers["If-Modified-Since"] = state["cordis_last_modified"]
    api_key = os.getenv("CORDIS_API_KEY", "").strip()
    if api_key:
        headers["X-API-Key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            state["cordis_etag"] = resp.headers.get("ETag") or state.get("cordis_etag")
            state["cordis_last_modified"] = resp.headers.get("Last-Modified") or state.get("cordis_last_modified")
            state["cordis_key_configured"] = bool(api_key)
            return body, True
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            state["cordis_key_configured"] = bool(api_key)
            return None, False
        raise


def read_cordis_projects(blob: bytes):
    projects = []
    coordinators = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            try:
                raw = zf.read(name).decode("utf-8-sig", errors="replace")
            except KeyError:
                continue
            reader = csv.DictReader(io.StringIO(raw))
            fields = [re.sub(r"[^a-z0-9]", "", (f or "").lower()) for f in (reader.fieldnames or [])]
            is_project = "acronym" in fields and ("id" in fields or "projectid" in fields) and ("title" in fields or "objective" in fields)
            is_org = any(x in fields for x in ("organizationname", "name")) and any(x in fields for x in ("projectid", "projectrcn", "projectid"))
            if is_project:
                for row in reader:
                    pid = pick(row, "id", "projectID", "projectId", "rcn")
                    if not pid:
                        continue
                    projects.append({
                        "id": pid,
                        "acronym": pick(row, "acronym") or pid,
                        "title": pick(row, "title"),
                        "status": pick(row, "status"),
                        "start_date": pick(row, "startDate", "start date"),
                        "end_date": pick(row, "endDate", "end date"),
                        "budget": pick(row, "totalCost", "ecMaxContribution", "ecContribution"),
                        "programme": pick(row, "frameworkProgramme", "programme") or "Horizon Europe",
                        "topics": pick(row, "topics", "topic"),
                        "objective": pick(row, "objective"),
                        "project_url": pick(row, "projectUrl", "website", "url"),
                        "content_update_date": pick(row, "contentUpdateDate", "lastUpdateDate")
                    })
            elif is_org:
                for row in reader:
                    pid = pick(row, "projectID", "projectId", "projectRcn", "projectRCN")
                    if not pid:
                        continue
                    role = pick(row, "role", "activityType", "type").lower()
                    org = pick(row, "organizationName", "name", "legalName")
                    country = pick(row, "country", "countryCode")
                    if not org:
                        continue
                    cur = coordinators.get(pid)
                    if cur is None or "coordinator" in role or "coordinator" in pick(row, "organisationRole", "organizationRole").lower():
                        coordinators[pid] = {"name": org, "country": country, "role": role}
    return projects, coordinators


def candidate_window(project: dict, policy: dict, today: dt.date) -> bool:
    start = parse_date(project.get("start_date", ""))
    end = parse_date(project.get("end_date", ""))
    if end and end < today:
        return False
    if start:
        low = today - dt.timedelta(days=int(policy.get("lookback_days", 240)))
        high = today + dt.timedelta(days=int(policy.get("lookahead_days", 180)))
        return low <= start <= high
    return True


def company_contact(coordinator: str):
    data = load_json(COMPANIES, {})
    companies = data.get("companies", data if isinstance(data, list) else [])
    target = norm(coordinator)
    if not target:
        return None
    for company in companies:
        org = norm(str(company.get("organization") or company.get("company_id") or company.get("name") or ""))
        if not org:
            continue
        if target in org or org in target:
            emails = company.get("emails") or []
            if emails:
                return str(emails[0]).strip()
    return None


def smtp_ready() -> bool:
    return all(os.getenv(k) for k in ("VDS_SMTP_HOST", "VDS_SMTP_USER", "VDS_SMTP_PASSWORD"))


def send_first_contact(project: dict, recipient: str, policy: dict):
    host = os.environ["VDS_SMTP_HOST"]
    port = int(os.getenv("VDS_SMTP_PORT", "465"))
    user = os.environ["VDS_SMTP_USER"]
    password = os.environ["VDS_SMTP_PASSWORD"]
    sender = os.getenv("VDS_SMTP_FROM", user)
    acronym = project.get("acronym") or project.get("id")
    subject = policy.get("contact_subject_template", "Web support for {acronym}").format(acronym=acronym)
    body = f"""Dear {acronym} team,

I am Giuseppe Allocca, founder of Visual Design Studio. I work on web development and digital communication infrastructure for European research and innovation projects.

I came across {acronym} ({project.get('programme') or 'EU-funded project'}) and would be glad to support the consortium with a high-performance project website, UX/UI implementation, dissemination-oriented content architecture, publications/results repositories and ongoing technical maintenance.

Visual Design Studio: {policy['website_url']}
EU project portfolio: {policy['portfolio_url']}

If this area is managed by a specific Communication & Dissemination partner or WP leader, I would appreciate it if you could forward my message to the appropriate contact.

Best regards,
Giuseppe Allocca
Visual Design Studio
{policy['website_url']}
"""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)
    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls(context=context)
            smtp.login(user, password)
            smtp.send_message(msg)


def main():
    policy = load_json(POLICY, {})
    radar = load_json(RADAR, {"recent": [], "summary": {}})
    state = load_json(STATE, {"seen": {}, "contacted_project_ids": [], "contacted_recipients": [], "runs": 0})
    today = dt.datetime.now(dt.timezone.utc).date()
    changed = False
    try:
        blob, changed = download_cordis(policy, state)
    except Exception as exc:
        state["last_error"] = f"CORDIS download failed: {type(exc).__name__}: {exc}"[:500]
        blob = None

    previous_by_id = {str(x.get("id") or x.get("project_id") or x.get("project") or ""): x for x in radar.get("recent", [])}
    candidates = []
    coordinators = {}
    if blob:
        projects, coordinators = read_cordis_projects(blob)
        for p in projects:
            if not candidate_window(p, policy, today):
                continue
            p["score"] = score_project(p, policy, today)
            p["priority"] = "HIGH" if p["score"] >= int(policy.get("high_priority_min_score", 8)) else "MEDIUM" if p["score"] >= 5 else "LOW"
            coord = coordinators.get(str(p["id"])) or {}
            p["coordinator"] = coord.get("name", "")
            p["country"] = coord.get("country", "")
            candidates.append(p)
        candidates.sort(key=lambda x: (x.get("score", 0), x.get("start_date", "")), reverse=True)
        state["dataset_project_count"] = len(projects)
        state["candidate_count"] = len(candidates)
        state["last_dataset_refresh"] = now_utc()

    contacted_ids = set(str(x) for x in state.get("contacted_project_ids", []))
    contacted_recipients = set(str(x).lower() for x in state.get("contacted_recipients", []))
    queue_rows = []
    sent_now = 0
    qualified_now = 0
    recent = []

    source = candidates if candidates else [x for x in radar.get("recent", []) if isinstance(x, dict)]
    for p in source[:250]:
        pid = str(p.get("id") or p.get("project_id") or p.get("project") or "")
        acronym = p.get("acronym") or p.get("project") or pid
        if not pid:
            pid = acronym
        previous = previous_by_id.get(pid, {})
        status = previous.get("status", "REVIEW")
        reason = previous.get("reason") or "EU project candidate identified by cyclic radar"
        priority = p.get("priority") or previous.get("priority") or "MEDIUM"
        if pid in contacted_ids:
            status = "CONTACTED"
        recipient = previous.get("contact_email") or company_contact(p.get("coordinator", ""))
        if status != "CONTACTED" and priority in {"HIGH", "MEDIUM"}:
            qualified_now += 1
            if recipient and recipient.lower() not in contacted_recipients and smtp_ready() and policy.get("auto_first_contact", True):
                try:
                    send_first_contact(p, recipient, policy)
                    status = "CONTACTED"
                    sent_now += 1
                    contacted_ids.add(pid)
                    contacted_recipients.add(recipient.lower())
                    reason = "First contact sent automatically by EU Project Outreach Engine"
                except Exception as exc:
                    status = "READY_CONTACT"
                    reason = f"Contact found; SMTP send failed: {type(exc).__name__}"
            elif recipient:
                status = "READY_CONTACT"
                reason = "Verified contact available; waiting for configured mail transport"
            else:
                status = "ENRICH_CONTACT"
                reason = "Qualified project; coordinator/contact enrichment required"
        item = {
            "id": pid,
            "project": acronym,
            "title": p.get("title", ""),
            "programme": p.get("programme") or "Horizon Europe",
            "priority": priority,
            "status": status,
            "score": p.get("score"),
            "start_date": p.get("start_date", ""),
            "end_date": p.get("end_date", ""),
            "budget": p.get("budget", ""),
            "coordinator": p.get("coordinator", ""),
            "country": p.get("country", ""),
            "project_url": p.get("project_url", ""),
            "contact_email": recipient or "",
            "reason": reason
        }
        recent.append(item)
        state.setdefault("seen", {})[pid] = {"last_seen": now_utc(), "status": status}
        if status in {"ENRICH_CONTACT", "READY_CONTACT"}:
            queue_rows.append({"generated_at": now_utc(), **item})

    state["contacted_project_ids"] = sorted(contacted_ids)
    state["contacted_recipients"] = sorted(contacted_recipients)
    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_run"] = now_utc()
    state["last_sent_count"] = sent_now
    state.pop("last_error", None) if blob else None

    existing_summary = radar.get("summary", {})
    summary = {
        "discovered": len(state.get("seen", {})),
        "qualified": sum(1 for x in recent if x.get("status") in {"ENRICH_CONTACT", "READY_CONTACT", "CONTACTED"}),
        "contacted": len(contacted_ids) or int(existing_summary.get("contacted", 0)),
        "skipped": sum(1 for x in recent if x.get("status") == "SKIPPED"),
        "replied": int(existing_summary.get("replied", 0)),
        "high_priority": sum(1 for x in recent if x.get("priority") == "HIGH"),
        "sent_this_cycle": sent_now,
        "queued_for_enrichment": sum(1 for x in recent if x.get("status") == "ENRICH_CONTACT"),
        "ready_contact": sum(1 for x in recent if x.get("status") == "READY_CONTACT")
    }
    out = {
        "generated_at": now_utc(),
        "engine": {
            "name": "EU Project Outreach Engine",
            "status": "ACTIVE",
            "cadence": f"cyclic/{policy.get('cycle_minutes', 10)}m",
            "programmes": policy.get("programmes", []),
            "cordis_api_key_configured": bool(state.get("cordis_key_configured")),
            "mail_transport_configured": smtp_ready(),
            "rules": {
                "auto_first_contact": bool(policy.get("auto_first_contact", True)),
                "auto_follow_up": False,
                "dedup_required": True,
                "portfolio_url": policy.get("portfolio_url"),
                "website_url": policy.get("website_url")
            }
        },
        "summary": summary,
        "recent": recent[:120]
    }
    write_json(RADAR, out)
    write_json(STATE, state)
    append_jsonl(QUEUE, queue_rows)
    print(json.dumps({"changed": changed, "candidates": len(recent), "sent": sent_now, "queue": len(queue_rows)}))


if __name__ == "__main__":
    main()
