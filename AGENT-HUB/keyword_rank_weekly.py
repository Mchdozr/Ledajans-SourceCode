#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
GSC_DATA_DIR = HUB / "DATA"

QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_DOMAIN = "ledajans.com"
DEVICES = ("mobile", "desktop")
USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        url = f"https://{url}"
    return url + "/" if url.count("/") == 2 else url


def find_domain_rank(urls: list[str], domain: str) -> tuple[int | None, str | None]:
    for index, url in enumerate(urls, start=1):
        if domain in url.lower():
            return index, url
    return None, None


def fetch_serper(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return [], ""
    payload = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
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
    urls = [item.get("link", "") for item in data.get("organic", []) if item.get("link")]
    return urls, "serper_google"


def fetch_serpapi(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return [], ""
    params = {
        "engine": "google",
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    urls = [item.get("link", "") for item in data.get("organic_results", []) if item.get("link")]
    return urls, "serpapi_google"


def latest_gsc_queries_file() -> Path | None:
    candidates = sorted(GSC_DATA_DIR.glob("gsc-performance-*/Sorgular.csv"), reverse=True)
    return candidates[0] if candidates else None


def gsc_export_age_days(path: Path) -> int:
    match = re.search(r"gsc-performance-(\d{4}-\d{2}-\d{2})", path.parent.name)
    if match:
        export_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
        return (datetime.now(UTC) - export_date).days
    return (datetime.now(UTC) - datetime.fromtimestamp(path.stat().st_mtime, UTC)).days


def fetch_gsc(query: str) -> tuple[str | None, str, str]:
    path = latest_gsc_queries_file()
    if not path:
        return None, "", ""
    age_days = gsc_export_age_days(path)
    if age_days > 7:
        return None, "", f"GSC export {age_days} gün eski; atlandı"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        name = (row.get("En çok yapılan sorgular") or "").strip().lower()
        if name == query.lower():
            position = (row.get("Pozisyon") or "").strip()
            clicks = (row.get("Tıklamalar") or "").strip()
            impressions = (row.get("Gösterimler") or "").strip()
            ctr = (row.get("TO") or "").strip()
            source = f"gsc_performance_{path.parent.name.removeprefix('gsc-performance-')}"
            notes = (
                f"avg_position={position}; Clicks={clicks}; Impressions={impressions}; CTR={ctr}; "
                f"export_age_days={age_days}"
            )
            return position, source, notes
    return None, "", "GSC export içinde sorgu bulunamadı"


def fetch_duckduckgo(query: str, device: str) -> tuple[list[str], str]:
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query, "kl": "tr-tr"},
        headers={"User-Agent": USER_AGENTS[device]},
        timeout=30,
    )
    response.raise_for_status()
    blocks = re.findall(
        r'<div class="result results_links[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        response.text,
        re.S,
    )
    urls: list[str] = []
    for block in blocks:
        match = re.search(r'class="result__a"[^>]*href="([^"]+)"', block)
        if not match:
            continue
        href = match.group(1)
        if "uddg=" in href:
            href = unquote(re.search(r"uddg=([^&]+)", href).group(1))
        urls.append(href)
    return urls, "duckduckgo_html_tr"


def measure_device(device: str, captured_at: str) -> dict[str, str]:
    rank: int | str | None = None
    target_url = ""
    source = ""
    notes = ""

    for fetcher in (fetch_serper, fetch_serpapi):
        try:
            urls, src = fetcher(QUERY, device)
        except requests.RequestException:
            urls, src = [], ""
        if urls:
            rank, target_url = find_domain_rank(urls, TARGET_DOMAIN)
            source = src
            notes = f"Google organic via {src}; device={device}"
            break

    if rank is None and not source:
        urls, src = fetch_duckduckgo(QUERY, device)
        rank, target_url = find_domain_rank(urls, TARGET_DOMAIN)
        source = src
        if rank is None:
            notes = "ledajans.com ilk 10 sonuçta yok; Google ile birebir değil"
        else:
            notes = (
                f"DDG HTML kl=tr-tr; Google organic proxy değil; "
                f"top_competitor={urls[0] if urls else 'n/a'}"
            )

    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": "google" if "google" in source or source.startswith("gsc_") else "duckduckgo",
        "target_url": target_url or "https://ledajans.com/",
        "rank_position": str(rank) if rank is not None else "not_found",
        "serp_features": "",
        "primary_competitor": "",
        "competitor_rank": "",
        "source": source or "unavailable",
        "notes": notes,
    }


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    existing = read_baseline_rows()
    keys = {
        (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        for row in existing
    }
    to_append = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in keys
    ]
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})
    return len(to_append)


