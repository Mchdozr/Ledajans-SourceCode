from __future__ import annotations

import json
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
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-VERIFY/1.0", "Cache-Control": "no-cache"}
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/5001",
        params={"context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    raw = (r.json().get("meta") or {}).get("_elementor_data") or ""
    for needle in (
        "magaza-vitrin-led-cadde-1.webp",
        "magaza-vitrin-led.webp",
        "cephe-led-ekran.webp",
        "cephe-led-ekran-bina.webp",
    ):
        print("el5001", needle, needle in raw)

    pages = {
        "/led-ekran/": ("magaza-vitrin-led-cadde-1.webp", "cephe-led-ekran.webp"),
        "/magaza-vitrin-led-ekran/": ("magaza-vitrin-led-cadde-1.webp",),
        "/istanbul-led-ekran/": ("magaza-vitrin-led-cadde-1.webp", "cephe-led-ekran.webp"),
        "/cephe-led-ekran/": ("cephe-led-ekran.webp",),
        "/projeler/": ("magaza-vitrin-led-cadde-1.webp",),
    }
    for path, needles in pages.items():
        pub = requests.get(site + path, headers=headers, timeout=60)
        print("PUBLIC", path, pub.status_code)
        for needle in needles:
            print(" ", needle, needle in pub.text)
        if path == "/projeler/":
            import re

            titles = re.findall(r'data-title="([^"]+)"', pub.text)
            print("  titles", titles[:4])
        if path == "/led-ekran/":
            print("  old vitrin", "magaza-vitrin-led.webp" in pub.text and "cadde-1" not in pub.text)
            print("  old cephe bina", "cephe-led-ekran-bina.webp" in pub.text)


if __name__ == "__main__":
    main()
