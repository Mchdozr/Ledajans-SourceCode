#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
DEVICES = ("mobile", "desktop")

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

USER_AGENT_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
USER_AGENT_MOBILE = (
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


@dataclass
class RankResult:
    device: str
    rank_position: int | str
    target_url: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    path = parsed.path or "/"
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path = f"{path}/"
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}{path}"


def domain_matches(url: str, domain: str = TARGET_DOMAIN) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host == domain or host.endswith(f".{domain}")


def extract_ddg_redirect(href: str) -> str:
    if href.startswith("//"):
        href = f"https:{href}"
    parsed = urlparse(href)
    if "uddg" in parse_qs(parsed.query):
        return unquote(parse_qs(parsed.query)["uddg"][0])
    return href


def fetch_with_retry(url: str, headers: dict[str, str], retries: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)
    raise RuntimeError(f"HTTP isteği başarısız: {last_error}") from last_error


def parse_ddg_lite(body: str) -> list[str]:
    hrefs = re.findall(r'<a rel="nofollow" href="([^"]+)"', body)
    if not hrefs:
        hrefs = re.findall(r'<a rel="nofollow" class="result-link" href="([^"]+)"', body)
    urls: list[str] = []
    for href in hrefs:
        url = extract_ddg_redirect(href)
        if url.startswith("http"):
            urls.append(normalize_url(url))
    return urls


def find_rank(urls: list[str]) -> tuple[int | str, str]:
    for index, url in enumerate(urls, start=1):
        if domain_matches(url):
            return index, url
    return "not_in_top10", ""


def search_duckduckgo_lite(query: str, device: str) -> RankResult:
    user_agent = USER_AGENT_MOBILE if device == "mobile" else USER_AGENT_DESKTOP
    params = urllib.parse.urlencode({"q": query, "kl": "tr-tr"})
    url = f"https://lite.duckduckgo.com/lite/?{params}"
    body = fetch_with_retry(url, {"User-Agent": user_agent})
    urls = parse_ddg_lite(body)
    rank, target_url = find_rank(urls)
    competitor = ""
    competitor_rank = ""
    if urls:
        competitor = urlparse(urls[0]).netloc
        if domain_matches(urls[0]):
            competitor = urlparse(urls[1]).netloc if len(urls) > 1 else ""
            competitor_rank = "2" if len(urls) > 1 else ""
        else:
            competitor_rank = "1"
    return RankResult(
        device=device,
        rank_position=rank,
        target_url=target_url or f"https://{TARGET_DOMAIN}/",
        source="ddg_lite_proxy",
        notes=(
            "DuckDuckGo lite TR proxy; Google organic ile birebir aynı olmayabilir. "
            f"Top10 sonuç sayısı={len(urls)}."
        ),
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
    )


def search_serper(query: str, device: str, api_key: str) -> RankResult:
    payload = json.dumps(
        {
            "q": query,
            "gl": "tr",
            "hl": "tr",
            "num": 50,
            "device": device,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    organic = data.get("organic") or []
    urls = [normalize_url(item.get("link", "")) for item in organic if item.get("link")]
    rank, target_url = find_rank(urls)
    competitor = ""
    competitor_rank = ""
    if urls:
        competitor = urlparse(urls[0]).netloc
        if domain_matches(urls[0]):
            competitor = urlparse(urls[1]).netloc if len(urls) > 1 else ""
            competitor_rank = "2" if len(urls) > 1 else ""
        else:
            competitor_rank = "1"
    return RankResult(
        device=device,
        rank_position=rank,
        target_url=target_url or f"https://{TARGET_DOMAIN}/",
        source="serper_google",
        notes=f"Serper Google organic; sonuç={len(urls)}.",
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
    )


def search_serpapi(query: str, device: str, api_key: str) -> RankResult:
    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "num": 50,
            "device": device,
            "api_key": api_key,
        }
    )
    url = f"https://serpapi.com/search.json?{params}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    organic = data.get("organic_results") or []
    urls = [normalize_url(item.get("link", "")) for item in organic if item.get("link")]
    rank, target_url = find_rank(urls)
    competitor = ""
    competitor_rank = ""
    if urls:
        competitor = urlparse(urls[0]).netloc
        if domain_matches(urls[0]):
            competitor = urlparse(urls[1]).netloc if len(urls) > 1 else ""
            competitor_rank = "2" if len(urls) > 1 else ""
        else:
            competitor_rank = "1"
    return RankResult(
        device=device,
        rank_position=rank,
        target_url=target_url or f"https://{TARGET_DOMAIN}/",
        source="serpapi_google",
        notes=f"SerpAPI Google organic; sonuç={len(urls)}.",
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
    )


def measure_device(query: str, device: str) -> RankResult:
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()
    errors: list[str] = []
    if serper_key:
        try:
            return search_serper(query, device, serper_key)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"serper:{exc}")
    if serpapi_key:
        try:
            return search_serpapi(query, device, serpapi_key)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"serpapi:{exc}")
    try:
        result = search_duckduckgo_lite(query, device)
        if errors:
            result.notes = f"{result.notes} Fallback: {'; '.join(errors)}"
        return result
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Tüm kaynaklar başarısız ({device}): {'; '.join(errors + [str(exc)])}") from exc


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_rows(captured_at: str, results: list[RankResult]) -> int:
    existing = read_baseline_rows()
    capture_date = captured_at[:10]
    existing_keys = {
        (
            row.get("captured_at_utc", "")[:10],
            row.get("query", ""),
            row.get("device", ""),
            row.get("source", ""),
        )
        for row in existing
    }
    appended = 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        for result in results:
            key = (capture_date, QUERY, result.device, result.source)
            if key in existing_keys:
                continue
            writer.writerow(
                {
                    "captured_at_utc": captured_at,
                    "query": QUERY,
                    "locale": LOCALE,
                    "device": result.device,
                    "search_engine": SEARCH_ENGINE,
                    "target_url": result.target_url,
                    "rank_position": str(result.rank_position),
                    "serp_features": "",
                    "primary_competitor": result.primary_competitor,
                    "competitor_rank": result.competitor_rank,
                    "source": result.source,
                    "notes": result.notes,
                }
            )
            appended += 1
    return appended