def previous_led_ekran_rows(before_utc: str | None = None) -> list[dict[str, str]]:
    before_date = before_utc[:10] if before_utc else None
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY
        and row.get("rank_position", "") not in {"", "pending", "not_found", "top3", "top5", "top10", "top20"}
        and (before_utc is None or row.get("captured_at_utc", "") < before_utc)
        and (before_date is None or row.get("captured_at_utc", "")[:10] < before_date)
    ]
    rows.sort(key=lambda item: item.get("captured_at_utc", ""), reverse=True)
    return rows


def format_delta(current: str, previous: str | None) -> str:
    if previous is None:
        return "önceki ölçüm yok"
    try:
        cur = float(current)
        prev = float(previous)
    except ValueError:
        return "karşılaştırma N/A (farklı ölçüm tipi)"
    diff = prev - cur
    if diff > 0:
        return f"↑ {diff:.2f} sıra (iyileşme)"
    if diff < 0:
        return f"↓ {abs(diff):.2f} sıra (kayıp)"
    return "değişim yok"


def write_weekly_summary(rows: list[dict[str, str]], appended: int) -> Path:
    today = datetime.now(UTC).date()
    path = HUB / f"WEEKLY-MONITORING-{today.isoformat()}.md"
    batch_ts = rows[0]["captured_at_utc"] if rows else utc_now_iso()
    prior = previous_led_ekran_rows(before_utc=batch_ts)
    prior_by_device: dict[str, str] = {}
    for row in prior:
        device = row.get("device", "")
        if device and device not in prior_by_device:
            prior_by_device[device] = row.get("rank_position", "")

    lines = [
        f"# Haftalık SEO İzleme — {today.isoformat()}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm UTC: `{rows[0]['captured_at_utc']}`",
        f"- Script: `python3 AGENT-HUB/keyword_rank_weekly.py`",
        f"- `SERP-BASELINE.csv` yeni satır: **{appended}**",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Not |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['device']} | **{row['rank_position']}** | {row['target_url']} | "
            f"{row['source']} | {row['notes']} |"
        )

    lines.extend(["", "## Trend (önceki sayısal ölçüme göre)", ""])
    for row in rows:
        prev = prior_by_device.get(row["device"])
        lines.append(
            f"- **{row['device']}**: {row['rank_position']} — {format_delta(row['rank_position'], prev)}"
        )
        if prev:
            lines.append(f"  - Önceki: {prev}")

    if prior:
        latest_prior = prior[0]
        lines.extend(
            [
                "",
                f"- Son önceki kayıt: `{latest_prior.get('captured_at_utc')}` "
                f"({latest_prior.get('source')}) → sıra **{latest_prior.get('rank_position')}**",
            ]
        )
        if latest_prior.get("source", "").startswith("gsc_"):
            lines.append(
                "  - Not: GSC `avg_position` ile DDG organic sırası doğrudan karşılaştırılmamalı."
            )

    lines.extend(
        [
            "",
            "## Cron",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "## Sonraki hafta",
            "",
            "- `SERPER_API_KEY` veya `SERPAPI_KEY` tanımlanırsa Google organic ölçümü otomatik önceliklenir.",
            "- GSC Performance export ≤7 gün taze ise ortalama pozisyon yedek kaynak olarak kullanılır.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    captured_at = utc_now_iso()
    measured = [measure_device(device, captured_at) for device in DEVICES]
    appended = append_baseline_rows(measured)
    weekly_path = write_weekly_summary(measured, appended)
    print(json.dumps({"appended": appended, "weekly": str(weekly_path), "rows": measured}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
