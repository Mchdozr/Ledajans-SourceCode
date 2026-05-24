#!/usr/bin/env python3
"""
Haftalık (varsayılan: 7 günde bir) 'led ekran' sorgusunda ledajans.com organik sırası.

Google SERP bu VM'de JS tabanlı yanıt verdiği için ölçüm kaynağı DuckDuckGo Lite'dır;
Google sırası ile birebir olmayabilir — raporda source_engine alanına bakın.

Kullanım (repo kökü):
  python3 AGENT-HUB/weekly_led_ekran_rank.py
  python3 AGENT-HUB/weekly_led_ekran_rank.py --force
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
REPORT_MD = REPORTS / "weekly-led-ekran-rank.md"
STATE_FILE = HUB / ".weekly-led-ekran-state.json"

DDG_LITE = "https://lite.duckduckgo.com/lite/?q={q}"
UA = "Mozilla/5.0 (compatible; LEDAJANS-weekly-rank/1.0; +https://ledajans.com)"

RESULT_RE = re.compile(
    r"<a[^>]*href=\"//duckduckgo\.com/l/\?uddg=([^&]+)[^\"]*\"[^>]*class=['\"]result-link['\"]",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_ddg_lite(query: str) -> str:
    url = DDG_LITE.format(q=urllib.parse.quote_plus(query))
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def organic_urls(html: str) -> list[str]:
    out: list[str] = []
    for enc in RESULT_RE.findall(html):
        out.append(urllib.parse.unquote(enc))
    return out


def rank_for_domain(urls: list[str], domain: str) -> tuple[int | None, str | None]:
    d = domain.lower().rstrip("/")
    if d.startswith("www."):
        d = d[4:]
    for i, raw in enumerate(urls, start=1):
        u = raw.lower()
        host = urllib.parse.urlparse(
            raw if "://" in raw else "https://" + raw
        ).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host == d or host.endswith("." + d):
            return i, raw
    return None, None


def should_skip_weekly(force: bool) -> bool:
    if force:
        return False
    st = read_json(STATE_FILE)
    last = st.get("last_run")
    if not last:
        return False
    try:
        prev = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if prev.tzinfo is None:
            prev = prev.replace(tzinfo=UTC)
    except ValueError:
        return False
    return datetime.now(UTC) - prev < timedelta(days=7)


def append_report_row(
    *,
    captured_at: str,
    query: str,
    rank: int | None,
    matched_url: str | None,
    source_engine: str,
    note: str,
) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    rank_s = str(rank) if rank is not None else "İlk sayfada yok (≤10)"
    url_s = matched_url or "—"
    line = (
        f"| {captured_at} | {source_engine} | {query} | {rank_s} | {url_s} | {note} |\n"
    )
    if not REPORT_MD.exists():
        header = (
            "# Haftalık — \"led ekran\" — ledajans.com sırası\n\n"
            "Ölçüm kaynağı **DuckDuckGo Lite** organik web sonuçlarıdır; "
            "**Google.com.tr sırası değildir** (konum, kişiselleştirme ve indeks farkı).\n\n"
            "| Yakalanma (UTC) | Kaynak | Sorgu | Sıra | Eşleşen URL | Not |\n"
            "|---|---|---|---:|---|---|\n"
        )
        REPORT_MD.write_text(header + line, encoding="utf-8")
    else:
        with REPORT_MD.open("a", encoding="utf-8") as f:
            f.write(line)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", default="led ekran")
    p.add_argument("--domain", default="ledajans.com")
    p.add_argument("--force", action="store_true", help="7 günlük beklemeden yine kaydet")
    args = p.parse_args()

    if should_skip_weekly(args.force):
        print("Son ölçümden 7 gün geçmedi; --force ile zorlayabilirsiniz.", file=sys.stderr)
        return 0

    try:
        html = fetch_ddg_lite(args.query)
    except Exception as e:
        print(f"SERP çekilemedi: {e}", file=sys.stderr)
        return 1

    urls = organic_urls(html)
    rank, matched = rank_for_domain(urls, args.domain)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
    note = "İlk 10 organik içinde arandı; DDG Lite tek sayfa."
    append_report_row(
        captured_at=now,
        query=args.query,
        rank=rank,
        matched_url=matched,
        source_engine="duckduckgo_lite",
        note=note,
    )
    write_json(
        STATE_FILE,
        {
            "last_run": datetime.now(UTC).isoformat(timespec="seconds"),
            "query": args.query,
            "domain": args.domain,
            "rank": rank,
            "matched_url": matched,
            "source_engine": "duckduckgo_lite",
        },
    )
    print(json.dumps({"rank": rank, "url": matched, "source": "duckduckgo_lite"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
