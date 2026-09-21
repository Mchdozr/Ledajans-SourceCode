#!/usr/bin/env python3
"""GSC kalan: coverage plugin + hub ic link + video sayfasi + RankMath + probe."""
from __future__ import annotations

import io
import json
import os
import sys
import zipfile

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-GSC-Remaining/1.0"
PLUGIN_SLUG = "ledajans-gsc-coverage/ledajans-gsc-coverage"

RANKMATH = [
    {
        "slug": "teknik-destek-videolari",
        "title": "LED Ekran Teknik Destek Videoları | Kurulum ve Bakım | LEDAJANS",
        "description": (
            "LED ekran kurulum, Huidu/Colorlight ayar, arıza ve bakım videoları. "
            "LEDAJANS teknik destek ekibinden adım adım görüntülü rehber."
        ),
        "focus": "led ekran teknik destek,led ekran kurulum videosu,huidu ayarlama",
    },
    {
        "slug": "led-ekran-nedir",
        "title": "LED Ekran Nedir? Türleri ve Seçim Rehberi | LEDAJANS",
        "description": (
            "LED ekran nedir, nasıl çalışır, SMD/COB/GOB farkları nelerdir? "
            "İç-dış mekan seçimi ve kullanım alanları. LEDAJANS 2026 rehberi."
        ),
        "focus": "led ekran nedir,led ekran çeşitleri,led ekran nasıl çalışır",
    },
    {
        "slug": "led-ekran-bakim",
        "title": "LED Ekran Bakım Rehberi | Temizlik ve Arıza | LEDAJANS",
        "description": (
            "LED ekran bakımı: temizlik, modül değişimi, arıza tespiti ve ömür. "
            "Yerinde servis ve yedek parça. LEDAJANS teknik bakım rehberi."
        ),
        "focus": "led ekran bakım,led ekran arıza,led modül değişimi",
    },
    {
        "slug": "toplanti-odasi-led-ekran",
        "title": "Toplantı Odası LED Ekran | Indoor Pitch Rehberi | LEDAJANS",
        "description": (
            "Toplantı odası LED ekran seçimi: izleme mesafesi, P değeri, ses ve kurulum. "
            "Indoor LED çözümleri. Ücretsiz keşif — LEDAJANS."
        ),
        "focus": "toplantı odası led ekran,toplantı salonu led ekran,indoor led toplantı",
    },
]

PROBES = [
    ("https://ledajans.com/case/", 301, "/projeler"),
    ("https://ledajans.com/en/case/", 301, "/projeler"),
    ("https://ledajans.com/en/case/power-supply/", 301, "/guc-kaynaklari"),
    ("https://ledajans.com/gva_template/tr-2/", 410, None),
    ("https://ledajans.com/feed/", 301, None),
    ("https://ledajans.com/led-ekran-bakim/", 200, None),
    ("https://ledajans.com/led-ekran-nedir/", 200, None),
    ("https://ledajans.com/toplanti-odasi-led-ekran/", 200, None),
    ("https://ledajans.com/teknik-destek-videolari/", 200, None),
    ("https://ledajans.com/led-ekran/", 200, None),
]


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data.get("WP_USERNAME", ""),
        data.get("WP_APP_PASSWORD", "").replace(" ", ""),
    )


def walk_set_html(nodes, new_html: str, marker: str) -> list[str]:
    ids: list[str] = []
    if isinstance(nodes, list):
        for x in nodes:
            ids.extend(walk_set_html(x, new_html, marker))
        return ids
    if not isinstance(nodes, dict):
        return ids
    settings = nodes.get("settings")
    if isinstance(settings, dict):
        for field in ("html", "editor"):
            val = settings.get(field)
            if isinstance(val, str) and marker in val:
                settings[field] = new_html
                ids.append(f"{nodes.get('id')}:{field}")
                break
    for key in ("elements", "content"):
        if key in nodes:
            ids.extend(walk_set_html(nodes[key], new_html, marker))
    return ids


def find_page_id(site: str, slug: str, auth, headers) -> int | None:
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages",
        params={"slug": slug, "status": "publish,draft,private", "per_page": 5},
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code != 200 or not r.json():
        return None
    return int(r.json()[0]["id"])


