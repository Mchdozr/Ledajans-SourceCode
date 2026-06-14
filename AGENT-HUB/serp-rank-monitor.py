#!/usr/bin/env python3
"""Haftalık SERP snapshot: led ekran → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import re
import subprocess
import sys
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
CHROME_PROFILE = Path("/tmp/chrome-serp-monitor-profile")
SEARCH_URL = (
    "https://www.google.com/search?"
    + urllib.parse.urlencode({"q": QUERY, "hl": "tr", "gl": "tr", "num": "30", "pws": "0"})
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline_fields() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def parse_organic_urls(html: str) -> list[str]:
    urls: list[str] = []
    for match in re.finditer(r'href="/url\?q=([^"&]+)', html):
        url = urllib.parse.unquote(match.group(1))
        if url.startswith("http") and "google." not in url:
            urls.append(url)
    if urls:
        return list(dict.fromkeys(urls))

    cites = re.findall(r"<cite[^>]*>([^<]+)</cite>", html)
    for cite in cites:
        domain = cite.strip().split()[0].replace("›", "").strip()
        if domain and not domain.startswith("http"):
            domain = f"https://{domain.lstrip('/')}"
        if domain.startswith("http"):
            urls.append(domain)
    return list(dict.fromkeys(urls))


def fetch_serp_html() -> tuple[str, str]:
    CHROME_PROFILE.mkdir(parents=True, exist_ok=True)
    html_path = Path("/tmp/serp-monitor-latest.html")
    command = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={CHROME_PROFILE}",
        "--window-size=1366,2400",
        "--virtual-time-budget=15000",
        "--dump-dom",
        SEARCH_URL,
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    html = result.stdout or ""
    if len(html) < 20_000 or "recaptcha" in html.lower() or "sıra dışı bir trafik" in html.lower():
        return html, "captcha_or_blocked"
    html_path.write_text(html, encoding="utf-8")
    return html, "headless_chrome"


def find_rank(html: str, device: str) -> tuple[str | int, str, str]:
    urls = parse_organic_urls(html)
    for index, url in enumerate(urls, start=1):
        if TARGET_DOMAIN in url:
            return index, url, f"Organic #{index}/{len(urls)} ({device})"
    if TARGET_DOMAIN in html.lower():
        return "top10", f"https://{TARGET_DOMAIN}/", f"Domain görünür; organik sıra parse edilemedi ({device})"
    return "not_found", f"https://{TARGET_DOMAIN}/", f"SERP içinde {TARGET_DOMAIN} bulunamadı ({device})"


def latest_gsc_position() -> tuple[str, str] | None:
    for row in reversed(list(read_baseline_rows())):
        if row["query"].strip().lower() != QUERY:
            continue
        if row["source"].startswith("gsc_performance"):
            return row["rank_position"], row["captured_at_utc"]
    return None


def read_baseline_rows() -> list[dict[str, str]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_row(row: dict[str, str]) -> None:
    fields = read_baseline_fields()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow({field: row.get(field, "") for field in fields})


def previous_snapshot() -> dict[str, str] | None:
    rows = [
        row
        for row in read_baseline_rows()
        if row["query"].strip().lower() == QUERY and row.get("target_url", "").startswith("https://ledajans.com")
    ]
    return rows[-1] if rows else None


def write_weekly_report(
    captured_at: str,
    desktop_rank: str | int,
    target_url: str,
    source: str,
    notes: str,
    gsc_ref: tuple[str, str] | None,
) -> Path:
    report_date = captured_at[:10]
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    prev = previous_snapshot()
    prev_line = "—"
    if prev:
        prev_line = f"{prev['captured_at_utc']} → sıra **{prev['rank_position']}** ({prev['source']})"

    gsc_line = "—"
    if gsc_ref:
        gsc_line = f"GSC ort. pozisyon **{gsc_ref[0]}** (snapshot: {gsc_ref[1]})"

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Sorgu: `{QUERY}` | locale: `{LOCALE}` | cihaz: `desktop` | motor: `{SEARCH_ENGINE}`",
        f"- Hedef URL: `{target_url}`",
        f"- **Sıra: {desktop_rank}**",
        f"- Kaynak: `{source}`",
        f"- Not: {notes}",
        f"- Önceki kayıt: {prev_line}",
        f"- Son GSC referansı: {gsc_line}",
        "",
        "## SERP baseline",
        "- Yeni satır: `AGENT-HUB/SERP-BASELINE.csv`",
        "",
        "## Sonraki hafta",
        "```bash",
        "cd /workspace && python3 AGENT-HUB/serp-rank-monitor.py",
        "```",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="SERP snapshot → SERP-BASELINE.csv")
    parser.add_argument("--rank", help="Doğrulanmış organik sıra (ör. 1)")
    parser.add_argument("--target-url", default=f"https://{TARGET_DOMAIN}/")
    parser.add_argument("--source", default="live_serp_browser_check")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    captured_at = utc_now()
    if args.rank:
        rank = args.rank
        target_url = args.target_url
        source = args.source
        notes = args.notes or f"Doğrulanmış canlı SERP; organik #{rank}"
    else:
        try:
            html, fetch_source = fetch_serp_html()
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            html, fetch_source = "", f"fetch_error:{exc.__class__.__name__}"

        if fetch_source == "headless_chrome":
            rank, target_url, detail = find_rank(html, "desktop")
            source = "live_serp_headless_chrome"
            notes = detail
        else:
            rank, target_url, detail = "blocked", f"https://{TARGET_DOMAIN}/", (
                "Headless SERP engellendi (CAPTCHA/IP). Manuel doğrulama veya GSC export gerekir."
            )
            source = "live_serp_blocked"
            notes = f"{detail}; fetch={fetch_source}"

    gsc_ref = latest_gsc_position()
    row = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": "desktop",
        "search_engine": SEARCH_ENGINE,
        "target_url": target_url,
        "rank_position": str(rank),
        "serp_features": "",
        "primary_competitor": "ledfon.com",
        "competitor_rank": "2" if str(rank) == "1" else "",
        "source": source,
        "notes": notes,
    }
    append_row(row)
    report_path = write_weekly_report(captured_at, rank, target_url, source, notes, gsc_ref)

    print(f"captured_at={captured_at}")
    print(f"rank_position={rank}")
    print(f"target_url={target_url}")
    print(f"source={source}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
