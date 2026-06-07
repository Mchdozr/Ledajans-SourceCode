#!/usr/bin/env python3
"""Haftalık SERP snapshot: led ekran → ledajans.com sırası.

Google CAPTCHA engellerse GSC export ve Brave TR proxy ile yedekler.
Her çalışmada AGENT-HUB/SERP-BASELINE.csv ve haftalık özet dosyasını günceller.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
DATA_DIR = ROOT / "AGENT-HUB" / "DATA"
REPORTS_DIR = ROOT / "AGENT-HUB" / "REPORTS"

DEFAULT_QUERY = "led ekran"
DEFAULT_TARGET = "https://ledajans.com/"
LOCALE = "tr-TR"
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline_fields() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    fields = read_baseline_fields()
    existing: set[tuple[str, str, str, str, str]] = set()
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            existing.add(
                (
                    row.get("captured_at_utc", ""),
                    row.get("query", "").lower(),
                    row.get("device", ""),
                    row.get("search_engine", ""),
                    row.get("source", ""),
                )
            )

    to_write: list[dict[str, str]] = []
    for row in rows:
        key = (
            row["captured_at_utc"],
            row["query"].lower(),
            row["device"],
            row["search_engine"],
            row["source"],
        )
        if key in existing:
            continue
        to_write.append({field: row.get(field, "") for field in fields})

    if not to_write:
        return 0

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for row in to_write:
            writer.writerow(row)
    return len(to_write)


def try_google_playwright(query: str) -> tuple[str | int, str, list[str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "blocked", "playwright_missing", []

    def parse_links(html: str) -> list[str]:
        links: list[str] = []
        for match in re.finditer(r'href="(/url\?q=[^"]+|https?://[^"]+)"', html):
            href = match.group(1)
            if href.startswith("/url?q="):
                url = urllib.parse.unquote(href.split("/url?q=")[1].split("&")[0])
            else:
                url = href
            if not url.startswith("http"):
                continue
            if any(token in url for token in ("google.", "gstatic", "webcache", "accounts.google")):
                continue
            links.append(url)
        seen: set[str] = set()
        ordered: list[str] = []
        for url in links:
            if url in seen:
                continue
            seen.add(url)
            ordered.append(url)
        return ordered

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            locale="tr-TR",
            user_agent=MOBILE_UA,
            viewport={"width": 412, "height": 915},
        )
        page = context.new_page()
        page.goto(
            "https://www.google.com/search?"
            + urllib.parse.urlencode({"q": query, "hl": "tr", "gl": "tr", "num": "50", "pws": "0"}),
            wait_until="networkidle",
            timeout=45000,
        )
        page.wait_for_timeout(2500)
        html = page.content()
        browser.close()

    if "recaptcha" in html.lower() or "sıra dışı bir trafik" in html.lower():
        return "blocked", "google_captcha_blocked", []

    links = parse_links(html)
    for index, url in enumerate(links, start=1):
        if "ledajans.com" in url:
            return index, "google_live_mobile", links[:10]
    return "not_found", "google_live_mobile", links[:10]


def try_bing_proxy(query: str) -> tuple[str | int, str, list[str]]:
    url = "https://www.bing.com/search?" + urllib.parse.urlencode(
        {"q": query, "setlang": "tr", "cc": "TR", "count": "50"}
    )
    try:
        response = requests.get(
            url,
            headers={"User-Agent": MOBILE_UA, "Accept-Language": "tr-TR,tr;q=0.9"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return "blocked", "", [f"bing_error={exc}"]

    blocks = re.findall(r'<li class="b_algo"[\s\S]*?</li>', response.text)
    urls: list[str] = []
    for block in blocks:
        match = re.search(r'href="(https?://[^"]+)"', block)
        if match:
            urls.append(match.group(1))

    for index, candidate in enumerate(urls, start=1):
        if "ledajans.com" in candidate:
            return index, candidate, urls[:10]
    return "not_found", "", urls[:10]


def try_brave_proxy(query: str) -> tuple[str | int, str, list[str]]:
    url = "https://search.brave.com/search?" + urllib.parse.urlencode(
        {"q": query, "country": "TR", "lang": "tr"}
    )
    try:
        response = requests.get(
            url,
            headers={"User-Agent": MOBILE_UA, "Accept-Language": "tr-TR,tr;q=0.9"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return "blocked", "", [f"brave_error={exc}"]
    html = response.text
    urls: list[str] = []
    for match in re.finditer(r'href="(https?://[^"]+)"', html):
        candidate = match.group(1)
        if "brave.com" in candidate or "google.com/goto" in candidate:
            continue
        if candidate not in urls:
            urls.append(candidate)

    for index, candidate in enumerate(urls, start=1):
        if "ledajans.com" in candidate:
            return index, candidate, urls[:10]
    return "not_found", "", urls[:10]


def latest_gsc_position(query: str) -> tuple[str | None, str, str]:
    folders = sorted(DATA_DIR.glob("gsc-performance-*"), reverse=True)
    for folder in folders:
        queries_path = folder / "Sorgular.csv"
        if not queries_path.exists():
            continue
        with queries_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                name = (row.get("En çok yapılan sorgular") or row.get("query") or "").strip().lower()
                if name != query.lower():
                    continue
                position = (row.get("Pozisyon") or row.get("position") or "").strip()
                clicks = (row.get("Tıklamalar") or row.get("clicks") or "").strip()
                impressions = (row.get("Gösterimler") or row.get("impressions") or "").strip()
                ctr = (row.get("TO") or row.get("ctr") or "").strip()
                source = f"gsc_performance_{folder.name.replace('gsc-performance-', '')}"
                notes = f"Clicks={clicks}; Impressions={impressions}; CTR={ctr}; avg_position={position}"
                return position, source, notes
    return None, "", ""


def build_row(
    captured_at: str,
    query: str,
    device: str,
    search_engine: str,
    target_url: str,
    rank_position: str | int,
    source: str,
    notes: str,
) -> dict[str, str]:
    return {
        "captured_at_utc": captured_at,
        "query": query,
        "locale": LOCALE,
        "device": device,
        "search_engine": search_engine,
        "target_url": target_url,
        "rank_position": str(rank_position),
        "serp_features": "",
        "primary_competitor": "",
        "competitor_rank": "",
        "source": source,
        "notes": notes,
    }


def update_weekly_summary(
    captured_at: str,
    query: str,
    google_rank: str | int,
    gsc_rank: str | None,
    proxy_rank: str | int,
    proxy_url: str,
    appended: int,
) -> Path:
    date_label = captured_at[:10]
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_label}.md"
    previous = path.read_text(encoding="utf-8") if path.exists() else ""

    lines = [
        f"# Haftalık SEO İzleme — {date_label}",
        "",
        "## SERP snapshot (`led ekran` → ledajans.com)",
        f"- Zaman (UTC): `{captured_at}`",
        f"- Google canlı (mobile, tr-TR): **{google_rank}**",
    ]
    if gsc_rank:
        lines.append(f"- GSC ortalama pozisyon (son export): **{gsc_rank}**")
    if proxy_rank not in ("not_found", "blocked", ""):
        lines.append(
            f"- Organik proxy (Google CAPTCHA yedek): **{proxy_rank}. sıra** — `{proxy_url or DEFAULT_TARGET}`"
        )
    lines.extend(
        [
            f"- `SERP-BASELINE.csv` eklenen satır: **{appended}**",
            "",
            "## Komut",
            "```bash",
            "python3 scripts/check-serp-rank.py",
            "```",
            "",
        ]
    )

    if "## Smoke test" in previous:
        tail = previous.split("## Smoke test", 1)[1]
        lines.append("## Smoke test" + tail)
    else:
        lines.extend(
            [
                "## Smoke test",
                "- Komut: `powershell -File scripts/run-weekly-seo-check.ps1`",
                "- Sonuç: cron otomasyonu — manuel smoke test bekliyor",
                "",
                "## Sonraki hafta",
                "```bash",
                "python3 scripts/check-serp-rank.py",
                "powershell -File scripts/run-weekly-seo-check.ps1",
                "```",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_report(
    captured_at: str,
    query: str,
    google_rank: str | int,
    gsc_rank: str | None,
    proxy_rank: str | int,
    proxy_url: str,
    top_proxy: list[str],
) -> Path:
    date_label = captured_at[:10]
    path = REPORTS_DIR / f"{date_label}-serp-rank-check.md"
    lines = [
        f"# SERP Rank Check — {date_label}",
        "",
        f"- Sorgu: `{query}`",
        f"- Hedef: `{DEFAULT_TARGET}`",
        f"- Zaman (UTC): `{captured_at}`",
        "",
        "## Sonuç",
        "",
        f"| Kaynak | Sıra | Not |",
        f"|---|---:|---|",
        f"| Google (mobile, tr-TR) | {google_rank} | Canlı tarama |",
    ]
    if gsc_rank:
        lines.append(f"| GSC avg position | {gsc_rank} | Son performance export |")
    if proxy_rank not in ("not_found", "blocked", ""):
        lines.append(f"| Organik proxy | {proxy_rank} | `{proxy_url}` |")

    if top_proxy and not str(top_proxy[0]).startswith("brave_error"):
        lines.extend(["", "## Organik proxy — ilk 10", ""])
        for index, url in enumerate(top_proxy, start=1):
            mark = " ← LEDAJANS" if "ledajans.com" in url else ""
            lines.append(f"{index}. {url}{mark}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP baseline snapshot for led ekran")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--target-url", default=DEFAULT_TARGET)
    parser.add_argument("--skip-google", action="store_true")
    args = parser.parse_args()

    captured_at = utc_now_iso()
    rows: list[dict[str, str]] = []

    google_rank: str | int = "skipped" if args.skip_google else "blocked"
    if not args.skip_google:
        google_rank, google_source, _ = try_google_playwright(args.query)
        rows.append(
            build_row(
                captured_at,
                args.query,
                "mobile",
                "google",
                args.target_url,
                google_rank,
                google_source,
                "Google mobile tr-TR; CAPTCHA engeli varsa blocked döner",
            )
        )

    gsc_rank, gsc_source, gsc_notes = latest_gsc_position(args.query)
    if gsc_rank:
        rows.append(
            build_row(
                captured_at,
                args.query,
                "mobile",
                "google",
                args.target_url,
                gsc_rank,
                gsc_source,
                gsc_notes,
            )
        )

    brave_rank, brave_url, top_brave = try_brave_proxy(args.query)
    if brave_rank in ("not_found", "blocked"):
        bing_rank, bing_url, top_bing = try_bing_proxy(args.query)
        proxy_rank, proxy_url, proxy_top = (
            (bing_rank, bing_url, top_bing)
            if bing_rank not in ("not_found", "blocked")
            else (brave_rank, brave_url, top_brave)
        )
        proxy_engine = "bing" if bing_rank not in ("not_found", "blocked") else "brave"
        proxy_source = (
            "bing_organic_proxy_tr"
            if proxy_engine == "bing"
            else "brave_organic_proxy_tr"
        )
    else:
        proxy_rank, proxy_url, proxy_top = brave_rank, brave_url, top_brave
        proxy_engine = "brave"
        proxy_source = "brave_organic_proxy_tr"

    if proxy_rank not in ("not_found", "blocked"):
        rows.append(
            build_row(
                captured_at,
                args.query,
                "mobile",
                proxy_engine,
                proxy_url or args.target_url,
                proxy_rank,
                proxy_source,
                "Google CAPTCHA yedek; TR organik proxy — kesin Google sırası değildir",
            )
        )

    appended = append_baseline_rows(rows)
    weekly_path = update_weekly_summary(
        captured_at,
        args.query,
        google_rank,
        gsc_rank,
        proxy_rank,
        proxy_url,
        appended,
    )
    report_path = write_report(
        captured_at,
        args.query,
        google_rank,
        gsc_rank,
        proxy_rank,
        proxy_url,
        proxy_top,
    )

    print(f"query={args.query}")
    print(f"google_rank={google_rank}")
    print(f"gsc_rank={gsc_rank or 'N/A'}")
    print(f"proxy_rank={proxy_rank}")
    print(f"baseline_appended={appended}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    print(f"report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
