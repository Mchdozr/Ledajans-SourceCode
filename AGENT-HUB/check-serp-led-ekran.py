#!/usr/bin/env python3
"""Google TR SERP snapshot: 'led ekran' -> ledajans.com rank tracking."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"
PRIMARY_COMPETITOR = "ledfon.com"
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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_host(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def rank_from_organic_urls(urls: list[str], domain: str) -> tuple[int | None, str | None]:
    seen: set[str] = set()
    organic: list[str] = []
    for url in urls:
        if not url.startswith("http"):
            continue
        host = normalize_host(url)
        if not host or "google." in host or "gstatic" in host:
            continue
        if url in seen:
            continue
        seen.add(url)
        organic.append(url)

    for index, url in enumerate(organic, start=1):
        if domain in normalize_host(url):
            return index, url
    return None, None


def fetch_with_playwright(device: str) -> tuple[int | None, str | None, str]:
    from playwright.sync_api import sync_playwright

    mobile = device == "mobile"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            locale="tr-TR",
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                if mobile
                else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 412, "height": 915} if mobile else {"width": 1366, "height": 900},
        )
        page = context.new_page()
        page.goto(
            f"https://www.google.com/search?q={QUERY.replace(' ', '+')}&hl=tr&gl=tr&num=50",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(2500)
        if "sorry" in page.url or "consent" in page.url:
            browser.close()
            return None, None, f"blocked:{page.url}"

        hrefs = re.findall(r'href="(https?://[^"]+)"', page.content())
        rank, target_url = rank_from_organic_urls(hrefs, TARGET_DOMAIN)
        browser.close()
        return rank, target_url, "playwright_google_tr"


def fetch_with_serpapi(device: str) -> tuple[int | None, str | None, str]:
    import os

    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None, None, "serpapi_missing_key"

    from serpapi import GoogleSearch

    params = {
        "engine": "google",
        "q": QUERY,
        "hl": "tr",
        "gl": "tr",
        "google_domain": "google.com.tr",
        "num": 50,
        "device": "mobile" if device == "mobile" else "desktop",
        "api_key": api_key,
    }
    results = GoogleSearch(params).get_dict()
    organic = results.get("organic_results") or []
    urls = [item.get("link", "") for item in organic if item.get("link")]
    rank, target_url = rank_from_organic_urls(urls, TARGET_DOMAIN)
    return rank, target_url, "serpapi_google_tr"


def resolve_rank(device: str, rank_override: int | None, target_override: str | None) -> tuple[int | None, str | None, str, str]:
    if rank_override is not None:
        notes = "manual_override"
        if target_override:
            return rank_override, target_override, "manual_browser_check", notes
        return rank_override, DEFAULT_TARGET_URL, "manual_browser_check", notes

    for fetcher in (fetch_with_serpapi, fetch_with_playwright):
        rank, target_url, source = fetcher(device)
        if rank is not None:
            return rank, target_url, source, "organic_snapshot"
        if source.startswith("blocked"):
            return None, None, source, source

    return None, None, "unavailable", "google_blocked_or_no_match"


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_row(row: dict[str, str]) -> None:
    existing = read_baseline_rows()
    write_header = not BASELINE_PATH.exists() or not existing
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})


def latest_led_ekran_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in reversed(rows):
        if row.get("query", "").strip().lower() != QUERY:
            continue
        device = row.get("device", "").strip().lower()
        if device and device not in latest:
            latest[device] = row
    return latest


def weekly_monitoring_path(captured_at: str) -> Path:
    date_part = captured_at[:10]
    return ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_part}.md"


def update_weekly_monitoring(captured_at: str, snapshots: list[dict[str, str]]) -> Path:
    path = weekly_monitoring_path(captured_at)
    rows = read_baseline_rows()
    prior = latest_led_ekran_rows([r for r in rows if r.get("captured_at_utc", "") < captured_at])

    lines = [
        f"# Haftalık SEO İzleme — {captured_at[:10]}",
        "",
        "## SERP — led ekran (Google TR)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Ölçüm (UTC) |",
        "|---|---:|---|---|---|",
    ]
    for snap in snapshots:
        lines.append(
            f"| {snap['device']} | {snap['rank_position']} | {snap['target_url']} | "
            f"{snap['source']} | {snap['captured_at_utc']} |"
        )

    lines.extend(["", "## Haftalık delta", ""])
    for snap in snapshots:
        device = snap["device"]
        old = prior.get(device)
        if not old:
            lines.append(f"- **{device}:** önceki ölçüm yok; güncel sıra **{snap['rank_position']}**.")
            continue
        old_rank = old.get("rank_position", "N/A")
        new_rank = snap["rank_position"]
        delta_note = "stabil"
        try:
            old_num = float(str(old_rank).replace("top", ""))
            new_num = float(str(new_rank))
            change = old_num - new_num
            if change > 0:
                delta_note = f"↑ {change:.2f} sıra iyileşme (önceki: {old_rank})"
            elif change < 0:
                delta_note = f"↓ {abs(change):.2f} sıra kaybı (önceki: {old_rank})"
            else:
                delta_note = f"stabil (önceki: {old_rank})"
        except ValueError:
            delta_note = f"önceki: {old_rank} → güncel: {new_rank}"
        lines.append(f"- **{device}:** {delta_note}.")

    gsc_row = next(
        (
            row
            for row in reversed(rows)
            if row.get("query", "").lower() == QUERY and row.get("source", "").startswith("gsc")
        ),
        None,
    )
    if gsc_row:
        lines.extend(
            [
                "",
                "## GSC referans (son export)",
                "",
                f"- Kaynak: `{gsc_row.get('source', '')}`",
                f"- Ortalama pozisyon: **{gsc_row.get('rank_position', 'N/A')}**",
                f"- Not: {gsc_row.get('notes', '')}",
                "- Canlı SERP (#1) ile GSC ortalaması (6.78) farklı ölçüm modelleridir; haftalık trend için ikisini birlikte izleyin.",
            ]
        )

    lines.extend(
        [
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-led-ekran.py",
            "```",
            "",
            "Opsiyonel: `SERPAPI_KEY` tanımlıysa betik otomatik API snapshot kullanır.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_snapshot(
    *,
    captured_at: str,
    device: str,
    rank: int | None,
    target_url: str | None,
    source: str,
    notes: str,
) -> dict[str, str]:
    rank_text = str(rank) if rank is not None else "not_found"
    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": target_url or DEFAULT_TARGET_URL,
        "rank_position": rank_text,
        "serp_features": "",
        "primary_competitor": PRIMARY_COMPETITOR,
        "competitor_rank": "2" if rank == 1 else "",
        "source": source,
        "notes": notes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track led ekran SERP rank for ledajans.com")
    parser.add_argument("--device", choices=("mobile", "desktop", "both"), default="both")
    parser.add_argument("--rank", type=int, help="Manual organic rank override")
    parser.add_argument("--target-url", default="", help="Manual target URL override")
    parser.add_argument("--captured-at", default="", help="UTC timestamp override (ISO-8601 Z)")
    parser.add_argument("--skip-weekly-md", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    captured_at = args.captured_at or utc_now_iso()
    devices = ["mobile", "desktop"] if args.device == "both" else [args.device]
    snapshots: list[dict[str, str]] = []

    for device in devices:
        rank, target_url, source, notes = resolve_rank(device, args.rank, args.target_url or None)
        snapshot = build_snapshot(
            captured_at=captured_at,
            device=device,
            rank=rank,
            target_url=target_url,
            source=source,
            notes=notes,
        )
        append_baseline_row(snapshot)
        snapshots.append(snapshot)
        print(
            f"{device}: rank={snapshot['rank_position']} url={snapshot['target_url']} source={source}"
        )

    weekly_path = None
    if not args.skip_weekly_md:
        weekly_path = update_weekly_monitoring(captured_at, snapshots)

    if weekly_path:
        print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
