#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
DEFAULT_QUERY = "led ekran"
DEFAULT_TARGET = "https://ledajans.com/"
DEFAULT_LOCALE = "tr-TR"
DEFAULT_ENGINE = "google"
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


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return CSV_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or CSV_FIELDS)
        return fields, list(reader)


def fetch_serper(query: str, device: str) -> tuple[int | None, str, str]:
    key = os.environ.get("SERPER_API_KEY") or os.environ.get("SERPER_DEV_API_KEY")
    if not key:
        return None, DEFAULT_TARGET, ""
    payload = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
    }
    if device == "mobile":
        payload["device"] = "mobile"
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=json.dumps(payload).encode(),
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    return _rank_from_links(
        [item.get("link", "") for item in data.get("organic", [])],
        "ledajans.com",
    )


def fetch_serpapi(query: str, device: str) -> tuple[int | None, str, str]:
    key = os.environ.get("SERPAPI_KEY") or os.environ.get("SERPAPI_API_KEY")
    if not key:
        return None, DEFAULT_TARGET, ""
    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "num": 20,
            "device": device,
            "api_key": key,
        }
    )
    with urllib.request.urlopen(f"https://serpapi.com/search.json?{params}", timeout=30) as response:
        data = json.load(response)
    return _rank_from_links(
        [item.get("link", "") for item in data.get("organic_results", [])],
        "ledajans.com",
    )


def fetch_ddg_lite(query: str) -> tuple[int | None, str, str]:
    params = urllib.parse.urlencode({"q": query, "kl": "tr-tr"})
    url = f"https://lite.duckduckgo.com/lite/?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LedajansSERPBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    links = [urllib.parse.unquote(match) for match in re.findall(r"uddg=([^&\"]+)", html)]
    return _rank_from_links(links[:30], "ledajans.com")


def _rank_from_links(links: list[str], domain: str) -> tuple[int | None, str, str]:
    for index, link in enumerate(links, start=1):
        if domain in link:
            return index, link, ""
    return None, DEFAULT_TARGET, "not_in_top_results"


def resolve_rank(
    query: str,
    device: str,
    override: int | None,
    override_url: str | None,
) -> tuple[int | str, str, str, str]:
    if override is not None:
        url = override_url or DEFAULT_TARGET
        return override, url, "google_live_check", "Manuel/doğrulanmış canlı Google ölçümü"

    for source, fetcher in (
        ("serper_api", lambda: fetch_serper(query, device)),
        ("serpapi", lambda: fetch_serpapi(query, device)),
        ("ddg_lite_proxy", lambda: fetch_ddg_lite(query)),
    ):
        try:
            rank, url, note = fetcher()
        except Exception as exc:  # noqa: BLE001 — kaynak fallback zinciri
            note = str(exc)
            rank = None
            url = DEFAULT_TARGET
        if rank is not None:
            suffix = f"; {note}" if note else ""
            return rank, url, source, f"Otomatik ölçüm ({source}){suffix}"

    return "not_in_top_20", DEFAULT_TARGET, "unavailable", "API anahtarı yok; Google scrape engelli"


def row_exists(rows: list[dict[str, str]], captured_day: str, query: str, device: str, source: str) -> bool:
    for row in rows:
        captured = row.get("captured_at_utc", "")[:10]
        if (
            captured == captured_day
            and row.get("query", "").lower() == query.lower()
            and row.get("device", "") == device
            and row.get("source", "") == source
        ):
            return True
    return False


def build_row(
    captured_at: str,
    query: str,
    device: str,
    rank: int | str,
    target_url: str,
    source: str,
    notes: str,
    primary_competitor: str = "",
    competitor_rank: str = "",
) -> dict[str, str]:
    return {
        "captured_at_utc": captured_at,
        "query": query,
        "locale": DEFAULT_LOCALE,
        "device": device,
        "search_engine": DEFAULT_ENGINE,
        "target_url": target_url,
        "rank_position": str(rank),
        "serp_features": "",
        "primary_competitor": primary_competitor,
        "competitor_rank": competitor_rank,
        "source": source,
        "notes": notes,
    }


def latest_led_ekran_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    matches = [row for row in rows if row.get("query", "").lower() == DEFAULT_QUERY.lower()]
    matches.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    by_device: dict[str, dict[str, str]] = {}
    for row in matches:
        device = row.get("device", "")
        if device and device not in by_device:
            by_device[device] = row
    return by_device


