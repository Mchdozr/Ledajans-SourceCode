#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
REPORTS_DIR = ROOT / "AGENT-HUB"

QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"
PRIMARY_COMPETITOR = "ledeksan.com"

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


@dataclass
class RankResult:
    device: str
    rank_position: int | str
    target_url: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""
    serp_features: str = ""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/") or "/"
    return f"https://{host}{path}"


def find_rank(urls: list[str], domain: str = TARGET_DOMAIN) -> tuple[int | str, str]:
    for index, url in enumerate(urls, start=1):
        if domain in url.lower():
            return index, normalize_url(url)
    return "not_found", ""


def find_competitor_rank(urls: list[str], competitor: str) -> str:
    for index, url in enumerate(urls, start=1):
        if competitor in url.lower():
            return str(index)
    return ""


def fetch_serper(query: str, device: str) -> list[str]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return []

    payload = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 50,
    }
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
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def fetch_serpapi(query: str, device: str) -> list[str]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": query,
        "hl": "tr",
        "gl": "tr",
        "num": 50,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"

    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    urls: list[str] = []
    for item in data.get("organic_results", []):
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def fetch_ddg_lite(query: str, device: str) -> list[str]:
    mobile = device == "mobile"
    user_agent = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        if mobile
        else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
    headers = {"User-Agent": user_agent, "Accept-Language": "tr-TR,tr;q=0.9"}
    data = {"q": query, "kl": "tr-tr"}

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.post(
                "https://lite.duckduckgo.com/lite/",
                data=data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            html = response.text
            links: list[str] = []
            for match in re.finditer(r'<a rel="nofollow" href="([^"]+)"', html):
                url = match.group(1)
                if url.startswith("//"):
                    url = "https:" + url
                if "duckduckgo.com" in url:
                    continue
                links.append(url)
            if not links:
                for encoded in re.findall(r"uddg=([^&\"]+)", html):
                    links.append(urllib.parse.unquote(encoded))

            seen: list[str] = []
            for url in links:
                if url not in seen:
                    seen.append(url)
            return seen
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)

    if last_error:
        raise last_error
    return []


def measure_device(query: str, device: str) -> RankResult:
    sources = [
        ("serper_google", fetch_serper),
        ("serpapi_google", fetch_serpapi),
        ("ddg_lite_proxy", fetch_ddg_lite),
    ]

    for source_name, fetcher in sources:
        try:
            urls = fetcher(query, device)
        except Exception as exc:  # noqa: BLE001
            continue
        if not urls:
            continue

        rank, target_url = find_rank(urls)
        competitor_rank = find_competitor_rank(urls, PRIMARY_COMPETITOR)
        top_preview = "; ".join(urls[:5])
        notes = (
            f"organic_results={len(urls)}; top5={top_preview}; "
            f"proxy_note=DDG lite Google sonuçlarını proxyler (canlı Google değil)"
            if source_name == "ddg_lite_proxy"
            else f"organic_results={len(urls)}; top5={top_preview}"
        )
        return RankResult(
            device=device,
            rank_position=rank,
            target_url=target_url or DEFAULT_TARGET_URL,
            source=source_name,
            notes=notes,
            primary_competitor=PRIMARY_COMPETITOR,
            competitor_rank=competitor_rank,
        )

    return RankResult(
        device=device,
        rank_position="error",
        target_url=DEFAULT_TARGET_URL,
        source="unavailable",
        notes="Tüm SERP kaynakları başarısız",
        primary_competitor=PRIMARY_COMPETITOR,
    )


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return BASELINE_FIELDS, []

    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or BASELINE_FIELDS)
        rows = list(reader)
    return fields, rows


def append_baseline_rows(captured_at: str, results: list[RankResult]) -> list[dict[str, str]]:
    fields, existing = read_baseline_rows()
    new_rows: list[dict[str, str]] = []

    for result in results:
        row = {
            "captured_at_utc": captured_at,
            "query": QUERY,
            "locale": LOCALE,
            "device": result.device,
            "search_engine": SEARCH_ENGINE,
            "target_url": result.target_url,
            "rank_position": str(result.rank_position),
            "serp_features": result.serp_features,
            "primary_competitor": result.primary_competitor,
            "competitor_rank": result.competitor_rank,
            "source": result.source,
            "notes": result.notes,
        }
        row_day = row["captured_at_utc"][:10]
        duplicate = any(
            existing_row.get("captured_at_utc", "")[:10] == row_day
            and existing_row.get("query") == row["query"]
            and existing_row.get("device") == row["device"]
            and existing_row.get("source") == row["source"]
            for existing_row in existing
        )
        if duplicate:
            continue
        new_rows.append(row)

    if not new_rows:
        return []

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    return new_rows


