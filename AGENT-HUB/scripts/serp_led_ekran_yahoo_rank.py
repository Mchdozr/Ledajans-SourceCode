#!/usr/bin/env python3
"""
Yahoo TR (fr=yfp-t-tr) sonuçlarından 'led ekran' sorgusu için ledajans.com
organik görünürlüğünü domain bazında tekilleştirerek sıra üretir.

Not: Bu çıktı Google sırasının yerine geçmez; Google SERP bu ortamda
güvenilir şekilde çekilemediği için ücretsiz bir proxy göstergedir.
Arama Konsolu (Performans > Sorgular > led ekran) Google average position
için kaynak olmalıdır.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "AGENT-HUB" / "REPORTS"
DEFAULT_CSV = REPORTS / "serp-led-ekran-yahoo-timeseries.csv"
YAHOO_URL = (
    "https://search.yahoo.com/search?p={q}&ei=UTF-8&fr=yfp-t-tr"
)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
)


def base_domain(netloc: str) -> str:
    netloc = netloc.lower().split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def fetch_html(query: str) -> str:
    url = YAHOO_URL.format(q=urllib.parse.quote(query))
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def ranked_domains(html: str) -> tuple[list[tuple[str, str]], int | None, str | None]:
    """İlk organik URL sırasından yahoo dışı domainleri tekilleştir."""
    all_ru = re.findall(r"/RU=([^/]+)/RK=", html)
    urls: list[str] = []
    for seg in all_ru:
        u = unquote(seg)
        if u.startswith("http"):
            urls.append(u)

    ext = [u for u in urls if "yahoo" not in urlparse(u).netloc.lower()]
    seen: set[str] = set()
    ranked: list[tuple[str, str]] = []
    for u in ext:
        b = base_domain(urlparse(u).netloc)
        if b in seen:
            continue
        seen.add(b)
        ranked.append((b, u))

    rank = next((i for i, (b, _) in enumerate(ranked, 1) if b == "ledajans.com"), None)
    top_led = next((u for b, u in ranked if b == "ledajans.com"), None)
    return ranked, rank, top_led


def append_csv(
    path: Path,
    *,
    captured_at: str,
    query: str,
    rank: int | None,
    top_url: str | None,
    note: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(
                [
                    "captured_at_utc",
                    "query",
                    "yahoo_tr_domain_rank",
                    "top_ledajans_url",
                    "engine_note",
                ]
            )
        w.writerow([captured_at, query, rank if rank is not None else "", top_url or "", note])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", default="led ekran")
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    p.add_argument("--no-csv", action="store_true")
    args = p.parse_args()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    note = "Yahoo TR UI (fr=yfp-t-tr); domain-dedup organic; not Google"

    html = ""
    ranked: list[tuple[str, str]] = []
    rank: int | None = None
    top_led: str | None = None
    for attempt in range(1, 4):
        try:
            html = fetch_html(args.query)
        except Exception as exc:  # noqa: BLE001
            print(f"HATA: Yahoo isteği başarısız (deneme {attempt}/3): {exc}", file=sys.stderr)
            if attempt == 3:
                return 2
            time.sleep(2.0)
            continue
        ranked, rank, top_led = ranked_domains(html)
        if rank is not None:
            break
        time.sleep(1.5)

    if rank is None:
        note = note + " | parse_failed_after_retries"

    print(f"captured_at_utc={now}")
    print(f"query={args.query!r}")
    print(f"yahoo_tr_domain_rank={rank}")
    print(f"top_ledajans_url={top_led}")
    print("dedup_domain_top10:")
    for i, (b, u) in enumerate(ranked[:10], 1):
        print(f"  {i:2} {b:32} {u[:72]}")

    if not args.no_csv:
        append_csv(
            args.csv,
            captured_at=now,
            query=args.query,
            rank=rank,
            top_url=top_led,
            note=note,
        )
        print(f"csv_appended={args.csv}")

    if rank is None:
        print("UYARI: Sıra çıkarılamadı; CSV satırı yine de eklendi.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
