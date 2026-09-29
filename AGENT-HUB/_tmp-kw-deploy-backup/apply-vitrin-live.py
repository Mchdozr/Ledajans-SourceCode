from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load_mod(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    land = load_mod("apply_land", "apply-landings.py")
    el = load_mod("apply_el", "apply-elementor.py")
    site, user, pw = land.load_env()
    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-VITRIN-LIVE/1.0", "Content-Type": "application/json"}

    jobs = [
        ("magaza-vitrin-led-ekran", ROOT / "SEO-Icerik-Widgets/sektor-rehberleri/magaza-vitrin-led-rehberi.html", 5836),
        ("istanbul-led-ekran", ROOT / "SEO-Icerik-Widgets/sehir-sayfalari/istanbul-led-ekran.html", int(
            json.loads((HERE / "media-urls.json").read_text(encoding="utf-8"))["istanbul-cephe-led-kurulum.webp:id"]
        )),
        ("projeler", ROOT / "Anasayfa/widget-7-projeler.html", 5836),
    ]
    for slug, path, featured in jobs:
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
        payload: dict = {"content": html, "featured_media": featured}
        if raw:
            data = json.loads(raw) if isinstance(raw, str) else raw
            changed = land.walk_replace(data, html)
            payload["meta"] = {
                "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                "_elementor_edit_mode": "builder",
            }
            print(f"{slug} id={pid} elementor={changed}")
        else:
            print(f"{slug} id={pid} content_only")
        u = requests.post(f"{site}/wp-json/wp/v2/pages/{pid}", json=payload, auth=auth, headers=headers, timeout=120)
        if u.status_code not in (200, 201):
            raise RuntimeError(f"POST {slug} {u.status_code} {u.text[:240]}")

    data = el.load_el(site, auth, headers, 5001)
    n = el.walk(data, el.hub_fn)
    el.save_page(site, auth, headers, 5001, data)
    print(f"hub 5001 widgets={n}")
    c = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("elementor_cache", c.status_code)


if __name__ == "__main__":
    main()
