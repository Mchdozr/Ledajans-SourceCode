#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"

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


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return BASELINE_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or BASELINE_FIELDS)
        return fields, list(reader)


def append_baseline_rows(rows: list[dict[str, str]], fields: list[str]) -> None:
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def domain_from_url(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def fetch_via_serper(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return [], ""
    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 20}
    if device == "mobile":
        payload["device"] = "mobile"
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    urls: list[str] = []
    for item in data.get("organic", []):
        link = item.get("link", "")
        if link:
            urls.append(link)
    return urls, "serper_api"


def fetch_via_serpapi(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return [], ""
    params = {
        "engine": "google",
        "q": query,
        "hl": "tr",
        "gl": "tr",
        "num": 20,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    urls = [item.get("link", "") for item in data.get("organic_results", []) if item.get("link")]
    return urls, "serpapi"


def accept_google_consent(page) -> None:
    for selector in (
        'button:has-text("Tümünü kabul et")',
        'button:has-text("Accept all")',
        "#L2AGLb",
    ):
        try:
            button = page.locator(selector).first
            if button.count() and button.is_visible(timeout=800):
                button.click()
                page.wait_for_timeout(800)
                return
        except Exception:
            continue


def extract_organic_urls(page) -> list[str]:
    seen_domains: set[str] = set()
    results: list[str] = []
    for anchor in page.query_selector_all("div#search a[href], div#rso a[href]"):
        href = anchor.get_attribute("href") or ""
        if href.startswith("/url?q="):
            url = parse_qs(urlparse(href).query).get("q", [""])[0]
        elif href.startswith("http"):
            url = href
        else:
            continue
        netloc = domain_from_url(url)
        if not netloc or "google." in netloc or "gstatic" in netloc:
            continue
        if netloc in seen_domains:
            continue
        seen_domains.add(netloc)
        results.append(url)
    return results


def fetch_via_playwright(query: str, device: str) -> tuple[list[str], str]:
    from playwright.sync_api import sync_playwright

    is_mobile = device == "mobile"
    if is_mobile:
        user_agent = (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        )
        viewport = {"width": 412, "height": 915}
    else:
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        viewport = {"width": 1366, "height": 900}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale=LOCALE,
            user_agent=user_agent,
            viewport=viewport,
            is_mobile=is_mobile,
            has_touch=is_mobile,
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9"},
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.goto("https://www.google.com/?hl=tr&gl=tr", timeout=60000)
        accept_google_consent(page)
        page.goto(
            f"https://www.google.com/search?q={query.replace(' ', '+')}&hl=tr&gl=tr&pws=0&num=20",
            timeout=60000,
        )
        page.wait_for_timeout(2500)
        urls = extract_organic_urls(page)
        context.close()
        browser.close()
    return urls, "playwright_google"


def resolve_rank(urls: list[str]) -> tuple[str | int, str, str]:
    competitor = urls[0] if urls else ""
    competitor_domain = domain_from_url(competitor) if competitor else ""
    for index, url in enumerate(urls, start=1):
        if TARGET_DOMAIN in urlparse(url).netloc:
            return index, url, competitor_domain
    return "not_found", TARGET_URL, competitor_domain


def latest_gsc_position(rows: list[dict[str, str]], query: str) -> str | None:
    pattern = re.compile(r"avg_position=([0-9.]+)")
    for row in reversed(rows):
        if row.get("query", "").lower() != query.lower():
            continue
        if not str(row.get("source", "")).startswith("gsc_"):
            continue
        match = pattern.search(row.get("notes", ""))
        if match:
            return match.group(1)
        if row.get("rank_position"):
            return str(row["rank_position"])
    return None


def fetch_rank(query: str, device: str) -> tuple[str | int, str, str, str, str]:
    providers = (fetch_via_serper, fetch_via_serpapi, fetch_via_playwright)
    last_error = ""
    for provider in providers:
        try:
            urls, source = provider(query, device)
            if urls:
                rank, target_url, competitor = resolve_rank(urls)
                notes = f"organic_top10={';'.join(domain_from_url(u) for u in urls[:10])}"
                return rank, target_url, competitor, source, notes
        except Exception as exc:
            last_error = str(exc)
            continue
    gsc_fallback = ""
    return "error", TARGET_URL, "", "unavailable", last_error or gsc_fallback


def build_measurement_rows(captured_at: str, existing_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    gsc_mobile = latest_gsc_position(existing_rows, QUERY)
    rows: list[dict[str, str]] = []
    for device in ("desktop", "mobile"):
        rank, target_url, competitor, source, notes = fetch_rank(QUERY, device)
        if rank == "error" and device == "mobile" and gsc_mobile:
            rank = gsc_mobile
            source = "gsc_fallback"
            notes = f"Canlı SERP başarısız; son GSC avg_position={gsc_mobile}"
        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": target_url,
                "rank_position": str(rank),
                "serp_features": "",
                "primary_competitor": competitor,
                "competitor_rank": "1" if competitor else "",
                "source": source,
                "notes": notes,
            }
        )
    return rows


def previous_led_ekran_snapshot(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("query", "").lower() != QUERY:
            continue
        device = row.get("device", "")
        if device and device not in latest:
            latest[device] = row
    return latest


def write_weekly_report(
    captured_at: str,
    new_rows: list[dict[str, str]],
    previous: dict[str, dict[str, str]],
) -> Path:
    report_date = captured_at[:10]
    report_path = HUB / f"WEEKLY-MONITORING-{report_date}.md"
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — `led ekran` (Google TR)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Rakip #1 |",
        "|---|---:|---|---|---|",
    ]
    for row in new_rows:
        lines.append(
            f"| {row['device']} | {row['rank_position']} | {row['target_url']} | "
            f"{row['source']} | {row['primary_competitor']} |"
        )

    lines.extend(["", "## Haftalık delta", ""])
    for row in new_rows:
        device = row["device"]
        prev = previous.get(device)
        if not prev:
            lines.append(f"- **{device}**: önceki kayıt yok → {row['rank_position']}")
            continue
        prev_rank = prev.get("rank_position", "N/A")
        curr_rank = row["rank_position"]
        if str(prev_rank).replace(".", "", 1).isdigit() and str(curr_rank).replace(".", "", 1).isdigit():
            delta = float(prev_rank) - float(curr_rank)
            direction = "↑ iyileşme" if delta > 0 else ("↓ düşüş" if delta < 0 else "→ stabil")
            lines.append(
                f"- **{device}**: {prev_rank} → {curr_rank} ({direction}, Δ={delta:+.2f}) "
                f"[{prev.get('captured_at_utc', '')[:10]}]"
            )
        else:
            lines.append(f"- **{device}**: {prev_rank} → {curr_rank}")

    lines.extend(
        [
            "",
            "## Kayıt",
            "",
            f"- Ölçüm UTC: `{captured_at}`",
            f"- CSV: `AGENT-HUB/SERP-BASELINE.csv` (+{len(new_rows)} satır)",
            "- Komut: `python3 AGENT-HUB/keyword_rank_weekly.py`",
            "",
            "## Not",
            "",
            "- Canlı organic sıra ile GSC `avg_position` farklı metriklerdir.",
            "- Mobil için `SERPER_API_KEY` ortam değişkeni önerilir (captcha riski).",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    fields, existing_rows = read_baseline_rows()
    new_rows = build_measurement_rows(captured_at, existing_rows)

    existing_keys = {
        (r["captured_at_utc"], r["query"].lower(), r["device"], r["source"]) for r in existing_rows
    }
    append_rows = [
        row
        for row in new_rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        not in existing_keys
    ]
    if append_rows:
        append_baseline_rows(append_rows, fields)

    previous = previous_led_ekran_snapshot(existing_rows)
    report_path = write_weekly_report(captured_at, new_rows, previous)

    for row in new_rows:
        print(f"{row['device']}: rank={row['rank_position']} source={row['source']}")
    print(f"baseline_appended={len(append_rows)}")
    print(f"report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
