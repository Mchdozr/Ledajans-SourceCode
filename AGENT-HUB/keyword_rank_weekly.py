#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_HOST = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
DEVICES = ("mobile", "desktop")
SEARCH_ENGINE = "google"

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


@dataclass
class SerpResult:
    rank_position: int | str
    target_url: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""
    serp_features: str = ""
    competitors: list[tuple[int, str, str]] | None = None


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def weekly_report_path(day: datetime) -> Path:
    return HUB / f"WEEKLY-MONITORING-{day.strftime('%Y-%m-%d')}.md"


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return CSV_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or CSV_FIELDS)
        return fields, list(reader)


def normalize_domain(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    if not match:
        return ""
    return re.sub(r"^www\.", "", match.group(1).lower())


def extract_target_rank(
    organic: list[tuple[str, str]],
    host: str = TARGET_HOST,
) -> tuple[int | None, str, list[tuple[int, str, str]]]:
    competitors: list[tuple[int, str, str]] = []
    target_rank: int | None = None
    target_url = TARGET_URL
    for index, (title, url) in enumerate(organic, start=1):
        domain = normalize_domain(url)
        competitors.append((index, domain, title))
        if host in domain and target_rank is None:
            target_rank = index
            target_url = url.split("?")[0].rstrip("/") + "/"
    return target_rank, target_url, competitors


def http_json_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_serper(query: str, device: str) -> SerpResult | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 30}
    if device == "mobile":
        payload["device"] = "mobile"
    data = http_json_post(
        "https://google.serper.dev/search",
        payload,
        {"X-API-KEY": api_key, "Content-Type": "application/json"},
    )
    organic = [(item.get("title", ""), item.get("link", "")) for item in data.get("organic", [])]
    rank, target_url, competitors = extract_target_rank(organic)
    if rank is None:
        return SerpResult("not_found", TARGET_URL, "serper_api", "ledajans.com ilk 30 sonuçta yok")
    primary = competitors[0][1] if competitors and competitors[0][1] != TARGET_HOST else (
        competitors[1][1] if len(competitors) > 1 else ""
    )
    comp_rank = "1" if primary and primary != TARGET_HOST else ""
    return SerpResult(
        rank,
        target_url,
        "serper_api",
        f"Google organic via Serper; device={device}",
        primary_competitor=primary if primary != TARGET_HOST else "",
        competitor_rank=comp_rank,
        competitors=competitors,
    )


def fetch_serpapi(query: str, device: str) -> SerpResult | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "num": 30,
            "device": device,
            "api_key": api_key,
        }
    )
    request = urllib.request.Request(f"https://serpapi.com/search.json?{params}")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    organic = [(item.get("title", ""), item.get("link", "")) for item in data.get("organic_results", [])]
    rank, target_url, competitors = extract_target_rank(organic)
    if rank is None:
        return SerpResult("not_found", TARGET_URL, "serpapi", "ledajans.com ilk 30 sonuçta yok")
    primary = next((domain for _, domain, _ in competitors if domain != TARGET_HOST), "")
    return SerpResult(
        rank,
        target_url,
        "serpapi",
        f"Google organic via SerpAPI; device={device}",
        primary_competitor=primary,
        competitor_rank="1" if primary else "",
        competitors=competitors,
    )


def fetch_jina_text(target_url: str, retries: int = 3) -> str:
    proxy_url = "https://r.jina.ai/" + target_url
    headers = {"Accept": "text/plain", "User-Agent": "ledajans-serp-monitor/1.0"}
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(proxy_url, headers=headers)
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"jina proxy başarısız: {last_error}")


