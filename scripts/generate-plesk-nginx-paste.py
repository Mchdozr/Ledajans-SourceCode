"""Plesk 'Ek nginx direktifleri' kutusuna yapistirilacak rewrite satirlari."""
from __future__ import annotations

import csv
import os
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "scripts", "plesk-nginx-blog-301-paste.conf")


def main() -> None:
    lines = [
        "# Plesk > ledajans.com > Apache ve nginx Ayarlari",
        "# Ek nginx direktifleri (DOMAIN) — include DEGIL, dogrudan yapistir",
        "# ledajans-blog-301.conf include satirini KALDIRIN (cift kural olmasin)",
        "",
    ]
    with open(os.path.join(ROOT, "blog-301.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = urlparse(row["source"].strip()).path.strip("/")
            tgt = urlparse(row["target"].strip()).path.strip("/")
            if src and tgt.startswith("blog/"):
                lines.append(f"rewrite ^/{src}/?$ /{tgt}/ permanent;")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"OK: {OUT} ({len(lines)-4} rewrite)")


if __name__ == "__main__":
    main()
