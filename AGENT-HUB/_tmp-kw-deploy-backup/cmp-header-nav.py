from __future__ import annotations

import hashlib
import re
from pathlib import Path

out = Path(__file__).resolve().parent
for slug in ["home", "hakkimizda", "blog", "led"]:
    html = (out / f"hdr-{slug}.html").read_text(encoding="utf-8")
    m = re.search(
        r'(<header[^>]*wp-site-header[\s\S]*?</header>)',
        html,
        re.I,
    )
    hdr = m.group(1) if m else ""
    # strip current-menu classes for structural compare
    stripped = re.sub(
        r"\b(current-menu-item|current_page_item|current-menu-ancestor|current-menu-parent|current_page_parent|current_page_ancestor|current-menu-parent)\b",
        "",
        hdr,
    )
    items = re.findall(
        r'<a[^>]*href="([^"]+)"[^>]*>\s*(?:<span[^>]*>)?([^<]{1,80})',
        hdr,
    )
    phones = re.findall(r"tel:[+\d]+", hdr)
    ids = re.findall(r"elementor-element-([0-9a-f]{5,})", hdr)
    print(f"\n=== {slug} header_len={len(hdr)} hash={hashlib.md5(hdr.encode()).hexdigest()[:12]} strip={hashlib.md5(stripped.encode()).hexdigest()[:12]} ===")
    print("ids", ids[:12], "n=", len(ids))
    print("phones", phones)
    print("links:")
    seen = set()
    for href, txt in items:
        key = (href, txt.strip())
        if key in seen:
            continue
        seen.add(key)
        if any(x in txt.lower() for x in ["anasayfa", "ürün", "proje", "blog", "ileti", "hakkı", "english", "dil", "home"]) or "/urun" in href or "ledajans.com/" == href or href.endswith("/"):
            print(f"  {txt.strip()[:40]:40} {href[:80]}")
    # body classes relevant
    bm = re.search(r'<body[^>]*class="([^"]+)"', html)
    cls = bm.group(1) if bm else ""
    interesting = [c for c in cls.split() if any(x in c for x in ["home", "page", "single", "elementor", "header", "rtl", "pll", "lang"])]
    print("body", " ".join(interesting[:25]))
    # page-content margin related classes
    print("has home class", "home" in cls.split())
    print("page-id", re.findall(r"page-id-\d+", cls))
    print("postid", re.findall(r"postid-\d+", cls))
