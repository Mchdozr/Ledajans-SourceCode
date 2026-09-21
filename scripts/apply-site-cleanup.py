#!/usr/bin/env python3
"""EN/DE kapat, demo/kopya 301, GSC plugin, zayif title. Hero dokunulmaz."""
from __future__ import annotations

import io
import os
import re
import sys
import time
import zipfile
from urllib.parse import urlparse

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Site-Cleanup/1.2"
PLUGIN_FILE = "ledajans-gsc-coverage/ledajans-gsc-coverage"
GROUP = 1
ORIGIN = "https://ledajans.com"

REDIRECTS = [
    ("/gallery", "/projeler/"),
    ("/portfolio-01", "/projeler/"),
    ("/portfolio-02", "/projeler/"),
    ("/portfolio-03", "/projeler/"),
    ("/about-me", "/hakkimizda/"),
    ("/led-ekran-2", "/led-ekran/"),
    ("/led-ekran-3", "/led-ekran/"),
    ("/led", "/led-ekran/"),
    ("/led-2", "/led-ekran/"),
    ("/tf-qs2n-kontrol-karti-2", "/tf-qs2n-kontrol-karti/"),
    ("/de/led-ekran-10", "/led-ekran/"),
    ("/de/gefuehrt", "/led-ekran/"),
    ("/de/gefuehrt-2", "/led-ekran/"),
    ("/de/gefuehrt-3", "/led-ekran/"),
    ("/de/hd-c10", "/colorlight/"),
    ("/de/ticker", "/blog/"),
    ("/de/p10-panel-2-2", "/p10-panel/"),
    ("/de/p10-panel-3", "/p10-panel/"),
    ("/de/p10-panel-4-2", "/p10-panel/"),
    ("/de/p10-panel-5", "/p10-panel/"),
    ("/de/p10-rotes-panel", "/p10-panel-kirmizi/"),
    ("/de/verwendung-des-p10-grafikdisplays", "/p10-panel/"),
    ("/de/was-ist-ein-led-streifen", "/blog/"),
    ("/de/category/genel-de", "/blog/"),
    ("/en/case/indoor-led-display", "/ic-mekan-led-ekran/"),
    ("/en/case/outdoor-led-screen", "/dis-mekan-led-ekran/"),
    ("/de/case/led-anzeige-fuer-den-innenbereich", "/ic-mekan-led-ekran/"),
    ("/de/case/mietbildschirm", "/rental-ekran/"),
    ("/de/case/rgb-panel-fuer-den-innenbereich", "/ic-mekan-rgb-panel/"),
    ("/de/case/steuerkarten", "/kontrol-kartlari/"),
    ("/de/case/stromversorgung", "/guc-kaynaklari/"),
    ("/de/case/verleihbildschirm", "/rental-ekran/"),
    ("/de-case-rgb-panel-fuer-den-aussenbereich", "/dis-mekan-rgb-panel/"),
    ("/feed", "/"),
    ("/comments/feed", "/"),
    ("/case", "/projeler/"),
    ("/en/case", "/projeler/"),
    ("/de/case", "/projeler/"),
]

REGEX_REDIRECTS = [
    (r"^/case(/.*)?$", "/projeler/"),
    (r"^/(en|de)/case(/.*)?$", "/projeler/"),
]

REGEX_410 = [r"^/gva_template/.*"]

DRAFT_PAGE_SLUGS = {
    "gallery",
    "portfolio-01",
    "portfolio-02",
    "portfolio-03",
    "about-me",
    "en",
    "de",
    "our-company-information",
    "kommunikation",
    "unsere-firmeninformationen",
    "de-case-rgb-panel-fuer-den-aussenbereich",
}

DRAFT_POST_SLUGS = {
    "led-ekran-2",
    "led-ekran-3",
    "led",
    "led-2",
    "tf-qs2n-kontrol-karti-2",
    "gefuehrt",
    "gefuehrt-2",
    "gefuehrt-3",
    "led-anzeige",
    "led-bildschirm",
    "led-ekran-10",
    "hd-c10",
    "ticker",
    "p10-panel-2-2",
    "p10-panel-3",
    "p10-panel-4-2",
    "p10-panel-5",
    "p10-rotes-panel",
    "verwendung-des-p10-grafikdisplays",
    "was-ist-ein-led-streifen",
}