def parse_ddg_jina_markdown(text: str) -> list[tuple[str, str]]:
    organic: list[tuple[str, str]] = []
    for match in re.finditer(
        r"##\s+\[([^\]]+)\]\((https?://duckduckgo\.com/l/\?uddg=([^&\)]+)[^\)]*)\)",
        text,
    ):
        title = match.group(1).strip()
        target = urllib.parse.unquote(match.group(3))
        organic.append((title, target))
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for title, url in organic:
        domain = normalize_domain(url)
        if not domain or domain in seen:
            continue
        seen.add(domain)
        deduped.append((title, url))
    return deduped


def parse_yahoo_jina_markdown(text: str) -> list[tuple[str, str]]:
    organic: list[tuple[str, str]] = []
    for match in re.finditer(
        r"\n(\d+)\.\s+\[!\[[^\]]*\]\([^\)]*\)\s+([a-z0-9.-]+)\s+https?://[^\s]+\s+###\s+([^\]]+)\]\((https?://[^\)]+)\)",
        text,
    ):
        organic.append((match.group(3).strip(), match.group(4)))
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for title, url in organic:
        domain = normalize_domain(url)
        if not domain or domain in seen:
            continue
        seen.add(domain)
        deduped.append((title, url))
    return deduped


def fetch_ddg_jina_proxy(query: str, device: str) -> SerpResult:
    encoded = urllib.parse.quote(query)
    ddg_url = f"https://html.duckduckgo.com/html/?q={encoded}&kl=tr-tr"
    text = fetch_jina_text(ddg_url)
    organic = parse_ddg_jina_markdown(text)
    rank, target_url, competitors = extract_target_rank(organic)
    if rank is None:
        return SerpResult(
            "not_found",
            TARGET_URL,
            "ddg_lite_jina_proxy",
            "Google doğrudan engelli; DDG lite jina proxy — ledajans.com bulunamadı",
        )
    primary = next((domain for _, domain, _ in competitors if domain != TARGET_HOST), "")
    return SerpResult(
        rank,
        target_url,
        "ddg_lite_jina_proxy",
        (
            f"Google CAPTCHA nedeniyle doğrudan ölçülemedi; DDG lite (jina proxy) "
            f"ile tahmini organic sıra; device={device}"
        ),
        primary_competitor=primary,
        competitor_rank=str(rank - 1) if rank > 1 else "",
        competitors=competitors,
    )


def fetch_yahoo_jina_proxy(query: str, device: str) -> SerpResult:
    encoded = urllib.parse.quote(query)
    yahoo_url = f"https://search.yahoo.com/search?p={encoded}"
    text = fetch_jina_text(yahoo_url)
    organic = parse_yahoo_jina_markdown(text)
    rank, target_url, competitors = extract_target_rank(organic)
    if rank is None:
        return SerpResult(
            "not_found",
            TARGET_URL,
            "yahoo_jina_proxy",
            "Yahoo jina proxy — ledajans.com bulunamadı",
        )
    primary = next((domain for _, domain, _ in competitors if domain != TARGET_HOST), "")
    return SerpResult(
        rank,
        target_url,
        "yahoo_jina_proxy",
        f"Yahoo (jina proxy) organic sıra; device={device}; Images bloğu hariç",
        primary_competitor=primary,
        competitor_rank="1" if primary else "",
        competitors=competitors,
    )


def measure_device(query: str, device: str) -> SerpResult:
    for fetcher in (fetch_serper, fetch_serpapi):
        result = fetcher(query, device)
        if result is not None:
            return result
    if device == "desktop":
        return fetch_yahoo_jina_proxy(query, device)
    return fetch_ddg_jina_proxy(query, device)


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    day = row["captured_at_utc"][:10]
    return day, row["query"].lower(), row["device"], row["source"]


def append_baseline_rows(
    fields: list[str],
    existing: list[dict[str, str]],
    new_rows: list[dict[str, str]],
) -> int:
    existing_keys = {row_key(row) for row in existing}
    to_append = [row for row in new_rows if row_key(row) not in existing_keys]
    if not to_append:
        return 0
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in fields})
    return len(to_append)


