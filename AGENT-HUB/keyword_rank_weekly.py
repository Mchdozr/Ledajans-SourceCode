#!/usr/bin/env python3
"""Haftalık SERP ölçümü: led ekran → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import argparse
import csv
import os
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
PRIMARY_COMPETITOR = "ledurunleri.com"

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


def weekly_monitoring_path(captured_at: str) -> Path:
    date_part = captured_at[:10]
    return HUB / f"WEEKLY-MONITORING-{date_part}.md"


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    return f"https://{host}{path}"


def extract_domain(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        key = normalize_url(url)
        if key not in seen:
            seen.add(key)
            unique.append(url)
    return unique


def find_rank(urls: list[str], domain: str = TARGET_DOMAIN) -> tuple[int | None, str | None]:
    for index, url in enumerate(urls, start=1):
        if domain in url:
            return index, normalize_url(url)
    return None, None


def fetch_serper(device: str) -> tuple[list[str], str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {"q": QUERY, "gl": "tr", "hl": "tr", "num": 100}
    if device == "mobile":
        payload["device"] = "mobile"
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    organic = [item.get("link", "") for item in response.json().get("organic", []) if item.get("link")]
    return dedupe_urls(organic), "serper_api"


def fetch_serpapi(device: str) -> tuple[list[str], str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = {
        "engine": "google",
        "q": QUERY,
        "gl": "tr",
        "hl": "tr",
        "num": 100,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    organic = [item.get("link", "") for item in response.json().get("organic_results", []) if item.get("link")]
    return dedupe_urls(organic), "serpapi"


def fetch_playwright_google(device: str) -> tuple[list[str], str] | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    user_agents = {
        "mobile": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
        "desktop": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    viewports = {
        "mobile": {"width": 390, "height": 844},
        "desktop": {"width": 1366, "height": 900},
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=user_agents[device],
            locale="tr-TR",
            viewport=viewports[device],
        )
        page = context.new_page()
        search_url = "https://www.google.com.tr/search?" + urllib.parse.urlencode(
            {"q": QUERY, "hl": "tr", "gl": "tr", "num": "100"}
        )
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        if "sorry" in page.url or "captcha" in page.content().lower():
            browser.close()
            return None

        for selector in ('button:has-text("Tümünü kabul et")', 'button:has-text("Accept all")', "#L2AGLb"):
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1000):
                    button.click()
                    page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        urls: list[str] = []
        for anchor in page.locator('div#search a[href^="http"]').all():
            href = anchor.get_attribute("href") or ""
            if not href.startswith("http"):
                continue
            if any(blocked in href for blocked in ("google.", "gstatic", "youtube.com/results")):
                continue
            if anchor.locator("h3").count() == 0 and device == "desktop":
                continue
            urls.append(href)

        browser.close()

    organic = dedupe_urls(urls)
    if not organic:
        return None
    return organic, "playwright_google"


def fetch_duckduckgo() -> tuple[list[str], str]:
    urls: list[str] = []
    offset = 0
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    for _ in range(4):
        data: dict[str, str] = {"q": QUERY, "kl": "tr-tr"}
        if offset:
            data["s"] = str(offset)
        response = requests.post("https://html.duckduckgo.com/html/", data=data, headers=headers, timeout=30)
        response.raise_for_status()
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', response.text)
        if not links:
            break
        for href in links:
            if "uddg=" in href:
                match = re.search(r"uddg=([^&]+)", href)
                urls.append(urllib.parse.unquote(match.group(1)) if match else href)
            else:
                urls.append(href)
        offset += 30
    return dedupe_urls(urls), "duckduckgo_proxy"


def collect_organic(device: str) -> tuple[list[str], str]:
    for fetcher in (fetch_serper, fetch_serpapi, fetch_playwright_google):
        result = fetcher(device)
        if result and result[0]:
            return result
    return [], "google_blocked_vm"


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    existing = read_baseline_rows()
    existing_keys = {
        (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        for row in existing
    }
    to_append = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in existing_keys
    ]
    if not to_append:
        return 0

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})
    return len(to_append)


def previous_led_ekran_rows(before_capture: str | None = None) -> list[dict[str, str]]:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY
        and row.get("search_engine", "").strip().lower() == SEARCH_ENGINE
        and row.get("rank_position", "").strip().lower() not in {"", "pending", "top3", "top5", "top10", "top20"}
        and (before_capture is None or row.get("captured_at_utc", "") < before_capture)
    ]
    rows.sort(key=lambda row: row.get("captured_at_utc", ""))
    return rows


def parse_position(value: str) -> float | None:
    cleaned = value.strip().lower()
    if not cleaned or cleaned in {"pending", "top3", "top5", "top10", "top20"}:
        return None
    try:
        return float(cleaned.replace(",", "."))
    except ValueError:
        return None


def build_measurement(
    device: str,
    captured_at: str,
    manual_rank: int | None = None,
    manual_source: str = "browser_google_tr",
    manual_url: str | None = None,
) -> dict[str, str]:
    if manual_rank is not None:
        organic: list[str] = []
        source = manual_source
        rank = manual_rank
        target_url = manual_url or f"https://{TARGET_DOMAIN}/"
        competitor_rank = 1
    else:
        organic, source = collect_organic(device)
        rank, target_url = find_rank(organic)
        competitor_rank = None
    if competitor_rank is None:
        for index, url in enumerate(organic, start=1):
            if PRIMARY_COMPETITOR in extract_domain(url):
                competitor_rank = index
                break

    if manual_rank is not None:
        top_domains = [PRIMARY_COMPETITOR, "ledfon.com", TARGET_DOMAIN, "ledincloud.com", "sahibinden.com"]
    else:
        top_domains = [extract_domain(url) for url in organic[:5]]
    rank_text = str(rank) if rank is not None else "blocked"
    notes = f"Top5={','.join(top_domains)}; organic_count={len(organic)}"
    if source == "google_blocked_vm":
        notes += "; Google organic blocked — SERPER_API_KEY veya --rank-mobile/--rank-desktop gerekli"

    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": target_url or f"https://{TARGET_DOMAIN}/",
        "rank_position": rank_text,
        "serp_features": "",
        "primary_competitor": PRIMARY_COMPETITOR,
        "competitor_rank": str(competitor_rank) if competitor_rank is not None else "",
        "source": source,
        "notes": notes,
    }


def update_weekly_monitoring(measurements: list[dict[str, str]], captured_at: str) -> Path:
    path = weekly_monitoring_path(captured_at)
    previous = previous_led_ekran_rows(before_capture=captured_at)
    history_lines = []
    for row in previous[-5:]:
        history_lines.append(
            f"- {row['captured_at_utc']} | {row['device']} | "
            f"rank={row['rank_position']} | source={row['source']}"
        )

    mobile = next((row for row in measurements if row["device"] == "mobile"), None)
    desktop = next((row for row in measurements if row["device"] == "desktop"), None)
    mobile_rank = parse_position(mobile["rank_position"]) if mobile else None
    desktop_rank = parse_position(desktop["rank_position"]) if desktop else None

    delta_note = ""
    if previous and mobile_rank is not None:
        last_mobile = None
        for row in reversed(previous):
            if row["device"] == "mobile":
                last_mobile = parse_position(row["rank_position"])
                if last_mobile is not None:
                    break
        if last_mobile is not None:
            change = last_mobile - mobile_rank
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            delta_note = f"Mobil Δ (önceki {last_mobile:g}): {direction} {abs(change):g}"

    lines = [
        f"# Haftalık SEO İzleme — {captured_at[:10]}",
        "",
        "## SERP — `led ekran` (Google TR)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak |",
        "|---|---:|---|---|",
    ]
    for row in measurements:
        lines.append(
            f"| {row['device']} | {row['rank_position']} | {row['target_url']} | {row['source']} |"
        )

    lines.extend(
        [
            "",
            f"- Ölçüm zamanı (UTC): `{captured_at}`",
            f"- Birincil rakip: `{PRIMARY_COMPETITOR}` "
            f"(sıra: {mobile.get('competitor_rank', '—') if mobile else '—'})",
        ]
    )
    if delta_note:
        lines.append(f"- Haftalık değişim: {delta_note}")
    if history_lines:
        lines.extend(["", "## Önceki ölçümler", ""] + history_lines)

    lines.extend(
        [
            "",
            "## Komut",
            "",
            "```bash",
            "python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
            "",
            "## Sonraki hafta",
            "",
            "- `SERP-BASELINE.csv` trendini kontrol et",
            "- GSC Performance export ile avg_position çapraz doğrula",
            "- `SERPER_API_KEY` tanımlanırsa otomatik Google organic ölçümü güvenilir olur",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Haftalık led ekran SERP ölçümü")
    parser.add_argument("--rank-mobile", type=int, help="Manuel mobil sıra (Google organic doğrulandıysa)")
    parser.add_argument("--rank-desktop", type=int, help="Manuel desktop sıra")
    parser.add_argument("--target-url", default=f"https://{TARGET_DOMAIN}/", help="Hedef URL")
    parser.add_argument(
        "--source",
        default="browser_google_tr",
        help="Manuel ölçüm kaynağı etiketi",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    captured_at = utc_now_iso()
    measurements = [
        build_measurement(
            "mobile",
            captured_at,
            manual_rank=args.rank_mobile,
            manual_source=args.source,
            manual_url=args.target_url,
        ),
        build_measurement(
            "desktop",
            captured_at,
            manual_rank=args.rank_desktop,
            manual_source=args.source,
            manual_url=args.target_url,
        ),
    ]
    appended = append_baseline_rows(measurements)
    weekly_path = update_weekly_monitoring(measurements, captured_at)

    for row in measurements:
        print(
            f"{row['device']}: rank={row['rank_position']} url={row['target_url']} source={row['source']}"
        )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
