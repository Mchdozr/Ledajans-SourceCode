#!/usr/bin/env python3
"""
ledajans.com için 'led ekran' organik sıra özeti.

Kaynak: DuckDuckGo Lite HTML. Google sırasının yerine geçmez; tr-TR Google için
Search Console veya onaylı bir SERP API kullanın.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
LOG_PATH = REPORTS / "led-ekran-weekly-serp.md"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DOMAIN = "ledajans.com"
QUERY = "led ekran"
DDG_LITE = "https://lite.duckduckgo.com/lite/"


def fetch_ddg_lite(query: str, offset: int) -> str:
    params = urllib.parse.urlencode({"q": query, "s": str(offset)})
    url = f"{DDG_LITE}?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_positions(html: str) -> list[tuple[str, str]]:
    """(href, anchor_text) sırasıyla organik sonuçlar (DDG Lite)."""
    pat = re.compile(
        r'<a[^>]+href="([^"]+)"[^>]*class=\'result-link\'>([^<]*)</a>',
        re.IGNORECASE,
    )
    return pat.findall(html)


def href_matches_domain(href: str, domain: str) -> bool:
    h = href.lower()
    if domain.lower() in h:
        return True
    if "uddg=" in h:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
        for v in q.get("uddg", []):
            if domain.lower() in urllib.parse.unquote(v).lower():
                return True
    return False


def rank_led_ekran(max_results: int = 80) -> tuple[int | None, str | None]:
    """İlk eşleşen ledajans.com URL'sinin 1 tabanlı sırası."""
    collected = 0
    for offset in range(0, max_results, 10):
        html = fetch_ddg_lite(QUERY, offset)
        batch = parse_positions(html)
        if not batch:
            break
        for href, _title in batch:
            collected += 1
            if href_matches_domain(href, DOMAIN):
                return collected, href
        if len(batch) < 10:
            break
    return None, None


def iso_week_id(now: dt.datetime) -> str:
    y, w, _ = now.date().isocalendar()
    return f"{y}-W{w:02d}"


def log_has_week(text: str, week_id: str) -> bool:
    return f"| {week_id} |" in text


def append_weekly_row(
    path: Path,
    week_id: str,
    captured: str,
    rank: int | None,
    matched_href: str | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        header = (
            "# led ekran — haftalık SERP özeti (ledajans.com)\n\n"
            "> **Uyarı:** Ölçüm kaynağı DuckDuckGo Lite sonuçlarıdır (oturumsuz, sunucu IP). "
            "Google.com.tr veya kişiselleştirilmiş arama ile sıra farklıdır. "
            "Kesin takip için Google Search Console veya onaylı SERP API kullanın.\n\n"
            "| ISO Hafta | Yakalanma (UTC) | Kaynak | Sıra | Ham eşleşme |\n"
            "|-------------|-----------------|--------|------|-------------|\n"
        )
        path.write_text(header, encoding="utf-8")
    rank_s = str(rank) if rank is not None else ">80 veya yok"
    href_s = (matched_href or "").replace("|", "\\|")[:200]
    line = f"| {week_id} | {captured} | duckduckgo_lite | {rank_s} | `{href_s}` |\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--append-weekly",
        action="store_true",
        help="ISO haftada yoksa tabloya bir satır ekle (haftalık cron için).",
    )
    parser.add_argument(
        "--append-run",
        action="store_true",
        help="Her çalıştırmada tabloya satır ekle (test veya günlük arşiv).",
    )
    args = parser.parse_args()
    if args.append_weekly and args.append_run:
        print("Hata: --append-weekly ve --append-run birlikte kullanılamaz.", flush=True)
        return 2

    now = dt.datetime.now(dt.UTC)
    captured = now.isoformat(timespec="seconds")
    week_id = iso_week_id(now)

    rank, href = rank_led_ekran()
    print(
        f"query={QUERY!r} domain={DOMAIN!r} "
        f"duckduckgo_lite_organic_rank={rank!s} captured_utc={captured}",
        flush=True,
    )

    if not args.append_weekly and not args.append_run:
        return 0

    if args.append_weekly:
        existing = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""
        if log_has_week(existing, week_id):
            print(f"--append-weekly: {week_id} zaten kayıtlı, atlanıyor.", flush=True)
            return 0

    append_weekly_row(LOG_PATH, week_id, captured, rank, href)
    print(f"yazıldı: {LOG_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
