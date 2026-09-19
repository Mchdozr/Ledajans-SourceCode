#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
GSC_SNAPSHOT = ROOT / "AGENT-HUB" / "DATA" / "gsc-queries-snapshot-2026-06-05.csv"

QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
PRIMARY_COMPETITOR = "ledfon.com"

CSV_FIELDS = [
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


def normalize_domain(url: str) -> str:
    host = urlparse(url if "://" in url else f"https://{url}").netloc or url
    return host.lower().removeprefix("www.")


def parse_google_cites(cites: list[str]) -> list[str]:
    domains: list[str] = []
    for cite in cites:
        cite = (cite or "").strip()
        if not cite.startswith("http"):
            continue
        domain = re.sub(r"^https?://", "", cite.split(" ")[0].split("›")[0]).rstrip("/")
        domains.append(domain.lower().removeprefix("www."))
    return domains


def rank_from_domains(domains: list[str], target: str = TARGET_DOMAIN) -> tuple[int | None, str | None]:
    target = target.lower().removeprefix("www.")
    for i, domain in enumerate(domains, 1):
        if target in domain:
            return i, f"https://{domain}/"
    return None, None


def fetch_serper(device: str) -> tuple[int | None, str | None, str, list[str]]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None, None, "", []
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
    organic = response.json().get("organic") or []
    domains = [normalize_domain(item.get("link", "")) for item in organic if item.get("link")]
    rank, url = rank_from_domains(domains)
    return rank, url, "serper_api", domains


def fetch_serpapi(device: str) -> tuple[int | None, str | None, str, list[str]]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None, None, "", []
    params = {
        "engine": "google",
        "q": QUERY,
        "google_domain": "google.com.tr",
        "gl": "tr",
        "hl": "tr",
        "num": 30,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    organic = response.json().get("organic_results") or []
    domains = [normalize_domain(item.get("link", "")) for item in organic if item.get("link")]
    rank, url = rank_from_domains(domains)
    return rank, url, "serpapi", domains


def fetch_playwright(device: str) -> tuple[int | None, str | None, str, list[str]]:
    from playwright.sync_api import sync_playwright

    ua_mobile = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    )
    ua_desktop = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="tr-TR",
            user_agent=ua_mobile if device == "mobile" else ua_desktop,
            viewport={"width": 412, "height": 915} if device == "mobile" else {"width": 1366, "height": 900},
            is_mobile=device == "mobile",
            has_touch=device == "mobile",
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9"},
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.goto(
            "https://www.google.com.tr/search?q=led+ekran&hl=tr&gl=tr&num=30",
            wait_until="domcontentloaded",
            timeout=90000,
        )
        page.wait_for_timeout(3000)
        for selector in ("button#L2AGLb", "button[aria-label='Tümünü kabul et']"):
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1500):
                    button.click()
                    page.wait_for_timeout(1500)
                    break
            except Exception:
                pass
        cites = page.eval_on_selector_all("div#search cite", "els => els.map(e => e.innerText)")
        domains = parse_google_cites(cites)
        rank, url = rank_from_domains(domains)
        browser.close()
    if rank is None:
        return None, None, "", domains
    return rank, url or TARGET_URL, "playwright_google", domains


def gsc_fallback_position() -> float | None:
    if not GSC_SNAPSHOT.exists():
        return None
    with GSC_SNAPSHOT.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("query", "").strip().lower() == QUERY:
                try:
                    return float(str(row.get("position", "")).replace(",", "."))
                except ValueError:
                    return None
    return None


