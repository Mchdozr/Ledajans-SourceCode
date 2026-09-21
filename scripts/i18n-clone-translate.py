#!/usr/bin/env python3
"""Polylang EN/DE: Elementor kopya, çeviri, iç link, Rank Math. TR Hero dosyasına dokunmaz."""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from ledajans_i18n import (  # noqa: E402
    LANGS,
    ORIGIN,
    PAGE_SLUGS,
    PILOT_PAGES,
    PILOT_POSTS,
    POST_SLUGS,
    load_state,
    link_lang,
    rankmath_for,
    save_state,
    skip_page,
    skip_post,
    slug_for,
    translate_elementor,
    translate_html,
    translate_title,
)
from wp_client import list_all, load_env, open_session  # noqa: E402

UA = "LEDAJANS-I18N/1.0"
STATE_PATH = os.path.join(ROOT, "AGENT-HUB", "i18n-state.json")
EMPTY_DRAFT_SLUGS = {
    "en",
    "de",
    "about-us",
    "contact",
    "our-company-information",
    "outdoor-led-screen",
    "uber-uns",
    "kommunikation",
    "unsere-firmeninformationen",
}
ELEMENTOR_META = (
    "_elementor_edit_mode",
    "_elementor_template_type",
    "_elementor_version",
    "_elementor_page_settings",
    "_elementor_controls_usage",
)


def _json(r: requests.Response) -> dict | list | None:
    try:
        return r.json()
    except Exception:
        return None


def restore_languages(sess: requests.Session, site: str) -> None:
    print("=== restore Polylang EN/DE ===")
    r = sess.get(f"{site}/wp-json/pll/v1/languages", timeout=30)
    existing = []
    if r.status_code == 200 and isinstance(r.json(), list):
        existing = [x.get("slug") for x in r.json()]
        print("langs", existing)
    want = [
        {"name": "English", "slug": "en", "locale": "en_GB", "rtl": False, "flag": "gb"},
        {"name": "Deutsch", "slug": "de", "locale": "de_DE", "rtl": False, "flag": "de"},
    ]
    for lang in want:
        if lang["slug"] in existing:
            print("exists", lang["slug"])
            continue
        c = sess.post(f"{site}/wp-json/pll/v1/languages", json=lang, timeout=40)
        print("create", lang["slug"], c.status_code, (c.text or "")[:180])
    st = sess.get(f"{site}/wp-json/pll/v1/settings", timeout=30)
    if st.status_code == 200 and isinstance(st.json(), dict):
        body = st.json()
        body["hide_default"] = True
        body["force_lang"] = 1
        body["browser"] = False
        body["redirect_lang"] = False
        # Polylang: post/page varsayılan; post_types yalnızca ek CPT.
        extras = [t for t in (body.get("post_types") or []) if t not in ("post", "page")]
        if "elementor_library" not in extras:
            extras.append("elementor_library")
        body["post_types"] = extras
        p = sess.post(f"{site}/wp-json/pll/v1/settings", json=body, timeout=30)
        print("pll_settings", p.status_code, "post_types", (p.json() or {}).get("post_types") if p.headers.get("content-type","").startswith("application/json") else (p.text or "")[:120])
    _delete_lang_catchall(sess, site)


