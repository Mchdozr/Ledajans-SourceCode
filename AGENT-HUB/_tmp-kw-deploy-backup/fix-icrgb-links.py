from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PID = 5006
B = "https://ledajans.com"

MAP = {
    "/p0-93-ic-mekan-led-ekran/": "/cob-ekran/",
    "/h1-25-ic-mekan-rgb-panel/": "/ic-mekan-led-ekran/",
    "/h1-53-ic-mekan-rgb-led-panel/": "/ic-mekan-led-ekran/",
    "/h1-86-ic-mekan-rgb-led-panel/": "/ic-mekan-led-ekran/",
    "/p2-5-ic-mekan-rgb-panel/": "/p25-indoor-rgb-panel/",
    "/p2-5-3840hz-ic-mekan-rgb-panel/": "/p25-indoor-rgb-panel/",
    "/h2-5-6000-hz-ic-mekan-rgb-panel/": "/p25-indoor-rgb-panel/",
    "/p3-07-ic-mekan-rgb-panel/": "/p3-indoor-rgb-panel/",
    "/p4-ic-mekan-rgb-panel/": "/p4-indoor-rgb-panel/",
    "/p0-93-3840hz-gob-ic-mekan-rgb-panel/": "/gob-led-ekran/",
    "/p1-25-6000hz-gob-ic-mekan-rgb-led-panel/": "/gob-led-ekran/",
    "/p1-53-6000hz-gob-ic-mekan-rgb-led-panel/": "/gob-led-ekran/",
    "/p1-86-6000hz-gob-ic-mekan-rgb-led-panel/": "/gob-led-ekran/",
    "/p2-5-gob-ic-mekan-rgb-led-panel/": "/gob-led-ekran/",
    "/q1-25-ic-mekan-flexible-led-panel/": "/ic-mekan-led-ekran/",
    "/q1-53-ic-mekan-flexible-led-panel/": "/ic-mekan-led-ekran/",
    "/q1-86-ic-mekan-flexible-led-panel/": "/ic-mekan-led-ekran/",
    "/q2-5-ic-mekan-flexible-led-panel/": "/ic-mekan-led-ekran/",
}


def load_env() -> tuple[str, str, str]:
    env: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return env.get("WP_SITE_URL", B).rstrip("/"), env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", "")


def rewrite(s: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for old, new in MAP.items():
        for o, n in (
            (B + old, B + new),
            (B + old.rstrip("/") + '"', B + new + '"'),
            (B.replace("/", "\\/") + old.replace("/", "\\/"), B.replace("/", "\\/") + new.replace("/", "\\/")),
        ):
            c = s.count(o)
            if c:
                counts[old] = counts.get(old, 0) + c
                s = s.replace(o, n)
    return s, counts


def main() -> None:
    apply = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    token = base64.b64encode(f"{user}:{pw}".encode()).decode("ascii")
    headers = {"User-Agent": "LEDAJANS-ICRGB-Fix/1.0", "Authorization": f"Basic {token}", "X-WP-Authorization": f"Basic {token}"}

    r = requests.get(f"{site}/wp-json/wp/v2/pages/{PID}", params={"context": "edit"}, auth=auth, headers=headers, timeout=60)
    r.raise_for_status()
    page = r.json()
    raw = (page.get("meta") or {}).get("_elementor_data")
    if not isinstance(raw, str) or not raw:
        raise SystemExit("no _elementor_data")
    content_raw = (page.get("content") or {}).get("raw") or ""

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (OUT / f"page-{PID}-elementor-{stamp}.json").write_text(raw, encoding="utf-8")
    (OUT / f"page-{PID}-content-{stamp}.html").write_text(content_raw, encoding="utf-8")
    print("backup", f"page-{PID}-elementor-{stamp}.json", len(raw), f"page-{PID}-content-{stamp}.html", len(content_raw))

    new_raw, counts = rewrite(raw)
    new_content, ccounts = rewrite(content_raw)
    print("elementor_counts", counts)
    print("content_counts", ccounts)
    missing = [k for k in MAP if k not in counts]
    print("missing_in_elementor", missing)
    json.loads(new_raw)

    if not apply:
        print("DRY-RUN; --apply ile uygula")
        return
    payload: dict = {"meta": {"_elementor_data": new_raw}}
    if ccounts:
        payload["content"] = new_content
    rr = requests.post(f"{site}/wp-json/wp/v2/pages/{PID}", json=payload, auth=auth, headers=headers, timeout=120)
    print("save", rr.status_code, rr.text[:200] if rr.status_code >= 300 else "")
    rr = requests.delete(f"{site}/wp-json/elementor/v1/cache", auth=auth, headers=headers, timeout=60)
    print("elementor_cache", rr.status_code)
    rr = requests.post(f"{site}/wp-json/ledajans/v1/purge", auth=auth, headers=headers, timeout=60)
    print("ledajans_purge", rr.status_code)
    try:
        rr = requests.get(f"{site}/?LSCWP_CTRL=purge&litespeed_type=purge_all", headers={"User-Agent": "LEDAJANS", "Cache-Control": "no-cache"}, timeout=20)
        print("lsc_purge", rr.status_code)
    except requests.RequestException as exc:
        print("lsc_purge ERR", type(exc).__name__)


if __name__ == "__main__":
    main()
