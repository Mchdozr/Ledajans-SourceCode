from __future__ import annotations

import json
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


def titles_of(text: str) -> list[str]:
    return re.findall(r'data-title="([^"]+)"', text)


def main() -> None:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-CHECK/1.0"}
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": "projeler", "context": "edit"},
        auth=auth,
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    page = r.json()[0]
    raw = (page.get("meta") or {}).get("_elementor_data") or ""
    print("pid", page["id"], "el_type", type(raw).__name__, "el_len", len(raw) if isinstance(raw, str) else "n/a")
    blob = raw if isinstance(raw, str) else json.dumps(raw)
    titles = titles_of(blob)
    print("elementor titles", len(titles))
    for i, t in enumerate(titles[:12], 1):
        print(i, t)
    pub = requests.get(
        f"{site}/projeler/",
        headers={**headers, "Cache-Control": "no-cache"},
        timeout=60,
    )
    print("public", pub.status_code, len(pub.text))
    pt = titles_of(pub.text)
    print("public titles", len(pt))
    for i, t in enumerate(pt[:12], 1):
        print("p", i, t)
    for needle in (
        "magaza-vitrin-led-cadde-1.webp",
        "magaza-vitrin-led-cadde.webp",
        "cephe-led-ekran.webp",
        "cephe-led-ekran-bina.webp",
    ):
        print(needle, needle in pub.text)


if __name__ == "__main__":
    main()