def _delete_lang_catchall(sess: requests.Session, site: str) -> None:
    drop = {
        r"^/(en|de)(/.*)?$",
        "/en",
        "/en/",
        "/de",
        "/de/",
        "/en/contact",
        "/en/contact/",
        "/en/about-us",
        "/en/about-us/",
        "/en/our-company-information",
        "/en/our-company-information/",
        "/en/outdoor-led-screen",
        "/en/outdoor-led-screen/",
        "/de/kommunikation",
        "/de/kommunikation/",
        "/de/uber-uns",
        "/de/uber-uns/",
        "/de/unsere-firmeninformationen",
        "/de/unsere-firmeninformationen/",
        "/de/led-ekran",
        "/de/led-anzeige",
        "/de/led-bildschirm",
        "/de/led-ekran/",
        "/de/led-anzeige/",
        "/de/led-bildschirm/",
    }
    for mapping in (PAGE_SLUGS, POST_SLUGS):
        for slugs in mapping.values():
            for lang, slug in slugs.items():
                drop.add(f"/{lang}/{slug}")
                drop.add(f"/{lang}/{slug}/")
    deleted = 0
    kill_ids: list[int] = []
    page = 0
    while page <= 30:
        r = sess.get(
            f"{site}/wp-json/redirection/v1/redirect",
            params={"per_page": 200, "page": page},
            timeout=40,
        )
        if r.status_code != 200:
            print("redir list", r.status_code, (r.text or "")[:120])
            break
        items = (r.json() or {}).get("items") or []
        if not items:
            break
        for it in items:
            url = (it.get("url") or "").strip()
            regex = bool(it.get("regex"))
            action = it.get("action_data") or {}
            dest = ""
            if isinstance(action, dict):
                dest = str(action.get("url") or "")
            kill = url in drop
            if regex and "en|de" in url and "case" not in url and (
                dest.rstrip("/") in ("https://ledajans.com", ORIGIN) or url.startswith("^/(en|de)")
            ):
                kill = True
            if kill and it.get("id"):
                kill_ids.append(int(it["id"]))
                print("queue_del", it.get("id"), url)
        page += 1
    if kill_ids:
        d = sess.post(
            f"{site}/wp-json/redirection/v1/bulk/redirect/delete",
            json={"items": kill_ids},
            timeout=60,
        )
        print("bulk_del", len(kill_ids), d.status_code, (d.text or "")[:120])
        if d.status_code in (200, 204):
            deleted = len(kill_ids)
    print("deleted_catchall", deleted)


def _ensure_junk_redirects(sess: requests.Session, site: str) -> None:
    have: set[str] = set()
    page = 0
    while page <= 30:
        r = sess.get(
            f"{site}/wp-json/redirection/v1/redirect",
            params={"per_page": 200, "page": page},
            timeout=30,
        )
        if r.status_code != 200:
            break
        items = (r.json() or {}).get("items") or []
        if not items:
            break
        for it in items:
            have.add((it.get("url") or "").rstrip("/"))
        page += 1
    rules = [
        ("/gallery", "/projeler/", 301),
        ("/portfolio-01", "/projeler/", 301),
        ("/portfolio-02", "/projeler/", 301),
        ("/portfolio-03", "/projeler/", 301),
        ("/about-me", "/hakkimizda/", 301),
        ("/led-ekran-2", "/led-ekran/", 301),
        ("/led-ekran-3", "/led-ekran/", 301),
        ("/led", "/led-ekran/", 301),
        ("/led-2", "/led-ekran/", 301),
        ("/case", "/projeler/", 301),
        ("/en/case", "/projeler/", 301),
        ("/de/case", "/projeler/", 301),
        ("/feed", "/", 301),
        ("/comments/feed", "/", 301),
    ]
    regex = [
        (r"^/case(/.*)?$", "/projeler/", 301),
        (r"^/(en|de)/case(/.*)?$", "/projeler/", 301),
        (r"^/gva_template/.*", "", 410),
    ]
    added = 0
    for src, dst, code in rules:
        if src.rstrip("/") in have:
            continue
        payload = {
            "url": src,
            "match_type": "url",
            "action_type": "url",
            "action_code": code,
            "action_data": {"url": ORIGIN + dst},
            "group_id": 1,
            "title": "i18n-junk",
        }
        r = sess.post(f"{site}/wp-json/redirection/v1/redirect", json=payload, timeout=30)
        print("redir", src, r.status_code)
        if r.status_code in (200, 201):
            added += 1
    for src, dst, code in regex:
        if src.rstrip("/") in have:
            continue
        payload = {
            "url": src,
            "regex": True,
            "match_type": "url",
            "action_type": "error" if code == 410 else "url",
            "action_code": code,
            "action_data": {} if code == 410 else {"url": ORIGIN + dst},
            "group_id": 1,
            "title": "i18n-junk-regex",
        }
        r = sess.post(f"{site}/wp-json/redirection/v1/redirect", json=payload, timeout=30)
        print("redir_re", src, r.status_code)
        if r.status_code in (200, 201):
            added += 1
    print("junk_added", added)


