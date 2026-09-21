#!/usr/bin/env python3
"""TR başlıkları revizyondan geri al; EN/DE başlığı TR kaynaktan çevir. İçeriğe dokunmaz."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from ledajans_i18n import (  # noqa: E402
    link_lang,
    load_state,
    rankmath_for,
    translate_title,
)
from wp_client import list_all, open_session  # noqa: E402

STATE_PATH = os.path.join(ROOT, "AGENT-HUB", "i18n-state.json")
CUTOFF = "2026-09-21T16:00:00"
TR_SEO_TITLE = {
    1248: "LED Ekran | Satış, Kiralama, Kurulum | LEDAJANS",
    5001: "LED Ekran Fiyatları ve Modelleri | İç-Dış Mekan | LEDAJANS",
}
TR_DESC = (
    "LED ekran satış, kiralama ve kurulum. Ücretsiz keşif ve B2B fiyat teklifi — LEDAJANS İstanbul."
)
TR_FOCUS = "led ekran,led ekran kiralama,iç mekan led"


def _title_raw(item: dict) -> str:
    t = item.get("title")
    if isinstance(t, dict):
        return (t.get("raw") or t.get("rendered") or "").strip()
    return str(t or "").strip()


def prev_title(sess, site: str, cpt: str, pid: int) -> str | None:
    r = sess.get(
        f"{site}/wp-json/wp/v2/{cpt}/{pid}/revisions",
        params={"per_page": 20},
        timeout=40,
    )
    if r.status_code != 200:
        return None
    for rev in r.json() or []:
        date = rev.get("date") or ""
        title = _title_raw(rev)
        if date < CUTOFF and title:
            return title
    return None


def patch_title(sess, site: str, cpt: str, pid: int, title: str, meta: dict) -> int:
    r = sess.post(
        f"{site}/wp-json/wp/v2/{cpt}/{pid}",
        json={"title": title, "meta": meta},
        timeout=60,
    )
    return r.status_code


def restore_tr(sess, site: str) -> dict[int, str]:
    restored: dict[int, str] = {}
    for cpt in ("pages", "posts"):
        for item in list_all(
            sess,
            site,
            f"wp/v2/{cpt}",
            params={"status": "publish", "context": "edit"},
        ):
            pid = int(item["id"])
            link = item.get("link") or ""
            if link_lang(link) != "tr":
                continue
            old = prev_title(sess, site, cpt, pid)
            current = _title_raw(item)
            if not old:
                restored[pid] = current
                continue
            seo_title = TR_SEO_TITLE.get(pid) or f"{old} | LEDAJANS"
            meta = {
                "rank_math_title": seo_title[:70],
                "rank_math_description": TR_DESC,
                "rank_math_focus_keyword": TR_FOCUS,
            }
            if current == old and pid not in TR_SEO_TITLE:
                restored[pid] = old
                continue
            code = patch_title(sess, site, cpt, pid, old, meta)
            print("restore_tr", code, cpt, pid, item.get("slug"), old[:70])
            restored[pid] = old
    return restored


def apply_en_de(sess, site: str, restored: dict[int, str]) -> None:
    state = load_state(Path(STATE_PATH))
    for kind, groups in (("pages", state.get("pages") or {}), ("posts", state.get("posts") or {})):
        cpt = kind
        for slug, group in groups.items():
            tr_id = int(group.get("tr") or 0)
            src_title = restored.get(tr_id)
            if not src_title and tr_id:
                r = sess.get(f"{site}/wp-json/wp/v2/{cpt}/{tr_id}", timeout=30)
                if r.status_code == 200:
                    src_title = _title_raw(r.json())
            if not src_title:
                continue
            for lang in ("en", "de"):
                pid = int(group.get(lang) or 0)
                if pid <= 0:
                    continue
                r = sess.get(f"{site}/wp-json/wp/v2/{cpt}/{pid}", timeout=30)
                if r.status_code != 200:
                    print("missing", lang, pid, r.status_code)
                    continue
                item = r.json()
                if link_lang(item.get("link") or "") != lang:
                    print("SKIP_WRONG_LANG", lang, pid, item.get("link"))
                    continue
                new_title = translate_title(src_title, lang)
                seo = rankmath_for(new_title, lang)
                code = patch_title(
                    sess,
                    site,
                    cpt,
                    pid,
                    new_title,
                    {
                        "rank_math_title": seo["rank_math_title"],
                        "rank_math_description": seo["rank_math_description"],
                        "rank_math_focus_keyword": seo["rank_math_focus_keyword"],
                    },
                )
                print("set", lang, code, slug, pid, new_title[:70])


def main() -> int:
    sess, site, user = open_session()
    print("auth", user, site)
    skip_tr = "--skip-tr" in sys.argv
    restored: dict[int, str] = {}
    if not skip_tr:
        restored = restore_tr(sess, site)
        print("tr_restored", len(restored))
    apply_en_de(sess, site, restored)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
