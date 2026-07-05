#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
GSC_QUERIES_PATH = ROOT / "AGENT-HUB" / "DATA" / "gsc-performance-2026-06-05" / "Sorgular.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_HOST = "ledajans.com"
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def gsc_avg_position(query: str) -> str | None:
    rows = read_csv_rows(GSC_QUERIES_PATH)
    for row in rows:
        key = row.get("En çok yapılan sorgular", "").strip().lower()
        if key == query.lower():
            return row.get("Pozisyon", "").strip() or None
    return None


def fetch_serper(query: str, device: str) -> dict | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = json.dumps({"q": query, "gl": "tr", "hl": "tr", "num": 30}).encode("utf-8")
    request = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    organic = data.get("organic", [])
    rank = target_url = competitor_url = competitor_rank = None
    for index, item in enumerate(organic, start=1):
        link = item.get("link", "")
        if TARGET_HOST in link and rank is None:
            rank = index
            target_url = link
        if competitor_url is None and PRIMARY_COMPETITOR in link:
            competitor_url = link
            competitor_rank = index
    return {
        "rank": rank,
        "target_url": target_url,
        "competitor_rank": competitor_rank,
        "organic_count": len(organic),
        "source": "serper_api",
        "notes": f"Organic results={len(organic)}",
        "blocked": False,
    }


