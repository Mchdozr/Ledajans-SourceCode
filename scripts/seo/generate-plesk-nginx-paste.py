"""Plesk 'Ek nginx direktifleri' kutusuna yapistirilacak rewrite satirlari."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import csv
import os
from urllib.parse import urlparse

OUT = OPS_NGINX / "plesk-nginx-blog-301-paste.conf"


def main() -> None:
    lines = [
        "# Plesk > ledajans.com > Apache ve nginx Ayarlari",
        "# Ek nginx direktifleri (DOMAIN) — include DEGIL, dogrudan yapistir",
        "# ledajans-blog-301.conf include satirini KALDIRIN (cift kural olmasin)",
        "",
    ]
    with data_path("blog-301.csv").open(encoding="utf-8") as f:
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
