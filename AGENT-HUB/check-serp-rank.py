#!/usr/bin/env python3
"""Haftalık SERP snapshot: led ekran sorgusunda ledajans.com sırasını ölçer ve kaydeder."""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
DEFAULT_QUERY = "led ekran"
DEFAULT_TARGET = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"
SKIP_DOMAINS = {
    "google.",
    "gstatic.",
    "youtube.",
    "schema.org",
    "w3.org",
    "instagram.",
    "facebook.",
    "twitter.",
    "x.com",
    "tiktok.",
}

USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

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


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def normalize_url(url: str) -> str:
    url = unquote(url)
    if "google.com/url" in url:
        match = re.search(r"[?&]url=([^&]+)", url)
        if match:
            url = unquote(match.group(1))
    return url.rstrip("/")


def should_skip(url: str) -> bool:
    domain = domain_of(url)
    return not domain or any(token in domain for token in SKIP_DOMAINS)


def extract_organic_urls(html: str) -> list[str]:
    candidates: list[str] = []
    for match in re.finditer(r"https?://[^\"<> ]+", html):
        url = normalize_url(match.group(0))
        if url.startswith("http") and not should_skip(url):
            candidates.append(url)

    seen: list[str] = []
    organic: list[str] = []
    for url in candidates:
        domain = domain_of(url)
        if domain not in seen:
            seen.append(domain)
            organic.append(url)
    return organic


def fetch_google_serp(query: str, device: str, timeout_sec: int, retries: int) -> dict:
    last_snapshot = {
        "device": device,
        "html_len": 0,
        "organic_count": 0,
        "top10": [],
        "best_rank": None,
        "best_url": None,
        "primary_competitor": "",
        "competitor_rank": "",
    }
    for attempt in range(1, retries + 1):
        if attempt > 1:
            time.sleep(min(10 * attempt, 45))
        last_snapshot = _fetch_google_serp_once(query, device, timeout_sec)
        if last_snapshot["organic_count"] > 0:
            last_snapshot["attempt"] = attempt
            return last_snapshot
    last_snapshot["attempt"] = retries
    return last_snapshot


def _fetch_google_serp_once(query: str, device: str, timeout_sec: int) -> dict:
    search_url = (
        "https://www.google.com/search?"
        f"q={query.replace(' ', '+')}&hl=tr&gl=tr&num=30&pws=0"
    )
    cmd = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--user-agent={USER_AGENTS[device]}",
        f"--timeout={timeout_sec * 1000}",
        "--dump-dom",
        search_url,
    ]
    if device == "mobile":
        cmd.insert(1, "--window-size=412,915")

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 15)
    html = proc.stdout or ""
    organic = extract_organic_urls(html)
    matches = [(index, url) for index, url in enumerate(organic, 1) if DEFAULT_TARGET in url.lower()]
    return {
        "device": device,
        "html_len": len(html),
        "organic_count": len(organic),
        "top10": organic[:10],
        "best_rank": matches[0][0] if matches else None,
        "best_url": matches[0][1] if matches else None,
        "primary_competitor": domain_of(organic[1]) if len(organic) > 1 else "",
        "competitor_rank": 2 if len(organic) > 1 else "",
    }


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or BASELINE_FIELDS
        return fields, list(reader)


def latest_gsc_position(rows: list[dict[str, str]], query: str) -> str | None:
    latest: dict[str, str] | None = None
    for row in reversed(rows):
        if row.get("query", "").strip().lower() != query.lower():
            continue
        if row.get("source", "").startswith("gsc_performance"):
            latest = row
            break
    if not latest:
        return None
    return latest.get("rank_position")


def build_notes(device: str, snapshot: dict, gsc_position: str | None) -> str:
    parts = [
        f"Organic Google TR snapshot ({device})",
        f"organic_results={snapshot['organic_count']}",
    ]
    if snapshot["best_rank"] is None:
        parts.append("target_not_found_in_parsed_results")
    if gsc_position:
        parts.append(f"prev_gsc_avg_position={gsc_position}")
    return "; ".join(parts)


def append_baseline_row(fields: list[str], row: dict[str, str]) -> None:
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow({key: row.get(key, "") for key in fields})


def write_weekly_report(
    report_date: str,
    captured_at: str,
    snapshots: dict[str, dict],
    gsc_position: str | None,
) -> Path:
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    desktop = snapshots.get("desktop", {})
    mobile = snapshots.get("mobile", {})
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — `led ekran`",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        f"- Kaynak: `google_headless_chrome`",
        f"- Desktop sıra: **{desktop.get('best_rank', 'N/A')}** → `{desktop.get('best_url', '—')}`",
        f"- Mobile sıra: **{mobile.get('best_rank', 'N/A')}** → `{mobile.get('best_url', '—')}`",
    ]
    if gsc_position:
        lines.append(f"- Son GSC avg position (referans): **{gsc_position}**")
    lines.extend(
        [
            "",
            "### Desktop top 5",
            "",
        ]
    )
    for index, url in enumerate(desktop.get("top10", [])[:5], 1):
        lines.append(f"{index}. {url}")
    lines.extend(
        [
            "",
            "## Kayıt",
            "",
            "- Yeni satırlar: `AGENT-HUB/SERP-BASELINE.csv`",
            "- Komut: `python3 AGENT-HUB/check-serp-rank.py`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-rank.py",
            "```",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def run(timeout_sec: int, devices: list[str], dry_run: bool, retries: int) -> int:
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fields, existing_rows = read_baseline_rows()
    gsc_position = latest_gsc_position(existing_rows, DEFAULT_QUERY)

    snapshots: dict[str, dict] = {}
    appended: list[dict[str, str]] = []
    for device in devices:
        snapshot = fetch_google_serp(DEFAULT_QUERY, device, timeout_sec, retries)
        snapshots[device] = snapshot
        rank = snapshot["best_rank"]
        row = {
            "captured_at_utc": captured_at,
            "query": DEFAULT_QUERY,
            "locale": "tr-TR",
            "device": device,
            "search_engine": "google",
            "target_url": snapshot["best_url"] or DEFAULT_TARGET_URL,
            "rank_position": str(rank) if rank is not None else "not_found",
            "serp_features": "",
            "primary_competitor": snapshot.get("primary_competitor", ""),
            "competitor_rank": str(snapshot.get("competitor_rank", "")),
            "source": "google_headless_chrome",
            "notes": build_notes(device, snapshot, gsc_position),
        }
        appended.append(row)
        if not dry_run:
            append_baseline_row(fields, row)

    report_path = None
    if not dry_run:
        report_path = write_weekly_report(report_date, captured_at, snapshots, gsc_position)

    payload = {
        "captured_at_utc": captured_at,
        "query": DEFAULT_QUERY,
        "snapshots": snapshots,
        "appended_rows": appended,
        "weekly_report": str(report_path.relative_to(ROOT)) if report_path else None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="led ekran SERP snapshot ve haftalık kayıt")
    parser.add_argument("--timeout", type=int, default=45, help="Chrome timeout (saniye)")
    parser.add_argument(
        "--devices",
        default="desktop,mobile",
        help="Virgülle ayrılmış cihaz listesi (desktop,mobile)",
    )
    parser.add_argument("--retries", type=int, default=3, help="Başarısız parse sonrası deneme sayısı")
    parser.add_argument("--dry-run", action="store_true", help="CSV/rapor yazmadan sonucu göster")
    args = parser.parse_args()
    devices = [item.strip() for item in args.devices.split(",") if item.strip()]
    return run(args.timeout, devices, args.dry_run, args.retries)


if __name__ == "__main__":
    raise SystemExit(main())
