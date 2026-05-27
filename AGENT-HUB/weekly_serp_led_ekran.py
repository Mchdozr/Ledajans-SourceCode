#!/usr/bin/env python3
"""
'led ekran' sorgusu için DuckDuckGo HTML (html.duckduckgo.com) ilk sayfa sonuçlarında
ledajans.com görünürlüğünü ölçer ve haftalık günlük dosyasına ekler.

Bu çıktı Google / GSC sıralamasının yerine geçmez; aynı gün için yaklaşık bir sinyaldir.
Üretim KPI için Search Console → Sorgular veya ücretli SERP API kullanın.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "AGENT-HUB" / "REPORTS" / "serp-led-ekran-weekly-log.md"
QUERY = "led ekran"
TARGET_HOST = "ledajans.com"
HUB_PATH_MARKER = "/led-ekran"
DDG_URL = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": QUERY})

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class SerpSnapshot:
    when_tr: str
    source: str
    first_ledajans_rank: int | None
    first_ledajans_url: str | None
    hub_rank: int | None
    top_urls: list[str]


def _unwrap_duck_redirect(href: str) -> str:
    if "uddg=" not in href:
        return href
    q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [""])
    return urllib.parse.unquote(q[0]) if q else href


def fetch_ddg_organic_urls() -> list[str]:
    req = urllib.request.Request(DDG_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    hrefs = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    return [_unwrap_duck_redirect(h) for h in hrefs]


def analyze(urls: list[str]) -> SerpSnapshot:
    now = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M %Z")
    first_rank: int | None = None
    first_url: str | None = None
    hub_rank: int | None = None
    for i, u in enumerate(urls, start=1):
        if TARGET_HOST in u.lower():
            if first_rank is None:
                first_rank = i
                first_url = u
            if HUB_PATH_MARKER in u and "ledajans" in u.lower():
                hub_rank = i
                break
    return SerpSnapshot(
        when_tr=now,
        source="DuckDuckGo HTML (ilk sayfa)",
        first_ledajans_rank=first_rank,
        first_ledajans_url=first_url,
        hub_rank=hub_rank,
        top_urls=urls[:10],
    )


def append_log(s: SerpSnapshot) -> None:
    hub_note = str(s.hub_rank) if s.hub_rank is not None else "ilk 10'da yok"
    rank_note = str(s.first_ledajans_rank) if s.first_ledajans_rank is not None else "yok"
    url_note = (s.first_ledajans_url or "-").replace("|", "\\|")
    line = (
        f"| {s.when_tr} | {s.source} | {rank_note} | {url_note} | {hub_note} |\n"
    )
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        header = (
            "# «led ekran» — LEDAJANS sıra günlüğü\n\n"
            "Otomatik ölçüm **DuckDuckGo HTML** ilk sayfasıdır; **Google ile aynı değildir**. "
            "Kesin konum için [Google Search Console](https://search.google.com/search-console) "
            "Performans → Sorgular kullanın.\n\n"
            "| Tarih (TR) | Kaynak | İlk ledajans.com sırası | İlk eşleşen URL | "
            "`/led-ekran/` sırası (aynı ölçüm) |\n"
            "| --- | --- | ---: | --- | --- |\n"
        )
        LOG_PATH.write_text(header, encoding="utf-8")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    try:
        urls = fetch_ddg_organic_urls()
    except urllib.error.URLError as e:
        print(f"ERR: DuckDuckGo isteği başarısız: {e}", file=sys.stderr)
        return 2
    if not urls:
        print("ERR: Sonuç listesi boş.", file=sys.stderr)
        return 3
    snap = analyze(urls)
    append_log(snap)
    print(
        f"Tarih (TR): {snap.when_tr}\n"
        f"Kaynak: {snap.source}\n"
        f"İlk ledajans.com sırası: {snap.first_ledajans_rank or '—'}\n"
        f"URL: {snap.first_ledajans_url or '—'}\n"
        f"`/led-ekran/` hedefi (aynı ölçüm): sıra {snap.hub_rank or 'ilk sayfada görünmedi'}\n"
        f"Günlük: {LOG_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
