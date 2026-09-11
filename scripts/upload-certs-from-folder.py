#!/usr/bin/env python3
"""Sertifika PDF + ilk sayfa WebP yükle; anasayfa ve sertifikalarımız HTML güncelle."""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import fitz
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"c:\Users\kacma\OneDrive\Masaüstü\Temiz\Ledajans-Sertifikalar")
OUT_DIR = ROOT / "Anasayfa" / "certs-preview"
BACKUP = ROOT / "AGENT-HUB" / "BACKUPS" / "2026-09-11-certs-media.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
HOME = ROOT / "Anasayfa" / "sertifikalar-anasayfa.html"
PAGE = ROOT / "Kurumsal" / "Sertifikalarimiz" / "sertifikalarimiz.html"

CERTS = [
    {
        "key": "iso-9001",
        "pdf_name": "ISO 9001 2015.pdf",
        "slug": "iso-9001-2015",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/iso-9001-2015.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/iso-9001-2015.pdf",
        "aria": "ISO 9001",
        "alt": "ISO 9001:2015 kalite yönetim sistemi sertifikası önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO 9001:2015 kalite yönetim sistemi sertifikası — LED ekran imalat ve montaj",
    },
    {
        "key": "iso-45001",
        "pdf_name": "ISO 45001 2018.pdf",
        "slug": "iso-45001-2018",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/iso-45001-2018.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/iso-45001-2018.pdf",
        "aria": "ISO 45001",
        "alt": "ISO 45001:2018 iş sağlığı ve güvenliği sertifikası önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO 45001:2018 iş sağlığı ve güvenliği yönetim sistemi sertifikası",
    },
    {
        "key": "iso-14064",
        "pdf_name": "TAHA LED  14064.pdf",
        "slug": "taha-led-14064",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/taha-led-14064.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/taha-led-14064.pdf",
        "aria": "ISO 14064",
        "alt": "ISO 14064-1 sera gazı raporlama uygunluk belgesi önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO 14064-1:2019 sera gazı kurumsal raporlama uygunluk belgesi",
    },
    {
        "key": "iso-10002",
        "pdf_name": "ISO 10002 2018.pdf",
        "slug": "iso-10002-2018",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/iso-10002-2018.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/iso-10002-2018.pdf",
        "aria": "ISO 10002",
        "alt": "ISO 10002:2018 müşteri memnuniyeti belgesi önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO 10002:2018 müşteri memnuniyeti ve şikâyet yönetimi uygunluk belgesi",
    },
    {
        "key": "iso-14001",
        "pdf_name": "ISO 14001 2015.pdf",
        "slug": "iso-14001-2015",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/iso-14001-2015.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/iso-14001-2015.pdf",
        "aria": "ISO 14001",
        "alt": "ISO 14001:2015 çevre yönetimi sertifikası önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO 14001:2015 çevre yönetim sistemi sertifikası",
    },
    {
        "key": "iso-27001",
        "pdf_name": "ISO 27001 2022.pdf",
        "slug": "iso-27001-2022",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/iso-27001-2022.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/iso-27001-2022.pdf",
        "aria": "ISO 27001",
        "alt": "ISO/IEC 27001:2022 bilgi güvenliği sertifikası önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO IEC 27001:2022 bilgi güvenliği yönetim sistemi sertifikası",
    },
    {
        "key": "iso-31000",
        "pdf_name": "ISO 31000 2018.pdf",
        "slug": "iso-31000-2018",
        "old_img": "https://ledajans.com/wp-content/uploads/2026/09/iso-31000-2018.webp",
        "old_pdf": "https://ledajans.com/wp-content/uploads/2026/09/iso-31000-2018.pdf",
        "aria": "ISO 31000",
        "alt": "ISO 31000:2018 kurumsal risk yönetimi belgesi önizlemesi",
        "page_alt": "TAHA LED Dış Ticaret A.Ş. ISO 31000:2018 kurumsal risk yönetimi uygunluk belgesi",
    },
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


def find_pdf(name: str) -> Path:
    direct = SRC / name
    if direct.is_file():
        return direct
    target = " ".join(name.lower().split())
    for p in SRC.iterdir():
        if p.suffix.lower() == ".pdf" and " ".join(p.name.lower().split()) == target:
            return p
    raise FileNotFoundError(name)


def compress_pdf(pdf_path: Path, max_bytes: int = 1_700_000) -> bytes:
    src = fitz.open(pdf_path)
    page = src[0]
    zoom = min(2.0, 1500 / max(page.rect.width, 1))
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    quality = 80
    jpg = io.BytesIO()
    img.save(jpg, format="JPEG", quality=quality, optimize=True)
    while jpg.tell() > max_bytes - 80_000 and quality > 42:
        quality -= 8
        jpg = io.BytesIO()
        img.save(jpg, format="JPEG", quality=quality, optimize=True)
    out = fitz.open()
    rect = fitz.Rect(0, 0, img.width, img.height)
    npage = out.new_page(width=img.width, height=img.height)
    npage.insert_image(rect, stream=jpg.getvalue())
    buf = io.BytesIO()
    out.save(buf, deflate=True, garbage=4)
    src.close()
    out.close()
    data = buf.getvalue()
    print("compress_pdf", pdf_path.name, pdf_path.stat().st_size, "->", len(data), "q", quality)
    return data


def render_webp(pdf_path: Path) -> tuple[bytes, int, int]:
    doc = fitz.open(pdf_path)
    page = doc[0]
    zoom = min(2.4, 1600 / max(page.rect.width, 1))
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    bbox = img.convert("L").point(lambda x: 0 if x < 250 else 255).getbbox()
    if bbox:
        pad = 8
        l, t, r, b = bbox
        img = img.crop(
            (
                max(0, l - pad),
                max(0, t - pad),
                min(img.width, r + pad),
                min(img.height, b + pad),
            )
        )
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=84, method=6)
    doc.close()
    return buf.getvalue(), img.width, img.height


