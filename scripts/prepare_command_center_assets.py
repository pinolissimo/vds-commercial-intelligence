#!/usr/bin/env python3
"""Download pinned/local runtime assets for the VDS Command Center build.

Nothing is loaded from Google/CDNs at browser runtime. GitHub Actions downloads these
assets during the Pages build and publishes them under command-center/assets/.
"""
from __future__ import annotations

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
LIVE_EXPORT_MARKER = "assets/live-export.js"
EXPORT_CSS_MARKER = "assets/export.css"


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


def inject_command_center_enhancements(root: Path) -> None:
    index = root / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace(
        "Permessi consigliati: repository singolo · Contents read-only · Actions read/write.",
        "Permessi consigliati: repository singolo · Contents read-only · Actions read/write · Secrets read/write.",
    )
    if EXPORT_CSS_MARKER not in html:
        html = html.replace("</head>", '<link rel="stylesheet" href="assets/export.css">\n</head>')
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
    if scripts:
        html = html.replace("</body>", scripts + "</body>")
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

    inject_command_center_enhancements(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
