"""blog-301.csv -> Apache .htaccess 301 (Plesk nginx calismazsa yedek)."""
from __future__ import annotations

import csv
import os
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "blog-301.csv")
OUT = os.path.join(ROOT, "scripts", "ledajans-blog-301.htaccess")


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
