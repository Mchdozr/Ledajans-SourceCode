#!/usr/bin/env python3
"""
'led ekran' için ledajans.com organik sıra anlık görüntüsü.

Ölçüm: DuckDuckGo HTML sonuçları (POST). Bu, Google organik sırasının yerine
geçmez; bulut ortamında Google SERP'i güvenilir biçimde çekmek genelde mümkün
değildir. Google için Search Console veya ücretli SERP API önerilir.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

WORKSPACE = Path("/workspace")
HISTORY = WORKSPACE / "AGENT-HUB/REPORTS/data/serp-led-ekran-history.jsonl"
WEEKLY_MD = WORKSPACE / "AGENT-HUB/REPORTS/SERP-LED-EKRAN-HAFTALIK.md"
DDG_URL = "https://html.duckduckgo.com/html/"
QUERY = "led ekran"
TARGET_HOST_SUFFIX = "ledajans.com"


def _fetch_ddg_results(query: str) -> list[str]:
    body = f"q={query.replace(' ', '+')}&b=".encode("utf-8")
    req = Request(
        DDG_URL,
        data=body,
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-serp-snapshot/1.0)",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    hrefs = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    out: list[str] = []
    for raw in hrefs:
        m = re.search(r"uddg=([^&]+)", raw)
        url = unquote(m.group(1)) if m else raw.replace("&amp;", "&")
        if url.startswith("//"):
            url = "https:" + url
        out.append(url)
    return out


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _rank_for_target(urls: list[str]) -> tuple[int | None, str | None]:
    for i, u in enumerate(urls, start=1):
        h = _host(u)
        if h == TARGET_HOST_SUFFIX or h.endswith("." + TARGET_HOST_SUFFIX):
            return i, u
    return None, None


def _append_history(record: dict) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _rebuild_weekly_markdown() -> None:
    if not HISTORY.is_file():
        return
    lines = [json.loads(l) for l in HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]
    # ISO haftası -> en son kayıt
    by_week: dict[tuple[int, int], dict] = {}
    for rec in lines:
        ts = rec.get("captured_at_utc")
        if not ts:
            continue
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        key = (dt.isocalendar().year, dt.isocalendar().week)
        prev = by_week.get(key)
        if prev is None or ts > prev["captured_at_utc"]:
            by_week[key] = rec

    rows = sorted(by_week.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True)
    md: list[str] = [
        "# SERP — «led ekran» / ledajans.com (haftalık özet)",
        "",
        "## Ölçüm standardı",
        "- **Sorgu:** `led ekran`",
        "- **Motor (otomasyon):** DuckDuckGo HTML sonuçları (oturumsuz).",
        "- **Google:** Bu depo betiği Google sırasını ölçmez. Resmi karşılaştırma için Search Console "
        "(Performans → Sorgular) veya SERP API anahtarı gerekir.",
        "",
        "| ISO hafta | UTC tarih | Sıra (DDG) | Eşleşen URL | Üst 3 sonuç (DDG) |",
        "|------------|-------------|------------|-------------|-------------------|",
    ]
    for (y, w), rec in rows[:26]:
        top3 = rec.get("top_organic_urls") or []
        top3s = "; ".join((u[:60] + "…") if len(u) > 60 else u for u in top3[:3])
        iso = f"{y}-W{w:02d}"
        rank = rec.get("rank")
        rank_s = str(rank) if rank is not None else "—"
        url = rec.get("matched_url") or "—"
        md.append(
            f"| {iso} | {rec.get('captured_at_utc', '')[:10]} | {rank_s} | `{url}` | {top3s} |"
        )
    md.extend(
        [
            "",
            "## Ham kayıt",
            f"Satır bazlı JSON: `{HISTORY.relative_to(WORKSPACE)}`",
            "",
            "### Betik",
            "`python3 AGENT-HUB/scripts/serp_led_ekran_snapshot.py`",
            "",
        ]
    )
    WEEKLY_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    urls = _fetch_ddg_results(QUERY)
    rank, matched = _rank_for_target(urls)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = {
        "captured_at_utc": now,
        "query": QUERY,
        "engine": "duckduckgo_html",
        "locale_note": "Accept-Language tr-TR; DDG bölgesel karışımı olabilir",
        "rank": rank,
        "matched_url": matched,
        "top_organic_urls": urls[:10],
    }
    _append_history(record)
    _rebuild_weekly_markdown()
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if rank is None:
        print(
            "\nUYARI: ledajans.com ilk sonuç kümesinde bulunamadı; DDG yanıtını kontrol edin.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