def latest_led_ekran_rows() -> dict[str, dict[str, str]]:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY and row.get("search_engine", "") == SEARCH_ENGINE
    ]
    rows.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        device = row.get("device", "")
        if device and device not in latest:
            latest[device] = row
    return latest


def previous_week_rows(before_iso: str) -> dict[str, dict[str, str]]:
    before_date = before_iso[:10]
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY
        and row.get("search_engine", "") == SEARCH_ENGINE
        and row.get("captured_at_utc", "")[:10] < before_date
        and row.get("source", "") in {"ddg_lite_proxy", "serper_google", "serpapi_google", "manual_web_check"}
    ]
    rows.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        device = row.get("device", "")
        if device and device not in latest:
            latest[device] = row
    return latest


def delta_text(current: str, previous: str) -> str:
    try:
        cur = float(current)
        prev = float(previous)
    except ValueError:
        return "karşılaştırılamadı"
    diff = prev - cur
    if diff > 0:
        return f"↑ {diff:.1f} sıra iyileşme"
    if diff < 0:
        return f"↓ {abs(diff):.1f} sıra düşüş"
    return "değişmedi"


def write_weekly_report(captured_at: str, results: list[RankResult], appended: int) -> Path:
    report_date = captured_at[:10]
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    previous = previous_week_rows(captured_at)
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — `led ekran` (Google, tr-TR)",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- CSV eklenen satır: **{appended}** (`AGENT-HUB/SERP-BASELINE.csv`)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Rakip #1 |",
        "|---|---:|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.device} | **{result.rank_position}** | {result.target_url} | "
            f"{result.source} | {result.primary_competitor or '-'} |"
        )
    lines.extend(["", "## Haftalık değişim", ""])
    if previous:
        for result in results:
            old = previous.get(result.device)
            if not old:
                lines.append(f"- {result.device}: önceki canlı SERP kaydı yok")
                continue
            old_rank = old.get("rank_position", "N/A")
            lines.append(
                f"- {result.device}: {old_rank} → **{result.rank_position}** "
                f"({delta_text(str(result.rank_position), old_rank)}; "
                f"kayıt `{old.get('captured_at_utc', '')}` / {old.get('source', '')})"
            )
    else:
        lines.append("- Önceki canlı SERP kaydı bulunamadı.")
    gsc_rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY
        and row.get("source", "").startswith("gsc_performance")
    ]
    if gsc_rows:
        gsc_rows.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
        gsc = gsc_rows[0]
        lines.extend(
            [
                "",
                "## GSC referans (avg position)",
                f"- Son GSC kaydı: **{gsc.get('rank_position', 'N/A')}** "
                f"(`{gsc.get('captured_at_utc', '')}`) — organic sıra ile doğrudan karşılaştırılmamalı.",
            ]
        )
    lines.extend(
        [
            "",
            "## Notlar",
            "- Canlı organic sıra ile GSC `avg_position` farklı metriklerdir.",
            "- API anahtarı yoksa ölçüm DuckDuckGo lite TR proxy ile yapılır.",
            "- Otomasyon: `AGENT-HUB/run-keyword-rank-weekly.sh` (cron: `0 6 * * 1` UTC, Pazartesi).",
            "",
            "## Sonraki çalıştırma",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def today_existing_results(capture_date: str) -> list[RankResult]:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY
        and row.get("captured_at_utc", "")[:10] == capture_date
        and row.get("source", "") in {"ddg_lite_proxy", "serper_google", "serpapi_google"}
    ]
    rows.sort(key=lambda row: (row.get("device", ""), row.get("captured_at_utc", "")))
    latest_by_device: dict[str, dict[str, str]] = {}
    for row in rows:
        latest_by_device[row.get("device", "")] = row
    results: list[RankResult] = []
    for device in DEVICES:
        row = latest_by_device.get(device)
        if not row:
            continue
        results.append(
            RankResult(
                device=device,
                rank_position=row.get("rank_position", ""),
                target_url=row.get("target_url", f"https://{TARGET_DOMAIN}/"),
                source=row.get("source", ""),
                notes=row.get("notes", ""),
                primary_competitor=row.get("primary_competitor", ""),
                competitor_rank=row.get("competitor_rank", ""),
            )
        )
    return results


def main() -> int:
    captured_at = utc_now_iso()
    capture_date = captured_at[:10]
    existing_today = today_existing_results(capture_date)
    if existing_today:
        results = existing_today
        today_rows = [
            row
            for row in read_baseline_rows()
            if row.get("query", "").strip().lower() == QUERY
            and row.get("captured_at_utc", "")[:10] == capture_date
        ]
        captured_at = min(row.get("captured_at_utc", captured_at) for row in today_rows)
        appended = 0
    else:
        results = [measure_device(QUERY, device) for device in DEVICES]
        appended = append_baseline_rows(captured_at, results)
    report_path = write_weekly_report(captured_at, results, appended)

    print(f"captured_at_utc={captured_at}")
    for result in results:
        print(
            f"{result.device}: rank={result.rank_position} url={result.target_url} source={result.source}"
        )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
