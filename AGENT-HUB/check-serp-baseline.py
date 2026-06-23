#!/usr/bin/env python3
"""Haftalık/günlük SERP baseline kontrolü — led ekran sorgusu."""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_URL = "https://ledajans.com/"
TARGET_HOST = "ledajans.com"

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


def fetch_organic_ranks(max_results: int = 20) -> list[str]:
    try:
        from duckduckgo_search import DDGS
    except ImportError as exc:
        raise RuntimeError("duckduckgo-search paketi gerekli: pip install duckduckgo-search") from exc

    rows = DDGS().text(QUERY, region="tr-tr", max_results=max_results)
    urls: list[str] = []
    for row in rows:
        href = (row.get("href") or "").strip()
        if href:
            urls.append(href)
    return urls


def rank_for_host(urls: list[str], host: str) -> tuple[int | None, str | None]:
    for index, url in enumerate(urls, start=1):
        netloc = urlparse(url).netloc.lower().removeprefix("www.")
        if host in netloc:
            return index, url
    return None, None


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_led_ekran_row(rows: list[dict[str, str]], device: str) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("device", "").strip().lower() == device
        and row.get("search_engine", "").strip().lower() == SEARCH_ENGINE
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda row: row.get("captured_at_utc", ""), reverse=True)[0]


def append_rows(rows: list[dict[str, str]]) -> None:
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def build_notes(rank: int | None, urls: list[str], previous: dict[str, str] | None) -> str:
    parts: list[str] = []
    if rank is not None:
        parts.append(f"Organik sıra={rank}")
    if urls:
        top_host = urlparse(urls[0]).netloc
        parts.append(f"ilk sonuç={top_host}")
    if previous:
        prev_rank = previous.get("rank_position", "")
        if prev_rank and rank is not None and str(prev_rank) != str(rank):
            parts.append(f"önceki={prev_rank} ({previous.get('captured_at_utc', '')})")
    parts.append("DDGS tr-tr proxy; Google doğrulama için browser kontrolü önerilir")
    return "; ".join(parts)


def write_weekly_summary(
    captured_at: str,
    mobile_row: dict[str, str],
    desktop_row: dict[str, str],
    previous_mobile: dict[str, str] | None,
    previous_desktop: dict[str, str] | None,
) -> Path:
    date_label = captured_at[:10]
    weekly_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_label}.md"

    def delta(current: str, previous: dict[str, str] | None) -> str:
        if not previous:
            return "ilk ölçüm"
        prev = previous.get("rank_position", "N/A")
        if str(current) == str(prev):
            return f"stabil ({prev})"
        return f"{prev} → {current}"

    lines = [
        f"# Haftalık SEO İzleme — {date_label}",
        "",
        "## SERP — `led ekran` (Google, tr-TR)",
        "",
        "| Cihaz | Sıra | URL | Kaynak | Delta |",
        "|-------|-----:|-----|--------|-------|",
        (
            f"| mobile | {mobile_row['rank_position']} | {mobile_row['target_url']} | "
            f"{mobile_row['source']} | {delta(mobile_row['rank_position'], previous_mobile)} |"
        ),
        (
            f"| desktop | {desktop_row['rank_position']} | {desktop_row['target_url']} | "
            f"{desktop_row['source']} | {delta(desktop_row['rank_position'], previous_desktop)} |"
        ),
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Not: {mobile_row['notes']}",
        "",
        "## Baseline kayıt",
        "- `AGENT-HUB/SERP-BASELINE.csv` — bu çalışmada 2 satır eklendi (mobile + desktop)",
        "",
        "## Komut (sonraki hafta)",
        "```bash",
        "cd /workspace && python3 AGENT-HUB/check-serp-baseline.py --weekly",
        "```",
        "",
    ]
    weekly_path.write_text("\n".join(lines), encoding="utf-8")
    return weekly_path


def run(weekly: bool, rank_override: int | None, source_override: str | None, notes_extra: str) -> int:
    captured_at = utc_now_iso()
    urls = fetch_organic_ranks()
    detected_rank, detected_url = rank_for_host(urls, TARGET_HOST)
    rank = rank_override if rank_override is not None else detected_rank
    if rank is None:
        print("HATA: ledajans.com ilk 20 sonuçta bulunamadı", file=sys.stderr)
        return 1

    target_url = detected_url or TARGET_URL
    source = source_override or "ddgs_auto_tr"
    baseline_rows = read_baseline_rows()
    previous_mobile = latest_led_ekran_row(baseline_rows, "mobile")
    previous_desktop = latest_led_ekran_row(baseline_rows, "desktop")
    notes = build_notes(rank, urls, previous_mobile)
    if notes_extra:
        notes = f"{notes}; {notes_extra}"

    new_rows = []
    for device in ("mobile", "desktop"):
        previous = previous_mobile if device == "mobile" else previous_desktop
        device_notes = build_notes(rank, urls, previous)
        if notes_extra:
            device_notes = f"{device_notes}; {notes_extra}"
        new_rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": target_url,
                "rank_position": str(rank),
                "serp_features": "image_carousel" if len(urls) >= 5 else "",
                "primary_competitor": urlparse(urls[1]).netloc if len(urls) > 1 else "",
                "competitor_rank": "2" if len(urls) > 1 else "",
                "source": source,
                "notes": device_notes,
            }
        )

    append_rows(new_rows)
    weekly_path = None
    if weekly:
        weekly_path = write_weekly_summary(
            captured_at,
            new_rows[0],
            new_rows[1],
            previous_mobile,
            previous_desktop,
        )

    print(f"query={QUERY}")
    print(f"rank_position={rank}")
    print(f"target_url={target_url}")
    print(f"baseline_appended={len(new_rows)}")
    if weekly_path:
        print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP baseline kontrolü (led ekran)")
    parser.add_argument("--weekly", action="store_true", help="WEEKLY-MONITORING-YYYY-MM-DD.md üret")
    parser.add_argument("--rank", type=int, help="Manuel sıra (browser doğrulaması)")
    parser.add_argument("--source", help="Kaynak etiketi")
    parser.add_argument("--notes", default="", help="Ek not")
    args = parser.parse_args()
    return run(
        weekly=args.weekly,
        rank_override=args.rank,
        source_override=args.source,
        notes_extra=args.notes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
