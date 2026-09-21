#!/usr/bin/env python3
"""Anasayfa blog slider kapak gorSellerini yukle, featured media ata, widget 585fac3 guncelle."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Blog-Card-Images/1.0"
PAGE_ID = 1248
WIDGET_ID = "585fac3"
WIDGET_FILE = ROOT / "Anasayfa" / "widget-9-Blog.html"
PREVIEW_FILE = ROOT / "local-preview" / "anasayfa.html"
OUT_DIR = ROOT / "assets" / "blog-cards"
GEN_DIR = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode\assets"
)

POSTS = [
    {
        "id": 5022,
        "src": "blog-huidu-wf-kontrol-karti.png",
        "stem": "huidu-wf1-wf2-wf4",
        "alt": "Huidu LED Kontrol Kartı: WF1, WF2 ve WF4 Karşılaştırma Rehberi",
    },
    {
        "id": 5021,
        "src": "blog-cob-led-ekran-nedir-v2.png",
        "stem": "cob-led-ekran-nedir",
        "alt": "COB LED Ekran Nedir? Avantajları ve Ne Zaman Tercih Edilmeli",
    },
    {
        "id": 5000,
        "src": "blog-gob-led-ekran.png",
        "stem": "gob-led-ekran",
        "alt": "GOB LED Ekran Ne Zaman Tercih Edilir?",
    },
    {
        "id": 4999,
        "src": "blog-led-ekran-nasil-secilir-v3.png",
        "stem": "led-ekran-nasil-secilir",
        "alt": "LED Ekran Nasıl Seçilir? 2026 Rehber",
    },
    {
        "id": 4998,
        "src": "blog-rental-led-ekran-v3.png",
        "stem": "rental-led-ekran-kiralama",
        "alt": "Rental LED Ekran Kiralama Fiyatları 2026",
    },
    {
        "id": 4997,
        "src": "blog-dis-mekan-led-ekran.png",
        "stem": "dis-mekan-led-ekran-fiyatlari",
        "alt": "Dış Mekan LED Ekran Fiyatları 2026",
    },
    {
        "id": 4996,
        "src": "blog-ic-mekan-led-ekran-v3.png",
        "stem": "ic-mekan-led-ekran-fiyatlari",
        "alt": "İç Mekan LED Ekran Fiyatları 2026",
    },
    {
        "id": 4995,
        "src": "blog-led-ekran-fiyatlari-v3.png",
        "stem": "led-ekran-fiyatlari-2026",
        "alt": "LED Ekran Fiyatları 2026 (Mayıs Güncel)",
    },
    {
        "id": 4949,
        "src": "blog-colorlight-a60-player-v4.png",
        "stem": "colorlight-a60-player",
        "alt": "Colorlight A60 Player",
    },
    {
        "id": 4891,
        "src": "blog-huidu-c08l-controller.png",
        "stem": "huidu-c08l-controller",
        "alt": "Huidu C08L Controller Kartı",
    },
]

MONTHS = [
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
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


def to_webp(src: Path, dest: Path) -> None:
    im = Image.open(src)
    print(f"src {dest.stem}: size={im.size} mode={im.mode}")
    if im.mode in ("RGBA", "LA"):
        base = Image.new("RGB", im.size, (243, 244, 246))
        base.paste(im, mask=im.split()[-1])
        im = base
    elif im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((1280, 800), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, format="WEBP", quality=82, method=6)
    png = dest.with_suffix(".png")
    im.save(png, format="PNG", optimize=True)
    print(f"wrote {dest.name} bytes={dest.stat().st_size}")


def upload(site: str, auth: tuple[str, str], path: Path, title: str, alt: str) -> tuple[int, str]:
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
    body = up.json()
    mid = int(body["id"])
    url = body.get("source_url") or ""
    print(f"media {mid} {url}")
    return mid, url


def set_featured(site: str, auth: tuple[str, str], post_id: int, media_id: int) -> None:
    r = requests.post(
        f"{site}/wp-json/wp/v2/posts/{post_id}",
        json={"featured_media": media_id},
        auth=auth,
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        timeout=60,
    )
    print(f"featured post={post_id} media={media_id} status={r.status_code}")
    if r.status_code not in (200, 201):
        print(r.text[:400])
        raise SystemExit(1)


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def excerpt_of(text: str, n: int = 150) -> str:
    clean = re.sub(r"\s+", " ", strip_html(text)).strip()
    if len(clean) <= n:
        return clean
    return clean[:n].rstrip() + "..."


def format_date(iso: str) -> str:
    y, m, d = iso[:10].split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def static_cards(posts_meta: list[dict], covers: dict[int, str]) -> str:
    parts = []
    for p in posts_meta:
        pid = int(p["id"])
        url = covers[pid]
        title = strip_html(p["title"]["rendered"])
        href = p["link"]
        date = format_date(p.get("date") or "")
        excerpt = excerpt_of((p.get("excerpt") or {}).get("rendered") or "")
        parts.append(
            '<a href="'
            + html.escape(href, quote=True)
            + '" class="ledajans-blog-card-wrap">'
            + '<article class="ledajans-blog-card">'
            + '<div class="ledajans-blog-card-image">'
            + '<img src="'
            + html.escape(url, quote=True)
            + '" alt="'
            + html.escape(title, quote=True)
            + '" width="640" height="400" loading="lazy" decoding="async">'
            + "</div>"
            + '<div class="ledajans-blog-card-body">'
            + '<p class="ledajans-blog-card-date">'
            + html.escape(date)
            + "</p>"
            + '<h3 class="ledajans-blog-card-title">'
            + title
            + "</h3>"
            + '<p class="ledajans-blog-card-excerpt">'
            + html.escape(excerpt)
            + "</p>"
            + '<span class="ledajans-blog-card-link">Devamını Oku <span class="arrow"></span></span>'
            + "</div></article></a>"
        )
    return "\n          ".join(parts)


def patch_widget(src: str, covers: dict[int, str], cards_html: str) -> str:
    html_out = src
    old_css = """    .ledajans-blog-card-image img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.7s ease;
    }"""
    new_css = """    .ledajans-blog-card-image img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
      display: block;
      transition: transform 0.7s ease;
    }"""
    if old_css in html_out:
        html_out = html_out.replace(old_css, new_css)

    cover_js = "var COVER_BY_ID = " + json.dumps(
        {str(k): v for k, v in covers.items()}, ensure_ascii=False
    ) + ";\n    "
    if "var COVER_BY_ID" not in html_out:
        html_out = html_out.replace(
            "var track = document.getElementById('ledajans-blog-track');\n",
            "var track = document.getElementById('ledajans-blog-track');\n    "
            + cover_js,
            1,
        )
    else:
        html_out = re.sub(
            r"var COVER_BY_ID = \{.*?\};",
            "var COVER_BY_ID = "
            + json.dumps({str(k): v for k, v in covers.items()}, ensure_ascii=False)
            + ";",
            html_out,
            count=1,
            flags=re.S,
        )

    old_get = """    function getFeaturedImage(post) {
      if (post._embedded && post._embedded['wp:featuredmedia'] && post._embedded['wp:featuredmedia'][0]) {
        var fm = post._embedded['wp:featuredmedia'][0];
        return fm.source_url || (fm.media_details && fm.media_details.sizes && fm.media_details.sizes.medium_large && fm.media_details.sizes.medium_large.source_url) || '';
      }
      if (post.content && post.content.rendered) {
        var contentImage = getImageFromContent(post.content.rendered);
        if (contentImage) return contentImage;
      }
      return '';
    }"""
    new_get = """    function getFeaturedImage(post) {
      if (post._embedded && post._embedded['wp:featuredmedia'] && post._embedded['wp:featuredmedia'][0]) {
        var fm = post._embedded['wp:featuredmedia'][0];
        var u = fm.source_url || (fm.media_details && fm.media_details.sizes && fm.media_details.sizes.medium_large && fm.media_details.sizes.medium_large.source_url) || '';
        if (u) return u;
      }
      if (post.id && COVER_BY_ID[post.id]) return COVER_BY_ID[post.id];
      return '';
    }"""
    if old_get in html_out:
        html_out = html_out.replace(old_get, new_get)

    old_img = """        ? '<img src="' + escAttr(imageUrl) + '" alt="' + escAttr(titlePlain) + '" loading="lazy" decoding="async">'"""
    new_img = """        ? '<img src="' + escAttr(imageUrl) + '" alt="' + escAttr(titlePlain) + '" width="640" height="400" loading="lazy" decoding="async">'"""
    html_out = html_out.replace(old_img, new_img)

    old_err = """        .catch(function(error) {
          console.error('Blog yazıları yüklenirken hata:', error);
          track.innerHTML = '<div class="ledajans-blog-error">Blog yazıları yüklenirken bir hata oluştu.</div>';
        });"""
    new_err = """        .catch(function(error) {
          console.error('Blog yazıları yüklenirken hata:', error);
          if (!track.querySelector('.ledajans-blog-card')) {
            track.innerHTML = '<div class="ledajans-blog-error">Blog yazıları yüklenirken bir hata oluştu.</div>';
          }
        });"""
    html_out = html_out.replace(old_err, new_err)

    html_out = re.sub(
        r'(<div id="ledajans-blog-track" class="ledajans-blog-track">)[\s\S]*?(</div>\s*</div>\s*</div>\s*</section>)',
        r"\1\n          " + cards_html + r"\n        \2",
        html_out,
        count=1,
    )
    return html_out


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
    for key in ("elements", "content"):
        if key in nodes:
            n += walk_set_html(nodes[key], new_html)
    return n


def sync_preview(widget_html: str) -> None:
    if not PREVIEW_FILE.is_file():
        return
    preview = PREVIEW_FILE.read_text(encoding="utf-8")
    block = (
        "\n<!-- WIDGET 9 — Blog slider -->\n"
        "<script>window.LEDajansWpJsonBase='https://ledajans.com';</script>\n"
        + widget_html
        + "\n"
    )
    if 'class="ledajans-blog"' in preview or "class='ledajans-blog'" in preview:
        preview = re.sub(
            r"\n<!-- WIDGET 9 — Blog slider -->[\s\S]*?</script>\s*(?=</div>\s*</body>)",
            block,
            preview,
            count=1,
        )
        if "WIDGET 9 — Blog slider" not in preview:
            preview = re.sub(
                r"<section class=\"ledajans-blog\"[\s\S]*?</script>",
                block.strip(),
                preview,
                count=1,
            )
    else:
        preview = preview.replace(
            "</div>\n</body></html>",
            block + "</div>\n</body></html>",
            1,
        )
    PREVIEW_FILE.write_text(preview, encoding="utf-8")
    print("updated", PREVIEW_FILE.relative_to(ROOT))


def main() -> int:
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rposts = requests.get(
        site + "/wp-json/wp/v2/posts",
        params={
            "include": ",".join(str(p["id"]) for p in POSTS),
            "per_page": 10,
            "orderby": "include",
            "_embed": 1,
        },
        headers={"User-Agent": UA},
        timeout=60,
    )
    print("posts_fetch", rposts.status_code)
    posts_meta = rposts.json() if rposts.status_code == 200 else []
    by_id = {int(p["id"]): p for p in posts_meta}

    covers: dict[int, str] = {}
    media_ids: dict[int, int] = {}
    ordered_meta = []
    for item in POSTS:
        src = GEN_DIR / item["src"]
        if not src.is_file():
            print("HATA: kaynak yok", src)
            return 1
        dest = OUT_DIR / f"{item['stem']}.webp"
        to_webp(src, dest)
        mid, url = upload(site, auth, dest, item["alt"], item["alt"])
        set_featured(site, auth, item["id"], mid)
        covers[item["id"]] = url
        media_ids[item["id"]] = mid
        meta = by_id.get(item["id"]) or {
            "id": item["id"],
            "link": "",
            "date": "",
            "title": {"rendered": item["alt"]},
            "excerpt": {"rendered": ""},
        }
        ordered_meta.append(meta)

    cards_html = static_cards(ordered_meta, covers)
    widget_html = patch_widget(
        WIDGET_FILE.read_text(encoding="utf-8"), covers, cards_html
    )
    if "COVER_BY_ID" not in widget_html or "width=\"640\"" not in widget_html:
        print("HATA: widget patch eksik")
        return 2
    for url in covers.values():
        if url not in widget_html:
            print("HATA: kapak URL widget'ta yok", url)
            return 2
    WIDGET_FILE.write_text(widget_html, encoding="utf-8")
    print("wrote", WIDGET_FILE.relative_to(ROOT))
    sync_preview(widget_html)

    manifest = [
        {
            "id": item["id"],
            "title": item["alt"],
            "media_id": media_ids[item["id"]],
            "url": covers[item["id"]],
            "file": f"{item['stem']}.webp",
        }
        for item in POSTS
    ]
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

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

    chk = requests.get(
        site + "/wp-json/wp/v2/posts",
        params={"per_page": 10, "_embed": 1, "orderby": "date", "order": "desc"},
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=60,
    )
    print("verify_posts", chk.status_code)
    ok = 0
    for p in chk.json() if chk.status_code == 200 else []:
        pid = int(p["id"])
        fm = ((p.get("_embedded") or {}).get("wp:featuredmedia") or [None])[0]
        url = (fm or {}).get("source_url") or ""
        want = covers.get(pid, "")
        match = bool(want) and want in url
        print("verify", pid, "featured=", bool(url), "match=", match)
        if match:
            ok += 1
    print(f"COVERS={ok}/{len(covers)}")
    for item in POSTS:
        print("URL", item["id"], covers[item["id"]])
    return 0 if ok == len(covers) else 3


if __name__ == "__main__":
    raise SystemExit(main())
