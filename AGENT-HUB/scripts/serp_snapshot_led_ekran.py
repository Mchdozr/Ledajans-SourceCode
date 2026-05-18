#!/usr/bin/env python3
"""
DuckDuckGo Lite (kl=tr-tr) üzerinden 'led ekran' sorgusunda ledajans.com organik sırası.

Google SERP ile birebir aynı değildir; GSC "Ortalama konum" veya Search Console
API ile doğrulama önerilir. Bu betik tekrarlanabilir proxy ölçümü sağlar.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/workspace")
HISTORY_PATH = WORKSPACE / "AGENT-HUB" / "SERP_HISTORY" / "led-ekran-tr.jsonl"
DDG_URL = "https://lite.duckduckgo.com/lite/"
QUERY = "led ekran"
TARGET_HOST = "ledajans.com"
ROW_RE = re.compile(
    r'<td valign="top">\s*(\d+)\.&nbsp;\s*</td>\s*<td>\s*'
    r'<a rel="nofollow" href="(https?://[^"]+)"[^>]*class=\'result-link\'>',
    re.S,
)


def fetch_ddg_lite_ranks() -> list[tuple[int, str]]:
    data = urllib.parse.urlencode({"q": QUERY, "kl": "tr-tr"}).encode("utf-8")
    req = urllib.request.Request(
        DDG_URL,
        data=data,
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-serp-snapshot/1.0)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    rows: list[tuple[int, str]] = []
    for rank_s, href in ROW_RE.findall(html):
        rows.append((int(rank_s), href.strip()))
    return rows


def best_ledajans_rank(rows: list[tuple[int, str]]) -> tuple[int | None, str | None]:
    best: tuple[int | None, str | None] = (None, None)
    for rank, href in rows:
        if TARGET_HOST in href.lower():
            if best[0] is None or rank < best[0]:
                best = (rank, href)
    return best


def append_history(record: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_history_lines() -> list[dict]:
    if not HISTORY_PATH.is_file():
        return []
    out: list[dict] = []
    with HISTORY_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def write_weekly_summary() -> Path:
    lines = load_history_lines()
    out_path = WORKSPACE / "AGENT-HUB" / "REPORTS" / "serp-led-ekran-haftalik-ozet.md"
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - 8 * 24 * 3600
    recent = [r for r in lines if r.get("captured_at_unix", 0) >= cutoff]
    recent.sort(key=lambda r: r.get("captured_at_unix", 0))

    body = [
        "# led ekran — haftalık SERP proxy özeti (DuckDuckGo Lite, tr-tr)",
        "",
        f"- Son güncelleme (UTC): {now.strftime('%Y-%m-%d %H:%M')}",
        "- Kaynak: `AGENT-HUB/scripts/serp_snapshot_led_ekran.py` → `SERP_HISTORY/led-ekran-tr.jsonl`",
        "- **Not:** Google sırası değildir; trend için aynı kaynakla karşılaştırın.",
        "",
        "## Son ölçümler (en fazla 8 gün)",
        "",
    ]
    if not recent:
        body.append("_Henüz kayıt yok._\n")
    else:
        body.append("| Tarih (UTC) | En iyi sıra | URL |")
        body.append("|---|---|---|")
        for r in recent:
            ts = r.get("captured_at_utc", "")
            rank = r.get("ledajans_best_rank")
            url = (r.get("ledajans_best_url") or "").replace("|", "\\|")
            body.append(f"| {ts} | {rank if rank is not None else '—'} | {url} |")
        body.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weekly-summary",
        action="store_true",
        help="JSONL'den haftalık markdown özet üret.",
    )
    args = parser.parse_args()

    if args.weekly_summary:
        path = write_weekly_summary()
        print(f"Yazıldı: {path}")
        return 0

    try:
        rows = fetch_ddg_lite_ranks()
    except urllib.error.URLError as e:
        print(f"SERP isteği başarısız: {e}", file=sys.stderr)
        return 2

    rank, url = best_ledajans_rank(rows)
    now = datetime.now(timezone.utc)
    record = {
        "query": QUERY,
        "engine_proxy": "duckduckgo_lite",
        "locale_kl": "tr-tr",
        "captured_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "captured_at_unix": int(now.timestamp()),
        "organic_count_on_page": len(rows),
        "ledajans_best_rank": rank,
        "ledajans_best_url": url,
        "top_urls": [h for _, h in rows[:10]],
    }
    append_history(record)

    print(json.dumps(record, ensure_ascii=False, indent=2))
    if rank is None:
        print(
            f"\nUyarı: İlk sayfada ({len(rows)} sonuç) {TARGET_HOST} bulunamadı.",
            file=sys.stderr,
        )
        return 1

    wpath = write_weekly_summary()
    print(f"\nHaftalık özet güncellendi: {wpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
