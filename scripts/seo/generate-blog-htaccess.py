"""blog-301.csv -> Apache .htaccess 301 (Plesk nginx calismazsa yedek)."""
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

CSV_PATH = data_path("blog-301.csv")
OUT = OPS_NGINX / "ledajans-blog-301.htaccess"


def main() -> None:
    lines = [
        "# BEGIN LEDAJANS BLOG 301",
        "<IfModule mod_rewrite.c>",
        "RewriteEngine On",
        "",
    ]
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = urlparse(row["source"].strip()).path.strip("/")
            tgt = urlparse(row["target"].strip()).path.strip("/")
            if src and tgt.startswith("blog/"):
                lines.append(f"RewriteRule ^{src}/?$ /{tgt}/ [R=301,L]")
    lines.extend(["</IfModule>", "# END LEDAJANS BLOG 301", ""])
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"OK: {OUT} ({len(lines)-3} kural)")


if __name__ == "__main__":
    main()
