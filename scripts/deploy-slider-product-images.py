#!/usr/bin/env python3
"""COB + Dis Mekan RGB slider gorsellerini WP'ye yukle ve widget 70ca80d'yi tek seferde guncelle."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Slider-Product-Images/1.0"
PAGE_ID = 1248
WIDGET_ID = "70ca80d"
WIDGET_FILE = ROOT / "Anasayfa" / "widget-6-Urunlerimiz-Slider.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
LED_FILE = ROOT / "LED Ekran" / "led-ekran.html"
LED_PREVIEW = ROOT / "local-preview" / "led-ekran.html"
OUT_DIR = ROOT / "assets" / "products"

COB_SRC = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"7dfb9ce5533c561a018b26f3b896825b_images_Ba_l_ks_z-6__4_-2be1487a-34db-44cc-b71d-2cab55371bd8.png"
)
DIS_SRC = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode"
    r"\assets\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"7dfb9ce5533c561a018b26f3b896825b_images_Ba_l_ks_z-6__11_-cd95e38f-1d0c-4627-ac4b-18e2e00103f2.png"
)

OLD_COB = "https://ledajans.com/wp-content/uploads/2025/11/Basliksiz-6-7.png"
OLD_DIS = "https://ledajans.com/wp-content/uploads/2026/02/DisMekanRGBPanel.png"


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


def to_webp(src: Path, dest: Path, bg: tuple[int, int, int]) -> None:
    im = Image.open(src)
    print(f"src {dest.stem}: size={im.size} mode={im.mode} fmt={im.format}")
    if im.mode in ("RGBA", "LA"):
        base = Image.new("RGB", im.size, bg)
        base.paste(im, mask=im.split()[-1])
        im = base
    elif im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((1600, 900), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="WEBP", quality=82, method=6)
    png = dest.with_suffix(".png")
    im.save(png, format="PNG", optimize=True)
    print(f"wrote {dest.name} bytes={dest.stat().st_size} png={png.stat().st_size}")


def upload(site: str, auth: tuple[str, str], path: Path, title: str, alt: str) -> str:
    with path.open("rb") as fh:
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": UA,
                "Content-Disposition": f'attachment; filename="{path.name}"',
            },
            files={"file": (path.name, fh, "image/webp")},
            data={"title": title, "alt_text": alt},
            timeout=120,
        )
    print(f"upload {path.name} status={up.status_code}")
    if up.status_code not in (200, 201):
        print(up.text[:400])
        raise SystemExit(1)
    url = up.json().get("source_url")
    print(f"url {path.stem}={url}")
    return url


def patch_widget(html: str, cob_url: str, dis_url: str) -> str:
    html = html.replace(
        f'<div style="height: 256px; overflow: hidden;">\n'
        f'                <img src="{OLD_COB}" alt="COB - Smart Screen" '
        f'loading="lazy" decoding="async" style="width: 100%; height: 100%; '
        f'object-fit: cover; transition: transform 0.5s;">',
        f'<div style="height: 256px; overflow: hidden; background: #fff; '
        f'padding: 12px; box-sizing: border-box;">\n'
        f'                <img src="{cob_url}" alt="COB - Smart Screen" '
        f'loading="lazy" decoding="async" style="width: 100%; height: 100%; '
        f'object-fit: contain; transition: transform 0.5s;">',
    )
    html = html.replace(
        f'<div style="height: 256px; overflow: hidden;">\n'
        f'                <img src="{OLD_DIS}" alt="Dış Mekan RGB Panel" '
        f'loading="lazy" decoding="async" style="width: 100%; height: 100%; '
        f'object-fit: cover; transition: transform 0.5s;">',
        f'<div style="height: 256px; overflow: hidden; background: #000; '
        f'padding: 12px; box-sizing: border-box;">\n'
        f'                <img src="{dis_url}" alt="Dış Mekan RGB Panel" '
        f'loading="lazy" decoding="async" style="width: 100%; height: 100%; '
        f'object-fit: contain; transition: transform 0.5s;">',
    )
    if OLD_COB in html or OLD_DIS in html:
        print("WARN: old urls still in widget html")
    if cob_url not in html or dis_url not in html:
        print("HATA: widget patch failed")
        raise SystemExit(2)
    return html


def walk_set_html(nodes, new_html: str) -> int:
    n = 0
    if isinstance(nodes, list):
        for x in nodes:
            n += walk_set_html(x, new_html)
        return n
    if not isinstance(nodes, dict):
        return 0
    if nodes.get("id") == WIDGET_ID and nodes.get("widgetType") == "html":
        settings = nodes.get("settings") or {}
        settings["html"] = new_html
        nodes["settings"] = settings
        n += 1
    elif nodes.get("widgetType") == "html":
        html_val = (nodes.get("settings") or {}).get("html") or ""
        if "products-slider-section" in html_val:
            settings = nodes.get("settings") or {}
            settings["html"] = new_html
            nodes["settings"] = settings
            n += 1
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_set_html(nodes[key], new_html)
    return n


def replace_file(path: Path, mapping: dict[str, str]) -> int:
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in mapping.items():
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        print(f"updated {path.relative_to(ROOT)}")
        return 1
    return 0


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    cob_webp = OUT_DIR / "cob-smart-screen.webp"
    dis_webp = OUT_DIR / "dis-mekan-rgb-panel.webp"
    to_webp(COB_SRC, cob_webp, (255, 255, 255))
    to_webp(DIS_SRC, dis_webp, (0, 0, 0))

    cob_url = upload(site, auth, cob_webp, "COB Smart Screen", "COB - Smart Screen")
    dis_url = upload(
        site, auth, dis_webp, "Dis Mekan RGB Panel", "Dış Mekan RGB Panel"
    )

    widget_html = patch_widget(WIDGET_FILE.read_text(encoding="utf-8"), cob_url, dis_url)
    WIDGET_FILE.write_text(widget_html, encoding="utf-8")
    print(f"wrote {WIDGET_FILE.relative_to(ROOT)}")

    if PREVIEW_FILE.is_file():
        preview = PREVIEW_FILE.read_text(encoding="utf-8")
        if OLD_COB in preview and OLD_DIS in preview:
            PREVIEW_FILE.write_text(patch_widget(preview, cob_url, dis_url), encoding="utf-8")
            print(f"wrote {PREVIEW_FILE.relative_to(ROOT)}")
        else:
            replace_file(PREVIEW_FILE, {OLD_COB: cob_url, OLD_DIS: dis_url})

    mapping = {OLD_COB: cob_url, OLD_DIS: dis_url}
    for p in (LED_FILE, LED_PREVIEW):
        replace_file(p, mapping)

    r = requests.post(
        f"{site}/wp-json/ledajans/v1/hero-widget",
        json={"html": widget_html, "page_id": PAGE_ID, "widget_id": WIDGET_ID},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print("hero-widget", r.status_code, r.text[:400])
    if r.status_code not in (200, 201):
        rp = requests.get(
            f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
            params={"context": "edit"},
            auth=auth,
            headers={"User-Agent": UA},
            timeout=60,
        )
        print(f"page_get={rp.status_code}")
        if rp.status_code != 200:
            print(rp.text[:400])
            return 1
        raw = (rp.json().get("meta") or {}).get("_elementor_data")
        data = json.loads(raw) if isinstance(raw, str) else raw
        changed = walk_set_html(data, widget_html)
        print(f"widgets_updated={changed}")
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
        print(f"page_update={ru.status_code} {ru.text[:200]}")
        if ru.status_code not in (200, 201):
            return 1

    for path in (
        "/wp-json/ledajans/v1/purge",
        "/?LSCWP_CTRL=purge&litespeed_type=purge_all",
    ):
        try:
            pr = requests.get(
                site + path,
                auth=auth,
                headers={"User-Agent": UA, "Cache-Control": "no-cache"},
                timeout=30,
            )
            print("purge", path.split("?")[0], pr.status_code)
        except requests.RequestException as exc:
            print("purge_err", path, type(exc).__name__)

    live = requests.get(
        site + "/?nocache=slider-imgs-1",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Cache-Control": "no-cache",
        },
        timeout=45,
    )
    print("live", live.status_code, "len", len(live.text))
    print("live_cob", cob_url in live.text)
    print("live_dis", dis_url in live.text)
    print("live_old_cob", OLD_COB in live.text)
    print("live_old_dis", OLD_DIS in live.text)
    print("COB_URL=" + cob_url)
    print("DIS_URL=" + dis_url)
    return 0 if cob_url in live.text and dis_url in live.text else 3


if __name__ == "__main__":
    sys.exit(main())
