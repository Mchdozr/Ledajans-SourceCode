from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = Path(sys.argv[1])
name = sys.argv[2] if len(sys.argv) > 2 else "summary"
raw = HERE / f"{name}.pages.json"
shutil.copy(src, raw)
items = json.loads(raw.read_text(encoding="utf-8"))["result"]["value"]

summary = []
for it in items:
    if "err" in it:
        print(it["slug"], "ERR", it["err"])
        continue
    slug = it["slug"]
    (HERE / f"{slug}.page.html").write_text(it["html"], encoding="utf-8")
    (HERE / f"{slug}.page.css").write_text(it["css"], encoding="utf-8")
    links = re.findall(r'href="([^"]+)"', it["html"])
    specs = [l for l in links if re.search(r"drive\.google\.com/uc|\.pdf", l)]
    imgs = sorted(set(re.findall(r'src="(https://ledajans\.com/wp-content/uploads/[^"]+)"', it["html"])))
    heads = [re.sub(r"<[^>]+>", "", m).strip()[:60] for m in re.findall(r"<h1[^>]*>(.*?)</h1>", it["html"], re.S)]
    ts = re.search(r"/web/(\d+)", it["url"])
    summary.append({
        "slug": slug, "wayback": it["url"], "ts": ts.group(1) if ts else "", "old_page_id": it["pid"],
        "title": it["title"], "desc": it["desc"], "robots": it["robots"],
        "html_len": len(it["html"]), "css_len": len(it["css"]), "css_links": it["cssLinks"],
        "h1": heads, "specs": sorted(set(specs)), "images": imgs,
    })
    print(f"{slug:42} pid={it['pid']} html={len(it['html'])} css={len(it['css'])} h1={heads} specs={sorted(set(specs))}")

(HERE / f"{name}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
