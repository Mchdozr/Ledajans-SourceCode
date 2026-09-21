#!/usr/bin/env python3
"""GSC 404 301 (Redirection) + breadcrumb # + dual H1 deploy."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-GSC-Coverage/1.1"
GROUP = 1

EXACT = [
    ("/urunler/rental-ekran", "/rental-ekran/"),
    ("/urunler/kontrol-kartlari", "/kontrol-kartlari/"),
    ("/urunler/dis-mekan-rgb-panel", "/dis-mekan-rgb-panel/"),
    ("/urunler/ic-mekan-rgb-panel", "/ic-mekan-rgb-panel/"),
    ("/urunler/ic-mekan-led-ekran", "/ic-mekan-led-ekran/"),
    ("/urunler/dis-mekan-led-ekran", "/dis-mekan-led-ekran/"),
    ("/case", "/projeler/"),
    ("/case/", "/projeler/"),
    ("/en/case", "/projeler/"),
    ("/de/case", "/projeler/"),
    ("/case/dis-mekan-led-ekran", "/dis-mekan-led-ekran/"),
    ("/case/indoor-rgb-panels", "/ic-mekan-rgb-panel/"),
    ("/case/outdoor-rgb-panel", "/dis-mekan-rgb-panel/"),
    ("/case/rental-cabin", "/rental-ekran/"),
    ("/case/rental-ekran", "/rental-ekran/"),
    ("/case/control-cards", "/kontrol-kartlari/"),
    ("/case/power-supply", "/guc-kaynaklari/"),
    ("/case/power-supply-2", "/guc-kaynaklari/"),
    ("/case/power-supply-2-2", "/guc-kaynaklari/"),
    ("/ease/control-cards", "/kontrol-kartlari/"),
    ("/ease/indoor-rgb-panels", "/ic-mekan-rgb-panel/"),
    ("/de/case/rgb-panel-fuer-den-aussenbereich", "/dis-mekan-rgb-panel/"),
    ("/rehber/toplanti-odasi-led-ekran", "/ic-mekan-led-ekran/"),
    ("/sozluk/gob-led-nedir", "/gob-led-ekran/"),
    ("/led-ekran-10", "/blog/led-ekran-10/"),
    ("/ic-mekan-indoor-led-ekranlar", "/ic-mekan-led-ekran/"),
    ("/category/kontrol-kartlari", "/kontrol-kartlari/"),
    ("/kayan-yazi-2", "/blog/kayan-yazi/"),
    ("/about-me", "/hakkimizda/"),
    ("/p10-panel-2", "/blog/p10-panel/"),
    ("/p2-5-gob-ic-mekan-rgb-panel", "/ic-mekan-led-ekran/"),
    ("/p1-25-gob-ic-mekan-rgb-panel", "/ic-mekan-led-ekran/"),
    ("/p1-53-gob-ic-mekan-rgb-panel", "/ic-mekan-led-ekran/"),
    ("/p1-86-gob-ic-mekan-rgb-panel", "/ic-mekan-led-ekran/"),
    ("/q1-25-flexible-ic-mekan-led-panel", "/ic-mekan-led-ekran/"),
    ("/q1-53-flexible-ic-mekan-led-panel", "/ic-mekan-led-ekran/"),
    ("/q1-86-flexible-ic-mekan-led-panel", "/ic-mekan-led-ekran/"),
    ("/feed", "/"),
    ("/comments/feed", "/"),
]

REGEX_URL = [
    (r"^/urunler/([^/]+)/?$", "/$1/"),
    (r"^(.+)/feed/?$", "$1/"),
]

REGEX_410 = [
    r"^/gva_template/.*",
    r"^/events/(list|liste|kategori)/.*",
]

CRUMB_PAGES = [
    "hakkimizda",
    "firma-bilgilerimiz",
    "program-indir",
    "colorlight",
    "teknik-destek-videolari",
]

PROBES = [
    ("https://ledajans.com/urunler/rental-ekran", 301, "/rental-ekran"),
    ("https://ledajans.com/urunler/ic-mekan-led-ekran", 301, "/ic-mekan-led-ekran"),
    ("https://ledajans.com/case/dis-mekan-led-ekran", 301, "/dis-mekan-led-ekran"),
    ("https://ledajans.com/case/", 301, "/projeler"),
    ("https://ledajans.com/gva_template/dis-mekan-led-ekran/", 410, ""),
    ("https://ledajans.com/rehber/toplanti-odasi-led-ekran/", 301, "/ic-mekan-led-ekran"),
    ("https://ledajans.com/sozluk/gob-led-nedir/", 301, "/gob-led-ekran"),
    ("https://ledajans.com/led-ekran/", 200, ""),
]


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
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


def existing_urls(site: str, auth, headers) -> set[str]:
    found: set[str] = set()
    page = 0
    while True:
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
        items = body.get("items") or []
        for it in items:
            found.add((it.get("url") or "").rstrip("/"))
        if len(found) >= int(body.get("total") or 0) or not items:
            break
        page += 1
        if page > 20:
            break
    return found


def add_redirect(site: str, auth, headers, payload: dict) -> bool:
    r = requests.post(
        f"{site}/wp-json/redirection/v1/redirect",
        json=payload,
        auth=auth,
        headers=headers,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print("FAIL redirect", payload.get("url"), r.status_code, r.text[:200])
        return False
    return True


def walk_replace(nodes, n: list[int]) -> None:
    if isinstance(nodes, list):
        for x in nodes:
            walk_replace(x, n)
        return
    if not isinstance(nodes, dict):
        return
    settings = nodes.get("settings")
    if isinstance(settings, dict):
        for field in ("html", "editor"):
            val = settings.get(field)
            if isinstance(val, str) and '"item":"#"' in val:
                val = val.replace(
                    '{"@type":"ListItem","position":2,"name":"Kurumsal","item":"#"}',
                    '{"@type":"ListItem","position":2,"name":"Kurumsal","item":"https://ledajans.com/hakkimizda/"}',
                )
                val = val.replace(
                    '{"@type":"ListItem","position":2,"name":"Teknik Destek","item":"#"}',
                    '{"@type":"ListItem","position":2,"name":"Teknik Destek","item":"https://ledajans.com/teknik-destek-videolari/"}',
                )
                val = re.sub(r'("item"\s*:\s*)"#"', r'\1"https://ledajans.com/"', val)
                settings[field] = val
                n[0] += 1
    for key in ("elements", "content"):
        if key in nodes:
            walk_replace(nodes[key], n)


def patch_crumbs(site: str, auth, headers) -> None:
    for slug in CRUMB_PAGES:
        r = requests.get(
            f"{site}/wp-json/wp/v2/pages",
            params={"slug": slug, "context": "edit"},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        if r.status_code != 200 or not r.json():
            print("crumb skip", slug, r.status_code)
            continue
        page = r.json()[0]
        pid = page["id"]
        raw = (page.get("meta") or {}).get("_elementor_data")
        if not raw:
            print("crumb no elementor", slug)
            continue
        data = json.loads(raw) if isinstance(raw, str) else raw
        n = [0]
        walk_replace(data, n)
        if not n[0]:
            print("crumb no hash", slug)
            continue
        u = requests.post(
            f"{site}/wp-json/wp/v2/pages/{pid}",
            json={"meta": {"_elementor_data": json.dumps(data, ensure_ascii=False)}},
            auth=auth,
            headers={**headers, "Content-Type": "application/json"},
            timeout=60,
        )
        print("crumb", slug, "replacements", n[0], "post", u.status_code)


def probe() -> int:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Cache-Control": "no-cache"})
    fails = 0
    for url, want, loc in PROBES:
        r = s.get(url, timeout=25, allow_redirects=False)
        got = r.headers.get("Location", "")
        ok = r.status_code == want and (not loc or loc in got.lower())
        print(f"{'OK' if ok else 'FAIL'} {r.status_code} {url} -> {got[:90]}")
        if not ok:
            fails += 1
    hub = s.get("https://ledajans.com/led-ekran/", timeout=30)
    h1 = len(re.findall(r"<h1\b", hub.text, re.I))
    print(f"hub H1={h1} hide_css={'page-id-5001 .page-title' in hub.text}")
    hak = s.get("https://ledajans.com/hakkimizda/", timeout=30)
    bad = bool(re.search(r'"item"\s*:\s*"#"', hak.text))
    print(f"hakkimizda hash item={bad}")
    if bad:
        fails += 1
    return fails


def main() -> int:
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env")
        return 1
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    have = existing_urls(site, auth, headers)
    print("existing redirects", len(have))

    added = 0
    for src, dst in EXACT:
        key = src.rstrip("/")
        if key in have or src in have:
            continue
        if add_redirect(site, auth, headers, {
            "url": src,
            "match_type": "url",
            "action_type": "url",
            "action_code": 301,
            "action_data": {"url": dst},
            "group_id": GROUP,
            "title": "gsc-404",
        }):
            added += 1
            have.add(key)

    for src, dst in REGEX_URL:
        if src.rstrip("/") in have:
            continue
        if add_redirect(site, auth, headers, {
            "url": src,
            "regex": True,
            "match_type": "url",
            "action_type": "url",
            "action_code": 301,
            "action_data": {"url": dst},
            "group_id": GROUP,
            "title": "gsc-404-regex",
        }):
            added += 1
            have.add(src.rstrip("/"))

    for src in REGEX_410:
        if src.rstrip("/") in have:
            continue
        if add_redirect(site, auth, headers, {
            "url": src,
            "regex": True,
            "match_type": "url",
            "action_type": "error",
            "action_code": 410,
            "action_data": {},
            "group_id": GROUP,
            "title": "gsc-410",
        }):
            added += 1
            have.add(src.rstrip("/"))

    print("added", added)
    patch_crumbs(site, auth, headers)

    money = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "deploy-money-pages.py"), "--apply"],
        cwd=ROOT,
        check=False,
    )
    print("deploy-money-pages", money.returncode)

    fails = probe()
    print(f"fails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
