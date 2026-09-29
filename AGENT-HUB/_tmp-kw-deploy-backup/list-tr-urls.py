from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")
SITE = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
AUTH = (env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", ""))
H = {"User-Agent": "Mozilla/5.0 LEDAJANS-TR-URLS"}


def collect(cpt: str) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        r = requests.get(
            f"{SITE}/wp-json/wp/v2/{cpt}",
            params={
                "per_page": 100,
                "page": page,
                "status": "publish",
                "lang": "tr",
            },
            auth=AUTH,
            headers=H,
            timeout=40,
        )
        if r.status_code == 400 and page == 1:
            r = requests.get(
                f"{SITE}/wp-json/wp/v2/{cpt}",
                params={"per_page": 100, "page": page, "status": "publish"},
                auth=AUTH,
                headers=H,
                timeout=40,
            )
        if r.status_code != 200:
            print(cpt, "page", page, r.status_code, r.text[:180])
            break
        items = r.json()
        if not items:
            break
        out.extend(items)
        total = int(r.headers.get("X-WP-TotalPages") or "1")
        if page >= total:
            break
        page += 1
    return out


def is_tr(link: str) -> bool:
    u = link.lower()
    if "/en/" in u or "/de/" in u:
        return False
    return u.startswith("https://ledajans.com/")


def main() -> None:
    rows: list[tuple[str, str, str]] = []
    for cpt in ["pages", "posts"]:
        items = collect(cpt)
        print(cpt, len(items))
        for it in items:
            link = (it.get("link") or "").rstrip("/") + "/"
            if link == "https://ledajans.com//":
                link = "https://ledajans.com/"
            if not is_tr(link):
                continue
            title = (it.get("title") or {}).get("rendered") or it.get("slug") or ""
            rows.append((cpt, title, link))
    # unique by url
    seen: set[str] = set()
    uniq: list[tuple[str, str, str]] = []
    for cpt, title, link in rows:
        if link in seen:
            continue
        seen.add(link)
        uniq.append((cpt, title, link))
    uniq.sort(key=lambda x: (x[0], x[2]))
    outp = Path(__file__).resolve().parent / "tr-urls.json"
    outp.write_text(json.dumps(uniq, ensure_ascii=False, indent=2), encoding="utf-8")
    print("UNIQUE", len(uniq))
    for cpt, title, link in uniq:
        print(f"{cpt}\t{link}\t{title}")


if __name__ == "__main__":
    main()
