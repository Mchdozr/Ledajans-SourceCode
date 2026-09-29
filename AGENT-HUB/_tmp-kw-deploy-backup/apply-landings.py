from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
URLS = json.loads((Path(__file__).resolve().parent / "media-urls.json").read_text(encoding="utf-8"))

JOBS = [
    ("cephe-led-ekran", ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/cephe-led-ekran.html", int(URLS["cephe-led-ekran.webp:id"])),
    ("pitch-secim-rehberi", ROOT / "SEO-Icerik-Widgets/temel-rehberler/pitch-secim-rehberi.html", int(URLS["pitch-dis-mekan-p10.webp:id"])),
    ("gob-led-ekran", ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/gob-led-ekran.html", int(URLS["gob-led-yuzey.webp:id"])),
    ("fuar-led-ekran", ROOT / "SEO-Icerik-Widgets/kullanim-alanlari/fuar-led-ekran.html", int(URLS["fuar-led-stand.webp:id"])),
    ("magaza-vitrin-led-ekran", ROOT / "SEO-Icerik-Widgets/sektor-rehberleri/magaza-vitrin-led-rehberi.html", int(URLS["magaza-vitrin-led-cadde.webp:id"])),
    ("istanbul-led-ekran", ROOT / "SEO-Icerik-Widgets/sehir-sayfalari/istanbul-led-ekran.html", int(URLS["istanbul-cephe-led-kurulum.webp:id"])),
]


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


def walk_replace(nodes: Any, html: str) -> int:
    n = 0
    if isinstance(nodes, list):
        for item in nodes:
            n += walk_replace(item, html)
        return n
    if not isinstance(nodes, dict):
        return 0
    settings = nodes.get("settings") or {}
    for key in ("html", "editor"):
        val = settings.get(key)
        if isinstance(val, str) and "la-kw" in val:
            settings[key] = html
            nodes["settings"] = settings
            n += 1
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_replace(nodes[key], html)
    return n


def main() -> None:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-KW-Landing/1.0", "Content-Type": "application/json"}
    for slug, path, featured in JOBS:
        html = path.read_text(encoding="utf-8")
        r = requests.get(
            f"{site}/wp-json/wp/v2/pages",
            params={"slug": slug, "context": "edit"},
            auth=auth,
            headers=headers,
            timeout=60,
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            raise RuntimeError(f"missing {slug}")
        page = items[0]
        pid = page["id"]
        raw = (page.get("meta") or {}).get("_elementor_data")
        payload: dict[str, Any] = {"content": html, "featured_media": featured}
        if raw:
            data = json.loads(raw) if isinstance(raw, str) else raw
            changed = walk_replace(data, html)
            payload["meta"] = {
                "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                "_elementor_edit_mode": "builder",
            }
            print(f"{slug} id={pid} elementor_widgets={changed} featured={featured}")
        else:
            print(f"{slug} id={pid} no_elementor featured={featured}")
        u = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json=payload,
            auth=auth,
            headers=headers,
            timeout=120,
        )
        if u.status_code not in (200, 201):
            raise RuntimeError(f"POST {slug} {u.status_code} {u.text[:280]}")
    r = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("elementor_cache", r.status_code)


if __name__ == "__main__":
    main()
