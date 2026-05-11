#!/usr/bin/env python3
"""
Haftalık 'led ekran' sorgusunda ledajans.com görünürlüğü (DuckDuckGo HTML, tr-tr).

Google sırası bu API'siz ortamda güvenilir çekilemediği için motor açıkça
jsonl ve konsol çıktısında işaretlenir. Kesin Google metriği için GSC veya
SerpAPI/DataForSEO gibi kaynak kullanılmalıdır.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KEYWORD = "led ekran"
DOMAIN = "ledajans.com"
DDG_URL = "https://html.duckduckgo.com/html/"
HISTORY = Path(__file__).resolve().parent / "REPORTS" / "serp-led-ekran-ledajans-history.jsonl"


def _fetch_page(start: int) -> list[str]:
    data = urllib.parse.urlencode(
        {"q": KEYWORD, "kl": "tr-tr", "s": str(start)}
    ).encode()
    req = urllib.request.Request(
        DDG_URL,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-serp-weekly/1.0)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    raw = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    out: list[str] = []
    for link in raw:
        if "duckduckgo.com/l/?uddg=" in link:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get(
                "uddg", [link]
            )[0]
            out.append(urllib.parse.unquote(q))
        else:
            out.append(link)
    return out


def collect_organic(max_results: int = 120) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for start in range(0, max_results, 20):
        batch = _fetch_page(start)
        if not batch:
            break
        for u in batch:
            if u not in seen:
                seen.add(u)
                merged.append(u)
        if len(merged) >= max_results:
            break
    return merged[:max_results]


def find_ledajans_rank(urls: list[str]) -> tuple[int | None, str | None]:
    for i, u in enumerate(urls, start=1):
        if DOMAIN in u.lower():
            return i, u
    return None, None


def main() -> int:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    urls = collect_organic()
    rank, matched = find_ledajans_rank(urls)
    now = datetime.now(timezone.utc)
    record = {
        "captured_at_utc": now.isoformat(timespec="seconds"),
        "keyword": KEYWORD,
        "search_engine": "duckduckgo_html",
        "locale_hint": "tr-tr",
        "rank_position": rank,
        "matched_url": matched,
        "organic_sample_size": len(urls),
        "note": "Google değil; DDG HTML proxy. Google için GSC veya SERP API kullanın.",
    }
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    if rank is not None:
        print(f"{KEYWORD}: sıra {rank} (DDG HTML) — {matched}")
    else:
        print(f"{KEYWORD}: ilk {len(urls)} sonuçta {DOMAIN} yok (DDG HTML).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
