#!/usr/bin/env python3
"""QA-Auditor: live homepage + Hero.html + media (no secrets)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
HERO = ROOT / "Anasayfa" / "Hero.html"
SITE = "https://ledajans.com"
UA = "LEDAJANS-QA-Auditor/2026-09-22"
ASSETS = [
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-1280.mp4",
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-poster.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/hero-stant-poster-mobile.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/signistanbul-fair-bg.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/ledajans-logo.webp",
    "https://ledajans.com/wp-content/uploads/2026/09/ledajans-logo.jpg",
]
FORBIDDEN_MEDIA = [
    "https://ledajans.com/wp-content/uploads/StantVideo.mp4",
]


def head(url: str) -> tuple[int, str, str]:
    r = requests.head(
        url,
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=30,
        allow_redirects=False,
    )
    ctype = r.headers.get("Content-Type", "")
    clen = r.headers.get("Content-Length", "")
    if r.status_code in (301, 302, 303, 307, 308):
        loc = r.headers.get("Location", "")
        return r.status_code, ctype, loc
    return r.status_code, ctype, clen


def get(url: str, ua: str | None = None) -> requests.Response:
    return requests.get(
        url,
        headers={"User-Agent": ua or UA, "Cache-Control": "no-cache"},
        timeout=45,
    )


def main() -> int:
    html = HERO.read_text(encoding="utf-8")
    print("=== LOCAL HERO ===")
    h1s = re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.I | re.S)
    print("h1_count", len(h1s))
    print("h1", re.sub(r"\s+", " ", h1s[0]).strip() if h1s else None)
    print("noindex", "noindex" in html.lower())
    print("meta_robots", bool(re.search(r'name=["\']robots["\']', html, re.I)))
    print("canonical_in_widget", bool(re.search(r'rel=["\']canonical["\']', html, re.I)))
    print("StantVideo", "StantVideo" in html)
    print("Firefly", "Firefly" in html)
    print("as_video", bool(re.search(r'as=["\']video["\']', html, re.I)))
    print("preload_none", 'preload="none"' in html)
    print("picture", "<picture>" in html)
    print("ldjson_blocks", html.count("application/ld+json"))
    m = re.search(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>\s*\Z',
        html,
        re.S,
    )
    if not m:
        m = re.search(
            r'<script type="application/ld\+json">\s*(\{.*\})\s*</script>',
            html,
            re.S,
        )
    try:
        data = json.loads(m.group(1))
        types = [n.get("@type") for n in data.get("@graph", [])]
        print("schema_parse", "OK")
        print("schema_types", types)
    except Exception as exc:
        print("schema_parse", "FAIL", exc)
        types = []

    print("id_ledajans-video", 'id="ledajans-video"' in html)
    print("cta_hemen", "Hemen Arayın" in html)
    print("tel_sales", "tel:+902122204004" in html)

    hrefs = re.findall(r'href="([^"]+)"', html)
    print("hrefs", hrefs)

    print("=== MEDIA HEAD ===")
    for url in ASSETS:
        code, ctype, extra = head(url)
        print(f"{code} {ctype} {extra} {url.split('/')[-1]}")

    print("=== FORBIDDEN HEAD ===")
    for url in FORBIDDEN_MEDIA:
        try:
            code, ctype, extra = head(url)
            print(f"{code} {ctype} {extra} {url}")
        except Exception as exc:
            print("ERR", url, exc)

    print("=== LIVE HOME ===")
    live = get(SITE + "/")
    print("home_status", live.status_code, "len", len(live.text))
    page = live.text
    robots = re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', page, re.I
    )
    if not robots:
        robots = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']robots["\']',
            page,
            re.I,
        )
    canon = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', page, re.I
    )
    if not canon:
        canon = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            page,
            re.I,
        )
    print("robots", robots.group(1) if robots else "-")
    print("canonical", canon.group(1) if canon else "-")
    print("noindex", "noindex" in page.lower())
    print("live_stant_mp4", "hero-stant-1280.mp4" in page)
    print("live_firefly", "Firefly" in page)
    print("live_stantvideo", "StantVideo" in page)
    print("live_atrium_v2", "hero-atrium-led" in page)
    print("live_q60", "ldajsn2-mobile-q60" in page)
    print("live_widget_h1", "LED Ekran Satış, Kiralama ve Kurulum" in page)
    print("live_ldjson", page.lower().count("application/ld+json"))
    print("live_org", '"@type": "Organization"' in page or '"@type":"Organization"' in page)
    print("live_122e243", "122e243" in page)
    ld_types = []
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        page,
        re.I | re.S,
    ):
        block = block.strip()
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            ld_types.append("PARSE_FAIL")
            continue
        if isinstance(obj, dict) and "@graph" in obj:
            ld_types.append([n.get("@type") for n in obj.get("@graph", [])])
        elif isinstance(obj, dict):
            ld_types.append(obj.get("@type"))
        elif isinstance(obj, list):
            ld_types.append(
                [n.get("@type") if isinstance(n, dict) else type(n).__name__ for n in obj]
            )
        else:
            ld_types.append(type(obj).__name__)
    print("live_ldjson_types", ld_types)
    print("live_w3_about", "ledajans-about" in page)
    print("live_w4_indoor", "ledajans-indoor" in page)
    print("live_w5_outdoor", "ledajans-outdoor" in page)

    print("=== ROBOTS.TXT ===")
    rt = get(SITE + "/robots.txt")
    print("robots_status", rt.status_code)
    print("disallow_slash", re.search(r"(?m)^Disallow:\s*/\s*$", rt.text) is not None)
    print("noindex_in_robots", "noindex" in rt.text.lower())
    print("has_sitemap", "sitemap" in rt.text.lower())
    ascii_lines = []
    for line in rt.text.splitlines()[:25]:
        ascii_lines.append(line.encode("ascii", "replace").decode("ascii"))
    print("robots_head", " || ".join(ascii_lines[:8]))

    print("=== PLUGIN HINT ===")
    print("live_plugin_stant_preload", "hero-stant-poster-mobile.webp" in page)
    print("live_plugin_atrium_preload", "hero-atrium-led-mobile" in page)

    mobile = get(
        SITE + "/",
        ua=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    ).text
    print("mobile_q60", "ldajsn2-mobile-q60" in mobile)
    print("mobile_stant_poster", "hero-stant-poster-mobile.webp" in mobile)
    print("mobile_atrium", "hero-atrium-led" in mobile)
    print("mobile_video_tag_display_none", bool(re.search(
        r"@media \(max-width:\s*768px\)[\s\S]{0,1200}?\.ledajans-hero-video\s*\{\s*display:\s*none",
        mobile,
    )))

    ok_schema = set(types) >= {"Organization", "WebSite", "LocalBusiness"}
    print("LOCAL_SCHEMA_OK", ok_schema)
    return 0 if ok_schema else 1


if __name__ == "__main__":
    sys.exit(main())
