#!/usr/bin/env python3
"""Google SERP sıra takibi — ledajans.com anahtar kelime izleme ve haftalık rapor."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

HUB = Path("/workspace/AGENT-HUB")
DATA_DIR = HUB / "data"
HISTORY_FILE = DATA_DIR / "serp-history.json"
REPORTS = HUB / "REPORTS"
WEEKLY_REPORT = HUB / "SERP-WEEKLY-REPORT.md"
LATEST_REPORT = HUB / "SERP-RANK-LATEST.md"

TARGET_DOMAIN = "ledajans.com"
DEFAULT_KEYWORDS = ["led ekran"]
LOCALE = "tr-TR"
TR_TZ = ZoneInfo("Europe/Istanbul")

SKIP_DOMAINS = {
    "startpage.com",
    "google.com",
    "gstatic.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "mastodon.social",
    "wikipedia.org",
    "linkedin.com",
    "tiktok.com",
    "pinterest.com",
}


@dataclass
class RankResult:
    keyword: str
    position: int | None
    target_url: str | None
    all_matches: list[dict]
    top_competitors: list[dict]
    source: str
    locale: str
    captured_at_utc: str


def domain_of(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()


def fetch_via_serper(keyword: str, api_key: str) -> tuple[list[str], str]:
    payload = {
        "q": keyword,
        "gl": "tr",
        "hl": "tr",
        "num": 50,
    }
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    organic = [item.get("link", "") for item in data.get("organic", []) if item.get("link")]
    return organic, "serper.dev"


def fetch_via_startpage(keyword: str) -> tuple[list[str], str]:
    resp = requests.post(
        "https://www.startpage.com/sp/search",
        data={"query": keyword, "language": "turkish", "cat": "web"},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = unescape(resp.text)
    links = re.findall(r'class="[^"]*result-link[^"]*"[^>]*href="([^"]+)"', text)
    if not links:
        links = re.findall(r'class="[^"]*w-gl__result-title[^"]*"[^>]*href="([^"]+)"', text)
    return links, "startpage/google-proxy"


def dedupe_organic(urls: list[str]) -> list[str]:
    organic: list[str] = []
    seen: set[str] = set()
    for url in urls:
        d = domain_of(url)
        if any(skip in d for skip in SKIP_DOMAINS):
            continue
        if d in seen:
            continue
        seen.add(d)
        organic.append(url)
    return organic


def analyze_rank(keyword: str, organic: list[str], source: str) -> RankResult:
    matches: list[dict] = []
    competitors: list[dict] = []
    for idx, url in enumerate(organic, start=1):
        d = domain_of(url)
        if TARGET_DOMAIN in d:
            matches.append({"position": idx, "url": url})
        elif idx <= 10:
            competitors.append({"position": idx, "domain": d, "url": url})

    best = min(matches, key=lambda m: m["position"]) if matches else None
    return RankResult(
        keyword=keyword,
        position=best["position"] if best else None,
        target_url=best["url"] if best else None,
        all_matches=matches,
        top_competitors=competitors[:5],
        source=source,
        locale=LOCALE,
        captured_at_utc=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def fetch_rank(keyword: str) -> RankResult:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if api_key:
        organic, source = fetch_via_serper(keyword, api_key)
    else:
        organic, source = fetch_via_startpage(keyword)
    return analyze_rank(keyword, dedupe_organic(organic), source)


def load_history() -> dict:
    if not HISTORY_FILE.exists():
        return {"snapshots": []}
    return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))


def save_history(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_snapshot(results: list[RankResult]) -> None:
    history = load_history()
    history.setdefault("snapshots", []).append(
        {
            "captured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "results": [asdict(r) for r in results],
        }
    )
    # Son 90 gün (~13 hafta) tut
    cutoff = datetime.now(UTC) - timedelta(days=90)
    kept = []
    for snap in history["snapshots"]:
        ts = datetime.fromisoformat(snap["captured_at_utc"].replace("Z", "+00:00"))
        if ts >= cutoff:
            kept.append(snap)
    history["snapshots"] = kept
    save_history(history)


def find_snapshot_near(days_ago: int) -> dict | None:
    history = load_history()
    target = datetime.now(UTC) - timedelta(days=days_ago)
    best: dict | None = None
    best_delta = timedelta(days=999)
    for snap in history.get("snapshots", []):
        ts = datetime.fromisoformat(snap["captured_at_utc"].replace("Z", "+00:00"))
        delta = abs(ts - target)
        if delta < best_delta:
            best_delta = delta
            best = snap
    if best_delta > timedelta(days=2):
        return None
    return best


def position_label(pos: int | None) -> str:
    if pos is None:
        return "İlk 50'de yok"
    return f"**{pos}. sıra**"


def format_delta(current: int | None, previous: int | None) -> str:
    if current is None or previous is None:
        return "N/A (karşılaştırma verisi yok)"
    diff = previous - current
    if diff > 0:
        return f"▲ {diff} sıra yükseldi ({previous} → {current})"
    if diff < 0:
        return f"▼ {abs(diff)} sıra düştü ({previous} → {current})"
    return f"→ Değişmedi ({current}. sıra)"


def write_latest_report(results: list[RankResult]) -> None:
    now_tr = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S TR")
    lines = [
        "# SERP Sıra Raporu — Güncel",
        "",
        f"- Ölçüm zamanı: **{now_tr}**",
        f"- Hedef domain: `{TARGET_DOMAIN}`",
        f"- Locale: `{LOCALE}` | Kaynak: `{results[0].source if results else 'N/A'}`",
        "",
    ]
    for r in results:
        lines.extend(
            [
                f"## Anahtar kelime: `{r.keyword}`",
                "",
                f"- Mevcut sıra: {position_label(r.position)}",
                f"- Hedef URL: {r.target_url or '—'}",
                "",
            ]
        )
        if r.all_matches:
            lines.append("Tüm eşleşmeler:")
            for m in r.all_matches:
                lines.append(f"- Sıra {m['position']}: {m['url']}")
            lines.append("")
        if r.top_competitors:
            lines.append("İlk 5 rakip:")
            for c in r.top_competitors:
                lines.append(f"- {c['position']}. {c['domain']}")
            lines.append("")
    lines.append("## Not")
    lines.append(
        "- Ölçüm Startpage (Google proxy) üzerinden alınır. "
        "Daha hassas Google TR sonuçları için `SERPER_API_KEY` ortam değişkeni tanımlanabilir."
    )
    LATEST_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_weekly_report(results: list[RankResult]) -> None:
    now_tr = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S TR")
    week_ago = find_snapshot_near(7)
    lines = [
        "# Haftalık SERP Sıra Raporu — ledajans.com",
        "",
        f"- Rapor tarihi: **{now_tr}**",
        f"- Karşılaştırma: 7 gün önceki ölçüm",
        "",
        "## Özet",
        "",
        "| Anahtar kelime | Bu hafta | Geçen hafta | Değişim |",
        "|---|---:|---:|---|",
    ]
    for r in results:
        prev_pos = None
        if week_ago:
            for item in week_ago.get("results", []):
                if item.get("keyword") == r.keyword:
                    prev_pos = item.get("position")
                    break
        lines.append(
            f"| `{r.keyword}` | {r.position or '50+'} | {prev_pos or '—'} | {format_delta(r.position, prev_pos)} |"
        )

    lines.extend(["", "## Detay", ""])
    for r in results:
        lines.extend(
            [
                f"### `{r.keyword}`",
                "",
                f"- Sıra: {position_label(r.position)}",
                f"- URL: {r.target_url or '—'}",
                f"- Kaynak: {r.source}",
                "",
            ]
        )
        if r.top_competitors:
            lines.append("Üst rakipler:")
            for c in r.top_competitors:
                lines.append(f"- {c['position']}. [{c['domain']}]({c['url']})")
            lines.append("")

    history = load_history()
    recent = history.get("snapshots", [])[-8:]
    if len(recent) >= 2:
        lines.extend(["## Son ölçümler", "", "| Tarih (UTC) | led ekran sırası |", "|---|---:|"])
        for snap in recent:
            ts = snap.get("captured_at_utc", "")[:16]
            pos = "—"
            for item in snap.get("results", []):
                if item.get("keyword") == "led ekran":
                    pos = str(item.get("position") or "50+")
                    break
            lines.append(f"| {ts} | {pos} |")
        lines.append("")

    lines.append("## Yöntem")
    lines.append(
        "- Cron otomasyonu günlük ölçüm alır; bu rapor haftalık (Pazartesi) veya `--weekly` ile üretilir."
    )
    lines.append("- Veri: `AGENT-HUB/data/serp-history.json`")
    WEEKLY_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    date_prefix = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    dated = REPORTS / f"{date_prefix}-serp-rank-weekly.md"
    dated.write_text(WEEKLY_REPORT.read_text(encoding="utf-8"), encoding="utf-8")


def update_serp_watch_report(results: list[RankResult]) -> None:
    date_prefix = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    path = REPORTS / f"{date_prefix}-serp-watch.md"
    now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# SERP Watch Report - {date_prefix}",
        "",
        "## Keyword Set",
    ]
    for r in results:
        comp = r.top_competitors[0]["domain"] if r.top_competitors else "—"
        pos = str(r.position) if r.position else "N/A"
        lines.append(
            f"- anahtar kelime: {r.keyword} | mevcut sıra: {pos} | "
            f"rakip: {comp} | fark: N/A | not: Otomatik ölçüm ({r.source})"
        )
    lines.extend(
        [
            "",
            "## Baseline Positions",
        ]
    )
    for r in results:
        pos = str(r.position) if r.position else "N/A"
        url = r.target_url or "—"
        lines.append(
            f"- anahtar kelime: {r.keyword} | mevcut sıra: {pos} | "
            f"hedef URL: {url} | kaynak: {r.source} | locale: {LOCALE}"
        )
    lines.extend(
        [
            "",
            f"## Execution Update - {now_utc}",
            "### Completed Analysis",
            "- Otomatik SERP sıra ölçümü tamamlandı (`serp_rank_tracker.py`).",
            f"- Veri kaynağı: {results[0].source if results else 'N/A'}",
            "",
            "### Next Step",
            "- Haftalık delta için en az 7 günlük ölçüm birikmesi bekleniyor.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(results: list[RankResult]) -> None:
    for r in results:
        pos = r.position if r.position else "50+"
        print(f"[SERP] {r.keyword!r} → ledajans.com sıra: {pos} | URL: {r.target_url or '—'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ledajans.com SERP sıra takibi")
    parser.add_argument("--keywords", nargs="+", default=DEFAULT_KEYWORDS)
    parser.add_argument("--weekly", action="store_true", help="Haftalık rapor üret")
    parser.add_argument("--no-save", action="store_true", help="Geçmişe kaydetme")
    args = parser.parse_args()

    results: list[RankResult] = []
    for keyword in args.keywords:
        try:
            results.append(fetch_rank(keyword))
        except requests.RequestException as exc:
            print(f"HATA: {keyword!r} ölçülemedi: {exc}", file=sys.stderr)
            return 1

    if not args.no_save:
        append_snapshot(results)

    write_latest_report(results)
    update_serp_watch_report(results)

    is_monday = datetime.now(TR_TZ).weekday() == 0
    if args.weekly or is_monday:
        write_weekly_report(results)

    print_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
