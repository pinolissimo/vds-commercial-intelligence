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
SODIUM_URL = "https://cdn.jsdelivr.net/npm/libsodium-wrappers@0.7.15/dist/browsers/sodium.js"
DM_CSS = "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,100..1000&display=swap"
ICONS_CSS = "https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"


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
        vendor / "sodium.js": SODIUM_URL,
    }
    for path, url in assets.items():
        data = fetch(url)
        if len(data) < 1024:
            raise RuntimeError(f"Downloaded asset unexpectedly small: {url} ({len(data)} bytes)")
        path.write_bytes(data)
        print(f"asset {path}: {len(data)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
