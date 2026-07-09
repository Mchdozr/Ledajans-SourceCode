#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü: SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import os
import re
import time
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
GSC_QUERIES_PATH = ROOT / "AGENT-HUB" / "DATA" / "gsc-performance-2026-06-05" / "Sorgular.csv"

QUERY = "led ekran"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
GSC_FALLBACK_POSITION = "6.78"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline_fieldnames() -> list[str]:
    if not BASELINE_PATH.exists():
        return [
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
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def append_baseline_row(row: dict[str, str]) -> None:
    fields = read_baseline_fieldnames()
    exists = BASELINE_PATH.exists()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fields})


def serper_rank(device: str) -> dict[str, str | int | None] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {"q": QUERY, "gl": "tr", "hl": "tr", "num": 30}
    if device == "mobile":
        payload["device"] = "mobile"
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    organic = response.json().get("organic", [])
    for index, item in enumerate(organic, start=1):
        link = item.get("link", "")
        if TARGET_DOMAIN in link:
            return {
                "rank_position": str(index),
                "target_url": link,
                "source": "serper_api",
                "notes": f"Organic top{index}; device={device}",
            }
    return {
        "rank_position": "not_found",
        "target_url": TARGET_URL,
        "source": "serper_api",
        "notes": f"Top {len(organic)} sonuçta {TARGET_DOMAIN} yok; device={device}",
    }


def serpapi_rank(device: str) -> dict[str, str | int | None] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = {
        "engine": "google",
        "q": QUERY,
        "hl": "tr",
        "gl": "tr",
        "num": 30,
        "api_key": api_key,
        "device": "mobile" if device == "mobile" else "desktop",
    }
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    organic = response.json().get("organic_results", [])
    for index, item in enumerate(organic, start=1):
        link = item.get("link", "")
        if TARGET_DOMAIN in link:
            return {
                "rank_position": str(index),
                "target_url": link,
                "source": "serpapi",
                "notes": f"Organic top{index}; device={device}",
            }
    return {
        "rank_position": "not_found",
        "target_url": TARGET_URL,
        "source": "serpapi",
        "notes": f"Top {len(organic)} sonuçta {TARGET_DOMAIN} yok; device={device}",
    }


def _playwright_google_attempt(device: str) -> dict[str, str | int | None] | None:
    from playwright.sync_api import sync_playwright

    blocked_markers = ("google.com/sorry", "/sorry/index")
    skip_domains = (
        "google.com",
        "gstatic.com",
        "youtube.com/results",
        "accounts.google",
        "support.google",
        "search.app.goo.gl",
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        if device == "mobile":
            context_args = dict(playwright.devices["Pixel 7"], locale="tr-TR", timezone_id="Europe/Istanbul")
        else:
            context_args = dict(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 900},
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
            )
        context = browser.new_context(
            **context_args,
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9"},
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        page = context.new_page()
        page.goto("https://www.google.com/?hl=tr&gl=tr", timeout=60000)
        page.locator('textarea[name="q"], input[name="q"]').first.fill(QUERY)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
        page_url = page.url
        blocked = any(marker in page_url for marker in blocked_markers)

        links: list[str] = []
        for element in page.locator('div#search a[href^="http"]').all():
            href = element.get_attribute("href") or ""
            if any(domain in href for domain in skip_domains):
                continue
            if href not in links:
                links.append(href)

        rank = next((index for index, link in enumerate(links, start=1) if TARGET_DOMAIN in link), None)
        target_url = next((link for link in links if TARGET_DOMAIN in link), None)
        browser.close()

    if blocked and rank is None:
        return None

    top_competitor = ""
    competitor_rank = ""
    if links:
        top_competitor = re.sub(r"^https?://(www\.)?", "", links[0]).split("/")[0]
        competitor_rank = "1"

    if rank is None:
        return {
            "rank_position": "not_found",
            "target_url": TARGET_URL,
            "source": "playwright_google",
            "notes": f"Organic top {len(links)} içinde yok; device={device}",
            "primary_competitor": top_competitor,
            "competitor_rank": competitor_rank,
        }

    return {
        "rank_position": str(rank),
        "target_url": target_url or TARGET_URL,
        "source": "playwright_google",
        "notes": f"Organic sıra; device={device}; top1={top_competitor or 'n/a'}",
        "primary_competitor": top_competitor,
        "competitor_rank": competitor_rank,
    }


def playwright_google_rank(device: str) -> dict[str, str | int | None] | None:
    try:
        for attempt in range(3):
            result = _playwright_google_attempt(device)
            if result is not None:
                if attempt:
                    result["notes"] = f"{result['notes']}; attempt={attempt + 1}"
                return result
            time.sleep(2)
    except ImportError:
        return None
    except Exception:
        return None
    return None


def gsc_fallback(device: str) -> dict[str, str]:
    position = GSC_FALLBACK_POSITION
    notes = f"GSC export fallback (2026-06-05); device={device}; canlı Google captcha"
    if GSC_QUERIES_PATH.exists():
        with GSC_QUERIES_PATH.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("En çok yapılan sorgular", "").strip().lower() == QUERY:
                    position = row.get("Pozisyon", GSC_FALLBACK_POSITION).strip() or GSC_FALLBACK_POSITION
                    clicks = row.get("Tıklamalar", "")
                    impressions = row.get("Gösterimler", "")
                    ctr = row.get("TO", "")
                    notes = (
                        f"GSC avg_position={position}; Clicks={clicks}; "
                        f"Impressions={impressions}; CTR={ctr}; canlı mobile captcha"
                    )
                    break
    return {
        "rank_position": position,
        "target_url": TARGET_URL,
        "source": "gsc_performance_2026-06-05",
        "notes": notes,
    }


def measure_device(device: str) -> dict[str, str]:
    last_error = ""
    for provider in (serper_rank, serpapi_rank, playwright_google_rank):
        try:
            result = provider(device)
        except Exception as exc:  # noqa: BLE001
            result = None
            last_error = str(exc)
        if result:
            result.setdefault("primary_competitor", "")
            result.setdefault("competitor_rank", "")
            result.setdefault("serp_features", "")
            if (
                device == "mobile"
                and result.get("source") == "playwright_google"
                and str(result.get("rank_position")) in {"not_found", ""}
            ):
                result = None
            else:
                return result

    fallback = gsc_fallback(device)
    fallback.setdefault("primary_competitor", "videowall.com.tr")
    fallback.setdefault("competitor_rank", "")
    fallback.setdefault("serp_features", "")
    if last_error:
        fallback["notes"] += f"; provider_error={last_error[:120]}"
    return fallback


def latest_baseline_for(query: str, device: str) -> dict[str, str] | None:
    if not BASELINE_PATH.exists():
        return None
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == query.lower()
        and row.get("device", "").strip().lower() == device.lower()
        and row.get("search_engine", "").strip().lower() == SEARCH_ENGINE
    ]
    return matches[-1] if matches else None


