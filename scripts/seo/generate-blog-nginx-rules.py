"""blog-301.csv -> nginx (Plesk: return 301 location =)."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import csv
import os
import sys
from urllib.parse import urlparse

CSV_PATH = data_path("blog-301.csv")
OUT_PLESK = OPS_NGINX / "ledajans-blog-301.conf"
OUT_REWRITE = OPS_NGINX / "blog-nginx-301-only.conf"


def load_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = urlparse(row["source"].strip()).path.rstrip("/")
            tgt = urlparse(row["target"].strip()).path.rstrip("/")
            if src and tgt.startswith("/blog/"):
                pairs.append((src, tgt))
    return pairs


def main() -> None:
    if not os.path.isfile(CSV_PATH):
        print("HATA: blog-301.csv yok")
        sys.exit(1)

    pairs = load_pairs()

    plesk = [
        "# LEDAJANS blog 301 — Plesk include (conf/ledajans-blog-301.conf)",
        "# Ek nginx direktifleri: include /var/www/vhosts/ledajans.com/conf/ledajans-blog-301.conf;",
        "# Eski kok URL -> /blog/slug (404 yerine 301)",
        "",
    ]
    for src, tgt in pairs:
        path = src.lstrip("/")
        plesk.append(f"location = {src} {{ return 301 {tgt}/; }}")
        plesk.append(f"location = {src}/ {{ return 301 {tgt}/; }}")

    with open(OUT_PLESK, "w", encoding="utf-8") as f:
        f.write("\n".join(plesk) + "\n")

    rewrite = ["# rewrite permanent (bazi Plesk kurulumlarinda calismayabilir)", ""]
    for src, tgt in pairs:
        rewrite.append(f"rewrite ^{src}/?$ {tgt}/ permanent;")
    with open(OUT_REWRITE, "w", encoding="utf-8") as f:
        f.write("\n".join(rewrite) + "\n")

    print(f"Plesk: {OUT_PLESK} ({len(pairs)} slug, {len(pairs)*2} location)")
    print(f"rewrite yedek: {OUT_REWRITE}")


if __name__ == "__main__":
    main()
