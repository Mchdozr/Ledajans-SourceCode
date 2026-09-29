import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util  # noqa: E402

GROUPS = {}
for key, fn in (("rental", "create-rental-model-pages.py"), ("icrgb", "create-icrgb-model-pages.py"), ("disrgb", "create-disrgb-model-pages.py")):
    spec = importlib.util.spec_from_file_location(key, ROOT / "scripts" / fn)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    GROUPS[key] = [m.slug for m in mod.MODELS]

BAD = {
    "sidebar_urunlerimiz_h3": r"<h3[^>]*>\s*Ürünlerimiz\s*</h3>",
    "sidebar_menu": r"product-sidebar-(wrapper|nav|card)",
    "slider": r"product-slider-(container|viewport|wrapper)|product-slide\b",
    "neden_ledajans": r"Neden Ledajans",
    "features_block": r"product-features-title|product-contact-section",
    "card_grid": r"<h2[^>]*>[^<]*(Rental LED Ekranlar|RGB LED Paneller|GOB LED Paneller|Flexible LED Paneller)</h2>",
}
H = {"User-Agent": "Mozilla/5.0 LA-verify", "Cache-Control": "no-cache"}
rows, fails = [], 0
for group, slugs in GROUPS.items():
    for slug in slugs:
        url = f"https://ledajans.com/{slug}/"
        r = requests.get(url, params={"nocache": int(time.time())}, headers=H, timeout=60, allow_redirects=False)
        t = r.text
        body = re.search(r'<body[^>]*class="([^"]*)"', t)
        pid = re.search(r"page-id-(\d+)", body.group(1)) if body else None
        robots = re.search(r'<meta name="robots" content="([^"]*)"', t)
        canon = re.search(r'<link rel="canonical" href="([^"]*)"', t)
        bad = [f"{k}:{re.search(p, t).group(0)[:40]}" for k, p in BAD.items() if re.search(p, t)]
        h1 = len(re.findall(r"<h1[\s>]", t))
        ok = (r.status_code == 200 and h1 == 1 and not bad and "ledajans-blog-hero" in t
              and robots and "index" in robots.group(1) and "noindex" not in robots.group(1)
              and canon and canon.group(1) == url and "page-template-elementor_header_footer" in (body.group(1) if body else ""))
        fails += not ok
        rows.append({"group": group, "slug": slug, "status": r.status_code, "page_id": pid.group(1) if pid else None, "h1": h1,
                     "robots": robots.group(1) if robots else None, "canonical_ok": bool(canon and canon.group(1) == url),
                     "bad": bad, "ok": ok})
        print(("OK  " if ok else "FAIL"), group, slug, r.status_code, "id", rows[-1]["page_id"], "h1", h1, "robots", rows[-1]["robots"], "bad", bad)

hub = requests.get("https://ledajans.com/dis-mekan-rgb-panel/", headers=H, timeout=60).text
links = sorted(set(re.findall(r'https://ledajans\.com/(?:h2-5|h3-076|h4|h5|p10-4s)-dis-mekan-rgb-panel/', hub)))
print("3795 links:", len(links))
for u in links:
    r = requests.get(u, headers=H, timeout=60, allow_redirects=False)
    print("  ", r.status_code, u)
    fails += r.status_code != 200
(Path(__file__).parent / "verify-model-layout.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("TOTAL", len(rows), "FAILS", fails)
sys.exit(1 if fails else 0)
