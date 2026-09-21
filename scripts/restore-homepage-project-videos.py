#!/usr/bin/env python3
"""Eşleşen proje videolarını WP'ye yükle, widget 1beec58 HTML'ini güncelle."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
LOCAL = Path(r"C:\Users\kacma\OneDrive\Masaüstü\Temiz\Ledajans-Projerlerimiz")
WIDGET_FILE = ROOT / "Anasayfa" / "widget-7-projeler.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
UA = "LEDAJANS-Restore-Project-Videos/1.0"
PAGE_ID = 1248
WIDGET_ID = "1beec58"
UPLOAD_TIMEOUT = 600
MAX_UPLOAD_BYTES = 1_900_000

CARDS = [
    (
        "Dış Mekan LED Ekran",
        "https://ledajans.com/wp-content/uploads/2026/03/WhatsApp-Video-2026-03-12-at-11.51.08-AM-1.mp4",
        "WhatsApp Video 2026-03-12 at 11.51.08 AM (1).mp4",
        "WhatsApp-Video-2026-03-12-at-11.51.08-AM-1.mp4",
    ),
    (
        "Dış Mekan LED Kurulum",
        "https://ledajans.com/wp-content/uploads/2026/04/dis-mekan-proje.mp4",
        None,
        "dis-mekan-proje.mp4",
    ),
    (
        "İç Mekan LED Ekran",
        "https://ledajans.com/wp-content/uploads/2026/03/WhatsApp-Video-2026-03-12-at-11.51.07-AM.mp4",
        "WhatsApp Video 2026-03-12 at 11.51.07 AM.mp4",
        "WhatsApp-Video-2026-03-12-at-11.51.07-AM.mp4",
    ),
    (
        "Dış Mekan LED Ekran (Colorlight kullanıldı)",
        "https://ledajans.com/wp-content/uploads/2026/03/WhatsApp-Video-2026-03-12-at-11.51.07-AM-2.mp4",
        "WhatsApp Video 2026-03-12 at 11.51.07 AM (2).mp4",
        "WhatsApp-Video-2026-03-12-at-11.51.07-AM-2.mp4",
    ),
    (
        "Rental LED Ekran (Colorlight kullanıldı)",
        "https://ledajans.com/wp-content/uploads/2026/03/WhatsApp-Video-2026-03-12-at-11.51.07-AM-1.mp4",
        "WhatsApp Video 2026-03-12 at 11.51.07 AM (1).mp4",
        "WhatsApp-Video-2026-03-12-at-11.51.07-AM-1.mp4",
    ),
    (
        "COB-Smart Screen projesi",
        "https://ledajans.com/wp-content/uploads/2026/03/v1.mp4",
        "v1.mp4",
        "v1.mp4",
    ),
    (
        "Mağaza LED Bilgilendirme Ekranı",
        "https://ledajans.com/wp-content/uploads/2026/03/v2-Trim.mp4",
        "v2 - Trim.mp4",
        "v2-Trim.mp4",
    ),
]


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


def norm(name: str) -> str:
    stem = Path(unquote(name)).stem
    s = stem.lower().replace("_", " ")
    s = re.sub(r"[\(\)\[\]\{\}]", " ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def probe(url: str) -> tuple[int, str]:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30, stream=True)
    ct = (r.headers.get("Content-Type") or "").split(";")[0].strip()
    r.close()
    return r.status_code, ct


def ffprobe_json(src: Path, entries: str, kind: str) -> dict:
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            entries,
            "-of",
            "json",
            str(src),
        ]
    )
    data = json.loads(raw)
    if kind == "format":
        return data.get("format") or {}
    streams = data.get("streams") or [{}]
    return streams[0]


def compress_under(src: Path, dest: Path, max_bytes: int = MAX_UPLOAD_BYTES) -> Path:
    if src.stat().st_size <= max_bytes:
        return src
    dest.parent.mkdir(parents=True, exist_ok=True)
    fmt = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(src),
            ]
        )
    )
    dur = float((fmt.get("format") or {}).get("duration") or 8.0)
    width = int(ffprobe_json(src, "stream=width", "stream").get("width") or 720)
    bitrate = int(max_bytes * 8 / dur * 0.85)
    bitrate = max(200_000, min(bitrate, 1_500_000))
    attempts = [(720, bitrate), (540, int(bitrate * 0.7)), (480, int(bitrate * 0.5))]
    last_size = src.stat().st_size
    for max_w, bps in attempts:
        w = min(max_w, width)
        w -= w % 2
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            f"scale={w}:-2",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-b:v",
            str(bps),
            "-maxrate",
            str(int(bps * 1.15)),
            "-bufsize",
            str(int(bps * 2)),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(dest),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print("ffmpeg_err", dest.name, (proc.stderr or "")[-400:])
            continue
        last_size = dest.stat().st_size
        print(f"compress {src.name} -> {last_size} w={w} bps={bps}")
        if last_size <= max_bytes:
            return dest
    raise SystemExit(f"compress_too_big {src.name} {last_size}")


def upload_video(site: str, auth: tuple[str, str], path: Path, filename: str) -> str:
    mime = "video/mp4"
    with path.open("rb") as fh:
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": UA,
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            files={"file": (filename, fh, mime)},
            data={"title": Path(filename).stem, "caption": "LEDAJANS proje videosu"},
            timeout=UPLOAD_TIMEOUT,
        )
    print(f"upload {filename} status={up.status_code} bytes={path.stat().st_size}")
    if up.status_code not in (200, 201):
        print(up.text[:400])
        raise SystemExit(f"upload_fail {filename}")
    url = up.json().get("source_url")
    if not url:
        raise SystemExit(f"upload_no_url {filename}")
    print(f"  source {url}")
    return url


def patch_video_tags(html: str) -> str:
    pat = re.compile(
        r'<video class="ledajans-project-image ledajans-project-video"[^>]*>\s*'
        r"<source\s+([^>]+)/?>",
        re.I,
    )

    def repl(m: re.Match[str]) -> str:
        attrs = m.group(1)
        src_m = re.search(r'(?:data-src|src)="([^"]+)"', attrs)
        url = src_m.group(1) if src_m else ""
        return (
            f'<video class="ledajans-project-image ledajans-project-video" src="{url}" '
            f'muted autoplay loop playsinline preload="metadata">\n'
            f'                <source src="{url}" data-src="{url}" type="video/mp4" />'
        )

    html = pat.sub(repl, html)
    html = html.replace(
        """      .ledajans-project-image-wrap .ledajans-project-video {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }""",
        """      .ledajans-project-image-wrap .ledajans-project-video {
        width: 100%;
        height: 100%;
        display: block;
        object-fit: cover;
        background: #111;
      }""",
    )
    return html


def walk_set_html(nodes, new_html: str) -> int:
    changed = 0
    if isinstance(nodes, list):
        for n in nodes:
            changed += walk_set_html(n, new_html)
        return changed
    if not isinstance(nodes, dict):
        return 0
    settings = nodes.get("settings") or {}
    html_val = settings.get("html")
    is_target = str(nodes.get("id")) == WIDGET_ID or (
        nodes.get("widgetType") == "html"
        and isinstance(html_val, str)
        and "ledajans-proje-listesi" in html_val
    )
    if is_target and isinstance(html_val, str):
        settings["html"] = new_html
        nodes["settings"] = settings
        changed += 1
    for key in ("elements", "content"):
        if key in nodes:
            changed += walk_set_html(nodes[key], new_html)
    return changed


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    try:
        dlt = requests.delete(
            f"{site}/wp-json/wp/v2/media/5114",
            params={"force": "true"},
            auth=auth,
            headers={"User-Agent": UA},
            timeout=60,
        )
        print("delete_test_media", dlt.status_code)
    except requests.RequestException as exc:
        print("delete_test_media_err", type(exc).__name__)

    local_map = {
        norm(p.name): p
        for p in LOCAL.iterdir()
        if p.is_file() and p.suffix.lower() in {".mp4", ".webm", ".mov", ".m4v"}
    }
    needed_norms = {norm(upload_name) for _, _, local_name, upload_name in CARDS if local_name}
    unmatched_local = sorted(
        p.name for n, p in local_map.items() if n not in needed_norms
    )
    print("unmatched_local", unmatched_local)

    mapping: dict[str, str] = {}
    uploaded = 0
    reused = 0
    skipped = []
    results = []

    for title, old_url, local_name, upload_name in CARDS:
        if not local_name:
            skipped.append((title, old_url, "no_local_match"))
            results.append((title, old_url, "SKIP"))
            print(f"SKIP {title} no_local_match {old_url.rsplit('/', 1)[-1]}")
            continue
        path = LOCAL / local_name
        if not path.is_file():
            skipped.append((title, old_url, "missing_file"))
            results.append((title, old_url, "SKIP"))
            print(f"SKIP {title} missing {local_name}")
            continue
        status, ct = probe(old_url)
        print(f"probe {upload_name} {status} {ct}")
        if status == 200 and ct.startswith("video/"):
            mapping[old_url] = old_url
            reused += 1
            results.append((title, old_url, "REUSE"))
            continue
        work = path
        if path.stat().st_size > MAX_UPLOAD_BYTES:
            tmp = Path(tempfile.gettempdir()) / f"ledajans-{upload_name}"
            work = compress_under(path, tmp)
        new_url = upload_video(site, auth, work, upload_name)
        st2, ct2 = probe(new_url)
        print(f"  verify {st2} {ct2}")
        if not (st2 == 200 and ct2.startswith("video/")):
            print("  WARN new url not video/*")
        mapping[old_url] = new_url
        uploaded += 1
        results.append((title, new_url, "UPLOAD"))

    html = WIDGET_FILE.read_text(encoding="utf-8")
    for old, new in mapping.items():
        html = html.replace(old, new)
    html = patch_video_tags(html)
    WIDGET_FILE.write_text(html, encoding="utf-8")
    print("wrote", WIDGET_FILE.name)

    if PREVIEW_FILE.is_file():
        preview = PREVIEW_FILE.read_text(encoding="utf-8")
        for old, new in mapping.items():
            preview = preview.replace(old, new)
        preview = patch_video_tags(preview)
        PREVIEW_FILE.write_text(preview, encoding="utf-8")
        print("wrote", PREVIEW_FILE.as_posix())

    r = requests.post(
        f"{site}/wp-json/ledajans/v1/hero-widget",
        json={"html": html, "page_id": PAGE_ID, "widget_id": WIDGET_ID},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print("hero-widget", r.status_code, r.text[:300])
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
        changed = walk_set_html(data, html)
        print(f"widgets_updated={changed}")
        if changed == 0:
            return 2
        ru = requests.post(
            f"{site}/wp-json/wp/v2/pages/{PAGE_ID}",
            json={
                "status": "publish",
                "meta": {
                    "_elementor_data": json.dumps(
                        data, ensure_ascii=False, separators=(",", ":")
                    ),
                    "_elementor_edit_mode": "builder",
                },
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
            print("purge_err", type(exc).__name__)

    print("\n=== RESULT ===")
    print("uploaded", uploaded, "reused", reused)
    for title, url, kind in results:
        print(f"  {kind} | {title} | {url}")
    for title, url, reason in skipped:
        print(f"  SKIP {reason} | {title} | {url}")
    print("unmatched_local", unmatched_local)
    return 0


if __name__ == "__main__":
    sys.exit(main())
