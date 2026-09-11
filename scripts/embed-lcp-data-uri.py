#!/usr/bin/env python3
from __future__ import annotations

import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "Anasayfa" / "Hero.html"
WEBP = ROOT / "AGENT-HUB" / "ldajsn2-mobile-360-q50.webp"


def main() -> int:
    data_uri = "data:image/webp;base64," + base64.b64encode(WEBP.read_bytes()).decode("ascii")
    hero = HERO.read_text(encoding="utf-8")

    hero = re.sub(
        r'<link rel="preload" as="image" type="image/webp" href="https://ledajans\.com/wp-content/uploads/2026/08/ldajsn2-mobile-360-q50\.webp"[^>]*>\s*',
        "<!-- mobil LCP: data-uri (preload yok) -->\n",
        hero,
        count=1,
    )

    new_pic = (
        "        <picture>\n"
        f'          <source media="(max-width: 768px)" type="image/webp" srcset="{data_uri}">\n'
        f'          <img src="{data_uri}" width="412" height="201" '
        'alt="LEDAJANS LED ekran çözümleri - iç mekan ve dış mekan profesyonel LED ekran sistemleri" '
        'fetchpriority="high" loading="eager" decoding="sync">\n'
        "        </picture>"
    )
    hero2, n = re.subn(
        r"        <picture>\s*<source media=\"\(max-width: 768px\)\"[\s\S]*?</picture>",
        new_pic,
        hero,
        count=1,
    )
    if n != 1:
        print("picture_replace", n)
        return 1

    HERO.write_text(hero2, encoding="utf-8")
    print("ok bytes", len(hero2.encode("utf-8")), "data_uri", "data:image/webp;base64," in hero2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
