#!/usr/bin/env python3
"""Belirli SEO sayfa slug'larini WP'de olusturur/gunceller (publish, parent=0)."""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_catalog() -> dict[str, tuple[str, str]]:
    """deploy-to-wordpress.py PAGES_TO_DEPLOY (yalnizca page tipi)."""
    import importlib.util

    path = os.path.join(ROOT, "deploy-to-wordpress.py")
    spec = importlib.util.spec_from_file_location("deploy_wp", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("deploy-to-wordpress.py yuklenemedi")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out: dict[str, tuple[str, str]] = {}
    for file_path, slug, title, post_type in mod.PAGES_TO_DEPLOY:
        if post_type == "page" and slug != "projeler":
            out[slug] = (file_path, title)
    return out


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    if os.path.isfile(path):
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


def extract_meta(html: str) -> tuple[str, str]:
    desc = re.search(r"<!-- SEO Meta Description:\s*(.+?)\s*-->", html)
    kw = re.search(r"<!-- SEO Focus Keyword:\s*(.+?)\s*-->", html)
    return (desc.group(1).strip() if desc else "", kw.group(1).strip() if kw else "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slugs", nargs="*", help="Bos + --missing = canli 404 olanlar")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--missing", action="store_true", help="check-seo-page-urls ile 404 slug deploy")
    args = parser.parse_args()

    catalog = load_catalog()
    slugs = list(args.slugs)
    if args.missing:
        import subprocess

        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "check-seo-page-urls.py")],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=180,
        )
        for line in proc.stdout.splitlines():
            if line.startswith("  ('") and ", 404," in line:
                slug = line.split("'")[1]
                if slug in catalog:
                    slugs.append(slug)
        slugs = list(dict.fromkeys(slugs))
        print(f"404 slug: {len(slugs)}")

    if not slugs:
        print("Deploy edilecek slug yok.")
        return 1

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    auth = (user, pw)
    headers = {"User-Agent": "LEDAJANS-SEO-Slug-Deploy/1.0", "Content-Type": "application/json"}
    ok = 0

    for slug in slugs:
        if slug not in catalog:
            print(f"Bilinmeyen slug: {slug}")
            continue
        rel, title = catalog[slug]
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        with open(path, encoding="utf-8") as f:
            content = f.read()
        meta_desc, focus_kw = extract_meta(content)
        payload: dict = {
            "title": title,
            "slug": slug,
            "content": content,
            "status": "publish",
            "parent": 0,
        }
        if meta_desc:
            payload["excerpt"] = meta_desc
            meta: dict[str, str] = {"rank_math_description": meta_desc}
            if focus_kw:
                meta["rank_math_focus_keyword"] = focus_kw
            payload["meta"] = meta

        print(f">> /{slug}/")
        if not args.apply:
            ok += 1
            continue

        r = requests.get(
            f"{site}/wp-json/wp/v2/pages",
            params={"slug": slug, "status": "any"},
            auth=auth,
            headers=headers,
            timeout=30,
        )
        existing = r.json()[0] if r.status_code == 200 and r.json() else None
        if existing:
            u = requests.post(
                f"{site}/wp-json/wp/v2/pages/{existing['id']}",
                json=payload,
                auth=auth,
                headers=headers,
                timeout=120,
            )
        else:
            u = requests.post(
                f"{site}/wp-json/wp/v2/pages",
                json=payload,
                auth=auth,
                headers=headers,
                timeout=120,
            )
        if u.status_code in (200, 201):
            link = u.json().get("link", "")
            print(f"  OK id={u.json().get('id')} {link}")
            ok += 1
        else:
            print(f"  HATA {u.status_code} {u.text[:300]}")

    print(f"\n{'DRY-RUN' if not args.apply else 'APPLY'}: {ok}/{len(slugs)}")
    return 0 if ok == len(slugs) else 1


if __name__ == "__main__":
    sys.exit(main())
