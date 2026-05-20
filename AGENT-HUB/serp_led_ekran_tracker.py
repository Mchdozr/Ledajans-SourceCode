#!/usr/bin/env python3
"""
ledajans.com için 'led ekran' sorgusu — SERP görünürlük anlık görüntüsü.

Önemli: google.com.tr organik HTML çıktısı bu tür otomasyonlarda güvenilir
şekilde çekilemediği için kaynak olarak DuckDuckGo (html.duckduckgo.com)
kullanılır. Bu sıra Google ile birebir aynı olmayabilir; kesin Google sırası
için Search Console (performans) veya onaylı bir rank tracker gerekir.

Çıktılar:
  REPORTS/serp-led-ekran-snapshots.tsv — her çalıştırmada bir satır
  REPORTS/serp-led-ekran-haftalik.md — Çarşamba (UTC) günleri haftalık özet ekler
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "REPORTS"
TSV_PATH = REPORTS / "serp-led-ekran-snapshots.tsv"
WEEKLY_MD = REPORTS / "serp-led-ekran-haftalik.md"

QUERY = "led ekran"
DDG_URL = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(QUERY)
USER_AGENT = (
    "Mozilla/5.0 (compatible; LEDAJANS-serp-tracker/1.0; +https://ledajans.com)"
)


def fetch_ddg_links() -> list[str]:
    req = urllib.request.Request(
        DDG_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    hrefs = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    out: list[str] = []
    for href in hrefs:
        if "uddg=" in href:
            parsed = urllib.parse.urlparse("https:" + href if href.startswith("//") else href)
            q = urllib.parse.parse_qs(parsed.query).get("uddg", [])
            if q:
                out.append(urllib.parse.unquote(q[0]))
        else:
            out.append(href)
    return out


def first_ledajans_rank(urls: list[str]) -> tuple[int | None, str | None]:
    for i, u in enumerate(urls, start=1):
        try:
            host = urlparse(u).hostname or ""
        except ValueError:
            continue
        if host == "ledajans.com" or host.endswith(".ledajans.com"):
            return i, u
    return None, None


def append_tsv(captured_utc: str, rank: int | None, matched_url: str | None) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    new_file = not TSV_PATH.exists()
    with TSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        if new_file:
            w.writerow(
                [
                    "captured_at_utc",
                    "serp_source",
                    "query",
                    "rank_position",
                    "matched_url",
                    "note",
                ]
            )
        w.writerow(
            [
                captured_utc,
                "duckduckgo_html",
                QUERY,
                rank if rank is not None else "",
                matched_url or "",
                "proxy_not_google",
            ]
        )


def load_recent_ranks(days: int = 8) -> list[tuple[dt.datetime, int]]:
    if not TSV_PATH.exists():
        return []
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
    rows: list[tuple[dt.datetime, int]] = []
    with TSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            raw = row.get("captured_at_utc") or ""
            try:
                ts = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts < cutoff:
                continue
            rp = row.get("rank_position") or ""
            if not str(rp).strip().isdigit():
                continue
            rows.append((ts, int(rp)))
    rows.sort(key=lambda x: x[0])
    return rows


def append_weekly_summary(now_utc: dt.datetime, force: bool) -> None:
    if not force and now_utc.weekday() != 2:
        return
    week_label = now_utc.date().isoformat()
    if WEEKLY_MD.exists() and f"## Hafta özeti — {week_label}" in WEEKLY_MD.read_text(
        encoding="utf-8"
    ):
        return
    recent = [r for _, r in load_recent_ranks(8)]
    if not recent:
        return
    lo, hi = min(recent), max(recent)
    last = recent[-1]
    block = (
        f"\n## Hafta özeti — {week_label} (UTC)\n\n"
        f"- Ölçüm kaynağı: DuckDuckGo HTML (Google değildir).\n"
        f"- Son 8 gün içindeki kayıtlı sıralar: en iyi **{lo}**, en kötü **{hi}**, "
        f"son ölçüm **{last}** (organik listede `ledajans.com` ilk eşleşme).\n"
    )
    if not WEEKLY_MD.exists():
        WEEKLY_MD.write_text(
            "# led ekran — haftalık SERP özeti (LEDAJANS)\n\n"
            "Bu dosya `AGENT-HUB/serp_led_ekran_tracker.py` tarafından her Çarşamba "
            "(UTC) güncellenir. Sayılar DuckDuckGo organik sırasına dayanır; "
            "**google.com.tr sırası değildir**.\n",
            encoding="utf-8",
        )
    with WEEKLY_MD.open("a", encoding="utf-8") as f:
        f.write(block)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--force-weekly",
        action="store_true",
        help="Haftalık özet bloğunu Çarşamba olmasa da yaz.",
    )
    args = ap.parse_args()
    now = dt.datetime.now(dt.UTC)
    captured = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        urls = fetch_ddg_links()
    except Exception as e:
        print("FETCH_ERROR", e, file=sys.stderr)
        return 1
    rank, url = first_ledajans_rank(urls)
    append_tsv(captured, rank, url)
    append_weekly_summary(now, force=args.force_weekly)
    print("captured_at_utc", captured)
    print("duckduckgo_ledajans_rank", rank if rank is not None else "NOT_FOUND")
    print("matched_url", url or "")
    print("top_5")
    for i, u in enumerate(urls[:5], 1):
        print(f"  {i} {u}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
