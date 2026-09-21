#!/usr/bin/env python3
"""Outdoor küre LED videosunu 1. proje kartına ekle; yalnızca grid widget'larını güncelle."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Kure-LED/1.0"
WIDGET_FILE = ROOT / "Anasayfa" / "widget-7-projeler.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
OUT_MP4 = ROOT / "assets" / "products" / "outdoor-kure-led-ekran.mp4"
PLACEHOLDER = "__KURE_VIDEO_URL__"
PAGES = (
    (1248, "1beec58"),
    (4956, "3f35913"),
)


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


def find_src() -> Path:
    downloads = Path.home() / "Downloads"
    exact = downloads / "Zaman çizelgesi 1.mp4"
    if exact.is_file():
        return exact
    hits = sorted(downloads.glob("Zaman*.mp4"))
    if hits:
        return hits[0]
    raise FileNotFoundError("Küre LED videosu Downloads içinde yok")


def compress(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "26",
        "-maxrate",
        "900k",
        "-bufsize",
        "1800k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    subprocess.check_call(cmd)
    print("compressed", dest.stat().st_size, "from", src.stat().st_size)
    return dest


def upload(site: str, auth: tuple[str, str], path: Path) -> str:
    with path.open("rb") as fh:
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": UA,
                "Content-Disposition": f'attachment; filename="{path.name}"',
            },
            files={"file": (path.name, fh, "video/mp4")},
            data={
                "title": "Dış Mekan Küre LED Ekran",
                "alt_text": "Dış mekan küre LED ekran — outdoor spherical LED, hazır kurulum",
            },
            timeout=300,
        )
    print("upload", up.status_code)
    if up.status_code not in (200, 201):
        print(up.text[:500])
        raise SystemExit(1)
    url = up.json()["source_url"]
    print("url", url)
    return url


def walk_set(nodes, widget_id: str, html: str) -> int:
    n = 0
    if isinstance(nodes, list):
        return sum(walk_set(x, widget_id, html) for x in nodes)
    if not isinstance(nodes, dict):
        return 0
    if str(nodes.get("id")) == widget_id and nodes.get("widgetType") == "html":
        nodes.setdefault("settings", {})["html"] = html
        n += 1
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_set(nodes[key], widget_id, html)
    return n


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    src = find_src()
    print("src", src, src.stat().st_size)
    compress(src, OUT_MP4)
    if OUT_MP4.stat().st_size > 1_850_000:
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src),
                "-an",
                "-vf",
                "scale=404:-2",
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "28",
                "-maxrate",
                "700k",
                "-bufsize",
                "1400k",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(OUT_MP4),
            ]
        )
        print("recompressed", OUT_MP4.stat().st_size)
    url = upload(site, auth, OUT_MP4)

    html = WIDGET_FILE.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        print("HATA placeholder yok")
        return 2
    html = html.replace(PLACEHOLDER, url)
    WIDGET_FILE.write_text(html, encoding="utf-8")
    print("wrote widget")

    if PREVIEW_FILE.is_file():
        preview = PREVIEW_FILE.read_text(encoding="utf-8")
        marker = '<div class="ledajans-projects-grid">'
        start = html.find(marker)
        end = html.find("</div>", html.find("ledajans-projects-load-more-wrap"))
        if start != -1 and marker in preview and "Dış Mekan Küre LED Ekran" in html:
            # keep preview in sync only if it already has the grid
            if PLACEHOLDER in preview:
                PREVIEW_FILE.write_text(preview.replace(PLACEHOLDER, url), encoding="utf-8")
                print("wrote preview placeholder")
            elif "Dış Mekan Küre LED Ekran" not in preview:
                insert = html[start : html.find(
                    '<article class="ledajans-project-card" data-category="Dış Mekan LED Ekran" data-title="Dış Mekan LED Ekran"',
                    start,
                )]
                old = preview.find(marker)
                if old != -1:
                    PREVIEW_FILE.write_text(
                        preview.replace(marker, insert, 1), encoding="utf-8"
                    )
                    print("wrote preview insert")

    for page_id, widget_id in PAGES:
        rp = requests.get(
            f"{site}/wp-json/wp/v2/pages/{page_id}",
            params={"context": "edit"},
            auth=auth,
            headers={"User-Agent": UA},
            timeout=60,
        )
        print("page_get", page_id, rp.status_code)
        data = json.loads(rp.json()["meta"]["_elementor_data"])
        n = walk_set(data, widget_id, html)
        print("widgets", page_id, widget_id, n)
        if n == 0:
            return 2
        ru = requests.post(
            f"{site}/wp-json/wp/v2/pages/{page_id}",
            json={
                "meta": {
                    "_elementor_data": json.dumps(
                        data, ensure_ascii=False, separators=(",", ":")
                    )
                }
            },
            auth=auth,
            headers={"User-Agent": UA, "Content-Type": "application/json"},
            timeout=180,
        )
        print("page_update", page_id, ru.status_code)
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
    for path in ("/", "/projeler/"):
        live = requests.get(
            f"{site}{path}?nocache=kure1",
            headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            timeout=45,
        )
        print(
            path,
            live.status_code,
            "kure",
            "Dış Mekan Küre LED Ekran" in live.text,
            "url",
            url in live.text,
            "heroes",
            live.text.count('class="ledajans-projects-hero"'),
            "grids",
            live.text.count('class="ledajans-projects-grid"'),
        )
    print("URL", url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
