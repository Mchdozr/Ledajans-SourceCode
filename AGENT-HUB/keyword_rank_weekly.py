#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü: SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_HOST = "ledajans.com"
SEARCH_ENGINE = "google"
DATA_DIR = HUB / "DATA"

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


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    return f"https://{host}{path}"


def find_target_rank(urls: list[str], host: str = TARGET_HOST) -> tuple[int | None, str | None]:
    seen_domains: set[str] = set()
    for raw in urls:
        normalized = normalize_url(raw)
        domain = urllib.parse.urlparse(normalized).netloc.lower().removeprefix("www.")
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        rank = len(seen_domains)
        if domain == host.lower():
            return rank, normalized
    return None, None


def fetch_serper(query: str, device: str) -> list[str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 20}
    if device == "mobile":
        payload["device"] = "mobile"
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=json.dumps(payload).encode(),
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    return [item.get("link", "") for item in data.get("organic", []) if item.get("link")]


def fetch_serpapi(query: str, device: str) -> list[str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = {
        "engine": "google",
        "q": query,
        "hl": "tr",
        "gl": "tr",
        "num": 20,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return None
    return [item.get("link", "") for item in data.get("organic_results", []) if item.get("link")]


def fetch_duckduckgo(query: str, device: str) -> list[str]:
    body = urllib.parse.urlencode({"q": query, "kl": "tr-tr", "b": ""}).encode()
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=body,
        headers={
            "User-Agent": USER_AGENTS[device],
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', html)
    urls: list[str] = []
    for link in links:
        if "uddg=" in link:
            match = re.search(r"uddg=([^&]+)", link)
            if match:
                link = urllib.parse.unquote(match.group(1))
        urls.append(link)
    return urls


def latest_gsc_export_dir(max_age_days: int = 7) -> Path | None:
    if not DATA_DIR.is_dir():
        return None
    candidates: list[tuple[datetime, Path]] = []
    for path in DATA_DIR.iterdir():
        if not path.is_dir() or not path.name.startswith("gsc-performance-"):
            continue
        date_part = path.name.removeprefix("gsc-performance-")
        try:
            captured = datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            continue
        age = datetime.now(UTC) - captured
        if age.days <= max_age_days:
            candidates.append((captured, path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def fetch_gsc_position(query: str) -> tuple[str | None, str]:
    export_dir = latest_gsc_export_dir()
    if export_dir is None:
        return None, "GSC export yok veya 7 günden eski"
    queries_path = export_dir / "Sorgular.csv"
    if not queries_path.is_file():
        return None, f"{export_dir.name}: Sorgular.csv bulunamadı"
    with queries_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        name = (row.get("En çok yapılan sorgular") or "").strip().lower()
        if name == query.lower():
            position = (row.get("Pozisyon") or "").strip()
            clicks = (row.get("Tıklamalar") or "").strip()
            impressions = (row.get("Gösterimler") or "").strip()
            ctr = (row.get("TO") or "").strip()
            note = (
                f"GSC avg_position={position}; Clicks={clicks}; "
                f"Impressions={impressions}; CTR={ctr}; export={export_dir.name}"
            )
            return position, note
    return None, f"{export_dir.name}: sorgu bulunamadı"


def collect_measurement(device: str) -> dict[str, str]:
    captured_at = utc_now_iso()
    urls: list[str] | None = None
    source = ""
    notes = ""

    for provider, fetcher in (
        ("serper_api", fetch_serper),
        ("serpapi", fetch_serpapi),
    ):
        urls = fetcher(QUERY, device)
        if urls:
            source = provider
            notes = "Google organic API"
            break

    if not urls:
        urls = fetch_duckduckgo(QUERY, device)
        source = "duckduckgo_html_tr"
        notes = (
            "DDG HTML kl=tr-tr; Google organic ile birebir olmayabilir. "
            "Kesin ölçüm için SERPER_API_KEY veya SERPAPI_KEY."
        )

    rank, target_url = find_target_rank(urls)
    competitor = urls[0] if urls else ""
    competitor_host = urllib.parse.urlparse(competitor).netloc if competitor else ""

    gsc_position, gsc_note = fetch_gsc_position(QUERY)
    if gsc_position:
        notes = f"{notes} | {gsc_note}"

    rank_text = str(rank) if rank is not None else "not_found"
    if target_url is None:
        target_url = f"https://{TARGET_HOST}/"

    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": target_url,
        "rank_position": rank_text,
        "serp_features": "",
        "primary_competitor": competitor_host,
        "competitor_rank": "1" if competitor_host else "",
        "source": source,
        "notes": notes,
        "gsc_avg_position": gsc_position or "",
    }


def read_baseline_fields() -> list[str]:
    if not BASELINE_PATH.is_file():
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


def append_baseline_rows(rows: list[dict[str, str]]) -> None:
    fields = read_baseline_fields()
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_recent_baseline(query: str, limit: int = 8) -> list[dict[str, str]]:
    if not BASELINE_PATH.is_file():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("query", "").lower() == query.lower()]
    rows.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    return rows[:limit]


def update_weekly_report(measurements: list[dict[str, str]]) -> Path:
    today = datetime.now(UTC).date()
    week_start = today
    report_path = HUB / f"WEEKLY-MONITORING-{week_start.isoformat()}.md"
    history = load_recent_baseline(QUERY, limit=12)

    lines = [
        f"# Haftalık SEO İzleme — {week_start.isoformat()}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm UTC: `{measurements[0]['captured_at_utc']}`",
        "",
        "| Cihaz | Organic sıra | Hedef URL | Kaynak | Rakip #1 |",
        "|---|---:|---|---|---|",
    ]
    for row in measurements:
        lines.append(
            f"| {row['device']} | **{row['rank_position']}** | {row['target_url']} | "
            f"{row['source']} | {row['primary_competitor']} |"
        )

    gsc_values = [row.get("gsc_avg_position", "") for row in measurements if row.get("gsc_avg_position")]
    if gsc_values:
        lines.extend(
            [
                "",
                f"- GSC avg position (son export): **{gsc_values[0]}** (ortalama pozisyon; organic sıra değil)",
            ]
        )

    lines.extend(["", "## Son ölçümler (`SERP-BASELINE.csv`)", "", "| captured_at_utc | device | rank | source |", "|---|---|---:|---|"])
    for row in history:
        lines.append(
            f"| {row.get('captured_at_utc', '')} | {row.get('device', '')} | "
            f"{row.get('rank_position', '')} | {row.get('source', '')} |"
        )

    lines.extend(
        [
            "",
            "## Notlar",
            "",
            "- Organic sıra: DDG/Serper/SerpAPI snapshot.",
            "- GSC `avg_position` ile organic sıra doğrudan karşılaştırılmamalı.",
            "- Cron: `0 6 * * *` UTC → `bash AGENT-HUB/run-keyword-rank-weekly.sh`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    measurements = [collect_measurement(device) for device in ("mobile", "desktop")]
    baseline_rows = [{key: value for key, value in row.items() if key != "gsc_avg_position"} for row in measurements]
    append_baseline_rows(baseline_rows)
    report_path = update_weekly_report(measurements)

    for row in measurements:
        print(
            f"{row['device']}: rank={row['rank_position']} url={row['target_url']} "
            f"source={row['source']} competitor={row['primary_competitor']}"
        )
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
