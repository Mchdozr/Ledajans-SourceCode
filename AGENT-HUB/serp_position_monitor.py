#!/usr/bin/env python3
"""Google SERP sıra izleme — led ekran anahtar kelimesi için ledajans.com."""
from __future__ import annotations

import csv
import json
import re
import shlex
import subprocess
import tempfile
import time
import urllib.parse
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
AGENT_HUB = ROOT / "AGENT-HUB"

QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)
DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

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


def monday_of_week(day: datetime) -> datetime:
    return day - timedelta(days=day.weekday())


def build_search_url(query: str) -> str:
    params = {"q": query, "gl": "tr", "hl": "tr", "num": 50, "pws": 0}
    return "https://www.google.com/search?" + urllib.parse.urlencode(params)


def cleanup_chrome() -> None:
    subprocess.run(["pkill", "-f", "google-chrome"], check=False)
    time.sleep(2)


def fetch_serp_html(query: str, device: str, timeout: int = 90) -> str:
    user_agent = MOBILE_UA if device == "mobile" else DESKTOP_UA
    profile_dir = tempfile.mkdtemp(prefix=f"serp-chrome-{device}-")
    html_path = Path(tempfile.mktemp(suffix=f"-{device}.html"))
    shell_cmd = " ".join(
        [
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            shlex.quote(f"--user-data-dir={profile_dir}"),
            "--virtual-time-budget=25000",
            shlex.quote(f"--user-agent={user_agent}"),
            "--dump-dom",
            shlex.quote(build_search_url(query)),
            ">",
            shlex.quote(str(html_path)),
            "2>/dev/null",
        ]
    )
    proc = subprocess.Popen(shell_cmd, shell=True)
    deadline = time.monotonic() + timeout
    last_size = -1
    stable_reads = 0
    while time.monotonic() < deadline:
        if html_path.exists():
            size = html_path.stat().st_size
            if size > 100_000 and size == last_size:
                stable_reads += 1
                if stable_reads >= 2:
                    break
            else:
                stable_reads = 0
            last_size = size
        if proc.poll() is not None and html_path.exists() and html_path.stat().st_size > 0:
            break
        time.sleep(1.5)

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if not html_path.exists():
        return ""
    return html_path.read_text(encoding="utf-8", errors="ignore")


def extract_organic_urls(html: str) -> list[str]:
    urls: list[str] = []

    for match in re.finditer(r'href="/url\?q=([^&"]+)', html):
        url = urllib.parse.unquote(match.group(1))
        if url.startswith("http"):
            urls.append(url)

    for match in re.finditer(r'ping="[^"]*?\burl=([^&"]+)', html):
        url = urllib.parse.unquote(match.group(1))
        if url.startswith("http"):
            urls.append(url)

    for match in re.finditer(r'data-lpage="([^"]+)"', html):
        urls.append(match.group(1))

    for match in re.finditer(
        r'<script type="speculationrules"[^>]*>(\{.*?\})</script>', html, re.S
    ):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        for prefetch in payload.get("prefetch", []):
            urls.extend(prefetch.get("urls", []))

    seen: set[str] = set()
    ranked: list[str] = []
    for url in urls:
        normalized = url.split("#")[0]
        if "google." in normalized or "gstatic" in normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        ranked.append(normalized)
    return ranked


def find_domain_rank(urls: list[str], domain: str) -> tuple[int | None, str | None]:
    needle = domain.lower()
    for index, url in enumerate(urls, start=1):
        if needle in url.lower():
            return index, url
    return None, None


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_row(row: dict[str, str]) -> None:
    existing = read_baseline_rows()
    fieldnames = CSV_FIELDS
    if existing:
        fieldnames = list(existing[0].keys())

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def latest_rows_for_query(query: str, device: str) -> list[dict[str, str]]:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == query.lower()
        and row.get("device", "").strip().lower() == device.lower()
    ]
    rows.sort(key=lambda item: item.get("captured_at_utc", ""), reverse=True)
    return rows


def weekly_report_path(day: datetime) -> Path:
    week_start = monday_of_week(day).date().isoformat()
    return AGENT_HUB / f"WEEKLY-MONITORING-{week_start}.md"