KEEP_POST_SLUGS = {"led-ekran"}  # TR hub is a PAGE; DE post slug collides — draft only if /de/ in link

TITLES = [
    {
        "type": "pages",
        "slug": "cob-ekran",
        "title": "COB LED Ekran | Fine Pitch Smart Screen | LEDAJANS",
        "description": (
            "COB LED ekran ve smart screen. İnce pitch, yüksek kontrast, iç mekan vitrin ve stüdyo. "
            "Ücretsiz keşif ve fiyat teklifi — LEDAJANS."
        ),
        "focus": "cob led ekran,cob ekran,smart screen led,fine pitch led",
    },
    {
        "type": "pages",
        "slug": "iletisim",
        "title": "İletişim | LED Ekran Teklif ve Keşif | LEDAJANS",
        "description": (
            "LED ekran fiyat teklifi, ücretsiz keşif ve teknik destek. İstanbul Şişli — "
            "telefon, WhatsApp veya form ile ulaşın. LEDAJANS."
        ),
        "focus": "ledajans iletişim,led ekran teklif,led ekran keşif",
    },
    {
        "type": "pages",
        "slug": "blog",
        "title": "LED Ekran Blog | Rehberler ve Fiyat Yazıları | LEDAJANS",
        "description": (
            "LED ekran fiyatları, COB/GOB, kiralama ve teknik rehberler. "
            "Doğru ekranı seçmek için LEDAJANS uzman içerikleri."
        ),
        "focus": "led ekran blog,led ekran rehberi,led ekran fiyatları",
    },
]

PROBES = [
    ("https://ledajans.com/en/", 200, None),
    ("https://ledajans.com/de/", 200, None),
    ("https://ledajans.com/gallery/", 301, "/projeler"),
    ("https://ledajans.com/portfolio-01/", 301, "/projeler"),
    ("https://ledajans.com/about-me/", 301, "/hakkimizda"),
    ("https://ledajans.com/led-ekran-2/", 301, "/led-ekran"),
    ("https://ledajans.com/led/", 301, "/led-ekran"),
    ("https://ledajans.com/led-2/", 301, "/led-ekran"),
    ("https://ledajans.com/case/", 301, "/projeler"),
    ("https://ledajans.com/en/case/", 301, "/projeler"),
    ("https://ledajans.com/feed/", 301, None),
    ("https://ledajans.com/gva_template/tr-2/", 410, None),
    ("https://ledajans.com/cob-ekran/", 200, None),
    ("https://ledajans.com/iletisim/", 200, None),
    ("https://ledajans.com/blog/", 200, None),
    ("https://ledajans.com/", 200, None),
    ("https://ledajans.com/led-ekran/", 200, None),
]


def load_env():
    data = {}
    env_path = os.path.join(ROOT, ".env")
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    site = (os.environ.get("WP_SITE_URL") or data.get("WP_SITE_URL") or ORIGIN).rstrip("/")
    if "8880" in site or "ledajans.com" not in site.lower():
        site = ORIGIN
    return (
        site,
        os.environ.get("WP_USERNAME") or data.get("WP_USERNAME", ""),
        (os.environ.get("WP_APP_PASSWORD") or data.get("WP_APP_PASSWORD") or "").replace(" ", ""),
    )


def is_lang_path(link: str) -> bool:
    path = urlparse(link or "").path.lower()
    return (
        path == "/en"
        or path == "/en/"
        or path == "/de"
        or path == "/de/"
        or path.startswith("/en/")
        or path.startswith("/de/")
    )