def measure_device(device: str) -> dict[str, object]:
    sources = (fetch_serper, fetch_serpapi, fetch_playwright)
    rank: int | None = None
    url: str | None = None
    source = ""
    top_domains: list[str] = []
    notes: list[str] = []

    for fetcher in sources:
        try:
            candidate_rank, candidate_url, candidate_source, domains = fetcher(device)
        except Exception as exc:
            notes.append(f"{fetcher.__name__}_error={exc}")
            continue
        if candidate_rank is not None:
            rank = candidate_rank
            url = candidate_url or TARGET_URL
            source = candidate_source
            top_domains = domains
            break
        if domains and not top_domains:
            top_domains = domains

    if rank is None and device == "mobile":
        gsc_pos = gsc_fallback_position()
        if gsc_pos is not None:
            rank = gsc_pos
            url = TARGET_URL
            source = "gsc_snapshot_fallback"
            notes.append(
                f"Canlı mobil SERP alınamadı; son GSC avg_position={gsc_pos} ({GSC_SNAPSHOT.name})"
            )

    competitor_rank = 1 if top_domains and normalize_domain(top_domains[0]) == normalize_domain(PRIMARY_COMPETITOR) else (
        next((i for i, d in enumerate(top_domains, 1) if PRIMARY_COMPETITOR in d), "") if top_domains else ""
    )

    if top_domains:
        notes.append("top5=" + ",".join(top_domains[:5]))

    return {
        "device": device,
        "rank_position": rank if rank is not None else "N/A",
        "target_url": url or TARGET_URL,
        "source": source or "unavailable",
        "competitor_rank": competitor_rank,
        "notes": "; ".join(notes) if notes else "Google TR organic snapshot",
    }


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_row(captured_at: str, measurement: dict[str, object]) -> dict[str, str]:
    row = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": str(measurement["device"]),
        "search_engine": SEARCH_ENGINE,
        "target_url": str(measurement["target_url"]),
        "rank_position": str(measurement["rank_position"]),
        "serp_features": "",
        "primary_competitor": PRIMARY_COMPETITOR,
        "competitor_rank": str(measurement.get("competitor_rank", "")),
        "source": str(measurement["source"]),
        "notes": str(measurement["notes"]),
    }
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return row


def previous_led_ekran_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    matches = [row for row in rows if row.get("query", "").strip().lower() == QUERY]
    return sorted(matches, key=lambda row: row.get("captured_at_utc", ""))


def write_weekly_report(captured_at: str, measurements: list[dict[str, object]]) -> Path:
    date_label = captured_at[:10]
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_label}.md"
    prior_rows = previous_led_ekran_rows(read_baseline_rows())

    lines = [
        f"# Haftalık SEO İzleme — {date_label}",
        "",
        "## SERP — `led ekran` (Google TR)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak |",
        "|-------|-----:|-----------|--------|",
    ]
    for measurement in measurements:
        lines.append(
            f"| {measurement['device']} | {measurement['rank_position']} | "
            f"{measurement['target_url']} | {measurement['source']} |"
        )

    lines.extend(["", "### Önceki ölçümler (baseline)", ""])
    for row in prior_rows[-6:]:
        lines.append(
            f"- {row.get('captured_at_utc', '')} | {row.get('device', '')} | "
            f"sıra={row.get('rank_position', '')} | {row.get('source', '')}"
        )

    desktop = next((m for m in measurements if m["device"] == "desktop"), None)
    mobile = next((m for m in measurements if m["device"] == "mobile"), None)
    lines.extend(
        [
            "",
            "## Özet",
            "",
        ]
    )
    if desktop:
        lines.append(
            f"- **Desktop organic:** ledajans.com **{desktop['rank_position']}. sırada** "
            f"(`{desktop['source']}`)."
        )
    if mobile:
        lines.append(
            f"- **Mobile:** sıra **{mobile['rank_position']}** (`{mobile['source']}`)."
        )
    lines.extend(
        [
            f"- Ölçüm zamanı (UTC): `{captured_at}`",
            "- Kayıt: `AGENT-HUB/SERP-BASELINE.csv` yeni satırlar eklendi.",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    measurements = [measure_device(device) for device in ("desktop", "mobile")]
    appended: list[dict[str, str]] = []
    for measurement in measurements:
        appended.append(append_baseline_row(captured_at, measurement))
    report_path = write_weekly_report(captured_at, measurements)

    for measurement in measurements:
        print(
            f"{measurement['device']}: rank={measurement['rank_position']} "
            f"source={measurement['source']}"
        )
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)} rows_added={len(appended)}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
