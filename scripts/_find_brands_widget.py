#!/usr/bin/env python3
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    data = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def walk(nodes, path=""):
    if isinstance(nodes, list):
        for i, n in enumerate(nodes):
            yield from walk(n, f"{path}/{i}")
        return
    if not isinstance(nodes, dict):
        return
    wid = nodes.get("id")
    wtype = nodes.get("widgetType") or nodes.get("elType")
    html = ((nodes.get("settings") or {}).get("html") or "")
    if isinstance(html, str) and (
        "ledajans-brands" in html
        or "Markalarımız" in html
        or "ledajans-home-certs" in html
    ):
        print(
            {
                "id": wid,
                "type": wtype,
                "path": path,
                "bytes": len(html),
                "brands": "ledajans-brands" in html or "Markalarımız" in html,
                "certs": "ledajans-home-certs" in html,
            }
        )
    for key in ("elements", "content"):
        if key in nodes:
            yield from walk(nodes[key], f"{path}/{key}")


def main():
    site, user, pw = load_env()
    r = requests.get(
        f"{site}/wp-json/wp/v2/pages/1248",
        params={"context": "edit"},
        auth=(user, pw),
        headers={"User-Agent": "LEDAJANS/1.0"},
        timeout=60,
    )
    raw = (r.json().get("meta") or {}).get("_elementor_data")
    data = json.loads(raw) if isinstance(raw, str) else raw
    print("scan:")
    list(walk(data))
    html = requests.get(
        "https://ledajans.com/",
        headers={"User-Agent": "Mozilla/5.0 (iPhone)", "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    print("live brands", "ledajans-brands" in html or "Markalarımız" in html)
    print("live certs", "ledajans-home-certs" in html)


if __name__ == "__main__":
    main()