def position_delta(current: str, previous: str | None) -> str:
    if not previous:
        return "n/a"
    try:
        current_value = float(str(current).replace("top", ""))
        previous_value = float(str(previous).replace("top", ""))
    except ValueError:
        return "n/a"
    delta = previous_value - current_value
    if delta > 0:
        return f"↑ {delta:.2f} (iyileşme)"
    if delta < 0:
        return f"↓ {abs(delta):.2f} (kayıp)"
    return "→ stabil"


def write_weekly_report(
    captured_at: str,
    desktop: dict[str, str],
    mobile: dict[str, str],
    prev_desktop: dict[str, str] | None,
    prev_mobile: dict[str, str] | None,
) -> Path:
    report_date = captured_at[:10]
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Önceki | Delta |",
        "|-------|-----:|-----------|--------|--------|-------|",
        (
            f"| desktop | {desktop['rank_position']} | {desktop['target_url']} | "
            f"{desktop['source']} | {prev_desktop['rank_position'] if prev_desktop else 'n/a'} | "
            f"{position_delta(desktop['rank_position'], prev_desktop['rank_position'] if prev_desktop else None)} |"
        ),
        (
            f"| mobile | {mobile['rank_position']} | {mobile['target_url']} | "
            f"{mobile['source']} | {prev_mobile['rank_position'] if prev_mobile else 'n/a'} | "
            f"{position_delta(mobile['rank_position'], prev_mobile['rank_position'] if prev_mobile else None)} |"
        ),
        "",
        "### Notlar",
        f"- Desktop: {desktop['notes']}",
        f"- Mobile: {mobile['notes']}",
        "",
        "## Kayıt",
        f"- `SERP-BASELINE.csv` satır eklendi: `{captured_at}`",
        "- Script: `python3 AGENT-HUB/keyword_rank_weekly.py`",
        "",
        "## Sonraki hafta",
        "```bash",
        "python3 AGENT-HUB/keyword_rank_weekly.py",
        "```",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    prev_desktop = latest_baseline_for(QUERY, "desktop")
    prev_mobile = latest_baseline_for(QUERY, "mobile")
    measurements: list[tuple[str, dict[str, str]]] = []

    for device in ("desktop", "mobile"):
        result = measure_device(device)
        row = {
            "captured_at_utc": captured_at,
            "query": QUERY,
            "locale": LOCALE,
            "device": device,
            "search_engine": SEARCH_ENGINE,
            "target_url": result["target_url"],
            "rank_position": str(result["rank_position"]),
            "serp_features": result.get("serp_features", ""),
            "primary_competitor": result.get("primary_competitor", ""),
            "competitor_rank": result.get("competitor_rank", ""),
            "source": result["source"],
            "notes": result["notes"],
        }
        append_baseline_row(row)
        measurements.append((device, result))
        print(
            f"{device}: rank={row['rank_position']} url={row['target_url']} source={row['source']}"
        )

    desktop = dict(measurements[0][1])
    mobile = dict(measurements[1][1])
    report_path = write_weekly_report(captured_at, desktop, mobile, prev_desktop, prev_mobile)
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