def _parse_elementor(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def _dump_elementor(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _get_item(sess: requests.Session, site: str, cpt: str, item_id: int) -> dict | None:
    r = sess.get(
        f"{site}/wp-json/wp/v2/{cpt}/{item_id}",
        params={"context": "edit"},
        timeout=60,
    )
    if r.status_code != 200:
        print("get fail", cpt, item_id, r.status_code)
        return None
    body = r.json()
    return body if isinstance(body, dict) else None


def _find_by_slug(sess: requests.Session, site: str, cpt: str, slug: str) -> dict | None:
    r = sess.get(
        f"{site}/wp-json/wp/v2/{cpt}",
        params={"slug": slug, "status": "publish,draft,private", "context": "edit"},
        timeout=40,
    )
    if r.status_code != 200:
        return None
    items = r.json()
    return items[0] if isinstance(items, list) and items else None


def _title_text(item: dict) -> str:
    t = item.get("title")
    if isinstance(t, dict):
        return t.get("raw") or t.get("rendered") or ""
    return str(t or "")


def _copy_meta(src: dict) -> dict:
    meta = dict(src.get("meta") or {})
    out = {}
    for k in ELEMENTOR_META:
        if k in meta and meta[k] not in (None, "", []):
            out[k] = meta[k]
    out["_elementor_edit_mode"] = "builder"
    return out


def _set_pll(sess: requests.Session, site: str, cpt: str, ids: dict[str, int]) -> None:
    translations = {k: int(v) for k, v in ids.items() if v}
    r = sess.post(f"{site}/wp-json/ledajans/v1/pll-link", json=translations, timeout=40)
    print("pll_link", translations, r.status_code, (r.text or "")[:160])
    if r.status_code in (200, 201):
        return
    for lang, pid in translations.items():
        payload = {"lang": lang, "translations": translations}
        p = sess.post(
            f"{site}/wp-json/wp/v2/{cpt}/{pid}",
            params={"lang": lang},
            json=payload,
            timeout=40,
        )
        print("pll", cpt, lang, pid, p.status_code)


def _set_front(sess: requests.Session, site: str, lang: str, page_id: int) -> None:
    r = sess.get(f"{site}/wp-json/pll/v1/languages/{lang}", timeout=30)
    if r.status_code != 200:
        print("lang get", lang, r.status_code)
        return
    body = r.json()
    if not isinstance(body, dict):
        return
    body["page_on_front"] = page_id
    term = body.get("term_id")
    url = f"{site}/wp-json/pll/v1/languages/{term}" if term else f"{site}/wp-json/pll/v1/languages/{lang}"
    p = sess.post(url, json={"page_on_front": page_id}, timeout=30)
    print("front", lang, page_id, p.status_code, (p.text or "")[:120])


def clone_one(
    sess: requests.Session,
    site: str,
    src: dict,
    cpt: str,
    lang: str,
    *,
    dry: bool,
    use_mt: bool,
) -> int | None:
    tr_slug = src.get("slug") or ""
    kind = "page" if cpt == "pages" else "post"
    new_slug = slug_for(tr_slug, lang, kind)
    title = translate_title(_title_text(src), lang)
    meta_src = src.get("meta") or {}
    el = _parse_elementor(meta_src.get("_elementor_data"))
    new_meta = _copy_meta(src)
    if el is not None:
        translated = translate_elementor(copy.deepcopy(el), lang, use_mt=use_mt)
        new_meta["_elementor_data"] = _dump_elementor(translated)
    content = src.get("content")
    raw_html = content.get("raw") if isinstance(content, dict) else ""
    if raw_html and "_elementor_data" not in new_meta:
        new_meta_content = translate_html(raw_html, lang, use_mt=use_mt)
    else:
        new_meta_content = None
    seo = rankmath_for(title, lang)
    new_meta.update(seo)
    payload = {
        "title": title,
        "slug": new_slug,
        "status": "publish",
        "lang": lang,
        "translations": {"tr": src["id"]},
        "meta": new_meta,
    }
    if src.get("featured_media"):
        payload["featured_media"] = src["featured_media"]
    if src.get("template"):
        payload["template"] = src["template"]
    if new_meta_content:
        payload["content"] = new_meta_content
    if cpt == "posts":
        payload["categories"] = src.get("categories") or []
        payload["tags"] = src.get("tags") or []
    existing = _find_by_slug(sess, site, cpt, new_slug)
    if existing and existing.get("id") != src["id"]:
        link = (existing.get("link") or "").lower()
        same_lang = f"/{lang}/" in link or link.rstrip("/").endswith("/" + lang)
        if not same_lang:
            new_slug = f"{new_slug}-{lang}"
            payload["slug"] = new_slug
            existing = _find_by_slug(sess, site, cpt, new_slug)
    if dry:
        print("DRY", lang, tr_slug, "->", new_slug, "el", bool(el), "exist", bool(existing))
        return existing["id"] if existing else None
    if existing and existing.get("id") != src["id"]:
        pid = existing["id"]
        if link_lang(existing.get("link") or "") != lang:
            print("SKIP_WRONG_LANG", lang, pid, existing.get("link"))
            return None
        payload["status"] = "publish"
        r = sess.post(
            f"{site}/wp-json/wp/v2/{cpt}/{pid}",
            params={"lang": lang},
            json=payload,
            timeout=300,
        )
        print("update", lang, new_slug, pid, r.status_code, (r.text or "")[:120])
        return pid if r.status_code in (200, 201) else None
    r = sess.post(
        f"{site}/wp-json/wp/v2/{cpt}",
        params={"lang": lang},
        json=payload,
        timeout=180,
    )
    print("create", lang, new_slug, r.status_code, (r.text or "")[:160])
    body = _json(r)
    if r.status_code in (200, 201) and isinstance(body, dict):
        return int(body["id"])
    payload["slug"] = f"{new_slug}-{lang}"
    r = sess.post(
        f"{site}/wp-json/wp/v2/{cpt}",
        params={"lang": lang},
        json=payload,
        timeout=180,
    )
    print("create_retry", lang, payload["slug"], r.status_code, (r.text or "")[:160])
    body = _json(r)
    if r.status_code in (200, 201) and isinstance(body, dict):
        return int(body["id"])
    return None


def _is_tr(item: dict) -> bool:
    link = (item.get("link") or "").lower()
    slug = item.get("slug") or ""
    if slug in EMPTY_DRAFT_SLUGS:
        return False
    if "/en/" in link or link.rstrip("/").endswith("/en"):
        return False
    if "/de/" in link or link.rstrip("/").endswith("/de"):
        return False
    lang = item.get("lang")
    if lang and lang not in ("tr", "tr_TR"):
        return False
    return True


def _pick(items: list[dict], slugs: list[str] | None, kind: str) -> list[dict]:
    out = []
    for it in items:
        if not _is_tr(it):
            continue
        slug = it.get("slug") or ""
        if kind == "page" and skip_page(slug):
            continue
        if kind == "post" and skip_post(slug):
            continue
        if slugs is not None and slug not in slugs:
            continue
        if (it.get("status") or "") != "publish":
            continue
        out.append(it)
    return out


def run_clone(
    sess: requests.Session,
    site: str,
    *,
    pilot: bool,
    dry: bool,
    use_mt: bool,
) -> None:
    state = load_state(__import__("pathlib").Path(STATE_PATH))
    pages = list_all(
        sess, site, "wp/v2/pages", params={"status": "publish", "context": "edit"}
    )
    posts = list_all(
        sess, site, "wp/v2/posts", params={"status": "publish", "context": "edit"}
    )
    page_slugs = PILOT_PAGES if pilot else None
    post_slugs = PILOT_POSTS if pilot else None
    sel_pages = _pick(pages, page_slugs, "page")
    sel_posts = _pick(posts, post_slugs, "post")
    print("clone pages", len(sel_pages), "posts", len(sel_posts), "pilot", pilot, "dry", dry)
    for src in sel_pages + sel_posts:
        cpt = "pages" if src in sel_pages else "posts"
        kind = "page" if cpt == "pages" else "post"
        full = _get_item(sess, site, cpt, src["id"]) or src
        ids = {"tr": full["id"]}
        bucket = state["pages" if cpt == "pages" else "posts"]
        row = bucket.get(full.get("slug") or "", {})
        for lang in LANGS:
            pid = clone_one(sess, site, full, cpt, lang, dry=dry, use_mt=use_mt)
            if pid:
                ids[lang] = pid
                row[lang] = pid
            time.sleep(0.15)
        row["tr"] = full["id"]
        bucket[full.get("slug") or str(full["id"])] = row
        if not dry and len(ids) >= 2:
            _set_pll(sess, site, cpt, ids)
        if not dry and cpt == "pages" and full.get("slug") == "tr-2":
            if ids.get("en"):
                _set_front(sess, site, "en", ids["en"])
            if ids.get("de"):
                _set_front(sess, site, "de", ids["de"])
        save_state(__import__("pathlib").Path(STATE_PATH), state)


def clone_templates(sess: requests.Session, site: str, *, dry: bool, use_mt: bool) -> None:
    items = list_all(
        sess,
        site,
        "wp/v2/elementor_library",
        params={"status": "publish", "context": "edit"},
    )
    print("templates", len(items))
    for src in items:
        if src.get("id") == 9:
            print("skip kit", src.get("id"))
            continue
        slug = src.get("slug") or ""
        if skip_page(slug) or slug in EMPTY_DRAFT_SLUGS:
            continue
        if not _is_tr(src):
            continue
        types = src.get("template_type") or src.get("meta", {}).get("_elementor_template_type")
        t = str(types or "")
        if t not in {"header", "footer", "wp-page", "section", "archive", "single"} and "header" not in slug and "footer" not in slug:
            if t not in {"kit"}:
                continue
        full = _get_item(sess, site, "elementor_library", src["id"]) or src
        ids = {"tr": full["id"]}
        for lang in LANGS:
            pid = clone_one(
                sess, site, full, "elementor_library", lang, dry=dry, use_mt=use_mt
            )
            if pid:
                ids[lang] = pid
        if not dry and len(ids) >= 2:
            _set_pll(sess, site, "elementor_library", ids)


def clone_menus(sess: requests.Session, site: str, *, dry: bool) -> None:
    menus = list_all(sess, site, "wp/v2/menus", params={"context": "edit"})
    print("menus", [(m.get("id"), m.get("name"), m.get("slug")) for m in menus])
    tr = None
    for m in menus:
        name = (m.get("name") or "").lower()
        slug = (m.get("slug") or "").lower()
        if m.get("id") == 42 or "tr" in slug or name in {"menu", "ana menu", "ana menü"}:
            tr = m
            break
    if not tr and menus:
        tr = menus[0]
    if not tr:
        print("menu yok")
        return
    items = list_all(
        sess,
        site,
        "wp/v2/menu-items",
        params={"menus": tr["id"], "context": "edit", "per_page": 100},
    )
    print("menu_items", tr.get("id"), len(items))
    for lang in LANGS:
        exist = None
        want_slug = f"main-{lang}"
        for m in menus:
            if m.get("id") in (99, 119) and lang == ("en" if m.get("id") == 99 else "de"):
                exist = m
            if (m.get("slug") or "") == want_slug:
                exist = m
        payload = {
            "name": f"Main {lang.upper()}",
            "slug": want_slug,
            "lang": lang,
        }
        if dry:
            print("DRY menu", lang, "exist", bool(exist), "items", len(items))
            continue
        if exist:
            mid = exist["id"]
            sess.post(f"{site}/wp-json/wp/v2/menus/{mid}", json={"lang": lang}, timeout=30)
        else:
            r = sess.post(f"{site}/wp-json/wp/v2/menus", json=payload, timeout=30)
            print("menu create", lang, r.status_code, (r.text or "")[:160])
            body = _json(r)
            if r.status_code not in (200, 201) or not isinstance(body, dict):
                continue
            mid = body["id"]
        id_map: dict[int, int] = {}
        ordered = sorted(items, key=lambda x: int(x.get("parent") or 0))
        for it in ordered:
            url = it.get("url") or ""
            from ledajans_i18n import rewrite_href, translate_text

            new_url = rewrite_href(url, lang)
            title = translate_text(it.get("title", {}).get("raw") or it.get("title") or "", lang, use_mt=False)
            if isinstance(it.get("title"), str):
                title = translate_text(it["title"], lang, use_mt=False)
            parent = it.get("parent") or 0
            body = {
                "title": title if isinstance(title, str) else str(title),
                "url": new_url,
                "status": "publish",
                "menus": mid,
                "parent": id_map.get(int(parent), 0) if parent else 0,
                "type": it.get("type") or "custom",
                "lang": lang,
            }
            cr = sess.post(f"{site}/wp-json/wp/v2/menu-items", json=body, timeout=30)
            print("menuitem", lang, title, cr.status_code)
            cb = _json(cr)
            if cr.status_code in (200, 201) and isinstance(cb, dict):
                id_map[int(it["id"])] = int(cb["id"])


def generate_chrome(*, use_mt: bool) -> None:
    from pathlib import Path

    mapping = [
        (Path(ROOT) / "Ust-Menu" / "ust-menu.html", "Ust-Menu/ust-menu-{lang}.html"),
        (Path(ROOT) / "Footer" / "footer.html", "Footer/footer-{lang}.html"),
    ]
    for src, dest_tpl in mapping:
        raw = src.read_text(encoding="utf-8")
        for lang in LANGS:
            html = translate_html(raw, lang, use_mt=use_mt)
            out = Path(ROOT) / dest_tpl.format(lang=lang)
            out.write_text(html, encoding="utf-8")
            print("wrote", out, "bytes", out.stat().st_size)


def inject_chrome(sess: requests.Session, site: str, *, dry: bool) -> None:
    from pathlib import Path

    files = {
        "en": {
            "header": Path(ROOT) / "Ust-Menu" / "ust-menu-en.html",
            "footer": Path(ROOT) / "Footer" / "footer-en.html",
        },
        "de": {
            "header": Path(ROOT) / "Ust-Menu" / "ust-menu-de.html",
            "footer": Path(ROOT) / "Footer" / "footer-de.html",
        },
    }
    if dry:
        for lang, pair in files.items():
            print("DRY chrome", lang, pair["header"].is_file(), pair["footer"].is_file())
        return
    pages = list_all(sess, site, "wp/v2/pages", params={"status": "publish", "context": "edit"})
    for lang, pair in files.items():
        if not pair["header"].is_file() or not pair["footer"].is_file():
            continue
        header = pair["header"].read_text(encoding="utf-8")
        footer = pair["footer"].read_text(encoding="utf-8")
        for p in pages:
            link = (p.get("link") or "").lower()
            if f"/{lang}/" not in link and not link.rstrip("/").endswith(f"/{lang}"):
                continue
            full = _get_item(sess, site, "pages", p["id"])
            if not full:
                continue
            el = _parse_elementor((full.get("meta") or {}).get("_elementor_data"))
            if el is None:
                continue
            changed = _replace_widget_html(el, header, footer)
            if not changed:
                continue
            r = sess.post(
                f"{site}/wp-json/wp/v2/pages/{p['id']}",
                json={"meta": {"_elementor_data": _dump_elementor(el)}},
                timeout=90,
            )
            print("chrome inject", lang, p.get("slug"), r.status_code)


def _replace_widget_html(tree: Any, header: str, footer: str) -> bool:
    changed = False

    def walk(node: Any) -> None:
        nonlocal changed
        if isinstance(node, list):
            for x in node:
                walk(x)
            return
        if not isinstance(node, dict):
            return
        settings = node.get("settings") if isinstance(node.get("settings"), dict) else {}
        html = settings.get("html")
        if isinstance(html, str):
            if "ledajans-header-responsive-css" in html or "pll-parent-menu-item" in html:
                settings["html"] = header
                node["settings"] = settings
                changed = True
            elif "ledajans-footer" in html:
                settings["html"] = footer
                node["settings"] = settings
                changed = True
        for v in node.values():
            if isinstance(v, (list, dict)):
                walk(v)

    walk(tree)
    return changed


def keep_drafts(sess: requests.Session, site: str) -> None:
    print("=== empty drafts stay draft ===")
    for slug in EMPTY_DRAFT_SLUGS:
        p = _find_by_slug(sess, site, "pages", slug)
        if not p:
            print("page", slug, "none")
            continue
        print("page", slug, "id", p["id"], "status", p.get("status"), "KEEP")
        if p.get("status") != "publish" or slug not in EMPTY_DRAFT_SLUGS:
            continue
        content = p.get("content") or {}
        raw = content.get("raw") if isinstance(content, dict) else str(content or "")
        el = (p.get("meta") or {}).get("_elementor_data")
        if (raw or "")[:80].strip() and el:
            print("skip re-draft filled", slug)
            continue
        if el and isinstance(el, str) and len(el) > 200:
            print("skip re-draft elementor", slug)
            continue
        sess.post(
            f"{site}/wp-json/wp/v2/pages/{p['id']}",
            json={"status": "draft"},
            timeout=30,
        )
        print("re-draft", slug)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--restore-langs", action="store_true")
    ap.add_argument("--menus", action="store_true")
    ap.add_argument("--templates", action="store_true")
    ap.add_argument("--generate-chrome", action="store_true")
    ap.add_argument("--inject-chrome", action="store_true")
    ap.add_argument("--no-mt", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        from ledajans_i18n import self_test

        return self_test()
    use_mt = not args.no_mt
    if args.generate_chrome:
        generate_chrome(use_mt=use_mt)
        if not any(
            [
                args.restore_langs,
                args.pilot,
                args.batch,
                args.menus,
                args.templates,
                args.inject_chrome,
            ]
        ):
            return 0
    try:
        sess, site, user = open_session()
    except RuntimeError as exc:
        print("AUTH", exc)
        return 2
    print("auth_ok", user, site)
    if args.restore_langs or args.pilot or args.batch:
        restore_languages(sess, site)
        keep_drafts(sess, site)
        _ensure_junk_redirects(sess, site)
    if args.pilot or args.batch:
        run_clone(
            sess,
            site,
            pilot=bool(args.pilot and not args.batch),
            dry=args.dry_run,
            use_mt=use_mt,
        )
    if args.templates:
        clone_templates(sess, site, dry=args.dry_run, use_mt=use_mt)
    if args.menus:
        clone_menus(sess, site, dry=args.dry_run)
    if args.inject_chrome:
        inject_chrome(sess, site, dry=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
