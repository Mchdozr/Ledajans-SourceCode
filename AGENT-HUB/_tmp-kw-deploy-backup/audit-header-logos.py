from __future__ import annotations

import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")
SITE = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
AUTH = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
H = {"User-Agent": "Mozilla/5.0 LEDAJANS-LOGO"}

r = requests.get(f"{SITE}/wp-json/wp/v2/elementor_snippet/5026", auth=AUTH, headers=H, timeout=40)
code = (r.json().get("meta") or {}).get("_elementor_code") or ""
print("snippet_len", len(code))
print("has_logo_swap", "ledajans-logo-swap" in code)
print("has_logo_places", "ledajans-logo-places" in code)
print("2022_web", "ledajans-logo-web.jpg" in code)
print("2022_png", "LedajansLogo.png" in code)
print("2026_webp", "2026/09/ledajans-logo.webp" in code)
print("2026_08", "2026/08/LedajansLogo.webp" in code)

# extract script ids
print("scripts", re.findall(r'<script id="([^"]+)"', code))

PAGES = ["/", "/led-ekran/", "/gob-led-nedir/", "/hakkimizda/", "/blog/", "/huidu-c08l-controller/", "/en/home-en/"]
for path in PAGES:
    html = requests.get(f"https://ledajans.com{path}", headers=H, timeout=35).text
    logos = re.findall(
        r'(?:site-branding-logo|logo-mm)[^>]*>[\s\S]{0,80}?src="([^"]+)"',
        html,
        re.I,
    )
    all_logo = re.findall(r'src="(https://ledajans.com/wp-content/uploads/[^"]*[Ll]ogo[^"]*)"', html)
    uniq = []
    for u in logos + all_logo:
        if u not in uniq:
            uniq.append(u)
    print(f"\n{path}")
    for u in uniq[:8]:
        print(" ", u)
