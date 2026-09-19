#!/usr/bin/env python3
"""Haftalık/günlük 'led ekran' SERP konumu ölçümü ve baseline CSV güncellemesi."""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
REPORTS_DIR = ROOT / "AGENT-HUB" / "REPORTS"
GSC_DATA_DIR = ROOT / "AGENT-HUB" / "DATA"

QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_URL = "https://ledajans.com/"
PRIMARY_COMPETITOR = "ledfon.com"
LOCAL_PACK_DOMAINS = ("ledgrafik.com", "ledgaranti.com.tr")
SHOPPING_DOMAINS = ("hepsiburada.com", "trendyol.com", "n11.com", "amazon.com", "gittigidiyor.com")
SOCIAL_DOMAINS = ("instagram.com", "facebook.com", "youtube.com", "tiktok.com")
SKIP_DOMAINS = (
    "google.",
    "gstatic.com",
    "youtube.com",
    "webcache",
    "schema.org",
)

USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
}
WINDOW_SIZES = {"mobile": "412,915", "desktop": "1366,768"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def week_file_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def read_baseline_fieldnames() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def load_existing_keys() -> set[tuple[str, str, str, str]]:
    if not BASELINE_PATH.exists():
        return set()
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        for row in rows
    }


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    fieldnames = read_baseline_fieldnames()
    existing = load_existing_keys()
    to_write: list[dict[str, str]] = []
    for row in rows:
        key = (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        if key in existing:
            continue
        to_write.append({field: row.get(field, "") for field in fieldnames})

    if not to_write:
        return 0

    text = BASELINE_PATH.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        BASELINE_PATH.write_text(text + "\n", encoding="utf-8")

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        for row in to_write:
            writer.writerow(row)
    return len(to_write)


def fetch_serper(query: str, device: str) -> list[str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None

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
        body = json.loads(response.read().decode("utf-8"))

    urls: list[str] = []
    for item in body.get("organic", []):
        link = item.get("link", "").strip()
        if link and link not in urls:
            urls.append(link)
    return urls


def fetch_serpapi(query: str, device: str) -> list[str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None

    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "hl": "tr",
            "gl": "tr",
            "num": "30",
            "device": device,
            "api_key": api_key,
        }
    )
    with urllib.request.urlopen(f"https://serpapi.com/search.json?{params}", timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))

    urls: list[str] = []
    for item in body.get("organic_results", []):
        link = item.get("link", "").strip()
        if link and link not in urls:
            urls.append(link)
    return urls


def fetch_chrome_html(query: str, device: str) -> str:
    last_error = "unknown"
    for attempt in range(1, 4):
        profile_dir = tempfile.mkdtemp(prefix=f"chrome-serp-{device}-{attempt}-")
        html_path = Path(tempfile.mkstemp(prefix="serp-", suffix=".html")[1])
        search_url = "https://www.google.com/search?" + urllib.parse.urlencode(
            {"q": query, "hl": "tr", "gl": "tr", "num": "30", "pws": "0"}
        )
        command = [
            "timeout",
            "50",
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile_dir}",
            "--disable-blink-features=AutomationControlled",
            f"--user-agent={USER_AGENTS[device]}",
            f"--window-size={WINDOW_SIZES[device]}",
            "--virtual-time-budget=20000",
            "--dump-dom",
            search_url,
        ]
        with html_path.open("w", encoding="utf-8") as output_handle:
            completed = subprocess.run(
                command, stdout=output_handle, stderr=subprocess.DEVNULL, check=False
            )

        html = html_path.read_text(encoding="utf-8", errors="replace")
        html_path.unlink(missing_ok=True)
        if len(html) >= 100_000:
            return html
        last_error = f"exit={completed.returncode}, bytes={len(html)}, attempt={attempt}"

    raise RuntimeError(f"chrome scrape failed ({last_error})")


def extract_ping_urls(html: str) -> list[str]:
    urls: list[str] = []
    for match in re.findall(r'ping="/url\?[^"]*url=(https?://[^&"]+)', html):
        decoded = urllib.parse.unquote(match)
        if any(token in decoded for token in SKIP_DOMAINS):
            continue
        if decoded not in urls:
            urls.append(decoded)
    return urls


