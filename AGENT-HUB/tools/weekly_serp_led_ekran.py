#!/usr/bin/env python3
"""Haftalık (veya manuel) 'led ekran' sorgusunda ledajans.com sırası — DuckDuckGo Lite kaynaklı proxy ölçüm.

Google SERP'i kişiselleştirme ve bot koruması nedeniyle burada doğrudan çekilmez.
İş hedefi Google ise Search Console veya ücretli rank tracker ile doğrulama gerekir.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests

HUB = Path("/workspace/AGENT-HUB")
HISTORY = HUB / "SERP-LED-EKRAN-history.jsonl"
DDG_URL = "https://lite.duckduckgo.com/lite/"
ROW_RE = re.compile(
    r'<td valign="top">\s*(\d+)\.&nbsp;\s*</td>\s*<td>\s*<a[^>]+href="([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)


def fetch_ddg_ranks(query: str) -> list[tuple[int, str]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://lite.duckduckgo.com/",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    r = requests.post(DDG_URL, data={"q": query}, headers=headers, timeout=30)
    r.raise_for_status()
    rows: list[tuple[int, str]] = []
    for rank_s, href in ROW_RE.findall(r.text):
        rows.append((int(rank_s), unescape(href)))
    return rows


def best_rank_for_domain(rows: list[tuple[int, str]], domain: str) -> tuple[int | None, str | None]:
    domain_l = domain.lower().strip()
    best: int | None = None
    best_url: str | None = None
    for rank, url in rows:
        host = urlparse(url).netloc.lower()
        if host == domain_l or host.endswith("." + domain_l):
            if best is None or rank < best:
                best, best_url = rank, url
    return best, best_url


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", default="led ekran")
    p.add_argument("--domain", default="ledajans.com")
    p.add_argument("--no-history", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    override = os.environ.get("MANUAL_SERP_POSITION")
    rows: list[tuple[int, str]] = []
    source = "duckduckgo-lite"
    err: str | None = None
    rank: int | None = None
    url: str | None = None

    if override is not None and override.strip().isdigit():
        rank = int(override.strip())
        url = os.environ.get("MANUAL_SERP_URL") or None
        source = "manual-env"
    else:
        try:
            rows = fetch_ddg_ranks(args.query)
            rank, url = best_rank_for_domain(rows, args.domain)
            if rank is None:
                err = "domain_not_in_results"
        except requests.RequestException as e:
            err = f"request_error:{e}"
            source = "error"

    record = {
        "captured_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": args.query,
        "domain": args.domain,
        "engine": source,
        "rank_position": rank if err is None else None,
        "url": url if err is None else None,
        "top_n_preview": [{"rank": r, "url": u} for r, u in rows[:10]],
        "error": err,
    }

    if not args.no_history and err is None and record["rank_position"] is not None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    if args.json:
        print(json.dumps(record, ensure_ascii=False, indent=2))
    else:
        print(f"Sorgu: {args.query}")
        print(f"Hedef: {args.domain}")
        print(f"Kaynak: {source} (Google değil)")
        if err:
            print(f"Hata: {err}")
        else:
            print(f"Sıra: {record['rank_position']}")
            print(f"URL: {record['url']}")

    return 0 if err is None and record.get("rank_position") else 1


if __name__ == "__main__":
    sys.exit(main())
