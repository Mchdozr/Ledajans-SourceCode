#!/usr/bin/env python3
"""Sitemap/IA cleanup: 301 duplicates, noindex thin URLs, hub titles, www host.

Idempotent. Does not delete posts. Does not touch NAP or price canonical path.
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "AGENT-HUB" / "_tmp-hero-frames" / "ia-backup"
BACKUP.mkdir(parents=True, exist_ok=True)

REDIRECTS = [
    ("/led-ekran-4/", "/led-ekran/"),
    ("/led-ekran-5/", "/led-ekran/"),
    ("/led-ekran-6/", "/led-ekran/"),
    ("/led-ekran-7/", "/led-ekran/"),
    ("/led-ekran-9/", "/led-ekran/"),
    ("/teknik-destek-videolari-2/", "/teknik-destek-videolari/"),
    ("/ic-mekan-led-ekranlar/", "/ic-mekan-led-ekran/"),
    ("/dis-mekan-led-ekranlar/", "/dis-mekan-led-ekran/"),
    ("/p10-panel-kirmizi-3/", "/p10-panel-kirmizi/"),
    ("/p10-panel-kirmizi-4/", "/p10-panel-kirmizi/"),
    ("/p10-panel-kirmizi-5/", "/p10-panel-kirmizi/"),
    ("/power-supply/", "/guc-kaynaklari/"),
]

NOINDEX = [
    ("post", "led-ekran-4", None),
    ("post", "led-ekran-5", None),
    ("post", "led-ekran-6", None),
    ("post", "led-ekran-7", None),
    ("post", "led-ekran-9", None),
    ("page", "teknik-destek-videolari-2", None),
    ("post", "ic-mekan-led-ekranlar", None),
    ("post", "dis-mekan-led-ekranlar", None),
    ("post", "p10-panel-kirmizi-3", None),
    ("post", "p10-panel-kirmizi-4", None),
    ("post", "p10-panel-kirmizi-5", None),
    ("post", "led-ekran-2", None),
    ("post", "led-ekran-3", None),
    ("post", "led", None),
    ("post", "led-2", None),
    ("post", "tf-qs2n-kontrol-karti-2", None),
    ("post", "gefuehrt", "de"),
    ("post", "gefuehrt-2", "de"),
    ("post", "gefuehrt-3", "de"),
    ("post", "hd-c10", "de"),
    ("post", "led-anzeige", "de"),
    ("post", "led-bildschirm", "de"),
    ("post", "led-ekran-10", "de"),
    ("post", "led-ekran", "de"),
    ("post", "p10-panel-2-2", "de"),
    ("post", "p10-panel-3", "de"),
    ("post", "p10-panel-4-2", "de"),
    ("post", "p10-panel-5", "de"),
    ("post", "p10-rotes-panel", "de"),
    ("post", "ticker", "de"),
    ("post", "verwendung-des-p10-grafikdisplays", "de"),
    ("post", "was-ist-ein-led-streifen", "de"),
    ("page", "ankara-led-ekran", None),
    ("page", "izmir-led-ekran", None),
    ("page", "otel-led-ekran", None),
    ("page", "stadyum-led-ekran", None),
    ("page", "colorlight-4", "en"),
    ("page", "huidu-2", "en"),
    ("page", "blog-2", "en"),
    ("post", "colorlight-4", "en"),
    ("post", "huidu-2", "en"),
    ("post", "blog-2", "en"),
]

TITLES = {
    ("page", "led-ekran", None): {
        "rank_math_title": "LED Ekran Modelleri | İç-Dış Mekan ve Kiralama | LEDAJANS",
        "rank_math_description": "İç mekan, dış mekan ve rental LED ekran modelleri. Kurulum, keşif ve B2B teklif. LEDAJANS İstanbul.",
        "rank_math_focus_keyword": "led ekran,iç mekan led ekran,dış mekan led ekran",
    },
    ("post", "led-ekran-fiyatlari-2026", None): {
        "rank_math_title": "LED Ekran Fiyatları 2026 | LEDAJANS",
        "rank_math_description": "LED ekran m² fiyat aralığı 2026: iç mekan, dış mekan ve kiralama. Güncel liste ve teklif. LEDAJANS.",
        "rank_math_focus_keyword": "led ekran fiyatları,led ekran m2 fiyatı,led ekran fiyat listesi",
    },
    ("page", "istanbul-led-ekran", None): {
        "rank_math_title": "İstanbul LED Ekran | Satış ve Kurulum | LEDAJANS",
    },
    ("page", "fuar-led-ekran", None): {
        "rank_math_title": "Fuar LED Ekran | Kiralama ve Stand | LEDAJANS",
    },
    ("page", "magaza-vitrin-led-ekran", None): {
        "rank_math_title": "Mağaza Vitrin LED Ekran | LEDAJANS",
    },
    ("page", "markalarimiz", None): {
        "rank_math_title": "Markalarımız | LEDAJANS",
        "rank_math_description": "LEDAJANS LED ekran markaları ve kontrol sistemleri. Huidu, Colorlight ve proje bileşenleri.",
        "rank_math_focus_keyword": "led ekran markaları,ledajans markalar",
    },
}

GOOD_URLS = [
    "https://ledajans.com/",
    "https://ledajans.com/led-ekran/",
    "https://ledajans.com/ic-mekan-led-ekran/",
    "https://ledajans.com/dis-mekan-led-ekran/",
    "https://ledajans.com/rental-ekran/",
    "https://ledajans.com/cob-ekran/",
    "https://ledajans.com/gob-led-ekran/",
    "https://ledajans.com/magaza-vitrin-led-ekran/",
    "https://ledajans.com/cephe-led-ekran/",
    "https://ledajans.com/fuar-led-ekran/",
    "https://ledajans.com/istanbul-led-ekran/",
    "https://ledajans.com/pitch-secim-rehberi/",
    "https://ledajans.com/led-ekran-fiyatlari-2026/",
    "https://ledajans.com/ic-mekan-led-ekran-fiyatlari-2026/",
    "https://ledajans.com/dis-mekan-led-ekran-fiyatlari-2026/",
    "https://ledajans.com/rental-led-ekran-kiralama-fiyatlari-2026/",
    "https://ledajans.com/guc-kaynaklari/",
    "https://ledajans.com/kontrol-kartlari/",
    "https://ledajans.com/ic-mekan-rgb-panel/",
    "https://ledajans.com/dis-mekan-rgb-panel/",
    "https://ledajans.com/projeler/",
    "https://ledajans.com/markalarimiz/",
    "https://ledajans.com/iletisim/",
    "https://ledajans.com/hakkimizda/",
    "https://ledajans.com/blog/",
    "https://ledajans.com/sitemap_index.xml",
]

PROTECT_PATHS = {
    "/",
    "/led-ekran/",
    "/ic-mekan-led-ekran/",
    "/dis-mekan-led-ekran/",
    "/rental-ekran/",
    "/guc-kaynaklari/",
    "/kontrol-kartlari/",
    "/p10-panel-kirmizi/",
    "/teknik-destek-videolari/",
    "/led-ekran-fiyatlari-2026/",
    "/markalarimiz/",
    "/istanbul-led-ekran/",
    "/fuar-led-ekran/",
    "/magaza-vitrin-led-ekran/",
    "/projeler/",
    "/blog/",
    "/colorlight/",
    "/huidu/",
}


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def norm(url: str) -> str:
    path = url
    if "://" in url:
        path = "/" + url.split("://", 1)[1].split("/", 1)[-1]
    if not path.startswith("/"):
        path = "/" + path
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def head(url: str) -> tuple[int, str]:
    ctx = ssl.create_default_context()
    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url, headers={"User-Agent": "LEDAJANS-IA-Verify/1.0"})
    try:
        with opener.open(req, timeout=30) as response:
            return response.status, response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location", "")


def main() -> int:
    site, user, password = load_env()
    session = requests.Session()
    session.auth = (user, password)
    session.headers.update({"User-Agent": "LEDAJANS-IA-Cleanup/1.0", "Content-Type": "application/json"})

    me = session.get(f"{site}/wp-json/wp/v2/users/me", timeout=30)
    if me.status_code != 200:
        print("AUTH", me.status_code)
        return 1
    print("AUTH OK")

    existing: set[str] = set()
    page = 0
    while page < 20:
        response = session.get(
            f"{site}/wp-json/redirection/v1/redirect",
            params={"per_page": 100, "page": page},
            timeout=40,
        )
        items = response.json().get("items") or []
        if not items:
            break
        for item in items:
            existing.add(norm(str(item.get("url") or "")))
        if len(items) < 100:
            break
        page += 1
    print("EXISTING_REDIRECTS", len(existing))

    created = []
    for source, target in REDIRECTS:
        if norm(source) in existing:
            print("REDIR_SKIP", source)
            continue
        payload = {
            "url": source,
            "match_type": "url",
            "action_type": "url",
            "action_code": 301,
            "action_data": {"url": target},
            "group_id": 1,
            "regex": False,
            "enabled": True,
        }
        response = session.post(f"{site}/wp-json/redirection/v1/redirect", json=payload, timeout=30)
        print("REDIR", source, response.status_code, response.text[:180].replace("\n", " "))
        if response.status_code in (200, 201):
            created.append(source)
            existing.add(norm(source))
    (BACKUP / "created-redirects.json").write_text(json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nHEAD_REDIRECTS")
    for source, target in REDIRECTS:
        code, loc = head(site + source)
        print(f"  {code} {source} -> {loc}")

    def lookup(kind: str, slug: str, lang: str | None) -> list[dict]:
        kinds = ["pages", "posts"] if kind == "any" else [kind + "s" if not kind.endswith("s") else kind]
        if kind == "page":
            kinds = ["pages"]
        elif kind == "post":
            kinds = ["posts"]
        found = []
        for rest in kinds:
            params = {"slug": slug, "status": "any", "per_page": 20, "context": "edit"}
            if lang:
                params["lang"] = lang
            response = session.get(f"{site}/wp-json/wp/v2/{rest}", params=params, timeout=40)
            if response.status_code != 200 or not isinstance(response.json(), list):
                continue
            found.extend(response.json())
        return found

    noindex_ids: list[tuple[int, str]] = []
    seen_ids: set[int] = set()
    for kind, slug, lang in NOINDEX:
        matches = lookup(kind, slug, lang)
        if not matches and lang:
            continue
        for item in matches:
            link = norm(item.get("link") or "")
            if lang == "de" and "/de/" not in link:
                print("SKIP_NOT_DE", slug, link)
                continue
            if lang == "en" and "/en/" not in link:
                print("SKIP_NOT_EN", slug, link)
                continue
            if link in PROTECT_PATHS:
                print("SKIP_PROTECT", item["id"], link)
                continue
            if item["id"] in seen_ids:
                continue
            seen_ids.add(item["id"])
            noindex_ids.append((item["id"], link))

    print("\nNOINDEX_TARGETS", len(noindex_ids))
    noindex_ok = []
    for object_id, link in noindex_ids:
        response = session.post(
            f"{site}/wp-json/rankmath/v1/updateMeta",
            json={"objectType": "post", "objectID": object_id, "meta": {"rank_math_robots": ["noindex"]}},
            timeout=30,
        )
        print("NOINDEX", object_id, link, response.status_code)
        if response.status_code == 200:
            noindex_ok.append({"id": object_id, "link": link})
    (BACKUP / "noindex-ids.json").write_text(json.dumps(noindex_ok, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nTITLES")
    for (kind, slug, lang), meta in TITLES.items():
        matches = lookup(kind, slug, lang)
        if not matches:
            print("TITLE_MISSING", slug)
            continue
        item = matches[0]
        rest = "pages" if item.get("type") == "page" else "posts"
        before = {key: (item.get("meta") or {}).get(key) for key in meta}
        (BACKUP / f"meta-{item['id']}.json").write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
        response = session.post(
            f"{site}/wp-json/wp/v2/{rest}/{item['id']}",
            json={"meta": meta},
            timeout=40,
        )
        saved = (response.json().get("meta") or {}).get("rank_math_title") if response.status_code in (200, 201) else ""
        print("TITLE", slug, response.status_code, saved)

    page = session.get(f"{site}/wp-json/wp/v2/pages/5001", params={"context": "edit"}, timeout=60).json()
    elementor = (page.get("meta") or {}).get("_elementor_data") or ""
    raw = (page.get("content") or {}).get("raw") or ""
    (BACKUP / "page-5001-elementor.json").write_text(elementor if isinstance(elementor, str) else json.dumps(elementor), encoding="utf-8")
    (BACKUP / "page-5001-content.html").write_text(raw, encoding="utf-8")
    old_h1 = "LED Ekran Çözümleri ve Fiyatları"
    new_h1 = "LED Ekran Çözümleri"
    payload = {}
    if isinstance(elementor, str) and old_h1 in elementor:
        payload.setdefault("meta", {})["_elementor_data"] = elementor.replace(old_h1, new_h1)
    if old_h1 in raw:
        payload["content"] = raw.replace(old_h1, new_h1)
    slash_old = "https://ledajans.com/dis-mekan-led-ekran\""
    slash_new = "https://ledajans.com/dis-mekan-led-ekran/\""
    if payload.get("meta", {}).get("_elementor_data") and slash_old in payload["meta"]["_elementor_data"]:
        payload["meta"]["_elementor_data"] = payload["meta"]["_elementor_data"].replace(slash_old, slash_new)
    elif isinstance(elementor, str) and slash_old in elementor and "meta" not in payload:
        payload["meta"] = {"_elementor_data": elementor.replace(slash_old, slash_new)}
    if payload:
        response = session.post(f"{site}/wp-json/wp/v2/pages/5001", json=payload, timeout=60)
        print("H1_5001", response.status_code, "h1", old_h1 in json.dumps(payload))
    else:
        print("H1_5001 no string in elementor/content")

    brands = lookup("page", "markalarimiz", None)
    if brands:
        item = brands[0]
        elementor_b = (item.get("meta") or {}).get("_elementor_data") or ""
        raw_b = (item.get("content") or {}).get("raw") or ""
        (BACKUP / f"page-{item['id']}-elementor.json").write_text(
            elementor_b if isinstance(elementor_b, str) else "",
            encoding="utf-8",
        )
        brand_payload = {}
        if isinstance(elementor_b, str) and "Our Brands" in elementor_b:
            brand_payload["meta"] = {"_elementor_data": elementor_b.replace("Our Brands", "Markalarımız")}
        if "Our Brands" in raw_b:
            brand_payload["content"] = raw_b.replace("Our Brands", "Markalarımız")
        if brand_payload:
            response = session.post(f"{site}/wp-json/wp/v2/pages/{item['id']}", json=brand_payload, timeout=60)
            print("BRANDS_H1", response.status_code)
        else:
            print("BRANDS_H1 string not in content")

    print("\nWWW")
    response = session.post(
        f"{site}/wp-json/redirection/v1/setting",
        json={"name": "preferred_domain", "value": "nowww"},
        timeout=30,
    )
    print("PREFERRED", response.status_code, response.text[:200].replace("\n", " "))
    for url in (
        "https://www.ledajans.com/",
        "https://www.ledajans.com/led-ekran/",
        "http://www.ledajans.com/",
        "https://ledajans.com/",
    ):
        code, loc = head(url)
        print(f"  {code} {url} -> {loc}")

    print("\nFOOTER_SEARCH")
    templates = session.get(f"{site}/wp-json/elementor/v1/site-editor/templates", timeout=40)
    footer_ids = []
    if templates.status_code == 200 and isinstance(templates.json(), list):
        for item in templates.json():
            footer_ids.append((item.get("template_id"), item.get("type"), item.get("title")))
        print("TEMPLATE_COUNT", len(footer_ids))
        for row in footer_ids:
            if row[1] in ("footer", "header") or (row[2] and "ooter" in str(row[2]).lower()):
                print(" TPL", row)
    for snippet_id in (5024, 5026):
        snippet = session.get(
            f"{site}/wp-json/wp/v2/elementor_snippet/{snippet_id}",
            params={"context": "edit"},
            timeout=40,
        ).json()
        code = (snippet.get("meta") or {}).get("_elementor_code") or ""
        print("SNIP", snippet_id, "code_len", len(code), "twiter", "twiter.com" in code)

    print("\nINDEX_SUBMIT")
    response = session.post(
        f"{site}/wp-json/rankmath/v1/in/submitUrls",
        json={"urls": "\n".join(GOOD_URLS)},
        timeout=60,
    )
    print(response.status_code, response.text[:500].replace("\n", " "))

    session.delete(f"{site}/wp-json/elementor/v1/cache", timeout=60)
    session.post(f"{site}/wp-json/ledajans/v1/purge", timeout=60)
    print("PURGE requested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
