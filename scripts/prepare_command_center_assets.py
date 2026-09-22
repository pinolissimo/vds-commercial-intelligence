#!/usr/bin/env python3
"""Download pinned/local runtime assets for the VDS Command Center build.

Nothing is loaded from Google/CDNs at browser runtime. GitHub Actions downloads these
assets during the Pages build and publishes them under command-center/assets/.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
CHART_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"
XLSX_URL = "https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"
JSPDF_URL = "https://cdn.jsdelivr.net/npm/jspdf@4.2.1/dist/jspdf.umd.min.js"
AUTOTABLE_URL = "https://cdn.jsdelivr.net/npm/jspdf-autotable@5.0.8/dist/jspdf.plugin.autotable.min.js"
SODIUM_URL = "https://raw.githubusercontent.com/jedisct1/libsodium.js/2830fcf2ce8cefd3fdc7e1efc9fc1cee1d2d95b7/dist/browsers/sodium.js"
DM_CSS = "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,100..1000&display=swap"
ICONS_CSS = "https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"
ONBOARDING_MARKER = "assets/secure-onboarding.js"
TOKEN_HELPER_MARKER = "assets/github-token-helper.js"
TOKEN_PERSISTENCE_MARKER = "assets/token-persistence.js"
LIVE_EXPORT_MARKER = "assets/live-export.js"
EXECUTABLE_READY_MARKER = "assets/executable-ready.js"
EU_RADAR_MARKER = "assets/eu-radar.js"
REPLY_LIVE_MARKER = "assets/reply-live.js"
EXPORT_CSS_MARKER = "assets/export.css"
BUILD_ID = (os.environ.get("GITHUB_SHA") or "dev")[:12]
BUILD_CHECK_MARKER = "assets/build-check.js"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def font_url(css_url: str) -> str:
    css = fetch(css_url).decode("utf-8")
    urls = re.findall(r"url\((https://[^)]+\.woff2)\)", css)
    if not urls:
        raise RuntimeError(f"No WOFF2 found in {css_url}")
    return urls[-1]


def install_build_guard(root: Path, build_id: str) -> None:
    """Publish a build id and a runtime stale-build detector."""
    (root / "build-version.json").write_text(
        json.dumps({"build_id": build_id}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    guard = root / "assets" / "build-check.js"
    guard.write_text(
        "const VDS_BUILD_ID=" + json.dumps(build_id) + ";\n"
        "const VDS_BUILD_RELOAD_PREFIX='vds_cc_build_reload_';\n"
        "(async()=>{\n"
        "  try{\n"
        "    const response=await fetch('./build-version.json?t='+Date.now(),{cache:'no-store'});\n"
        "    if(!response.ok)return;\n"
        "    const remote=await response.json();\n"
        "    const active=String((remote&&remote.build_id)||'');\n"
        "    if(!active||active===VDS_BUILD_ID)return;\n"
        "    const guardKey=VDS_BUILD_RELOAD_PREFIX+active;\n"
        "    if(sessionStorage.getItem(guardKey)==='1')return;\n"
        "    sessionStorage.setItem(guardKey,'1');\n"
        "    const url=new URL(window.location.href);\n"
        "    url.searchParams.set('_vds_build',active);\n"
        "    window.location.replace(url.toString());\n"
        "  }catch(_){ }\n"
        "})();\n",
        encoding="utf-8",
    )


def version_static_asset_urls(html: str, build_id: str) -> str:
    """Cache-bust every local runtime asset with the deploy commit id."""
    pattern = re.compile(
        r'(?P<attr>src|href)="(?P<url>(?:assets/[^"?]+|manifest\.webmanifest))(?:\?[^\"]*)?"'
    )
    return pattern.sub(
        lambda m: f'{m.group("attr")}="{m.group("url")}?v={build_id}"',
        html,
    )

def inject_command_center_enhancements(root: Path) -> None:
    index = root / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace(
        "Permessi consigliati: repository singolo · Contents read-only · Actions read/write.",
        "Permessi consigliati: repository singolo · Contents read-only · Actions read/write · Secrets read/write.",
    )
    html = html.replace(
        "Permessi necessari per i comandi: repository singolo · Actions read/write.",
        "Permessi necessari per i comandi: repository singolo · Actions read/write · Secrets read/write.",
    )
    html = html.replace(
        "Il token resta soltanto nella sessione di questo browser.",
        "Il token viene conservato in questo browser e riutilizzato ai successivi avvii finché non scegli di disconnettere GitHub.",
    )
    if EXPORT_CSS_MARKER not in html:
        html = html.replace("</head>", '<link rel="stylesheet" href="assets/export.css">\n</head>')
    if TOKEN_PERSISTENCE_MARKER not in html:
        html = html.replace(
            '<script type="module" src="assets/app.js"></script>',
            '<script src="assets/token-persistence.js"></script><script type="module" src="assets/app.js"></script>',
        )
    scripts = ""
    if TOKEN_HELPER_MARKER not in html:
        scripts += '<script type="module" src="assets/github-token-helper.js"></script>'
    if ONBOARDING_MARKER not in html:
        scripts += (
            '<script src="assets/sodium-bootstrap.js"></script>'
            '<script src="assets/vendor/sodium.js"></script>'
            '<script type="module" src="assets/secure-onboarding.js"></script>'
        )
    if LIVE_EXPORT_MARKER not in html:
        scripts += '<script type="module" src="assets/live-export.js"></script>'
    if EXECUTABLE_READY_MARKER not in html:
        scripts += '<script type="module" src="assets/executable-ready.js"></script>'
    if EU_RADAR_MARKER not in html:
        scripts += '<script type="module" src="assets/eu-radar.js"></script>'
    if REPLY_LIVE_MARKER not in html:
        scripts += '<script type="module" src="assets/reply-live.js"></script>'
    if scripts:
        html = html.replace("</body>", scripts + "</body>")
    if BUILD_CHECK_MARKER not in html:
        html = html.replace("</body>", '<script src="assets/build-check.js"></script></body>')
    html = version_static_asset_urls(html, BUILD_ID)
    index.write_text(html, encoding="utf-8")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "command-center")
    fonts = root / "assets" / "fonts"
    vendor = root / "assets" / "vendor"
    fonts.mkdir(parents=True, exist_ok=True)
    vendor.mkdir(parents=True, exist_ok=True)

    assets = {
        fonts / "dm-sans.woff2": font_url(DM_CSS),
        fonts / "material-symbols-rounded.woff2": font_url(ICONS_CSS),
        vendor / "chart.umd.min.js": CHART_URL,
        vendor / "xlsx.full.min.js": XLSX_URL,
        vendor / "jspdf.umd.min.js": JSPDF_URL,
        vendor / "jspdf.plugin.autotable.min.js": AUTOTABLE_URL,
        vendor / "sodium.js": SODIUM_URL,
    }
    for path, url in assets.items():
        data = fetch(url)
        if len(data) < 1024:
            raise RuntimeError(f"Downloaded asset unexpectedly small: {url} ({len(data)} bytes)")
        path.write_bytes(data)
        print(f"asset {path}: {len(data)} bytes")

    install_build_guard(root, BUILD_ID)
    inject_command_center_enhancements(root)
    print(f"build {BUILD_ID}: cache-busted assets + runtime stale-build guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
