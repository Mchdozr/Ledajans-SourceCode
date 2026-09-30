import json
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from ledajans_model_layout import wp_session  # noqa: E402

BASE = "https://ledajans.com"
UA = {"User-Agent": "Mozilla/5.0 sitemap-gap"}


def norm(u):
    return u.split("#")[0].split("?")[0].rstrip("/").lower()


def sitemap_urls():
    idx = requests.get(f"{BASE}/sitemap_index.xml", headers=UA, timeout=30).text
    subs = re.findall(r"<loc>([^<]+)</loc>", idx)
    urls = set()
    for s in subs:
        body = requests.get(s, headers=UA, timeout=30).text
        urls.update(norm(u) for u in re.findall(r"<loc>([^<]+)</loc>", body) if not u.endswith(".xml"))
    return subs, urls


def wp_items(sess, kind):
    out, page = [], 1
    while True:
        r = sess.get(f"{BASE}/wp-json/wp/v2/{kind}", params={"per_page": 100, "page": page, "status": "publish",
                                                             "_fields": "id,link,title,meta"}, timeout=60)
        if r.status_code != 200:
            break
        data = r.json()
        if not data:
            break
        out.extend(data)
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            break
        page += 1
    return out


def main():
    subs, sm = sitemap_urls()
    sess, _ = wp_session(UA["User-Agent"])
    rows = []
    for kind in ("pages", "posts"):
        for it in wp_items(sess, kind):
            link = it["link"]
            if norm(link) in sm or norm(link) == norm(BASE):
                continue
            robots = (it.get("meta") or {}).get("rank_math_robots") or []
            rows.append({"kind": kind, "id": it["id"], "url": link,
                         "title": it["title"]["rendered"], "robots": robots})
    out = Path(__file__).with_name("sitemap-gap.json")
    out.write_text(json.dumps({"sitemaps": subs, "gap": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("sitemaps:", len(subs), "sitemap urls:", len(sm), "gap:", len(rows))
    for r in rows:
        print(r["kind"], r["id"], r["url"], "noindex" if "noindex" in r["robots"] else "", sep="\t")


if __name__ == "__main__":
    main()