def format_delta(current: int | None, previous: str | None) -> str:
    if current is None:
        return "ölçülemedi"
    if not previous:
        return f"{current} (ilk ölçüm)"
    try:
        prev_value = float(str(previous).replace("top", ""))
    except ValueError:
        if str(previous).startswith("top"):
            return f"{current} (önceki: {previous})"
        return f"{current} (önceki: {previous})"
    delta = prev_value - current
    if delta > 0:
        return f"{current} (↑ {delta:.1f} sıra iyileşme, önceki GSC/ölçüm: {previous})"
    if delta < 0:
        return f"{current} (↓ {abs(delta):.1f} sıra düşüş, önceki: {previous})"
    return f"{current} (değişim yok, önceki: {previous})"


def update_weekly_report(
    captured_at: datetime,
    mobile_rank: int | None,
    mobile_url: str | None,
    desktop_rank: int | None,
    desktop_url: str | None,
    mobile_urls: list[str],
) -> Path:
    report_path = weekly_report_path(captured_at)
    previous_mobile = latest_rows_for_query(QUERY, "mobile")
    prev_rank = previous_mobile[1]["rank_position"] if len(previous_mobile) > 1 else None

    top_competitors = []
    for url in mobile_urls[:5]:
        if TARGET_DOMAIN not in url.lower():
            top_competitors.append(urllib.parse.urlparse(url).netloc)

    lines = [
        f"# Haftalık SEO İzleme — {monday_of_week(captured_at).date().isoformat()}",
        "",
        f"Son güncelleme (UTC): `{captured_at.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        "",
        "## SERP — led ekran",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak |",
        "|---|---:|---|---|",
        f"| mobile | {mobile_rank if mobile_rank is not None else 'N/A'} | "
        f"{mobile_url or TARGET_URL} | google_live_serp |",
        f"| desktop | {desktop_rank if desktop_rank is not None else 'N/A'} | "
        f"{desktop_url or 'bulunamadı'} | google_live_serp |",
        "",
        f"- Mobil sıra özeti: **{format_delta(mobile_rank, prev_rank)}**",
        f"- İlk 5 rakip (mobil): {', '.join(top_competitors) if top_competitors else 'N/A'}",
        "",
        "## Baseline geçmişi",
        "",
        "| Tarih (UTC) | Cihaz | Sıra | Kaynak |",
        "|---|---|---:|---|",
    ]

    history = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY.lower()
        and row.get("target_url", "").startswith("https://ledajans.com")
    ][-8:]
    for row in history:
        lines.append(
            f"| {row.get('captured_at_utc', '')} | {row.get('device', '')} | "
            f"{row.get('rank_position', '')} | {row.get('source', '')} |"
        )

    lines.extend(
        [
            "",
            "## Sonraki kontrol",
            "",
            "```bash",
            "python3 AGENT-HUB/serp_position_monitor.py",
            "```",
            "",
            "Kaynak dosya: `AGENT-HUB/SERP-BASELINE.csv`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def monitor_device(
    captured_at: datetime, device: str
) -> tuple[int | None, str | None, list[str]]:
    html = fetch_serp_html(QUERY, device)
    urls = extract_organic_urls(html)
    rank, matched_url = find_domain_rank(urls, TARGET_DOMAIN)

    previous = latest_rows_for_query(QUERY, device)
    prev_note = ""
    if previous:
        prev_note = f" önceki={previous[0].get('rank_position', 'N/A')}"

    row = {
        "captured_at_utc": captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": matched_url or TARGET_URL,
        "rank_position": str(rank) if rank is not None else "not_found",
        "serp_features": "",
        "primary_competitor": (
            urllib.parse.urlparse(urls[1]).netloc if len(urls) > 1 and rank == 1 else ""
        ),
        "competitor_rank": "2" if rank == 1 and len(urls) > 1 else "",
        "source": "google_live_serp",
        "notes": (
            f"organic_results={len(urls)}; parser=ping+lpage+prefetch;"
            f"rank={rank if rank is not None else 'not_found'}{prev_note}"
        ),
    }
    append_baseline_row(row)
    return rank, matched_url, urls


def main() -> int:
    captured_at = datetime.now(UTC)
    mobile_rank, mobile_url, mobile_urls = monitor_device(captured_at, "mobile")
    cleanup_chrome()
    desktop_rank, desktop_url, _ = monitor_device(captured_at, "desktop")
    cleanup_chrome()
    report_path = update_weekly_report(
        captured_at,
        mobile_rank,
        mobile_url,
        desktop_rank,
        desktop_url,
        mobile_urls,
    )

    print(f"query={QUERY}")
    print(f"mobile_rank={mobile_rank}")
    print(f"desktop_rank={desktop_rank}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