def fetch_serpapi(query: str, device: str) -> dict | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "hl": "tr",
            "gl": "tr",
            "num": 30,
            "device": device,
            "api_key": api_key,
        }
    )
    with urllib.request.urlopen(f"https://serpapi.com/search.json?{params}", timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    organic = data.get("organic_results", [])
    rank = target_url = competitor_rank = None
    for index, item in enumerate(organic, start=1):
        link = item.get("link", "")
        if TARGET_HOST in link and rank is None:
            rank = index
            target_url = link
        if competitor_rank is None and PRIMARY_COMPETITOR in link:
            competitor_rank = index
    return {
        "rank": rank,
        "target_url": target_url,
        "competitor_rank": competitor_rank,
        "organic_count": len(organic),
        "source": "serpapi",
        "notes": f"Organic results={len(organic)}",
        "blocked": False,
    }


def fetch_playwright_google(query: str, device: str) -> dict:
    mobile_literal = "True" if device == "mobile" else "False"
    script = f"""
import json
from playwright.sync_api import sync_playwright

def run():
    mobile = {mobile_literal}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                if mobile
                else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={{"width": 412, "height": 915}} if mobile else {{"width": 1366, "height": 768}},
            is_mobile=mobile,
            has_touch=mobile,
            extra_http_headers={{"Accept-Language": "tr-TR,tr;q=0.9"}},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}})"
        )
        page = context.new_page()
        page.goto("https://www.google.com/?hl=tr&gl=tr", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)
        for selector in ["button:has-text('Tümünü kabul et')", "#L2AGLb"]:
            try:
                button = page.locator(selector).first
                if button.count():
                    button.click(timeout=2000)
                    page.wait_for_timeout(800)
                    break
            except Exception:
                pass
        page.goto(
            "https://www.google.com/search?q={urllib.parse.quote_plus(query)}&hl=tr&gl=tr&num=30",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        page.wait_for_timeout(4000)
        html = page.content().lower()
        links = page.eval_on_selector_all("div#search a:has(h3)", "els => els.map(e => e.href)")
        organic = []
        seen = set()
        for link in links:
            if not link or not link.startswith("http") or "google." in link or link in seen:
                continue
            seen.add(link)
            organic.append(link)
        rank = target_url = competitor_rank = None
        for index, link in enumerate(organic, start=1):
            if "{TARGET_HOST}" in link and rank is None:
                rank = index
                target_url = link
            if competitor_rank is None and "{PRIMARY_COMPETITOR}" in link:
                competitor_rank = index
        blocked = any(token in html for token in ["unusual traffic", "captcha", "/sorry/"])
        browser.close()
        return {{
            "rank": rank,
            "target_url": target_url,
            "competitor_rank": competitor_rank,
            "organic_count": len(organic),
            "blocked": blocked,
            "top5": organic[:5],
        }}

print(json.dumps(run(), ensure_ascii=False))
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "rank": None,
            "target_url": None,
            "competitor_rank": None,
            "organic_count": 0,
            "blocked": True,
            "source": "playwright_google",
            "notes": f"Playwright error: {proc.stderr.strip()[:180]}",
        }
    payload = json.loads(proc.stdout.strip() or "{}")
    notes = f"Organic results={payload.get('organic_count', 0)}"
    if payload.get("blocked"):
        notes += "; Google captcha/block"
    if payload.get("top5"):
        notes += f"; top1={payload['top5'][0]}"
    return {
        "rank": payload.get("rank"),
        "target_url": payload.get("target_url"),
        "competitor_rank": payload.get("competitor_rank"),
        "organic_count": payload.get("organic_count", 0),
        "blocked": bool(payload.get("blocked")),
        "source": "playwright_google",
        "notes": notes,
    }


def measure_device(query: str, device: str) -> dict:
    for fetcher in (fetch_serper, fetch_serpapi):
        try:
            result = fetcher(query, device)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
            result = None
        if result and result.get("rank") is not None:
            return result

    live = fetch_playwright_google(query, device)
    if live.get("rank") is not None:
        return live

    gsc_position = gsc_avg_position(query)
    if live.get("blocked") and gsc_position:
        return {
            "rank": gsc_position,
            "target_url": "https://ledajans.com/",
            "competitor_rank": live.get("competitor_rank"),
            "organic_count": live.get("organic_count", 0),
            "blocked": True,
            "source": "gsc_reference_fallback",
            "notes": (
                f"Live Google {device} blocked; GSC avg_position={gsc_position} "
                f"(export 2026-06-05). {live.get('notes', '')}"
            ),
        }

    if live.get("organic_count", 0) >= 5 and live.get("rank") is None:
        return {
            **live,
            "rank": "not_found",
            "target_url": "",
            "notes": live.get("notes", "") + "; ledajans.com not in top organic set",
        }

    if live.get("blocked"):
        return {
            **live,
            "rank": "blocked",
            "target_url": "",
            "notes": live.get("notes", "") + "; set SERPER_API_KEY for reliable mobile capture",
        }

    return {
        **live,
        "rank": live.get("rank") if live.get("rank") is not None else "not_found",
        "target_url": live.get("target_url") or "",
    }


def latest_baseline_for(query: str, device: str) -> dict[str, str] | None:
    rows = [row for row in read_csv_rows(BASELINE_PATH) if row.get("query", "").lower() == query.lower()]
    device_rows = [row for row in rows if row.get("device") == device]
    if not device_rows:
        return None
    return sorted(device_rows, key=lambda row: row.get("captured_at_utc", ""), reverse=True)[0]


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    existing = read_csv_rows(BASELINE_PATH)
    existing_keys = {
        (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        for row in existing
    }
    to_append = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in existing_keys
    ]
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})
    return len(to_append)


def format_delta(current: str | int | float | None, previous: str | None) -> str:
    if current is None or previous is None:
        return "n/a"
    if str(current) in {"blocked", "not_found", "pending"} or str(previous) in {"blocked", "not_found", "pending", "top3", "top5", "top10", "top20"}:
        return f"{previous} → {current}"
    try:
        cur = float(current)
        prev = float(previous)
    except ValueError:
        return f"{previous} → {current}"
    diff = prev - cur
    if diff > 0:
        return f"↑ {diff:.2f} (daha iyi)"
    if diff < 0:
        return f"↓ {abs(diff):.2f} (kayıp)"
    return "stabil"


def write_weekly_report(captured_at: str, measurements: list[dict[str, str]]) -> Path:
    report_date = captured_at[:10]
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## Özet",
        "",
    ]
    desktop_row = next((row for row in measurements if row["device"] == "desktop"), None)
    mobile_row = next((row for row in measurements if row["device"] == "mobile"), None)
    if desktop_row:
        lines.append(
            f"- **Google desktop (canlı organic):** {desktop_row['rank_position']}. sıra — "
            f"`{desktop_row['target_url'] or '—'}`"
        )
    if mobile_row:
        mobile_note = (
            "canlı ölçüm engellendi; GSC ortalama pozisyon referansı"
            if mobile_row["source"] == "gsc_reference_fallback"
            else "canlı organic"
        )
        lines.append(
            f"- **Google mobile:** {mobile_row['rank_position']} ({mobile_note})"
        )
    lines.extend(["", "## SERP — led ekran", "", "| Cihaz | Sıra | Hedef URL | Kaynak | Önceki | Değişim |", "|---|---:|---|---|---|---|"])
    for row in measurements:
        previous = latest_baseline_for(QUERY, row["device"])
        prev_rank = previous.get("rank_position") if previous else None
        if previous and previous.get("captured_at_utc", "")[:10] == captured_at[:10]:
            prev_rows = [
                item
                for item in read_csv_rows(BASELINE_PATH)
                if item.get("query", "").lower() == QUERY.lower()
                and item.get("device") == row["device"]
                and item.get("captured_at_utc", "") < captured_at
            ]
            prev_rank = sorted(prev_rows, key=lambda item: item.get("captured_at_utc", ""), reverse=True)[0].get("rank_position") if prev_rows else None
        lines.append(
            f"| {row['device']} | {row['rank_position']} | {row['target_url'] or '—'} | "
            f"{row['source']} | {prev_rank or '—'} | {format_delta(row['rank_position'], prev_rank)} |"
        )

    lines.extend(
        [
            "",
            "## Notlar",
            "",
        ]
    )
    for row in measurements:
        lines.append(f"- **{row['device']}**: {row['notes']}")
    lines.extend(
        [
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "Güvenilir mobil ölçüm için ortam değişkeni: `SERPER_API_KEY`.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    measurements: list[dict[str, str]] = []
    for device in ("mobile", "desktop"):
        result = measure_device(QUERY, device)
        measurements.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": result.get("target_url") or "",
                "rank_position": str(result.get("rank") if result.get("rank") is not None else "not_found"),
                "serp_features": "",
                "primary_competitor": PRIMARY_COMPETITOR,
                "competitor_rank": str(result.get("competitor_rank") or ""),
                "source": result.get("source", "unknown"),
                "notes": result.get("notes", ""),
            }
        )

    appended = append_baseline_rows(measurements)
    report_path = write_weekly_report(captured_at, measurements)
    print(f"captured_at={captured_at}")
    for row in measurements:
        print(f"{row['device']}: rank={row['rank_position']} source={row['source']}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