def load_history() -> list[dict[str, str]]:
    _, rows = read_baseline_rows()
    filtered = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("search_engine", "").strip().lower() == SEARCH_ENGINE
    ]
    filtered.sort(key=lambda row: row.get("captured_at_utc", ""))
    return filtered


ORGANIC_SOURCES = {"serper_google", "serpapi_google", "ddg_lite_proxy", "manual_web_check"}


def previous_week_snapshot(history: list[dict[str, str]], before_iso: str) -> dict[str, str]:
    week_ago = datetime.fromisoformat(before_iso.replace("Z", "+00:00")).timestamp() - 7 * 86400
    candidates = [
        row
        for row in history
        if row.get("source") in ORGANIC_SOURCES
        and datetime.fromisoformat(row["captured_at_utc"].replace("Z", "+00:00")).timestamp() <= week_ago
    ]
    if not candidates:
        return {}
    latest_ts = max(row["captured_at_utc"] for row in candidates)
    same_run = [row for row in candidates if row["captured_at_utc"] == latest_ts]
    return {row["device"]: row for row in same_run}


def format_delta(current: str, previous: str) -> str:
    try:
        cur = float(current)
        prev = float(previous)
    except ValueError:
        return "n/a"
    diff = prev - cur
    if diff > 0:
        return f"↑ {diff:.0f} sıra iyileşme"
    if diff < 0:
        return f"↓ {abs(diff):.0f} sıra kayıp"
    return "→ stabil"


def write_weekly_report(captured_at: str, results: list[RankResult], appended: list[dict[str, str]]) -> Path:
    report_date = captured_at[:10]
    report_path = REPORTS_DIR / f"WEEKLY-MONITORING-{report_date}.md"
    history = load_history()
    previous = previous_week_snapshot(history, captured_at)

    mobile = next((item for item in results if item.device == "mobile"), None)
    desktop = next((item for item in results if item.device == "desktop"), None)

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Hedef domain: `{TARGET_DOMAIN}`",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Rakip | Rakip sıra |",
        "|---|---:|---|---|---|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result.device} | {result.rank_position} | {result.target_url} | "
            f"{result.source} | {result.primary_competitor} | {result.competitor_rank or 'n/a'} |"
        )

    lines.extend(["", "## Haftalık delta", ""])
    for device in ("mobile", "desktop"):
        current = next((row for row in appended if row["device"] == device), None)
        prev_row = previous.get(device)
        if current and prev_row:
            lines.append(
                f"- **{device}**: {current['rank_position']} (önceki: {prev_row['rank_position']}, "
                f"{format_delta(str(current['rank_position']), str(prev_row['rank_position']))})"
            )
        elif current:
            lines.append(f"- **{device}**: {current['rank_position']} (önceki ölçüm yok)")

    gsc_rows = [row for row in history if row.get("source", "").startswith("gsc_performance")]
    if gsc_rows:
        last_gsc = gsc_rows[-1]
        lines.extend(
            [
                "",
                "## GSC referans (farklı metrik)",
                "",
                f"- Son GSC avg position: **{last_gsc.get('rank_position', 'n/a')}** "
                f"(`{last_gsc.get('captured_at_utc', '')}`)",
                "- Not: GSC ortalama pozisyon ile canlı organic sıra aynı metrik değildir.",
            ]
        )

    lines.extend(
        [
            "",
            "## Veri kaydı",
            "",
            f"- `SERP-BASELINE.csv` bu çalışmada eklenen satır: **{len(appended)}**",
            "- Komut: `python3 AGENT-HUB/keyword_rank_weekly.py`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    results = [measure_device(QUERY, device) for device in ("mobile", "desktop")]
    appended = append_baseline_rows(captured_at, results)
    report_path = write_weekly_report(captured_at, results, appended)

    summary = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "results": [
            {
                "device": result.device,
                "rank_position": result.rank_position,
                "target_url": result.target_url,
                "source": result.source,
            }
            for result in results
        ],
        "baseline_appended": len(appended),
        "weekly_report": str(report_path.relative_to(ROOT)),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
