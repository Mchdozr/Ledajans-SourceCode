#!/usr/bin/env python3
"""Sıradaki 2 benzersiz pending blog konusunu seç (kuyruk + canlı WP)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
QPATH = ROOT / "Blog" / "keyword-queue.json"
TITLES = ROOT / "Blog" / "yayinlanan-basliklar.md"
COUNT = 2


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
    site = (os.environ.get("WP_SITE_URL") or data.get("WP_SITE_URL") or "https://ledajans.com").rstrip("/")
    user = os.environ.get("WP_USERNAME") or data.get("WP_USERNAME") or ""
    pw = (os.environ.get("WP_APP_PASSWORD") or data.get("WP_APP_PASSWORD") or "").replace(" ", "")
    return site, user, pw


def live_slugs(site: str, user: str, pw: str) -> set[str]:
    slugs: set[str] = set()
    page = 1
    session = requests.Session()
    if user and pw:
        session.auth = (user, pw)
    session.headers["User-Agent"] = "LEDAJANS-Weekly-Blog/1.0"
    while page <= 20:
        r = session.get(
            f"{site}/wp-json/wp/v2/posts",
            params={"per_page": 100, "page": page, "status": "publish", "_fields": "slug,title"},
            timeout=60,
        )
        if r.status_code != 200:
            break
        items = r.json()
        if not items:
            break
        for it in items:
            slugs.add((it.get("slug") or "").lower())
        if len(items) < 100:
            break
        page += 1
    return slugs


def main() -> int:
    data = json.loads(QPATH.read_text(encoding="utf-8"))
    pubs = {s.lower() for s in (data.get("published_slugs") or [])}
    if TITLES.is_file():
        for line in TITLES.read_text(encoding="utf-8").splitlines():
            if "|" in line and not line.startswith("|") and "Slug" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    pubs.add(parts[1].lower())
    site, user, pw = load_env()
    live = live_slugs(site, user, pw)
    blocked = pubs | live
    pending = [
        t
        for t in sorted(data.get("topics") or [], key=lambda x: int(x.get("priority") or 999))
        if t.get("status") == "pending" and (t.get("slug") or "").lower() not in blocked
    ]
    picked = pending[:COUNT]
    out = {
        "need": COUNT,
        "picked": picked,
        "blocked_count": len(blocked),
        "remaining_after": max(0, len(pending) - len(picked)),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if len(picked) < COUNT:
        print("UYARI: kuyrukta yeterli unique pending yok; yeni topic üret", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