def list_all(site, auth, headers, path):
    items = []
    page = 1
    while page <= 40:
        r = requests.get(
            f"{site}/wp-json/{path}",
            params={
                "per_page": 100,
                "page": page,
                "status": "publish,draft,private",
                "context": "edit",
            },
            auth=auth,
            headers=headers,
            timeout=40,
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        if page >= int(r.headers.get("X-WP-TotalPages") or 1):
            break
        page += 1
    return items


def existing_redirects(site, auth, headers) -> set[str]:
    found: set[str] = set()
    page = 0
    while page <= 30:
        r = requests.get(
            f"{site}/wp-json/redirection/v1/redirect",
            params={"per_page": 200, "page": page},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        if r.status_code != 200:
            break
        body = r.json()
        for it in body.get("items") or []:
            found.add((it.get("url") or "").rstrip("/"))
        if not body.get("items"):
            break
        page += 1
    return found


def add_redirect(site, auth, headers, payload) -> bool:
    r = requests.post(
        f"{site}/wp-json/redirection/v1/redirect",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print("  FAIL", payload.get("url"), r.status_code, r.text[:160])
        return False
    return True


def plugin_zip() -> bytes:
    src = os.path.join(ROOT, "wordpress-gsc-coverage.php")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src, "ledajans-gsc-coverage/ledajans-gsc-coverage.php")
    return buf.getvalue()


def install_plugin(site, auth, headers) -> bool:
    slug = PLUGIN_FILE
    r = requests.get(
        f"{site}/wp-json/wp/v2/plugins/{slug}",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("plugin_get", r.status_code, r.text[:180])
    if r.status_code == 200:
        act = requests.post(
            f"{site}/wp-json/wp/v2/plugins/{slug}",
            json={"status": "active"},
            auth=auth,
            headers={**headers, "Content-Type": "application/json"},
            timeout=60,
        )
        print("plugin_activate", act.status_code, act.text[:200])
        if act.status_code in (200, 201):
            return True

    zbytes = plugin_zip()
    r2 = requests.post(
        f"{site}/wp-json/wp/v2/plugins",
        auth=auth,
        headers={"User-Agent": UA},
        files={"plugin": ("ledajans-gsc-coverage.zip", zbytes, "application/zip")},
        data={"status": "active"},
        timeout=120,
    )
    print("plugin_install", r2.status_code, r2.text[:450])
    if r2.status_code in (200, 201):
        return True

    r3 = requests.post(
        f"{site}/wp-json/wp/v2/plugins/{slug}",
        json={"status": "active"},
        auth=auth,
        headers={**headers, "Content-Type": "application/json"},
        timeout=60,
    )
    print("plugin_activate2", r3.status_code, r3.text[:200])
    return r3.status_code in (200, 201)


def draft_item(site, auth, headers, cpt, item) -> None:
    pid = item["id"]
    slug = item.get("slug")
    link = item.get("link") or ""
    st = item.get("status")
    if st != "publish":
        print(f"  skip {cpt} id={pid} {st} {slug}")
        return
    r = requests.post(
        f"{site}/wp-json/wp/v2/{cpt}/{pid}",
        json={"status": "draft"},
        auth=auth,
        headers={**headers, "Content-Type": "application/json"},
        timeout=40,
    )
    print(f"  draft {cpt} id={pid} {slug} {r.status_code} {link}")


def apply_titles(site, auth, headers) -> None:
    for row in TITLES:
        r = requests.get(
            f"{site}/wp-json/wp/v2/{row['type']}",
            params={"slug": row["slug"], "status": "publish,draft,private"},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        if r.status_code != 200 or not r.json():
            print("title skip", row["slug"], r.status_code)
            continue
        pid = r.json()[0]["id"]
        meta = {
            "rank_math_title": row["title"],
            "rank_math_description": row["description"],
            "rank_math_focus_keyword": row["focus"],
        }
        u = requests.post(
            f"{site}/wp-json/wp/v2/{row['type']}/{pid}",
            json={"meta": meta},
            auth=auth,
            headers={**headers, "Content-Type": "application/json"},
            timeout=40,
        )
        saved = ((u.json() or {}).get("meta") or {}).get("rank_math_title") if u.status_code in (200, 201) else ""
        print(f"  title {row['slug']} id={pid} http={u.status_code} saved={bool(saved)}")


def probe() -> int:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Cache-Control": "no-cache", "Pragma": "no-cache"})
    fails = 0
    for url, want, loc in PROBES:
        r = s.get(url, timeout=25, allow_redirects=False, headers={"Cache-Control": "no-cache"})
        got = r.headers.get("Location", "")
        title = ""
        if r.status_code == 200:
            m = re.search(r"<title>(.*?)</title>", r.text, re.I | re.S)
            title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        ok = r.status_code == want and (not loc or loc in got.lower())
        if want == 200 and url.rstrip("/").endswith("cob-ekran") and "cob led" not in title.lower():
            ok = False
        if want == 200 and url.rstrip("/").endswith("iletisim") and "teklif" not in title.lower():
            ok = False
        if want == 200 and url.rstrip("/").endswith("blog") and "rehber" not in title.lower():
            ok = False
        if url.rstrip("/") == ORIGIN and "led ekran" not in title.lower():
            ok = False
        print(f"{'OK' if ok else 'FAIL'} {r.status_code} {url} loc={got[:80]} title={title[:70]!r}")
        if not ok:
            fails += 1
    return fails


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env")
        return 1
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    print("=== 1 plugin ===")
    plugged = install_plugin(site, auth, headers)
    print("plugin_ok", plugged)

    print("=== 2 redirection ===")
    have = existing_redirects(site, auth, headers)
    print("existing", len(have))
    added = 0
    for src, dst in REDIRECTS:
        key = src.rstrip("/")
        if key in have or src in have:
            continue
        if add_redirect(
            site,
            auth,
            headers,
            {
                "url": src,
                "match_type": "url",
                "action_type": "url",
                "action_code": 301,
                "action_data": {"url": ORIGIN + (dst if dst != "/" else "/")},
                "group_id": GROUP,
                "title": "cleanup-lang-demo-dup",
            },
        ):
            added += 1
            have.add(key)
    for src, dst in REGEX_REDIRECTS:
        if src.rstrip("/") in have:
            continue
        if add_redirect(
            site,
            auth,
            headers,
            {
                "url": src,
                "regex": True,
                "match_type": "url",
                "action_type": "url",
                "action_code": 301,
                "action_data": {"url": ORIGIN + (dst if dst != "/" else "/")},
                "group_id": GROUP,
                "title": "cleanup-regex",
            },
        ):
            added += 1
            have.add(src.rstrip("/"))
    for src in REGEX_410:
        if src.rstrip("/") in have:
            continue
        if add_redirect(
            site,
            auth,
            headers,
            {
                "url": src,
                "regex": True,
                "match_type": "url",
                "action_type": "error",
                "action_code": 410,
                "action_data": {},
                "group_id": GROUP,
                "title": "cleanup-410",
            },
        ):
            added += 1
    print("added", added)

    print("=== 3 draft junk pages/posts (EN/DE çevirilere dokunma) ===")
    pages = list_all(site, auth, headers, "wp/v2/pages")
    posts = list_all(site, auth, headers, "wp/v2/posts")
    for p in pages:
        slug = p.get("slug") or ""
        if slug in DRAFT_PAGE_SLUGS:
            draft_item(site, auth, headers, "pages", p)
    for p in posts:
        slug = p.get("slug") or ""
        link = p.get("link") or ""
        if slug == "led-ekran" and not is_lang_path(link):
            continue
        if slug in DRAFT_POST_SLUGS:
            draft_item(site, auth, headers, "posts", p)

    print("=== 4 titles ===")
    apply_titles(site, auth, headers)

    print("=== 5 purge ===")
    try:
        requests.get(
            site + "/?LSCWP_CTRL=purge&litespeed_type=purge_all",
            headers={"User-Agent": UA},
            timeout=20,
        )
    except Exception as exc:
        print("purge", type(exc).__name__)

    time.sleep(2)
    print("=== 6 probe ===")
    fails = probe()
    print("fails", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
