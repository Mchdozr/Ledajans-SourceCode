#!/usr/bin/env python3
"""
ledajans.com için 'led ekran' sorgusunda proxy SERP sırası (Bing RSS + DuckDuckGo HTML).

Google organik SERP bu ortamda JS ile yüklendiği için güvenilir parse üretilemez;
Google sırası için Search Console veya harici rank tracker kullanılmalıdır.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
LATEST = REPORTS / "keyword-led-ekran-latest.md"
HISTORY = REPORTS / "keyword-led-ekran-history.log"
WEEKLY = REPORTS / "keyword-led-ekran-weekly.md"
STATE = HUB / ".keyword-led-ekran-weekly-state.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url: str, data: bytes | None = None) -> str:
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": UA,
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            **({"Content-Type": "application/x-www-form-urlencoded"} if data else {}),
        },
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def rank_bing_rss(query: str, host: str) -> tuple[int | None, list[str]]:
    rss = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)
    xml = fetch(rss)
    items = re.findall(r"<item>.*?</item>", xml, flags=re.DOTALL | re.IGNORECASE)
    urls: list[str] = []
    for it in items:
        m = re.search(r"<link>([^<]+)</link>", it, flags=re.IGNORECASE)
        if not m:
            continue
        urls.append(m.group(1).strip())
    for i, u in enumerate(urls, start=1):
        if host in u:
            return i, urls
    return None, urls


def rank_duckduckgo_html(query: str, host: str) -> tuple[int | None, list[str]]:
    url = "https://html.duckduckgo.com/html/"
    body = urllib.parse.urlencode({"q": query, "b": ""}).encode()
    html = fetch(url, data=body)
    urls = re.findall(r'class="result__a" href="([^"]+)"', html)
    for i, u in enumerate(urls, start=1):
        if host in u:
            return i, urls
    return None, urls


def load_week_state() -> dict:
    if not STATE.exists():
        return {"iso_year": 0, "iso_week": 0}
    return json.loads(STATE.read_text(encoding="utf-8"))


def save_week_state(year: int, week: int) -> None:
    STATE.write_text(
        json.dumps({"iso_year": year, "iso_week": week}, indent=2),
        encoding="utf-8",
    )


def ensure_weekly_header() -> None:
    if WEEKLY.exists():
        return
    WEEKLY.write_text(
        "| Hafta (ISO) | Tarih (UTC) | Bing RSS sıra | DDG HTML sıra | Not |\n"
        "|---|---:|---:|---:|---|\n",
        encoding="utf-8",
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", default="led ekran")
    p.add_argument("--host", default="ledajans.com")
    p.add_argument("--weekly-append", action="store_true")
    args = p.parse_args()

    now = datetime.now(timezone.utc)
    b_pos, b_urls = rank_bing_rss(args.query, args.host)
    d_pos, d_urls = rank_duckduckgo_html(args.query, args.host)

    REPORTS.mkdir(parents=True, exist_ok=True)

    md = (
        f"# Anahtar kelime snapshot: `{args.query}` → {args.host}\n\n"
        f"- **Ölçüm zamanı (UTC):** {now.isoformat(timespec='seconds')}\n"
        "- **Google organik sıra:** Bu betik Google SERP HTML’ini güvenilir biçimde "
        "parse edemez (Google sonuçları ağırlıklı olarak istemci tarafı JS ile üretilir). "
        "Resmi metrik için Search Console → Performans → `led ekran` sorgusu veya "
        "DataForSEO / Ahrefs / Semrush gibi bir kaynak kullanın.\n"
        f"- **Bing RSS (format=rss) sırası:** {b_pos if b_pos is not None else 'bulunamadı'}\n"
        f"- **DuckDuckGo HTML sırası:** {d_pos if d_pos is not None else 'bulunamadı'}\n\n"
        "## Bing RSS — ilk URL’ler\n"
        + "\n".join(f"{i}. {u}" for i, u in enumerate(b_urls[:10], start=1))
        + "\n\n## DDG HTML — ilk URL’ler\n"
        + "\n".join(f"{i}. {u}" for i, u in enumerate(d_urls[:10], start=1))
        + "\n"
    )
    LATEST.write_text(md, encoding="utf-8")

    line = (
        f"{now.date().isoformat()}T{now.strftime('%H:%M:%SZ')}\t"
        f"{args.query}\t{args.host}\t{b_pos}\t{d_pos}\n"
    )
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(line)

    iso = now.isocalendar()
    week_label = f"{iso.year}-W{iso.week:02d}"

    if args.weekly_append:
        st = load_week_state()
        if st.get("iso_year") == iso.year and st.get("iso_week") == iso.week:
            print("weekly: aynı ISO haftası, tabloya yeni satır eklenmedi")
        else:
            ensure_weekly_header()
            note = "Proxy SERP; Google değildir."
            row = (
                f"| {week_label} | {now.date().isoformat()} "
                f"| {b_pos if b_pos is not None else '—'} "
                f"| {d_pos if d_pos is not None else '—'} "
                f"| {note} |\n"
            )
            with WEEKLY.open("a", encoding="utf-8") as f:
                f.write(row)
            save_week_state(iso.year, iso.week)
            print("weekly: yeni satır eklendi", week_label)

    print("Bing_RSS", b_pos)
    print("DDG", d_pos)
    print("wrote", LATEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
