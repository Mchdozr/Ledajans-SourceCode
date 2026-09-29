from __future__ import annotations

import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]


def load_env() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return (
        env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        env["WP_USERNAME"],
        env["WP_APP_PASSWORD"].replace(" ", ""),
    )


def main() -> None:
    site, user, pw = load_env()
    headers = {"User-Agent": "LEDAJANS-VERIFY2/1.0", "Cache-Control": "no-cache"}
    media = [
        "https://ledajans.com/wp-content/uploads/2026/09/magaza-vitrin-led-cadde-1.webp",
        "https://ledajans.com/wp-content/uploads/2026/09/cephe-led-ekran.webp",
    ]
    for url in media:
        h = requests.head(url, headers=headers, timeout=30, allow_redirects=True)
        print("HEAD", url.split("/")[-1], h.status_code, h.headers.get("Content-Type"), h.headers.get("Content-Length"))
    auth = (user, pw)
    for mid in (5837, 5838):
        r = requests.get(f"{site}/wp-json/wp/v2/media/{mid}", auth=auth, headers=headers, timeout=30)
        js = r.json()
        print("media", mid, "alt", js.get("alt_text"), "src", js.get("source_url"))

    pages = [
        "/led-ekran/",
        "/magaza-vitrin-led-ekran/",
        "/istanbul-led-ekran/",
        "/cephe-led-ekran/",
        "/projeler/",
    ]
    old_vitrin = re.compile(r"magaza-vitrin-led\.webp")
    old_cephe = re.compile(r"cephe-led-ekran-bina\.webp")
    for path in pages:
        pub = requests.get(site + path, headers=headers, timeout=60)
        html = pub.text
        print(
            path,
            "new_vitrin",
            html.count("magaza-vitrin-led-cadde-1.webp"),
            "new_cephe",
            html.count("/cephe-led-ekran.webp"),
            "old_vitrin",
            len(old_vitrin.findall(html)),
            "old_cephe",
            len(old_cephe.findall(html)),
        )


if __name__ == "__main__":
    main()
