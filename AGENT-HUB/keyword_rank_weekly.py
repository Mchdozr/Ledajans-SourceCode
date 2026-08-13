#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import os
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
DEVICES = ("mobile", "desktop")
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


@dataclass
class RankResult:
    rank_position: int | str
    target_url: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    path = parsed.path or "/"
    if not path.endswith("/"):
        path += "/"
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}{path}"


def domain_matches(url: str, domain: str = TARGET_DOMAIN) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    return host == domain or host.endswith(f".{domain}")


def find_rank(urls: list[str], domain: str = TARGET_DOMAIN) -> tuple[int | str, str]:
    for index, url in enumerate(urls, start=1):
        if domain_matches(url, domain):
            return index, normalize_url(url)
    return "not_in_top20", ""


def top_competitor(urls: list[str]) -> tuple[str, str]:
    for index, url in enumerate(urls, start=1):
        if not domain_matches(url):
            return normalize_url(url), str(index)
    return "", ""


def fetch_serper(query: str, device: str, api_key: str) -> list[str]:
    payload = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
        "device": device,
    }
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
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def fetch_serpapi(query: str, device: str, api_key: str) -> list[str]:
    params = {
        "engine": "google",
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
        "device": device,
        "api_key": api_key,
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    urls: list[str] = []
    for item in data.get("organic_results", []):
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def fetch_ddg_lite(query: str) -> list[str]:
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query, "kl": "tr-tr"},
        headers={"User-Agent": USER_AGENTS["desktop"]},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    urls: list[str] = []
    for anchor in soup.select("a.result__a"):
        href = anchor.get("href", "").strip()
        if href.startswith("http"):
            urls.append(href)
    return urls[:20]


def measure_device(device: str) -> RankResult:
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()

    if serper_key:
        urls = fetch_serper(QUERY, device, serper_key)
        source = "serper_google"
        notes = f"Google organic via serper.dev; device={device}"
    elif serpapi_key:
        urls = fetch_serpapi(QUERY, device, serpapi_key)
        source = "serpapi_google"
        notes = f"Google organic via serpapi.com; device={device}"
    else:
        urls = fetch_ddg_lite(QUERY)
        source = "ddg_lite_proxy"
        notes = (
            "DuckDuckGo HTML proxy (Google CAPTCHA/API yok); "
            f"device={device}; organic sıra yaklaşık"
        )

    rank, target_url = find_rank(urls)
    competitor_url, competitor_rank = top_competitor(urls)
    if competitor_url and domain_matches(competitor_url):
        competitor_url, competitor_rank = top_competitor(urls[1:])

    if isinstance(rank, int) and rank > 1 and competitor_url:
        notes += f"; rakip #{competitor_rank} {competitor_url}"

    return RankResult(
        rank_position=rank,
        target_url=target_url or f"https://{TARGET_DOMAIN}/",
        source=source,
        notes=notes,
        primary_competitor=competitor_url,
        competitor_rank=competitor_rank if competitor_url else "",
    )


def read_baseline_fields() -> list[str]:
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
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def row_exists(captured_day: str, device: str, source: str) -> bool:
    if not BASELINE_PATH.exists():
        return False
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if (
                row.get("query", "").lower() == QUERY
                and row.get("device") == device
                and row.get("source") == source
                and row.get("captured_at_utc", "").startswith(captured_day)
            ):
                return True
    return False


def append_baseline_rows(captured_at: str, results: dict[str, RankResult]) -> int:
    fields = read_baseline_fields()
    captured_day = captured_at[:10]
    appended = 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        for device, result in results.items():
            if row_exists(captured_day, device, result.source):
                continue
            row = {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": result.target_url,
                "rank_position": str(result.rank_position),
                "serp_features": "",
                "primary_competitor": result.primary_competitor,
                "competitor_rank": result.competitor_rank,
                "source": result.source,
                "notes": result.notes,
            }
            writer.writerow({key: row.get(key, "") for key in fields})
            appended += 1
    return appended


def load_history() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    rows: list[dict[str, str]] = []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("query", "").lower() == QUERY:
                rows.append(row)
    return rows


def previous_week_rank(rows: list[dict[str, str]], device: str) -> str:
    organic_sources = {"serper_google", "serpapi_google", "ddg_lite_proxy", "manual_web_check"}
    device_rows = [
        row
        for row in rows
        if row.get("device") == device and row.get("source") in organic_sources
    ]
    if len(device_rows) < 2:
        return "—"
    device_rows.sort(key=lambda item: item.get("captured_at_utc", ""), reverse=True)
    return device_rows[1].get("rank_position", "—")


def write_weekly_report(captured_at: str, results: dict[str, RankResult], appended: int) -> Path:
    report_date = captured_at[:10]
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    history = load_history()

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Hedef domain: `{TARGET_DOMAIN}`",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Önceki hafta |",
        "|---|---:|---|---|---:|",
    ]
    for device, result in results.items():
        prev = previous_week_rank(history, device)
        lines.append(
            f"| {device} | **#{result.rank_position}** | {result.target_url} | "
            f"`{result.source}` | {prev} |"
        )

    lines.extend(
        [
            "",
            "## Notlar",
            "",
        ]
    )
    for device, result in results.items():
        lines.append(f"- **{device}:** {result.notes}")
    if result.primary_competitor:
        lines.append(
            f"- Birincil rakip: `{result.primary_competitor}` "
            f"(sıra #{result.competitor_rank})"
        )

    lines.extend(
        [
            "",
            "## Veri kaydı",
            "",
            f"- `SERP-BASELINE.csv` yeni satır: **{appended}**",
            "- Sonraki ölçüm: haftalık cron (`0 6 * * 1` UTC önerilir)",
            "",
            "## Referans",
            "",
            "- GSC `avg_position` ile canlı organic sıra farklı metriklerdir.",
            "- `SERPER_API_KEY` veya `SERPAPI_KEY` tanımlanırsa Google organic doğrudan ölçülür.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    results = {device: measure_device(device) for device in DEVICES}
    appended = append_baseline_rows(captured_at, results)
    report_path = write_weekly_report(captured_at, results, appended)

    for device, result in results.items():
        print(f"{device}: rank={result.rank_position} url={result.target_url} source={result.source}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
