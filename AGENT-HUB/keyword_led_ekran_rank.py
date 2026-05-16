#!/usr/bin/env python3
"""
ledajans.com için "led ekran" sorgusunda sıra izleme.

Kaynak: DuckDuckGo HTML (POST). Google organik sırasının yerine geçmez;
bulut ortamında Bing/Google SERP HTML'i genelde CAPTCHA döndürür.
Çapraz doğrulama: Search Console veya SerpAPI vb.
"""
from __future__ import annotations

import datetime as dt
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
LOG_MD = REPORTS / "keyword-led-ekran-weekly-log.md"

KEYWORD = "led ekran"
DOMAIN = "ledajans.com"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "Chrome/120.0.0.0 Safari/537.36"
)


def ddg_html_rank(keyword: str, domain: str) -> tuple[int | None, str | None, str | None]:
    body = urllib.parse.urlencode({"q": keyword, "b": ""}).encode()
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=body,
        headers={
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
        method="POST",
    )
    try:
        html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        return None, None, str(exc)

    if "anomaly-modal" in html or "Unfortunately, bots use DuckDuckGo" in html:
        return None, None, "ddg_challenge"

    rank: int | None = None
    url_hit: str | None = None
    for i, m in enumerate(re.finditer(r'class="result__a"[^>]+href="([^"]+)"', html), start=1):
        raw = m.group(1)
        u = raw
        qm = re.search(r"uddg=([^&]+)", raw)
        if qm:
            u = urllib.parse.unquote(qm.group(1))
        if domain.lower() in u.lower():
            rank = i
            url_hit = u
            break
    if rank is None:
        return None, None, "domain_not_in_serp"
    return rank, url_hit, None


def ensure_log_header() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if LOG_MD.exists():
        return
    LOG_MD.write_text(
        "# led ekran — sıra günlüğü\n\n"
        "Ölçüm: DuckDuckGo HTML (`html.duckduckgo.com`). "
        "Google Türkiye organik sırası değildir; GSC veya ücretli SERP API ile doğrulayın.\n\n"
        "| UTC tarih | ISO hafta | Sıra | URL |\n"
        "|---|---:|---:|---|\n",
        encoding="utf-8",
    )


def append_row(rank: int | None, url: str | None, err: str | None) -> None:
    ensure_log_header()
    now = dt.datetime.now(dt.UTC)
    week = now.isocalendar()
    iso_week = f"{week.year}-W{week.week:02d}"
    ts = now.strftime("%Y-%m-%d %H:%M")
    if err:
        line = f"| {ts} | {iso_week} | — | hata: {err} |\n"
    else:
        safe_url = (url or "").replace("|", "\\|")
        line = f"| {ts} | {iso_week} | {rank} | {safe_url} |\n"
    with LOG_MD.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    rank, url, err = ddg_html_rank(KEYWORD, DOMAIN)
    append_row(rank, url, err)
    if err:
        print(f"keyword_led_ekran_rank: ERROR {err}")
        return 1
    print(f"keyword_led_ekran_rank: ddg_html rank={rank} url={url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
