#!/usr/bin/env python3
"""Tek blog HTML'ini WP post olarak yayınla (Rank Math meta dahil).

Kullanım:
  python scripts/publish-blog-post.py Blog/slug.html --dry-run
  python scripts/publish-blog-post.py Blog/slug.html --publish

HTML yorumları:
  <!-- SEO Meta Description: ... -->
  <!-- SEO Focus Keyword: led ekran, cob led ekran -->
  <!-- SEO Title: ... -->  (opsiyonel; yoksa H2 veya dosya adı)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = "LEDAJANS-Publish-Blog/1.0"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    env_path = ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip("\"'")
    site = (
        os.environ.get("WP_SITE_URL")
        or data.get("WP_SITE_URL")
        or "https://ledajans.com"
    ).rstrip("/")
    user = os.environ.get("WP_USERNAME") or data.get("WP_USERNAME") or ""
    pw = (os.environ.get("WP_APP_PASSWORD") or data.get("WP_APP_PASSWORD") or "").replace(
        " ", ""
    )
    return site, user, pw


def extract(html: str, name: str) -> str:
    m = re.search(rf"<!-- SEO {name}:\s*(.+?)\s*-->", html)
    return m.group(1).strip() if m else ""


def extract_h2_title(html: str) -> str:
    m = re.search(
        r"<h2[^>]*>\s*(?:📌\s*)?(?:<strong>)?(.+?)(?:</strong>)?\s*</h2>",
        html,
        re.I | re.S,
    )
    if not m:
        return ""
    t = re.sub(r"<[^>]+>", "", m.group(1))
    return re.sub(r"\s+", " ", t).strip()


def slug_from_path(path: Path) -> str:
    return path.stem.replace("_", "-").lower()


def find_post(session: requests.Session, site: str, slug: str) -> dict | None:
    r = session.get(
        f"{site}/wp-json/wp/v2/posts",
        params={"slug": slug, "status": "any", "per_page": 1},
        timeout=60,
    )
    if r.status_code != 200:
        return None
    items = r.json()
    return items[0] if items else None


def mark_queue_published(slug: str) -> None:
    import json

    qpath = ROOT / "Blog" / "keyword-queue.json"
    if not qpath.is_file():
        return
    data = json.loads(qpath.read_text(encoding="utf-8"))
    pubs = set(data.get("published_slugs") or [])
    pubs.add(slug)
    data["published_slugs"] = sorted(pubs)
    for t in data.get("topics") or []:
        if t.get("slug") == slug:
            t["status"] = "published"
    qpath.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("queue_updated", slug)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html_path", help="Blog/*.html göreli veya mutlak yol")
    ap.add_argument("--slug", default="", help="WP slug (varsayılan: dosya adı)")
    ap.add_argument("--title", default="", help="WP başlık override")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--publish",
        action="store_true",
        help="status=publish (yoksa draft)",
    )
    ap.add_argument("--no-queue-update", action="store_true")
    args = ap.parse_args()

    path = Path(args.html_path)
    if not path.is_file():
        path = ROOT / args.html_path
    if not path.is_file():
        print("HATA: dosya yok", args.html_path)
        return 1

    html = path.read_text(encoding="utf-8")
    if "ledajans-seo-article" not in html:
        print("HATA: ledajans-seo-article yok — blog şablonuna uymuyor")
        return 1

    meta = extract(html, "Meta Description")
    focus = extract(html, "Focus Keyword")
    seo_title = extract(html, "Title")
    title = args.title or seo_title or extract_h2_title(html) or path.stem
    slug = (args.slug or slug_from_path(path)).strip("/")
    status = "publish" if args.publish else "draft"

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: WP_USERNAME / WP_APP_PASSWORD (.env) gerekli")
        return 1

    print("file", path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    print("slug", slug)
    print("title", title)
    print("focus", focus[:80] if focus else "(yok)")
    print("meta", meta[:100] if meta else "(yok)")
    print("status", status)

    if args.dry_run:
        print("DRY_RUN OK")
        return 0

    session = requests.Session()
    session.auth = (user, pw)
    session.headers.update({"User-Agent": UA, "Content-Type": "application/json"})

    payload: dict = {
        "title": title,
        "slug": slug,
        "content": html,
        "status": status,
    }
    if meta:
        payload["excerpt"] = meta
    meta_obj: dict[str, str] = {}
    if meta:
        meta_obj["rank_math_description"] = meta
    if focus:
        # İlk virgülden önceki odak + tam liste
        meta_obj["rank_math_focus_keyword"] = focus
    if title:
        # Rank Math SEO title: odak kelime başta kalsın diye title kullan
        meta_obj["rank_math_title"] = title
    if meta_obj:
        payload["meta"] = meta_obj

    existing = find_post(session, site, slug)
    if existing:
        url = f"{site}/wp-json/wp/v2/posts/{existing['id']}"
        r = session.post(url, json=payload, timeout=120)
        action = "update"
    else:
        r = session.post(f"{site}/wp-json/wp/v2/posts", json=payload, timeout=120)
        action = "create"

    print(action, r.status_code, r.text[:300])
    if r.status_code not in (200, 201):
        return 1

    link = r.json().get("link")
    print("link", link)
    if args.publish and not args.no_queue_update:
        mark_queue_published(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
