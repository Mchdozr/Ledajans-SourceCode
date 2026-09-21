#!/usr/bin/env python3
"""Anasayfa DIŞ MEKAN bloğuna outdoor cephe görselini yükle ve metin yüksekliğine hizala."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Outdoor-Section-Image/1.0"
PAGE_ID = 1248
WIDGET_FILE = ROOT / "Anasayfa" / "widget-5-Dis-Mekan.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
OUT_DIR = ROOT / "assets" / "products"
SRC = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"7dfb9ce5533c561a018b26f3b896825b_images_Firefly_Gemini_Flash__4_"
    r"-66a9e423-d151-4804-8582-27b47f67b956.jpg"
)
MARKER = "ledajans-outdoor"


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


def to_webp(src: Path, dest: Path) -> tuple[int, int]:
    im = Image.open(src)
    print(f"src size={im.size} mode={im.mode}")
    if im.mode in ("RGBA", "LA"):
        base = Image.new("RGB", im.size, (20, 24, 32))
        base.paste(im, mask=im.split()[-1])
        im = base
    elif im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((1800, 2200), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="WEBP", quality=88, method=6)
    png = dest.with_suffix(".png")
    im.save(png, format="PNG", optimize=True)
    print(f"wrote {dest.name} {im.size} bytes={dest.stat().st_size}")
    return im.size


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
                "title": "Dış Mekan Outdoor LED Ekran",
                "alt_text": "Dış Mekan LED Ekran - Outdoor LED cephe ekranı",
            },
            timeout=180,
        )
    print("upload", up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:400])
        raise SystemExit(1)
    url = up.json().get("source_url")
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
    if nodes.get("widgetType") == "html":
        html_val = (nodes.get("settings") or {}).get("html") or ""
        if MARKER in html_val:
            settings = nodes.get("settings") or {}
            settings["html"] = new_html
            nodes["settings"] = settings
            n += 1
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_set_html(nodes[key], new_html)
    return n


def main() -> int:
    if not SRC.is_file():
        print("HATA: kaynak yok", SRC)
        return 1
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    dest = OUT_DIR / "dis-mekan-outdoor-led-v2.webp"
    w, h = to_webp(SRC, dest)
    shutil.copy2(SRC, OUT_DIR / "dis-mekan-outdoor-led-v2.jpg")
    url = upload(site, auth, dest)

    html = WIDGET_FILE.read_text(encoding="utf-8")
    for old in (
        "https://ledajans.com/wp-content/uploads/2025/12/Basliksiz-5.png",
        "https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-led-ekran.webp",
        "https://ledajans.com/wp-content/uploads/2026/09/dis-mekan-outdoor-led.webp",
    ):
        html = html.replace(old, url)
    html = html.replace('width="1800"', f'width="{w}"')
    html = html.replace('width="1200"', f'width="{w}"')
    html = html.replace('height="1800"', f'height="{h}"')
    html = html.replace('height="1500"', f'height="{h}"')
    if url not in html:
        print("HATA: url widget'ta yok")
        return 2
    WIDGET_FILE.write_text(html, encoding="utf-8")
    print("wrote", WIDGET_FILE.relative_to(ROOT))

    if PREVIEW_FILE.is_file():
        preview = PREVIEW_FILE.read_text(encoding="utf-8")
        start = preview.find("<!-- WIDGET 5")
        if start < 0:
            start = preview.find('<section class="ledajans-outdoor"')
        end = preview.find("<!-- WIDGET 6", start)
        if start >= 0 and end > start:
            PREVIEW_FILE.write_text(preview[:start] + html + "\n\n" + preview[end:], encoding="utf-8")
            print("wrote", PREVIEW_FILE.relative_to(ROOT))

    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("page_get", rp.status_code)
    if rp.status_code != 200:
        print(rp.text[:400])
        return 1
    raw = (rp.json().get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
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
        headers=headers,
        timeout=120,
    )
    print("page_update", ru.status_code, ru.text[:180])
    if ru.status_code not in (200, 201):
        return 1
    dc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("cache_delete", dc.status_code)
    live = requests.get(
        f"{site}/?nocache=outdoor1",
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    )
    print("live", live.status_code, "has_url", url in live.text)
    print("URL", url)
    return 0 if url in live.text else 3


if __name__ == "__main__":
    raise SystemExit(main())