def domain_key(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def organic_urls(raw_urls: list[str]) -> list[str]:
    organic: list[str] = []
    seen_domains: set[str] = set()
    for url in raw_urls[:35]:
        if any(domain in url for domain in LOCAL_PACK_DOMAINS):
            continue
        if any(domain in url for domain in SHOPPING_DOMAINS):
            continue
        if any(domain in url for domain in SOCIAL_DOMAINS):
            continue
        key = domain_key(url)
        if key in seen_domains:
            continue
        seen_domains.add(key)
        organic.append(url)
    return organic


def find_rank(urls: list[str], target_domain: str = "ledajans.com") -> tuple[int | None, str | None]:
    for index, url in enumerate(organic_urls(urls), start=1):
        if target_domain in url:
            return index, url
    return None, None


def measure_device(query: str, device: str) -> tuple[int | None, str | None, str, list[str]]:
    for source, fetcher in (
        ("serper_api", fetch_serper),
        ("serpapi", fetch_serpapi),
    ):
        urls = fetcher(query, device)
        if urls:
            rank, matched = find_rank(urls)
            if rank is not None:
                return rank, matched, source, organic_urls(urls)

    html = fetch_chrome_html(query, device)
    urls = extract_ping_urls(html)
    rank, matched = find_rank(urls)
    top_organic = organic_urls(urls)
    if rank is None and len(top_organic) >= 5:
        html = fetch_chrome_html(query, device)
        urls = extract_ping_urls(html)
        rank, matched = find_rank(urls)
        top_organic = organic_urls(urls)
    return rank, matched, "google_chrome_headless", top_organic


def latest_gsc_position(query: str) -> str | None:
    folders = sorted(GSC_DATA_DIR.glob("gsc-performance-*"), reverse=True)
    for folder in folders:
        queries_path = folder / "Sorgular.csv"
        if not queries_path.exists():
            continue
        with queries_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("En çok yapılan sorgular", "").strip().lower() == query.lower():
                    return row.get("Pozisyon", "").strip() or None
    return None


def build_measurement_rows(captured_at: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for device in ("mobile", "desktop"):
        rank, matched_url, source, top_organic = measure_device(QUERY, device)
        if rank is None:
            rank_text = "not_found"
            notes = f"target={TARGET_URL}; organic_top10={len(top_organic)}"
        else:
            rank_text = str(rank)
            competitor = top_organic[1] if len(top_organic) > 1 and rank == 1 else (top_organic[0] if top_organic else "")
            notes = (
                f"organic_rank={rank}; matched={matched_url or TARGET_URL}; "
                f"competitor_next={competitor}; top3={'; '.join(top_organic[:3])}"
            )

        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": "google",
                "target_url": matched_url or TARGET_URL,
                "rank_position": rank_text,
                "serp_features": "local_pack" if device == "mobile" else "",
                "primary_competitor": PRIMARY_COMPETITOR,
                "competitor_rank": "2" if rank == 1 else "",
                "source": source,
                "notes": notes,
            }
        )
    return rows


def update_weekly_monitoring(captured_at: str, rows: list[dict[str, str]], appended: int) -> Path:
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{week_file_date()}.md"
    gsc_position = latest_gsc_position(QUERY)

    mobile = next((row for row in rows if row["device"] == "mobile"), rows[0])
    desktop = next((row for row in rows if row["device"] == "desktop"), rows[-1])

    previous_lines: list[str] = []
    if BASELINE_PATH.exists():
        with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
            history = [row for row in csv.DictReader(handle) if row["query"].lower() == QUERY.lower()]
        led_history = [
            row
            for row in history
            if row["source"] in {"google_chrome_headless", "serper_api", "serpapi", "manual_web_check"}
            and row["device"] == "mobile"
        ]
        if len(led_history) >= 2:
            prev = led_history[-2]
            previous_lines.append(
                f"- Önceki mobil ölçüm ({prev['captured_at_utc']}): **{prev['rank_position']}** ({prev['source']})"
            )

    content = "\n".join(
        [
            f"# Haftalık SEO İzleme — {week_file_date()}",
            "",
            "## SERP — led ekran",
            f"- Ölçüm UTC: `{captured_at}`",
            f"- Mobil Google organic: **{mobile['rank_position']}** — {mobile['target_url']} (`{mobile['source']}`)",
            f"- Masaüstü Google organic: **{desktop['rank_position']}** — {desktop['target_url']} (`{desktop['source']}`)",
            f"- Birincil rakip: {PRIMARY_COMPETITOR}",
            f"- `SERP-BASELINE.csv` eklenen satır: **{appended}**",
            *previous_lines,
            "",
            "## GSC referans (avg position)",
            f"- Son export avg_position: **{gsc_position or 'N/A (export güncelle)'}**",
            "- Not: GSC ortalama pozisyon ile canlı organic sıra farklı metriklerdir.",
            "",
            "## Komut",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "## Sonraki ölçüm",
            "- Cron: `0 6 * * *` UTC (`run-keyword-rank-weekly.sh`)",
            "- SERPER/SERPAPI anahtarı tanımlanırsa API öncelikli kullanılır.",
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    return path


def write_report(captured_at: str, rows: list[dict[str, str]], appended: int) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{week_file_date()}-serp-led-ekran.md"
    lines = [
        f"# SERP Ölçüm — led ekran — {week_file_date()}",
        "",
        f"- captured_at_utc: `{captured_at}`",
        f"- baseline_appended: {appended}",
        "",
        "| device | rank | target_url | source |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['device']} | {row['rank_position']} | {row['target_url']} | {row['source']} |"
        )
    lines.extend(["", "## Notlar", ""])
    for row in rows:
        lines.append(f"- **{row['device']}**: {row['notes']}")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    rows = build_measurement_rows(captured_at)
    appended = append_baseline_rows(rows)
    weekly_path = update_weekly_monitoring(captured_at, rows, appended)
    report_path = write_report(captured_at, rows, appended)

    mobile_rank = next(row["rank_position"] for row in rows if row["device"] == "mobile")
    desktop_rank = next(row["rank_position"] for row in rows if row["device"] == "desktop")
    print(f"query={QUERY}")
    print(f"mobile_rank={mobile_rank}")
    print(f"desktop_rank={desktop_rank}")
    print(f"baseline_appended={appended}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    print(f"report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
