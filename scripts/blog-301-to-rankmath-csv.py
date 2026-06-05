"""blog-301.csv -> Rank Math PRO import format."""
from __future__ import annotations

import csv
import os
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(ROOT, "blog-301.csv")
OUT_PATH = os.path.join(ROOT, "blog-301-rankmath.csv")


def main() -> None:
    rows = []
    with open(IN_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src = urlparse(row["source"].strip()).path or "/"
            dst = urlparse(row["target"].strip()).path or "/"
            if not src.endswith("/"):
                src += "/"
            if not dst.endswith("/"):
                dst += "/"
            rows.append({
                "id": "",
                "source": src,
                "matching": "exact",
                "destination": dst,
                "type": "301",
                "category": "blog-migration",
                "status": "active",
                "ignore": "",
            })

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "source", "matching", "destination", "type", "category", "status", "ignore"],
        )
        w.writeheader()
        w.writerows(rows)
    print(f"OK: {len(rows)} satir -> {OUT_PATH}")


if __name__ == "__main__":
    main()