def install_plugin(site: str, auth, headers) -> bool:
    src = os.path.join(ROOT, "wordpress-gsc-coverage.php")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src, "ledajans-gsc-coverage/ledajans-gsc-coverage.php")
    zip_bytes = buf.getvalue()

    r = requests.get(
        f"{site}/wp-json/wp/v2/plugins/{PLUGIN_SLUG}",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("plugin_get", r.status_code, r.text[:220])

    r2 = requests.post(
        f"{site}/wp-json/wp/v2/plugins",
        auth=auth,
        headers={"User-Agent": UA},
        files={"file": ("ledajans-gsc-coverage.zip", zip_bytes, "application/zip")},
        data={"status": "active"},
        timeout=120,
    )
    print("plugin_install", r2.status_code, r2.text[:400])
    if r2.status_code in (200, 201):
        return True

    r3 = requests.post(
        f"{site}/wp-json/wp/v2/plugins/{PLUGIN_SLUG}",
        json={"status": "active"},
        auth=auth,
        headers={**headers, "Content-Type": "application/json"},
        timeout=60,
    )
    print("plugin_activate", r3.status_code, r3.text[:250])
    return r3.status_code in (200, 201)


def deploy_html(site: str, auth, headers, slug: str, rel_path: str, marker: str) -> bool:
    path = os.path.join(ROOT, rel_path.replace("/", os.sep))
    html = open(path, encoding="utf-8").read()
    pid = 5001 if slug == "led-ekran" else find_page_id(site, slug, auth, headers)
    if not pid:
        print(f"HATA sayfa yok slug={slug}")
        return False
    r = requests.post(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        json={"content": html},
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print(f"content {slug}", r.status_code)
    if r.status_code not in (200, 201):
        print(r.text[:300])
        return False
    rp = requests.get(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        params={"context": "edit"},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    raw = (rp.json().get("meta") or {}).get("_elementor_data")
    if not raw:
        print(f"UYARI elementor yok {slug}")
        return True
    data = json.loads(raw) if isinstance(raw, str) else raw
    ids = walk_set_html(data, html, marker)
    print(f"elementor {slug}", ids)
    if not ids:
        print(f"HATA widget yok {slug}")
        return False
    ru = requests.post(
        f"{site}/wp-json/wp/v2/pages/{pid}",
        json={
            "meta": {
                "_elementor_data": json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            }
        },
        auth=auth,
        headers=headers,
        timeout=120,
    )
    print(f"elementor_save {slug}", ru.status_code)
    return ru.status_code in (200, 201)


def apply_rankmath(site: str, auth, headers) -> None:
    for page in RANKMATH:
        pid = find_page_id(site, page["slug"], auth, headers)
        if not pid:
            print("rankmath skip", page["slug"])
            continue
        r = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json={
                "meta": {
                    "rank_math_title": page["title"],
                    "rank_math_description": page["description"],
                    "rank_math_focus_keyword": page["focus"],
                }
            },
            auth=auth,
            headers=headers,
            timeout=30,
        )
        saved = ((r.json() or {}).get("meta") or {}).get("rank_math_title") if r.status_code in (200, 201) else ""
        print(f"rankmath {page['slug']}", r.status_code, bool(saved))


def probe() -> int:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    fail = 0
    for url, expect, loc_part in PROBES:
        r = s.get(url, timeout=25, allow_redirects=False)
        loc = r.headers.get("Location", "")
        ok = r.status_code == expect
        if loc_part and loc_part not in loc:
            ok = False
        extra = ""
        if expect == 200 and r.status_code == 200:
            body = r.text
            if "led-ekran/" in url:
                extra = "hub_cards=" + str("led-ekran-nedir" in body and "led-ekran-bakim" in body)
            if "teknik-destek" in url:
                extra = "videoobject=" + str("VideoObject" in body and "gJQv-leg8oc" in body)
                extra += " title_iframe=" + str('title="LED Ekran Kurulum Rehberi"' in body)
        print(f"PROBE {r.status_code} {url} loc={loc[:80]} {extra} {'OK' if ok else 'FAIL'}")
        if not ok:
            fail += 1
    return fail


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    if not install_plugin(site, auth, headers):
        print("UYARI: plugin kurulumu başarısız, içerik deploy devam")

    ok_hub = deploy_html(
        site, auth, headers, "led-ekran", "LED Ekran/led-ekran.html", "la-wrapper"
    )
    ok_vid = deploy_html(
        site,
        auth,
        headers,
        "teknik-destek-videolari",
        "Teknik-Destek-Bilgi/Teknik-Destek-Videolari/body.html",
        "ld-td-wrap",
    )
    apply_rankmath(site, auth, headers)

    dc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("elementor_cache_delete", dc.status_code)

    fails = probe()
    if not ok_hub or not ok_vid:
        return 2
    return 0 if fails == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