def latest_led_ekran_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("search_engine", "") == SEARCH_ENGINE
        and row.get("target_url", "").startswith("https://ledajans.com")
    ]
    matches.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    return matches


def format_rank_delta(current: str, previous: str | None) -> str:
    if not previous or previous in {"pending", "not_found", "top3", "top5", "top10", "top20"}:
        return "—"
    try:
        delta = float(current) - float(previous)
    except ValueError:
        return "—"
    if delta < 0:
        return f"↑ {abs(delta):.2f} sıra"
    if delta > 0:
        return f"↓ {delta:.2f} sıra"
    return "stabil"


def build_weekly_report(
    captured_at: str,
    measurements: dict[str, SerpResult],
    appended: int,
    all_rows: list[dict[str, str]],
) -> str:
    day = captured_at[:10]
    prior = latest_led_ekran_rows(
        [row for row in all_rows if row.get("captured_at_utc", "") < captured_at]
    )
    prior_by_device = {row["device"]: row for row in prior}

    mobile = measurements["mobile"]
    desktop = measurements["desktop"]
    mobile_prev = prior_by_device.get("mobile", {}).get("rank_position")
    desktop_prev = prior_by_device.get("desktop", {}).get("rank_position")

    lines = [
        f"# Haftalık SEO İzleme — {day}",
        "",
        "## SERP — led ekran",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Önceki | Delta |",
        "|---|---:|---|---|---|---|",
        f"| mobile | {mobile.rank_position} | {mobile.target_url} | {mobile.source} | "
        f"{mobile_prev or '—'} | {format_rank_delta(str(mobile.rank_position), mobile_prev)} |",
        f"| desktop | {desktop.rank_position} | {desktop.target_url} | {desktop.source} | "
        f"{desktop_prev or '—'} | {format_rank_delta(str(desktop.rank_position), desktop_prev)} |",
        "",
        "### Rakip özeti (mobile)",
        "",
    ]
    if mobile.competitors:
        for rank, domain, title in mobile.competitors[:5]:
            mark = " **(biz)**" if TARGET_HOST in domain else ""
            lines.append(f"- #{rank} {domain} — {title[:60]}{mark}")
    else:
        lines.append("- Rakip listesi alınamadı")

    lines.extend(
        [
            "",
            "### Notlar",
            f"- Ölçüm zamanı (UTC): `{captured_at}`",
            f"- `SERP-BASELINE.csv` eklenen satır: **{appended}**",
            f"- Mobile: {mobile.notes}",
            f"- Desktop: {desktop.notes}",
            "- GSC avg_position (son kayıt 2026-06-05): **6.78** — farklı metrik; canlı organic ile karıştırma.",
            "",
            "## Otomasyon",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "Cron: `0 6 * * *` UTC (haftalık SERP snapshot).",
            "Google doğrudan erişim için ortam değişkeni: `SERPER_API_KEY` veya `SERPAPI_KEY`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    captured_at = utc_now_iso()
    measurements: dict[str, SerpResult] = {}
    new_rows: list[dict[str, str]] = []

    for device in DEVICES:
        result = measure_device(QUERY, device)
        measurements[device] = result
        new_rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": result.target_url,
                "rank_position": str(result.rank_position),
                "serp_features": result.serp_features,
                "primary_competitor": result.primary_competitor,
                "competitor_rank": result.competitor_rank,
                "source": result.source,
                "notes": result.notes,
            }
        )

    fields, existing = read_baseline_rows()
    appended = append_baseline_rows(fields, existing, new_rows)
    all_rows = existing + new_rows

    report_path = weekly_report_path(datetime.now(UTC))
    report_path.write_text(
        build_weekly_report(captured_at, measurements, appended, all_rows),
        encoding="utf-8",
    )

    print(f"captured_at={captured_at}")
    print(f"mobile_rank={measurements['mobile'].rank_position}")
    print(f"desktop_rank={measurements['desktop'].rank_position}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
