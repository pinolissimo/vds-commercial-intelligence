#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "views/human-review-high-value.json"
PENDING_DIR = ROOT / "data/human-review-pending"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stamp():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    queue = load(QUEUE, {"schema_version":"1.0","status":"ACTIVE","items":[],"metrics":{}})
    items = queue.setdefault("items", [])
    by_key = {x.get("canonical_identity_key"): i for i, x in enumerate(items) if x.get("canonical_identity_key")}
    merged = 0
    for path in sorted(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []:
        rec = load(path, None)
        if not isinstance(rec, dict):
            continue
        key = rec.get("canonical_identity_key")
        if not key:
            continue
        rec.pop("merge_target", None)
        if key in by_key:
            idx = by_key[key]
            existing = items[idx]
            # Never overwrite an executed/owner-decided record with a stale PENDING sidecar.
            if existing.get("owner_decision") not in (None, "PENDING") and rec.get("owner_decision") == "PENDING":
                continue
            created = existing.get("created_at") or rec.get("created_at")
            merged_rec = dict(existing)
            merged_rec.update(rec)
            if created:
                merged_rec["created_at"] = created
            items[idx] = merged_rec
        else:
            by_key[key] = len(items)
            items.append(rec)
        merged += 1

    queue["updated_at"] = stamp()
    metrics = queue.setdefault("metrics", {})
    metrics["pending"] = sum(1 for x in items if x.get("owner_decision") == "PENDING")
    metrics["approved_outreach"] = sum(1 for x in items if x.get("owner_decision") == "APPROVE_OUTREACH")
    metrics["manual_apply"] = sum(1 for x in items if x.get("owner_decision") == "MANUAL_APPLY")
    metrics["hold"] = sum(1 for x in items if x.get("owner_decision") == "HOLD")
    metrics["rejected"] = sum(1 for x in items if x.get("owner_decision") == "REJECT")
    metrics["submitted_by_owner"] = sum(1 for x in items if x.get("execution_status") in {"CONTACT_ALREADY_EXECUTED","SUBMITTED_BY_OWNER"})
    save(QUEUE, queue)
    print(json.dumps({"pending_files_merged_or_refreshed": merged, "queue_items": len(items), "pending": metrics["pending"]}))


if __name__ == "__main__":
    main()
