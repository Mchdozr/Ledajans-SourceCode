#!/usr/bin/env python3
"""
Haftalık anahtar kelime sırası: DuckDuckGo HTML (kl=tr-tr) üzerinden organcı sonuç sırası.
Google SERP bu VM'den güvenilir çekilemediği için raporda kaynak açıkça belirtilir.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/AGENT-HUB")
DATA_PATH = ROOT / "data" / "keyword-rank-led-ekran.jsonl"
REPORTS_DIR = ROOT / "REPORTS"

DEFAULT_KEYWORD = "led ekran"
DEFAULT_DOMAIN = "ledajans.com"
DDG_URL = "https://html.duckduckgo.com/html/"


def fetch_ddg_html(keyword: str) -> str:
    params = urllib.parse.urlencode({"q": keyword, "kl": "tr-tr"})
    url = f"{DDG_URL}?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def organic_urls(html: str) -> list[str]:
    parts = re.split(r'<div class="result results_links', html)
    out: list[str] = []
    for chunk in parts[1:]:
        m = re.search(r"uddg=([^&\"]+)", chunk)
        if not m:
            continue
        out.append(urllib.parse.unquote(m.group(1)))
    return out


def rank_for_domain(urls: list[str], domain: str) -> tuple[int | None, str | None]:
    d = domain.lower().rstrip("/")
    for i, u in enumerate(urls, start=1):
        if d in u.lower():
            return i, u
    return None, None


def main() -> int:
    keyword = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_KEYWORD
    domain = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DOMAIN

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    captured = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        html = fetch_ddg_html(keyword)
    except urllib.error.URLError as e:
        rec = {
            "captured_at_utc": captured,
            "keyword": keyword,
            "target_domain": domain,
            "engine": "duckduckgo_html",
            "locale": "tr-tr",
            "organic_rank": None,
            "matched_url": None,
            "error": str(e),
        }
        DATA_PATH.open("a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 1

    urls = organic_urls(html)
    pos, matched = rank_for_domain(urls, domain)

    rec = {
        "captured_at_utc": captured,
        "keyword": keyword,
        "target_domain": domain,
        "engine": "duckduckgo_html",
        "locale": "tr-tr",
        "organic_rank": pos,
        "matched_url": matched,
        "organic_results_sampled": len(urls),
        "google_note": "Google organic rank not fetched here (bot/JS); use GSC or rank tracker for google.com.tr.",
    }
    DATA_PATH.open("a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")

    day = captured[:10]
    report = REPORTS_DIR / f"{day}-keyword-led-ekran.md"
    lines = [
        f"# Anahtar kelime sırası — {day}",
        "",
        f"- **Sorgu:** `{keyword}`",
        f"- **Hedef:** `{domain}`",
        "- **Kaynak:** DuckDuckGo HTML, bölge `tr-tr` (Google ile aynı değildir).",
        f"- **Ölçüm zamanı (UTC):** {captured}",
        f"- **Organik sıra (DDG):** {pos if pos is not None else 'bulunamadı'}",
        f"- **Eşleşen URL:** {matched or '—'}",
        f"- **Örneklenen organik sonuç sayısı:** {len(urls)}",
        "",
        "## Google (ledajans.com / led ekran)",
        "Bu ortamda Google SERP güvenilir şekilde parse edilemedi (CAPTCHA/JS). "
        "Resmi sıra için Search Console “Ortalama konum” veya "
        "DataForSEO / Semrush / Ahrefs gibi bir kaynak kullanın.",
        "",
        "## Haftalık geçmiş",
        f"Tüm satırlar: `{DATA_PATH.relative_to(Path('/workspace'))}`",
        "",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(rec, ensure_ascii=False, indent=2))
    print(f"Wrote {report}", file=sys.stderr)
    return 0 if pos is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