def upload(site: str, auth: tuple[str, str], filename: str, data: bytes, mime: str) -> dict:
    r = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=auth,
        headers={"User-Agent": UA, "Content-Disposition": f'attachment; filename="{filename}"'},
        files={"file": (filename, data, mime)},
        timeout=180,
    )
    print("upload", filename, r.status_code, (r.text or "")[:120].replace("\n", " "))
    if r.status_code not in (200, 201):
        raise RuntimeError(f"upload fail {filename} {r.status_code}")
    return r.json()


def patch_html(mapping: dict[str, dict]) -> None:
    home = HOME.read_text(encoding="utf-8")
    page = PAGE.read_text(encoding="utf-8")
    home = home.replace('loading="lazy"', 'loading="eager"')
    for c in CERTS:
        m = mapping[c["key"]]
        pdf_url = m["pdf_url"]
        img_url = m["img_url"]
        w, h = m["w"], m["h"]
        for blob_name, old, new in (
            ("home_img", c["old_img"], img_url),
            ("home_pdf", c["old_pdf"], pdf_url),
            ("page_img", c["old_img"], img_url),
            ("page_pdf", c["old_pdf"], pdf_url),
        ):
            target = home if blob_name.startswith("home") else page
            if old != new and old in target:
                if blob_name.startswith("home"):
                    home = home.replace(old, new)
                else:
                    page = page.replace(old, new)
        dim_re = re.compile(
            rf'(<img src="{re.escape(img_url)}" )width="\d+" height="\d+"'
        )
        home = dim_re.sub(rf'\1width="{w}" height="{h}"', home)
        page = dim_re.sub(rf'\1width="{w}" height="{h}"', page)
    HOME.write_text(home, encoding="utf-8")
    PAGE.write_text(page, encoding="utf-8")
    print("html_patched", HOME.name, PAGE.name)


def main() -> int:
    apply = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, dict] = {}

    for c in CERTS:
        pdf_path = find_pdf(c["pdf_name"])
        webp, w, h = render_webp(pdf_path)
        preview = OUT_DIR / f"{c['slug']}.webp"
        preview.write_bytes(webp)
        print("preview", c["key"], pdf_path.name, pdf_path.stat().st_size, "webp", len(webp), f"{w}x{h}")
        if not apply:
            mapping[c["key"]] = {
                "pdf_local": str(pdf_path),
                "img_local": str(preview),
                "w": w,
                "h": h,
            }
            continue
        raw_pdf = pdf_path.read_bytes()
        try:
            pdf_media = upload(site, auth, f"{c['slug']}.pdf", raw_pdf, "application/pdf")
        except RuntimeError:
            pdf_media = upload(site, auth, f"{c['slug']}.pdf", compress_pdf(pdf_path), "application/pdf")
        img_media = upload(site, auth, f"{c['slug']}.webp", webp, "image/webp")
        mapping[c["key"]] = {
            "pdf_url": pdf_media.get("source_url"),
            "pdf_id": pdf_media.get("id"),
            "img_url": img_media.get("source_url"),
            "img_id": img_media.get("id"),
            "w": w,
            "h": h,
        }

    BACKUP.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print("map", BACKUP.name)
    if not apply:
        print("DRY_RUN: medya/html yazilmadi")
        return 0
    patch_html(mapping)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
