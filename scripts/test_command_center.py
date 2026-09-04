#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "command-center"


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            if data["id"] in self.ids:
                raise AssertionError(f"duplicate id: {data['id']}")
            self.ids.add(data["id"])
        for attr in ("src", "href"):
            if data.get(attr):
                self.refs.append((tag, data[attr]))


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def main() -> int:
    html = (APP / "index.html").read_text(encoding="utf-8")
    css = (APP / "assets" / "app.css").read_text(encoding="utf-8")
    command_css = (APP / "assets" / "command.css").read_text(encoding="utf-8")
    js = (APP / "assets" / "app.js").read_text(encoding="utf-8")
    onboarding = (APP / "assets" / "secure-onboarding.js").read_text(encoding="utf-8")
    sodium_boot = (APP / "assets" / "sodium-bootstrap.js").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "vds-command-center-pages.yml").read_text(encoding="utf-8")

    parser = Collector()
    parser.feed(html)

    static_text = html + css + command_css + js + onboarding + sodium_boot
    require(not re.search(r"sk-[A-Za-z0-9_-]{20,}", static_text), "OpenAI secret value pattern leaked to static app")
    require("api.github.com" in html and "api.github.com" in js, "private GitHub API transport missing")
    require("sessionStorage" in js and "sessionStorage" in onboarding, "session-only token storage invariant missing")
    require("localStorage" not in static_text, "credentials must not persist in localStorage")
    require("eval(" not in static_text and "new Function" not in static_text, "dynamic code execution forbidden")
    require("fonts.googleapis.com" not in html and "cdn.jsdelivr.net" not in html, "runtime CDN reference found")
    require("assets/vendor/chart.umd.min.js" in html, "local Chart.js reference missing")
    require("assets/command.css" in html, "command console CSS missing")
    require("connect-src 'self' https://api.github.com" in html, "CSP private API rule missing")
    require("api/v1" not in workflow or "cp -R api/v1" not in workflow, "Pages workflow must not publish private CRM JSON")
    require("test ! -d .pages/api" in workflow, "Pages security smoke test missing")

    # Secure first-access OpenAI configuration: secret name is metadata only; value must be sealed locally.
    require("OPENAI_API_KEY" in onboarding, "OpenAI repository secret target missing")
    require("crypto_box_seal" in onboarding, "LibSodium sealed-box encryption missing")
    require("actions/secrets/public-key" in onboarding, "GitHub repository public-key endpoint missing")
    require("actions/secrets/${VDS_SECRET_NAME}" in onboarding, "GitHub repository secret write endpoint missing")
    require("input.value=''" in onboarding, "OpenAI key input clearing missing")
    require("memzero" in onboarding, "best-effort plaintext memory clearing missing")
    require("__vdsSodiumReady" in sodium_boot and "onload" in sodium_boot, "LibSodium readiness bootstrap missing")

    for tag, ref in parser.refs:
        if ref.startswith(("http://", "https://", "#", "mailto:", "tel:")):
            continue
        target = (APP / ref.split("?", 1)[0].split("#", 1)[0]).resolve()
        generated = any(part in ref for part in ("assets/vendor/", "assets/fonts/"))
        if not generated:
            require(target.exists(), f"missing static reference: {tag} {ref}")

    builder = (ROOT / "scripts" / "build_command_center_api.py").read_text(encoding="utf-8")
    require("writes only under api/v1" in builder.lower(), "projection read-model invariant missing")
    require("production_search_independent" in builder, "search independence health field missing")
    require("companies.json" in builder and "territory-productivity.json" in builder, "required read models missing")

    router = (ROOT / "scripts" / "vds_ai_command.py").read_text(encoding="utf-8")
    require("NEVER sends mail" in router, "AI no-direct-send invariant missing")
    require("requires_existing_gates" in router, "existing gate requirement missing")
    require("VDS_REQUEST_ID" in router, "command correlation missing")
    require("target_workers" in router and "normal_cycle_must_continue" in router, "formal worker routing missing")
    for worker in ("AGENCY_RADAR", "LINKEDIN_HUNTER", "UNIFIED_LOOP"):
        require(worker in router, f"worker routing missing: {worker}")

    pending = json.loads((APP / "commands" / "pending.json").read_text(encoding="utf-8"))
    processed = json.loads((APP / "commands" / "processed.json").read_text(encoding="utf-8"))
    require(pending.get("schema_version") == "1.2", "pending command schema must be 1.2")
    require(isinstance(pending.get("commands"), list), "pending commands must be a list")
    require(isinstance(processed.get("receipts"), list), "processed receipts must be a list")
    bridge = (ROOT / "project" / "COMMAND_CENTER_TASK_BRIDGE_PROTOCOL.md").read_text(encoding="utf-8")
    require("Failure to read, parse or write Command Center files MUST NOT stop normal discovery" in bridge, "availability invariant missing")
    require("command_id + worker_id" in bridge, "idempotent receipt key missing")

    manifest = json.loads((APP / "manifest.webmanifest").read_text(encoding="utf-8"))
    require(manifest.get("display") == "standalone", "PWA standalone mode missing")

    require("prefers-reduced-motion" in css, "reduced motion support missing")
    require("skip-link" in html, "skip navigation missing")
    require('aria-live="polite"' in html, "live region missing")
    require("@font-face" in css and "DM Sans Local" in css, "local font configuration missing")
    require("Material Symbols Rounded Local" in css, "local icon font configuration missing")

    print("VDS Command Center static/security QA: PASS")
    print(f"HTML ids checked: {len(parser.ids)}")
    print(f"Static references checked: {len(parser.refs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"QA FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
