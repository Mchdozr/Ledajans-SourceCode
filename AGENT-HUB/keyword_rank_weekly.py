#!/usr/bin/env python3
"""Haftalık/günlük 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_HOST = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"

BASELINE_FIELDS = [
    "captured_at_utc",
    "query",
    "locale",
    "device",
    "search_engine",
    "target_url",
    "rank_position",
    "serp_features",
    "primary_competitor",
    "competitor_rank",
    "source",
    "notes",
]


@dataclass
class RankResult:
    device: str
    rank_position: int | str | None
    target_url: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def week_start_monday(day: datetime) -> datetime:
    return day - timedelta(days=day.weekday())


def weekly_monitoring_path(day: datetime | None = None) -> Path:
    ref = day or datetime.now(UTC)
    monday = week_start_monday(ref)
    return ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{monday.date().isoformat()}.md"


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_rank_for_query(query: str, device: str | None = None) -> dict[str, str] | None:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == query.lower()
        and (device is None or row.get("device", "").strip().lower() == device.lower())
    ]
    if not rows:
        return None
    rows.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    return rows[0]


def normalize_host(url: str) -> str:
    match = re.match(r"https?://([^/]+)", url)
    if not match:
        return ""
    return match.group(1).lower().replace("www.", "")


def parse_organic_rank(results: list[dict[str, str]], device: str) -> RankResult | None:
    organic: list[str] = []
    rank: int | None = None
    target_url = DEFAULT_TARGET_URL
    primary_competitor = ""

    for item in results:
        link = item.get("link") or item.get("href") or ""
        title = item.get("title") or item.get("h3") or ""
        if not link:
            continue
        host = normalize_host(link)
        if not host or any(token in host for token in ("google.", "gstatic.", "accounts.google")):
            continue
        if title == "" and "h3" not in item:
            continue
        if link in organic:
            continue
        organic.append(link)
        if rank is None and TARGET_HOST not in host and not primary_competitor:
            primary_competitor = host
        if TARGET_HOST in host and rank is None:
            rank = len(organic)
            target_url = link

    if rank is None:
        return None

    return RankResult(
        device=device,
        rank_position=rank,
        target_url=target_url,
        source="serper_api",
        notes=f"Organic sıra; rakip #1: {primary_competitor or 'n/a'}",
        primary_competitor=primary_competitor,
        competitor_rank="1" if primary_competitor else "",
    )


def fetch_serper(query: str, device: str, api_key: str) -> RankResult | None:
    payload = json.dumps(
        {
            "q": query,
            "gl": "tr",
            "hl": "tr",
            "num": 30,
            "device": device,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    organic = data.get("organic", [])
    parsed = parse_organic_rank(organic, device)
    if parsed:
        parsed.source = "serper_api"
    return parsed


def fetch_serpapi(query: str, device: str, api_key: str) -> RankResult | None:
    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "gl": "tr",
            "hl": "tr",
            "num": "30",
            "device": device,
            "api_key": api_key,
        }
    )
    url = f"https://serpapi.com/search.json?{params}"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    organic = data.get("organic_results", [])
    parsed = parse_organic_rank(organic, device)
    if parsed:
        parsed.source = "serpapi"
    return parsed


def fetch_playwright(query: str, device: str) -> RankResult | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    ua_mobile = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    )
    ua_desktop = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    is_mobile = device == "mobile"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=device != "desktop",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            user_agent=ua_mobile if is_mobile else ua_desktop,
            viewport={"width": 390, "height": 844} if is_mobile else {"width": 1366, "height": 900},
            is_mobile=is_mobile,
            has_touch=is_mobile,
            geolocation={"latitude": 41.0082, "longitude": 28.9784},
            permissions=["geolocation"],
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9"},
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        search_url = (
            f"https://www.google.com.tr/search?q={urllib.parse.quote_plus(query)}"
            "&hl=tr&gl=tr&num=30&pws=0"
        )
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        for selector in ('button:has-text("Tümünü kabul et")', "#L2AGLb"):
            try:
                locator = page.locator(selector)
                if locator.count():
                    locator.first.click(timeout=2000)
                    page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        html = page.content()
        hrefs = page.eval_on_selector_all(
            'div#search a[href^="http"]',
            'els => els.map(e => ({href:e.href, h3: e.querySelector("h3")?.innerText || ""}))',
        )
        browser.close()

    organic: list[str] = []
    rank: int | None = None
    target_url = DEFAULT_TARGET_URL
    primary_competitor = ""
    captcha = "captcha" in html.lower() or "olağandışı" in html.lower()

    for item in hrefs:
        href = item.get("href", "")
        title = item.get("h3", "")
        if not href or not title:
            continue
        host = normalize_host(href)
        if not host or any(token in host for token in ("google.", "gstatic.", "accounts.google", "support.google")):
            continue
        if href in organic:
            continue
        organic.append(href)
        if rank is None and TARGET_HOST not in host and not primary_competitor:
            primary_competitor = host
        if TARGET_HOST in host and rank is None:
            rank = len(organic)
            target_url = href

    if rank is None:
        note = "CAPTCHA/sonuç yok" if captcha else "Hedef URL ilk 30 sonuçta yok"
        return RankResult(
            device=device,
            rank_position="n/a",
            target_url=DEFAULT_TARGET_URL,
            source="browser_google_tr",
            notes=note,
            primary_competitor=primary_competitor,
        )

    return RankResult(
        device=device,
        rank_position=rank,
        target_url=target_url,
        source="browser_google_tr",
        notes=f"Organic sıra; rakip #1: {primary_competitor or 'n/a'}",
        primary_competitor=primary_competitor,
        competitor_rank="1" if primary_competitor else "",
    )


def measure_device(device: str, rank_override: int | None, source_override: str | None) -> RankResult:
    if rank_override is not None:
        return RankResult(
            device=device,
            rank_position=rank_override,
            target_url=DEFAULT_TARGET_URL,
            source=source_override or "manual_override",
            notes="CLI override",
        )

    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()

    for fetcher, key, label in (
        (fetch_serper, serper_key, "serper_api"),
        (fetch_serpapi, serpapi_key, "serpapi"),
    ):
        if not key:
            continue
        try:
            result = fetcher(QUERY, device, key)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result = RankResult(
                device=device,
                rank_position="n/a",
                target_url=DEFAULT_TARGET_URL,
                source=label,
                notes=f"API hata: {exc}",
            )
            continue
        if result and result.rank_position not in (None, "n/a"):
            return result

    playwright_result = fetch_playwright(QUERY, device)
    if playwright_result:
        return playwright_result

    return RankResult(
        device=device,
        rank_position="n/a",
        target_url=DEFAULT_TARGET_URL,
        source="unavailable",
        notes="Ölçüm kaynağı yok; SERPER_API_KEY veya --rank-* kullanın",
    )


def append_baseline(captured_at: str, results: list[RankResult]) -> int:
    existing = read_baseline_rows()
    existing_keys = {
        (row.get("captured_at_utc", ""), row.get("query", "").lower(), row.get("device", ""), row.get("source", ""))
        for row in existing
    }

    appended = 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        for result in results:
            key = (captured_at, QUERY.lower(), result.device, result.source)
            if key in existing_keys:
                continue
            writer.writerow(
                {
                    "captured_at_utc": captured_at,
                    "query": QUERY,
                    "locale": LOCALE,
                    "device": result.device,
                    "search_engine": SEARCH_ENGINE,
                    "target_url": result.target_url,
                    "rank_position": str(result.rank_position),
                    "serp_features": "",
                    "primary_competitor": result.primary_competitor,
                    "competitor_rank": result.competitor_rank,
                    "source": result.source,
                    "notes": result.notes,
                }
            )
            appended += 1
    return appended


def format_delta(current: str | int | None, previous: str | int | None) -> str:
    try:
        cur = float(current)  # type: ignore[arg-type]
        prev = float(previous)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "n/a"
    diff = prev - cur
    if diff > 0:
        return f"↑ {diff:.2f} sıra (iyileşme)"
    if diff < 0:
        return f"↓ {abs(diff):.2f} sıra (kayıp)"
    return "sabit"


def update_weekly_monitoring(captured_at: str, results: list[RankResult]) -> Path:
    path = weekly_monitoring_path()
    previous_mobile = latest_rank_for_query(QUERY, "mobile")
    previous_desktop = latest_rank_for_query(QUERY, "desktop")
    previous_gsc = latest_rank_for_query(QUERY, "mobile")
    gsc_ref = None
    for row in read_baseline_rows():
        if row.get("query", "").lower() == QUERY.lower() and row.get("source", "").startswith("gsc_performance"):
            gsc_ref = row
    if gsc_ref is None:
        gsc_ref = previous_gsc

    lines = [
        f"# Haftalık SEO İzleme — {path.stem.replace('WEEKLY-MONITORING-', '')}",
        "",
        f"- Son ölçüm (UTC): `{captured_at}`",
        f"- Sorgu: **{QUERY}** | Locale: `{LOCALE}` | Motor: `{SEARCH_ENGINE}`",
        "",
        "## SERP konumu (led ekran)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Önceki | Değişim |",
        "|---|---:|---|---|---|---|",
    ]

    for result in results:
        prev = previous_mobile if result.device == "mobile" else previous_desktop
        prev_rank = prev.get("rank_position", "n/a") if prev else "n/a"
        lines.append(
            f"| {result.device} | {result.rank_position} | {result.target_url} | {result.source} "
            f"| {prev_rank} | {format_delta(result.rank_position, prev_rank)} |"
        )

    gsc_pos = gsc_ref.get("rank_position", "n/a") if gsc_ref else "n/a"
    gsc_at = gsc_ref.get("captured_at_utc", "n/a") if gsc_ref else "n/a"
    desktop_rank = next((r.rank_position for r in results if r.device == "desktop"), "n/a")
    mobile_rank = next((r.rank_position for r in results if r.device == "mobile"), "n/a")

    lines.extend(
        [
            "",
            "## Özet",
            "",
            f"- **Canlı organic (desktop):** {desktop_rank}. sıra — `https://ledajans.com/`",
            f"- **Canlı organic (mobile):** {mobile_rank}. sıra",
            f"- **GSC avg position referansı:** {gsc_pos} (`{gsc_at}`)",
            "- Not: GSC `avg_position` ile canlı organic sıra farklı metriklerdir.",
            "",
            "## Komut",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "## Sonraki adımlar",
            "",
            "- `SERPER_API_KEY` tanımlanırsa mobil CAPTCHA riski azalır.",
            "- GSC Performance export yenilendiğinde `scripts/update-serp-baseline-from-gsc.py` çalıştır.",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="led ekran SERP ölçümü ve haftalık rapor")
    parser.add_argument("--rank-mobile", type=int, help="Mobil organic sıra override")
    parser.add_argument("--rank-desktop", type=int, help="Desktop organic sıra override")
    parser.add_argument("--source", default="manual_override", help="Override kaynak etiketi")
    parser.add_argument("--dry-run", action="store_true", help="CSV/MD yazmadan sonucu yazdır")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    captured_at = utc_now_iso()

    results = [
        measure_device("mobile", args.rank_mobile, args.source if args.rank_mobile is not None else None),
        measure_device("desktop", args.rank_desktop, args.source if args.rank_desktop is not None else None),
    ]

    payload = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "results": [result.__dict__ for result in results],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0

    appended = append_baseline(captured_at, results)
    weekly_path = update_weekly_monitoring(captured_at, results)
    print(f"baseline_appended={appended}")
    print(f"weekly_monitoring={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
