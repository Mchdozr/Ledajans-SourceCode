#!/usr/bin/env python3
"""Dış Mekan LED Ekran Referans kartına EspressoLab görseli (video/gif değil)."""
from __future__ import annotations

import json
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Project-Ref-Image/1.0"
PAGE_ID = 1248
WIDGET_ID = "1beec58"
WIDGET_FILE = ROOT / "Anasayfa" / "widget-7-projeler.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
OUT_DIR = ROOT / "assets" / "products"
SRC = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"7dfb9ce5533c561a018b26f3b896825b_images_WhatsApp_Image_2026-09-18_at_"
    r"1.21.13_PM-69c6f06e-ac5b-437a-b826-d1dc431f438f.jpg"
)
OLD = "https://ledajans.com/wp-content/uploads/2026/04/dis-mekan-led-ekran.gif"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def to_webp(src: Path, dest: Path) -> None:
    im = Image.open(src)
    print("src", im.size, im.mode)
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="WEBP", quality=86, method=6)
    print("webp", dest.name, im.size, dest.stat().st_size)


def upload(site: str, auth: tuple[str, str], path: Path) -> str:
    with path.open("rb") as fh:
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": UA,
                "Content-Disposition": f'attachment; filename="{path.name}"',
            },
            files={"file": (path.name, fh, "image/webp")},
            data={
                "title": "Dış Mekan LED Ekran Referans EspressoLab",
                "alt_text": "Dış mekan LED ekran referans — EspressoLab cephe LED tabela",
            },
            timeout=120,
        )
    print("upload", up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:400])
        raise SystemExit(1)
    url = up.json()["source_url"]
    print("url", url)
    return url


def walk_set_html(nodes, new_html: str) -> int:
    n = 0
    if isinstance(nodes, list):
        for x in nodes:
            n += walk_set_html(x, new_html)
        return n
    if not isinstance(nodes, dict):
        return 0
    html_val = (nodes.get("settings") or {}).get("html")
    is_target = str(nodes.get("id")) == WIDGET_ID or (
        nodes.get("widgetType") == "html"
        and isinstance(html_val, str)
        and "ledajans-proje-listesi" in html_val
    )
    if is_target and isinstance(html_val, str):
        nodes.setdefault("settings", {})["html"] = new_html
        n += 1
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_set_html(nodes[key], new_html)
    return n


def main() -> int:
    if not SRC.is_file():
        print("HATA kaynak yok", SRC)
        return 1
    site, user, pw = load_env()
    auth = (user, pw)
    dest = OUT_DIR / "dis-mekan-led-ekran-referans.webp"
    to_webp(SRC, dest)
    url = upload(site, auth, dest)

    html = WIDGET_FILE.read_text(encoding="utf-8")
    old_block = (
        'data-media-type="image" data-media-src="'
        + OLD
        + '">\n            <div class="ledajans-project-image-wrap ledajans-project-image-wrap--shift-up">\n'
        '              <img class="ledajans-project-image" src="'
        + OLD
        + '" alt="Dış mekan LED ekran proje görseli" loading="lazy" />'
    )
    new_block = (
        'data-media-type="image" data-media-src="'
        + url
        + '">\n            <div class="ledajans-project-image-wrap ledajans-project-image-wrap--cover">\n'
        '              <img class="ledajans-project-image" src="'
        + url
        + '" alt="Dış mekan LED ekran referans — EspressoLab cephe LED tabela" loading="lazy" decoding="async" />'
    )
    if old_block not in html:
        print("HATA kart blogu bulunamadi")
        return 2
    html = html.replace(old_block, new_block, 1)
    WIDGET_FILE.write_text(html, encoding="utf-8")
    print("wrote widget")

    if PREVIEW_FILE.is_file():
        preview = PREVIEW_FILE.read_text(encoding="utf-8")
        if OLD in preview:
            PREVIEW_FILE.write_text(preview.replace(old_block, new_block), encoding="utf-8")
            print("wrote preview")

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("page_get", rp.status_code)
    data = json.loads(rp.json()["meta"]["_elementor_data"])
    changed = walk_set_html(data, html)
    print("widgets_updated", changed)
    if changed == 0:
        return 2
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        json={
            "meta": {
                "_elementor_data": json.dumps(
                    data, ensure_ascii=False, separators=(",", ":")
                )
            }
        },
        auth=auth,
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        timeout=120,
    )
    print("page_update", ru.status_code)
    if ru.status_code not in (200, 201):
        print(ru.text[:300])
        return 1
    dc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("cache_delete", dc.status_code)
    live = requests.get(
        f"{site}/?nocache=projeref1",
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    )
    print("live_has_url", url in live.text, "still_gif", OLD in live.text)
    print("URL", url)
    return 0 if url in live.text and OLD not in live.text else 3


if __name__ == "__main__":
    raise SystemExit(main())