def write_weekly_report(
    report_date: str,
    captured_at: str,
    new_rows: list[dict[str, str]],
    prior_rows: list[dict[str, str]],
) -> Path:
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    previous = latest_led_ekran_rows(prior_rows)

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Anahtar kelime: **{DEFAULT_QUERY}**",
        f"- Hedef URL: `{DEFAULT_TARGET}`",
        "",
        "## SERP sırası (led ekran)",
        "",
        "| Cihaz | Sıra | URL | Kaynak | Not |",
        "|---|---:|---|---|---|",
    ]
    for row in new_rows:
        lines.append(
            f"| {row['device']} | {row['rank_position']} | {row['target_url']} | "
            f"{row['source']} | {row['notes']} |"
        )

    lines.extend(["", "## Önceki ölçümle karşılaştırma", ""])
    for row in new_rows:
        device = row["device"]
        prev = previous.get(device)
        if not prev:
            lines.append(f"- **{device}:** önceki kayıt yok")
            continue
        delta = _delta_text(prev.get("rank_position", ""), row["rank_position"])
        lines.append(
            f"- **{device}:** {prev.get('rank_position')} → {row['rank_position']} ({delta}); "
            f"önceki tarih `{prev.get('captured_at_utc', '')}` kaynak `{prev.get('source', '')}`"
        )

    gsc_prev = next(
        (
            row
            for row in prior_rows
            if row.get("query", "").lower() == DEFAULT_QUERY.lower()
            and row.get("source", "").startswith("gsc_")
        ),
        None,
    )
    if gsc_prev:
        lines.extend(
            [
                "",
                "## GSC referans",
                "",
                f"- Son GSC avg position: **{gsc_prev.get('rank_position')}** "
                f"(`{gsc_prev.get('captured_at_utc', '')}`)",
                "- Canlı organic sıra ile GSC ortalama pozisyon farklı metriklerdir.",
            ]
        )

    lines.extend(
        [
            "",
            "## Sonraki adım",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "Opsiyonel: `SERPER_API_KEY` veya `SERPAPI_KEY` ile otomatik Google ölçümü.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _delta_text(previous: str, current: str) -> str:
    try:
        prev_val = float(previous)
        curr_val = float(current)
    except ValueError:
        return "karşılaştırılamadı"
    diff = prev_val - curr_val
    if diff > 0:
        return f"↑ {diff:.0f} sıra iyileşme"
    if diff < 0:
        return f"↓ {abs(diff):.0f} sıra düşüş"
    return "değişmedi"


def append_rows(fields: list[str], rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})
    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Haftalık led ekran SERP ölçümü")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--captured-at", default=utc_now_iso())
    parser.add_argument("--report-date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--mobile-rank", type=int, default=None)
    parser.add_argument("--desktop-rank", type=int, default=None)
    parser.add_argument("--target-url", default=DEFAULT_TARGET)
    parser.add_argument(
        "--mobile-competitor",
        default="ledinterleri.com",
        help="Birincil rakip domain (mobile)",
    )
    parser.add_argument(
        "--desktop-competitor",
        default="ledfon.com",
        help="Birincil rakip domain (desktop)",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fields, existing = read_baseline()
    captured_day = args.captured_at[:10]
    new_rows: list[dict[str, str]] = []

    device_overrides = {
        "mobile": args.mobile_rank,
        "desktop": args.desktop_rank,
    }
    competitors = {
        "mobile": (args.mobile_competitor, "1"),
        "desktop": (args.desktop_competitor, "1"),
    }

    for device, override in device_overrides.items():
        rank, url, source, notes = resolve_rank(args.query, device, override, args.target_url)
        if row_exists(existing, captured_day, args.query, device, source):
            print(f"skip_exists device={device} source={source}")
            continue
        competitor, competitor_rank = competitors[device]
        new_rows.append(
            build_row(
                captured_at=args.captured_at,
                query=args.query,
                device=device,
                rank=rank,
                target_url=url,
                source=source,
                notes=notes,
                primary_competitor=competitor,
                competitor_rank=competitor_rank,
            )
        )

    if args.dry_run:
        for row in new_rows:
            print(json.dumps(row, ensure_ascii=False))
        return 0

    appended = append_rows(fields, new_rows)
    report_path = write_weekly_report(args.report_date, args.captured_at, new_rows, existing)
    print(f"appended={appended}")
    print(f"report={report_path.relative_to(ROOT)}")
    for row in new_rows:
        print(f"{row['device']}_rank={row['rank_position']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
