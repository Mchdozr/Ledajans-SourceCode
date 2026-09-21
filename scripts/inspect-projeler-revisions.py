#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "LEDAJANS-fix-dup/1"}


def load_env():
    data = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    auth = (data["WP_USERNAME"], data["WP_APP_PASSWORD"].replace(" ", ""))
    return site, auth


def walk_find(nodes, widget_id: str):
    hits = []
    if isinstance(nodes, list):
        for x in nodes:
            hits.extend(walk_find(x, widget_id))
        return hits
    if not isinstance(nodes, dict):
        return hits
    if str(nodes.get("id")) == widget_id:
        html = (nodes.get("settings") or {}).get("html") or ""
        hits.append(
            {
                "id": widget_id,
                "widgetType": nodes.get("widgetType"),
                "html_len": len(html),
                "has_list": "ledajans-proje-listesi" in html,
                "has_page": "ledajans-projects-page" in html,
                "snippet": html[:180].replace("\n", " "),
            }
        )
    for key in ("elements", "content"):
        if key in nodes:
            hits.extend(walk_find(nodes[key], widget_id))
    return hits


def main() -> int:
    site, auth = load_env()
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/4956/revisions",
        params={"per_page": 10, "context": "edit"},
        auth=auth,
        headers=UA,
        timeout=60,
    )
    print("rev_status", r.status_code, r.headers.get("X-WP-Total"))
    if not r.ok:
        print(r.text[:500])
        # fallback: current page meta
        p = requests.get(
            f"{site}/wp-json/wp/v2/pages/4956",
            params={"context": "edit"},
            auth=auth,
            headers=UA,
            timeout=60,
        )
        print("page", p.status_code)
        return 1
    revs = r.json()
    print("n", len(revs))
    for x in revs[:8]:
        meta = x.get("meta") or {}
        raw = meta.get("_elementor_data")
        print("rev", x.get("id"), x.get("date"), "has_el", bool(raw), "keys", list(x.keys())[:15])
        if raw:
            data = json.loads(raw) if isinstance(raw, str) else raw
            for wid in ("a0baf1e", "3f35913"):
                print(" ", wid, walk_find(data, wid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
