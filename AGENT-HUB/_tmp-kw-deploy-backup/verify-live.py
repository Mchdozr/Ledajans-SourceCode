from __future__ import annotations

import base64
import time
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

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
user, pw = env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", "")
token = base64.b64encode(f"{user}:{pw}".encode()).decode("ascii")
auth = (user, pw)
headers = {
    "User-Agent": "LEDAJANS-KW-Verify/1.0",
    "Authorization": f"Basic {token}",
    "X-WP-Authorization": f"Basic {token}",
}

r = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
print("elementor_cache", r.status_code)

r = requests.post(f"{site}/wp-json/ledajans/v1/purge", auth=auth, headers=headers, timeout=60)
print("ledajans_purge", r.status_code, r.text[:180])

time.sleep(2)

checks = {
    "/led-ekran/": [
        "Kullanım senaryoları",
        "pitch-secim-rehberi",
        "gob-led-ekran",
        "/led-ekran-fiyatlari-2026/",
        "cephe-led-ekran",
        "magaza-vitrin-led",
    ],
    "/cob-ekran/": ["gob-led-ekran", "pitch-secim-rehberi"],
    "/ic-mekan-led-ekran/": ["pitch-secim-rehberi", "/p2-vs-p3-led-ekran/"],
    "/dis-mekan-led-ekran/": ["/dis-mekan-led-ekran-fiyatlari/", "cephe-led-ekran"],
    "/rental-led-ekran/": ["fuar-led-ekran", "pitch-secim-rehberi"],
    "/cephe-led-ekran/": ["la-kw", "cephe"],
    "/pitch-secim-rehberi/": ["la-kw", "pitch"],
    "/gob-led-ekran/": ["la-kw", "GOB"],
    "/magaza-vitrin-led-rehberi/": ["la-kw"],
    "/fuar-led-ekran/": ["la-kw"],
    "/istanbul-led-ekran/": ["istanbul"],
}

ua = {
    "User-Agent": "Mozilla/5.0 LEDAJANS-KW-Verify",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
bust = str(int(time.time()))
out_dir = ROOT / "AGENT-HUB/_tmp-kw-deploy-backup"
for path, needles in checks.items():
    url = f"{site}{path}?nocache={bust}"
    rr = requests.get(url, headers=ua, timeout=40, allow_redirects=True)
    html = rr.text
    slug = path.strip("/").replace("/", "-") or "home"
    (out_dir / f"live-{slug}.html").write_text(html, encoding="utf-8")
    found = {n: (n in html) for n in needles}
    print(rr.status_code, rr.url.split("?")[0], found, "len", len(html))

# cephe alias
rr = requests.get(
    f"{site}/dis-cephe-led-ekran/?nocache={bust}",
    headers=ua,
    timeout=20,
    allow_redirects=False,
)
print(
    "alias /dis-cephe-led-ekran/",
    rr.status_code,
    rr.headers.get("Location", ""),
    rr.headers.get("X-Redirect-By", ""),
)
