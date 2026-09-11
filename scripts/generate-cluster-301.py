"""cluster-301.csv -> Rank Math CSV + nginx paste + Apache htaccess."""
from __future__ import annotations

import csv
import os
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(ROOT, "AGENT-HUB", "cluster-301.csv")
RM_PATH = os.path.join(ROOT, "AGENT-HUB", "cluster-301-rankmath.csv")
NGX_PATH = os.path.join(ROOT, "scripts", "plesk-nginx-cluster-301-paste.conf")
HT_PATH = os.path.join(ROOT, "scripts", "ledajans-cluster-301.htaccess")


def path_of(url: str) -> str:
    p = urlparse(url.strip()).path or "/"
    if not p.endswith("/"):
        p += "/"
    return p


def main() -> None:
    rows = []
    with open(IN_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = path_of(row["source"])
            dst = path_of(row["target"])
            rows.append((src, dst, row.get("category", "cluster")))

    with open(RM_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "source", "matching", "destination", "type", "category", "status", "ignore"],
        )
        w.writeheader()
        for src, dst, cat in rows:
            w.writerow({
                "id": "",
                "source": src,
                "matching": "exact",
                "destination": dst,
                "type": "301",
                "category": cat,
                "status": "active",
                "ignore": "",
            })

    ngx = [
        "# Plesk > ledajans.com > Apache ve nginx Ayarlari > Ek nginx direktifleri",
        "# Uc KW cluster 301 — Rank Math import yoksa bunu yapistirin",
        "",
    ]
    ht = [
        "# BEGIN LEDAJANS CLUSTER 301",
        "<IfModule mod_rewrite.c>",
        "RewriteEngine On",
        "",
    ]
    for src, dst, _cat in rows:
        src_pat = src.strip("/")
        dst_slash = dst if dst.endswith("/") else dst + "/"
        ngx.append(f"rewrite ^/{src_pat}/?$ {dst_slash} permanent;")
        ht.append(f"RewriteRule ^{src_pat}/?$ {dst_slash} [R=301,L]")
    ht.extend(["</IfModule>", "# END LEDAJANS CLUSTER 301", ""])

    with open(NGX_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(ngx) + "\n")
    with open(HT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(ht) + "\n")
    print(f"OK: {len(rows)} kural -> RankMath/nginx/htaccess")


if __name__ == "__main__":
    main()
