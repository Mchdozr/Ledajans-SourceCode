#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_DOMAIN = "ledajans.com"
PREFERRED_PATHS = ("/led-ekran/", "/")
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


@dataclass
class SerpHit:
    rank_position: int | str
    target_url: str
    search_engine: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if not path.endswith("/"):
        path += "/"
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def pick_ledajans_hit(urls: list[str]) -> tuple[int, str] | None:
    hits: list[tuple[int, str, int]] = []
    for index, raw in enumerate(urls, start=1):
        parsed = urlparse(raw)
        if TARGET_DOMAIN not in parsed.netloc.lower():
            continue
        path = parsed.path or "/"
        priority = len(PREFERRED_PATHS)
        for pref_index, pref in enumerate(PREFERRED_PATHS):
            if path == pref or path.startswith(pref.rstrip("/")):
                priority = pref_index
                break
        hits.append((index, normalize_url(raw), priority))
    if not hits:
        return None
    hits.sort(key=lambda item: (item[0], item[2]))
    best_rank, best_url, _ = hits[0]
    return best_rank, best_url


def first_competitor(urls: list[str], led_rank: int) -> tuple[str, str]:
    for index, raw in enumerate(urls, start=1):
        if index == led_rank:
            continue
        host = urlparse(raw).netloc.lower()
        if TARGET_DOMAIN in host or not host:
            continue
        return host, str(index)
    return "", ""


def fetch_serper(query: str, api_key: str) -> list[str]:
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "gl": "tr", "hl": "tr", "num": 20},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    urls: list[str] = []
    for item in payload.get("organic", []):
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def fetch_serpapi(query: str, api_key: str) -> list[str]:
    response = requests.get(
        "https://serpapi.com/search.json",
        params={"q": query, "gl": "tr", "hl": "tr", "num": 20, "api_key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    urls: list[str] = []
    for item in payload.get("organic_results", []):
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def fetch_duckduckgo(query: str) -> list[str]:
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query, "kl": "tr-tr"},
        headers={"User-Agent": USER_AGENT, "Accept-Language": "tr-TR,tr;q=0.9"},
        timeout=30,
    )
    response.raise_for_status()
    links = re.findall(r'class="result__a"[^>]+href="([^"]+)"', response.text)
    urls: list[str] = []
    for href in links:
        if "uddg=" in href:
            match = re.search(r"uddg=([^&]+)", href)
            if match:
                urls.append(unquote(match.group(1)))
        elif href.startswith("http"):
            urls.append(href)
    return urls


def measure_query() -> SerpHit:
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()
    urls: list[str] = []
    engine = "google"
    source = ""

    if serper_key:
        urls = fetch_serper(QUERY, serper_key)
        source = "serper_api"
    elif serpapi_key:
        urls = fetch_serpapi(QUERY, serpapi_key)
        source = "serpapi"
    else:
        urls = fetch_duckduckgo(QUERY)
        engine = "duckduckgo"
        source = "duckduckgo_html_tr"

    picked = pick_ledajans_hit(urls)
    if not picked:
        return SerpHit(
            rank_position="not_found",
            target_url=f"https://{TARGET_DOMAIN}/",
            search_engine=engine,
            source=source,
            notes="ledajans.com ilk 20 sonuçta görünmedi",
        )

    rank, target_url = picked
    competitor, competitor_rank = first_competitor(urls, rank)
    note_parts = [f"organic_top20={len(urls)}"]
    if engine != "google":
        note_parts.append("Google API anahtarı yok; DuckDuckGo tr-tr proxy")
    else:
        note_parts.append("Google organic via API")

    return SerpHit(
        rank_position=rank,
        target_url=target_url,
        search_engine=engine,
        source=source,
        notes="; ".join(note_parts),
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
    )


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def append_baseline_row(captured_at: str, hit: SerpHit, device: str = "mobile") -> None:
    fields, rows = read_baseline_rows()
    row = {key: "" for key in fields}
    row.update(
        {
            "captured_at_utc": captured_at,
            "query": QUERY,
            "locale": LOCALE,
            "device": device,
            "search_engine": hit.search_engine,
            "target_url": hit.target_url,
            "rank_position": str(hit.rank_position),
            "primary_competitor": hit.primary_competitor,
            "competitor_rank": hit.competitor_rank,
            "source": hit.source,
            "notes": hit.notes,
        }
    )
    key = (row["captured_at_utc"], row["query"].lower(), row["source"], row["device"])
    existing = {
        (r["captured_at_utc"], r["query"].lower(), r.get("source", ""), r.get("device", ""))
        for r in rows
    }
    if key in existing:
        return
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow({field: row.get(field, "") for field in fields})


