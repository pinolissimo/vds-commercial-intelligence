#!/usr/bin/env python3
"""Publish a static last-known-good Command Center snapshot.

Only validated API projections are copied. If live GitHub API reads fail or rate-limit,
the browser can render this snapshot instead of becoming empty/unusable.
"""
from __future__ import annotations
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
API=ROOT/"api/v1"
OUT=ROOT/"command-center/fallback"
FILES=[
 "dashboard.json","today.json","companies.json","territory-productivity.json",
 "opportunities.json","sources.json","health.json","eu-project-radar.json"
]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    copied=[]
    for name in FILES:
        src=API/name
        if not src.exists() or src.stat().st_size==0: continue
        # Validate JSON before promotion to last-known-good.
        json.loads(src.read_text(encoding="utf-8"))
        shutil.copyfile(src,OUT/name); copied.append(name)
    manifest={
      "schema_version":"1.0",
      "generated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
      "mode":"LAST_KNOWN_GOOD",
      "files":copied,
      "fallback_is_read_only":True
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest))
if __name__=="__main__": raise SystemExit(main())
