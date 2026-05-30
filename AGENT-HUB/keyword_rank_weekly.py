#!/usr/bin/env python3
"""Haftalık anahtar kelime sıra raporu — ledajans.com (Google öncelikli)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("/workspace")
HUB = WORKSPACE / "AGENT-HUB"
DATA_DIR = HUB / "data"
HISTORY_FILE = DATA_DIR / "keyword-rank-history.jsonl"
REPORTS_DIR = HUB / "REPORTS"

KEYWORD = "led ekran"
DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/led-ekran/"
LOCALE = "tr"
COUNTRY = "tr"
DEVICE = "mobile"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_url(url: str) -> str:
    u = url.strip().rstrip("/")
    u = re.sub(r"^https?://", "", u, flags=re.I)
    u = re.sub(r"^www\.", "", u, flags=re.I)
    return u.lower()


def domain_in_url(url: str) -> bool:
    return DOMAIN in normalize_url(url)


def fetch_serpapi(keyword: str, api_key: str, device: str) -> list[dict[str, Any]]:
    params = {
        "engine": "google",
        "q": keyword,
        "google_domain": "google.com.tr",
        "gl": COUNTRY,
        "hl": LOCALE,
        "device": device,
        "num": 100,
        "api_key": api_key,
    }
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    results: list[dict[str, Any]] = []
    for block in ("organic_results", "local_results", "inline_videos"):
        for item in data.get(block) or []:
            link = item.get("link") or item.get("website")
            if link:
                results.append(
                    {
                        "position": item.get("position"),
                        "title": item.get("title", ""),
                        "url": link,
                    }
                )
    results.sort(key=lambda x: (x.get("position") or 9999))
    return results


def fetch_serper(keyword: str, api_key: str, device: str) -> list[dict[str, Any]]:
    payload = json.dumps(
        {
            "q": keyword,
            "gl": COUNTRY,
            "hl": LOCALE,
            "num": 100,
            "location": "Turkey",
        }
    ).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    results = []
    for item in data.get("organic", []):
        results.append(
            {
                "position": item.get("position"),
                "title": item.get("title", ""),
                "url": item.get("link", ""),
            }
        )
    return results


def fetch_duckduckgo_html(keyword: str) -> list[dict[str, Any]]:
    data = urllib.parse.urlencode({"q": keyword, "kl": "tr-tr"}).encode()
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    results = []
    for i, m in enumerate(
        re.finditer(
            r'class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]*)</a>',
            html,
            re.I,
        ),
        1,
    ):
        results.append({"position": i, "title": m.group(2).strip(), "url": m.group(1)})
    return results


def find_rankings(
    results: list[dict[str, Any]],
) -> tuple[int | None, str | None, int | None, str | None]:
    """domain_rank, domain_url, target_rank, target_url."""
    domain_rank: int | None = None
    domain_url: str | None = None
    target_rank: int | None = None
    target_url_hit: str | None = None
    target_norm = normalize_url(TARGET_URL)

    for item in results:
        pos = item.get("position")
        if pos is None:
            continue
        url = item.get("url", "")
        if domain_in_url(url):
            if domain_rank is None or pos < domain_rank:
                domain_rank = int(pos)
                domain_url = url
            if target_norm in normalize_url(url) or normalize_url(url).startswith(
                target_norm
            ):
                if target_rank is None or pos < target_rank:
                    target_rank = int(pos)
                    target_url_hit = url

    return domain_rank, domain_url, target_rank, target_url_hit


def load_last_snapshot() -> dict[str, Any] | None:
    if not HISTORY_FILE.exists():
        return None
    last = None
    with HISTORY_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last = json.loads(line)
    return last


def append_history(record: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_report(record: dict[str, Any], prev: dict[str, Any] | None) -> str:
    date = record["date"]
    source = record["source"]
    dr = record.get("domain_rank")
    tr = record.get("target_url_rank")
    lines = [
        f"# Anahtar Kelime Sıra Raporu — {date}",
        "",
        "## Özet",
        f"- **Anahtar kelime:** {KEYWORD}",
        f"- **Hedef domain:** {DOMAIN}",
        f"- **Hedef URL:** {TARGET_URL}",
        f"- **Ölçüm kaynağı:** {source}",
        f"- **Locale:** {LOCALE}-{COUNTRY.upper()} | **Cihaz:** {DEVICE}",
        f"- **Ölçüm zamanı (UTC):** {record['captured_at_utc']}",
        "",
        "## Sıralama",
    ]
    if dr is not None:
        lines.append(f"- **Domain en iyi sıra:** {dr}. sıra ({record.get('domain_url', '—')})")
    else:
        lines.append("- **Domain en iyi sıra:** İlk 100 sonuçta bulunamadı")
    if tr is not None:
        lines.append(
            f"- **Hedef URL sırası:** {tr}. sıra ({record.get('target_url_hit', TARGET_URL)})"
        )
    else:
        lines.append(f"- **Hedef URL sırası:** İlk 100 sonuçta bulunamadı")

    if prev:
        prev_dr = prev.get("domain_rank")
        if dr is not None and prev_dr is not None:
            delta = prev_dr - dr
            if delta > 0:
                lines.append(f"- **Haftalık değişim (domain):** ↑ {delta} sıra iyileşme")
            elif delta < 0:
                lines.append(f"- **Haftalık değişim (domain):** ↓ {abs(delta)} sıra düşüş")
            else:
                lines.append("- **Haftalık değişim (domain):** Değişiklik yok")
        lines.append(
            f"- **Önceki ölçüm:** {prev.get('date')} ({prev.get('source', '—')})"
        )

    if source != "google_serpapi" and source != "google_serper":
        lines.extend(
            [
                "",
                "## Uyarı",
                "Bu ölçüm **Google SERP API** ile alınmadı. Kesin Google sırası için Cursor Automation "
                "ortam değişkenine `SERPAPI_KEY` veya `SERPER_API_KEY` ekleyin.",
            ]
        )

    lines.extend(
        [
            "",
            "## İlk 10 sonuç",
            "",
        ]
    )
    for item in record.get("top_results", [])[:10]:
        lines.append(f"{item['position']}. [{item.get('title') or item['url']}]({item['url']})")

    return "\n".join(lines) + "\n"


def resolve_source(device: str) -> tuple[str, list[dict[str, Any]]]:
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()

    if serpapi_key:
        try:
            return "google_serpapi", fetch_serpapi(KEYWORD, serpapi_key, device)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
            print(f"SerpAPI hatası: {exc}", file=sys.stderr)

    if serper_key:
        try:
            return "google_serper", fetch_serper(KEYWORD, serper_key, device)
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
            print(f"Serper hatası: {exc}", file=sys.stderr)

    return "duckduckgo_html_tr (yaklaşık — Google değil)", fetch_duckduckgo_html(KEYWORD)


def should_skip_weekly(force: bool) -> bool:
    if force:
        return False
    prev = load_last_snapshot()
    if not prev:
        return False
    try:
        last_date = datetime.strptime(prev["date"], "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        return (today - last_date).days < 7
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="LEDAJANS haftalık anahtar kelime sıra raporu")
    parser.add_argument("--force", action="store_true", help="7 gün dolmadan da çalıştır")
    parser.add_argument("--dry-run", action="store_true", help="Dosya yazma, yalnız stdout")
    args = parser.parse_args()

    if should_skip_weekly(args.force):
        prev = load_last_snapshot()
        print(
            f"Atlandı: son ölçüm {prev['date']} — haftalık aralık dolmadı. --force ile zorla.",
            file=sys.stderr,
        )
        return 0

    source, results = resolve_source(DEVICE)
    domain_rank, domain_url, target_rank, target_url_hit = find_rankings(results)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record: dict[str, Any] = {
        "date": today,
        "keyword": KEYWORD,
        "domain": DOMAIN,
        "target_url": TARGET_URL,
        "locale": f"{LOCALE}-{COUNTRY}",
        "device": DEVICE,
        "source": source,
        "captured_at_utc": utc_now(),
        "domain_rank": domain_rank,
        "domain_url": domain_url,
        "target_url_rank": target_rank,
        "target_url_hit": target_url_hit,
        "top_results": [
            {
                "position": r.get("position"),
                "title": r.get("title", ""),
                "url": r.get("url", ""),
            }
            for r in results[:15]
        ],
    }

    prev = load_last_snapshot()
    report_md = build_report(record, prev)
    report_path = REPORTS_DIR / f"{today}-keyword-rank-weekly.md"

    print(report_md)

    if args.dry_run:
        return 0

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")
    append_history(record)

    # SERP watch ile uyumlu kısa güncelleme
    serp_watch = REPORTS_DIR / f"{today}-serp-watch.md"
    if not serp_watch.exists():
        serp_watch.write_text(
            f"# SERP Watch Report - {today}\n\n"
            f"## Baseline Positions\n"
            f"- anahtar kelime: {KEYWORD} | mevcut sıra: {domain_rank or 'N/A'} | "
            f"hedef URL sıra: {target_rank or 'N/A'} | kaynak: {source} | "
            f"ölçüm: {record['captured_at_utc']}\n",
            encoding="utf-8",
        )

    print(f"\nRapor: {report_path}", file=sys.stderr)
    print(f"Geçmiş: {HISTORY_FILE}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
