#!/usr/bin/env python3
"""Haftalık/günlük 'led ekran' SERP ölçümü → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"

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

USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def week_monitoring_path(run_date: datetime) -> Path:
    return HUB / f"WEEKLY-MONITORING-{run_date.strftime('%Y-%m-%d')}.md"


def extract_domain(url: str) -> str:
    return re.sub(r"^https?://(?:www\.)?", "", url).split("/")[0].lower()


def find_ledajans_rank(links: list[str]) -> tuple[int | None, str, str]:
    organic: list[str] = []
    seen: set[str] = set()
    for link in links:
        domain = extract_domain(link)
        if not domain or domain.endswith("duckduckgo.com") or domain in seen:
            continue
        seen.add(domain)
        organic.append(link)

    rank: int | None = None
    target_url = TARGET_URL
    for index, link in enumerate(organic, start=1):
        if TARGET_DOMAIN in link.lower():
            rank = index
            target_url = link if link.endswith("/") or "/led-ekran" in link else link
            break

    competitor_url = ""
    competitor_rank = ""
    if rank == 1 and len(organic) > 1:
        competitor_url = organic[1]
        competitor_rank = "2"
    elif rank and rank > 1:
        competitor_url = organic[0]
        competitor_rank = "1"

    return rank, competitor_url, competitor_rank


def fetch_serper(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return [], "serper_skipped"

    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 30}
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
    links = [item.get("link", "") for item in data.get("organic", []) if item.get("link")]
    return links, "serper_api"


def fetch_serpapi(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return [], "serpapi_skipped"

    params = {
        "engine": "google",
        "q": query,
        "hl": "tr",
        "gl": "tr",
        "num": 30,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"

    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    links = [item.get("link", "") for item in data.get("organic_results", []) if item.get("link")]
    return links, "serpapi"


def fetch_ddg_lite(query: str, device: str) -> tuple[list[str], str]:
    headers = {
        "User-Agent": USER_AGENTS[device],
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    response = requests.post(
        "https://lite.duckduckgo.com/lite/",
        data={"q": query},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    links = re.findall(r'href="(https?://[^"]+)"', response.text)
    return links, "ddg_lite_proxy"


def fetch_rank(query: str, device: str) -> dict[str, str]:
    errors: list[str] = []
    for fetcher in (fetch_serper, fetch_serpapi, fetch_ddg_lite):
        try:
            links, source = fetcher(query, device)
            if not links:
                continue
            rank, competitor_url, competitor_rank = find_ledajans_rank(links)
            if rank is None:
                errors.append(f"{source}: ledajans not in top {len(links)}")
                continue
            return {
                "rank_position": str(rank),
                "target_url": TARGET_URL,
                "primary_competitor": competitor_url,
                "competitor_rank": competitor_rank,
                "source": source,
                "notes": f"Organic proxy rank; top-{len(links)} snapshot; device={device}",
            }
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fetcher.__name__}: {exc}")

    return {
        "rank_position": "N/A",
        "target_url": TARGET_URL,
        "primary_competitor": "",
        "competitor_rank": "",
        "source": "unavailable",
        "notes": "; ".join(errors) or "No SERP provider available",
    }


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    day = row["captured_at_utc"][:10]
    return day, row["query"].lower(), row["device"], row["source"]


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    existing = read_baseline_rows()
    existing_keys = {row_key(row) for row in existing}

    to_append: list[dict[str, str]] = []
    for row in rows:
        if row_key(row) not in existing_keys:
            to_append.append(row)
            existing_keys.add(row_key(row))

    if not to_append:
        return 0

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})

    return len(to_append)


def load_week_history(query: str, days: int = 14) -> list[dict[str, str]]:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").lower() == query.lower() and row.get("device") == "mobile"
    ]
    rows.sort(key=lambda item: item.get("captured_at_utc", ""), reverse=True)
    return rows[:days]


def update_weekly_monitoring(captured_at: str, measurements: list[dict[str, str]]) -> Path:
    run_dt = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    path = week_monitoring_path(run_dt)
    history = load_week_history(QUERY)

    mobile = next((row for row in measurements if row["device"] == "mobile"), None)
    desktop = next((row for row in measurements if row["device"] == "desktop"), None)

    prev_mobile = history[1] if len(history) > 1 else None
    delta = ""
    if mobile and prev_mobile and mobile["rank_position"] != "N/A" and prev_mobile.get("rank_position"):
        try:
            delta_val = int(prev_mobile["rank_position"]) - int(mobile["rank_position"])
            if delta_val > 0:
                delta = f" (▲ {delta_val} vs önceki mobile)"
            elif delta_val < 0:
                delta = f" (▼ {abs(delta_val)} vs önceki mobile)"
            else:
                delta = " (stabil vs önceki mobile)"
        except ValueError:
            delta = ""

    lines = [
        f"# Haftalık SEO İzleme — {run_dt.strftime('%Y-%m-%d')}",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        f"- Sorgu: **{QUERY}** | locale: `{LOCALE}` | motor: `{SEARCH_ENGINE}`",
        "",
        "## SERP — led ekran",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Rakip | Not |",
        "|---|---:|---|---|---|---|",
    ]

    for row in measurements:
        lines.append(
            f"| {row['device']} | **#{row['rank_position']}** | {row['target_url']} | "
            f"`{row['source']}` | {row.get('primary_competitor') or '—'} | {row.get('notes', '')} |"
        )

    if mobile:
        lines.extend(
            [
                "",
                f"**Özet:** Mobile organic sıra **#{mobile['rank_position']}**{delta}.",
            ]
        )
    if desktop:
        lines.append(f"Desktop organic sıra **#{desktop['rank_position']}**.")

    lines.extend(
        [
            "",
            "## Son ölçümler (mobile)",
            "",
            "| Tarih (UTC) | Sıra | Kaynak |",
            "|---|---:|---|",
        ]
    )
    for row in history[:8]:
        lines.append(
            f"| {row.get('captured_at_utc', '')[:10]} | {row.get('rank_position', '')} | `{row.get('source', '')}` |"
        )

    lines.extend(
        [
            "",
            "## Veri dosyaları",
            "",
            f"- Baseline: `AGENT-HUB/SERP-BASELINE.csv` (+{len(measurements)} satır bu çalışmada)",
            "- GSC avg_position ile canlı organic sıra farklı metriklerdir.",
            "",
            "## Sonraki çalışma",
            "",
            "```bash",
            "python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    captured_at = utc_now_iso()
    measurements: list[dict[str, str]] = []

    for device in ("mobile", "desktop"):
        result = fetch_rank(QUERY, device)
        measurements.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": result["target_url"],
                "rank_position": result["rank_position"],
                "serp_features": "",
                "primary_competitor": result["primary_competitor"],
                "competitor_rank": result["competitor_rank"],
                "source": result["source"],
                "notes": result["notes"],
            }
        )

    appended = append_baseline_rows(measurements)
    weekly_path = update_weekly_monitoring(captured_at, measurements)

    summary = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "mobile_rank": measurements[0]["rank_position"],
        "desktop_rank": measurements[1]["rank_position"],
        "source": measurements[0]["source"],
        "baseline_appended": appended,
        "weekly_report": str(weekly_path.relative_to(ROOT)),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