def led_ekran_history(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    history = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("rank_position", "") not in {"", "pending", "not_found", "top3", "top5", "top10", "top20"}
    ]

    def sort_key(row: dict[str, str]) -> str:
        return row.get("captured_at_utc", "")

    numeric = []
    for row in history:
        try:
            float(str(row["rank_position"]).replace(",", "."))
        except ValueError:
            continue
        numeric.append(row)
    numeric.sort(key=sort_key)
    return numeric[-8:]


def format_weekly_markdown(captured_at: str, hit: SerpHit) -> str:
    _, rows = read_baseline_rows()
    history = led_ekran_history(rows)
    report_date = captured_at[:10]
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Sıra: **{hit.rank_position}**",
        f"- Hedef URL: `{hit.target_url}`",
        f"- Motor: `{hit.search_engine}` | Kaynak: `{hit.source}`",
    ]
    if hit.primary_competitor:
        lines.append(
            f"- İlk rakip (organik): `{hit.primary_competitor}` (sıra {hit.competitor_rank})"
        )
    lines.extend(["", f"- Not: {hit.notes}", ""])

    gsc_rows = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY and row.get("source", "").startswith("gsc_")
    ]
    if gsc_rows:
        latest_gsc = sorted(gsc_rows, key=lambda row: row.get("captured_at_utc", ""))[-1]
        lines.extend(
            [
                "## GSC referans (son kayıt)",
                "",
                f"- Tarih: `{latest_gsc.get('captured_at_utc', '')}`",
                f"- Ortalama pozisyon: **{latest_gsc.get('rank_position', 'N/A')}**",
                f"- URL: `{latest_gsc.get('target_url', '')}`",
                f"- Not: {latest_gsc.get('notes', '')}",
                "",
            ]
        )

    if history:
        lines.extend(["## Son sayısal ölçümler", "", "| Tarih (UTC) | Sıra | Kaynak | URL |", "|---|---:|---|---|"])
        for row in history:
            lines.append(
                f"| {row.get('captured_at_utc', '')} | {row.get('rank_position', '')} | "
                f"{row.get('source', '')} | {row.get('target_url', '')} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Komut",
            "",
            "```bash",
            "cd /workspace && python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
            "",
            "## API (kesin Google için)",
            "",
            "- `SERPER_API_KEY` veya `SERPAPI_KEY` ortam değişkeni tanımlayın.",
            "- Bulut IP Google HTML scrape edemez; API olmadan DuckDuckGo tr-tr proxy kullanılır.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_weekly_report(captured_at: str, hit: SerpHit) -> Path:
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{captured_at[:10]}.md"
    report_path.write_text(format_weekly_markdown(captured_at, hit), encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    hit = measure_query()
    append_baseline_row(captured_at, hit)
    report_path = write_weekly_report(captured_at, hit)
    print(
        json.dumps(
            {
                "query": QUERY,
                "rank_position": hit.rank_position,
                "target_url": hit.target_url,
                "search_engine": hit.search_engine,
                "source": hit.source,
                "captured_at_utc": captured_at,
                "weekly_report": str(report_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
