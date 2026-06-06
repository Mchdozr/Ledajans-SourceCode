#!/usr/bin/env python3
"""SERP sıra izleme — Bing otomatik, Google manuel/browser doğrulama ile."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
REPORTS_DIR = ROOT / "AGENT-HUB" / "REPORTS"

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

DEFAULT_QUERY = "led ekran"
DEFAULT_TARGET = "https://ledajans.com/"
DEFAULT_LOCALE = "tr-TR"
UA_MOBILE = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return CSV_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or CSV_FIELDS)
        return fields, list(reader)


def append_rows(rows: list[dict[str, str]], fields: list[str]) -> int:
    existing = {(r.get("captured_at_utc"), r.get("query"), r.get("device"), r.get("source")) for r in read_baseline()[1]}
    to_write = [
        r
        for r in rows
        if (r.get("captured_at_utc"), r.get("query"), r.get("device"), r.get("source")) not in existing
    ]
    if not to_write:
        return 0
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in to_write:
            writer.writerow({k: row.get(k, "") for k in fields})
    return len(to_write)


def check_bing_rank(query: str, target_domain: str = "ledajans.com") -> tuple[int | None, str | None, list[str]]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}&cc=tr&setlang=tr"
    response = requests.get(
        url,
        headers={"User-Agent": UA_MOBILE, "Accept-Language": "tr-TR,tr;q=0.9"},
        timeout=25,
    )
    response.raise_for_status()
    urls: list[str] = []
    for match in re.finditer(r'<li class="b_algo"[\s\S]*?</li>', response.text):
        href_match = re.search(r'<a href="([^"]+)"', match.group(0))
        if href_match:
            urls.append(href_match.group(1))
    rank: int | None = None
    target_url: str | None = None
    for index, href in enumerate(urls, start=1):
        if target_domain in urlparse(href).netloc:
            rank = index
            target_url = href
            break
    top_hosts = [urlparse(u).netloc for u in urls[:10]]
    return rank, target_url, top_hosts


def latest_google_rank(query: str, device: str = "mobile") -> dict[str, str] | None:
    for row in reversed(read_baseline()[1]):
        if (
            row.get("query", "").lower() == query.lower()
            and row.get("device") == device
            and row.get("search_engine") == "google"
            and row.get("rank_position") not in ("", "pending", "N/A", "top3", "top5", "top10", "top20")
        ):
            try:
                float(row["rank_position"])
            except (TypeError, ValueError):
                continue
            return row
    return None


def week_start_label(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def build_weekly_markdown(
    captured_at: str,
    query: str,
    google_rank: str | None,
    google_source: str | None,
    bing_rank: int | None,
    bing_top: list[str],
    appended: int,
    prev_google: dict[str, str] | None = None,
) -> str:
    date_label = captured_at[:10]
    prev = prev_google
    prev_rank = prev.get("rank_position") if prev else None
    prev_date = (prev or {}).get("captured_at_utc", "")[:10]
    prev_source = (prev or {}).get("source", "")
    delta = ""
    if google_rank and prev_rank:
        try:
            delta_val = float(google_rank) - float(prev_rank)
            if delta_val < 0:
                delta = f"↑ {abs(delta_val):.0f} sıra iyileşme"
            elif delta_val > 0:
                delta = f"↓ {delta_val:.0f} sıra düşüş"
            else:
                delta = "değişim yok"
        except ValueError:
            delta = f"önceki: {prev_rank} ({prev_date})"

    lines = [
        f"# Haftalık SEO İzleme — {date_label}",
        "",
        "## SERP — led ekran",
        "",
        f"| Metrik | Değer |",
        f"|--------|-------|",
        f"| Ölçüm zamanı (UTC) | {captured_at} |",
        f"| Google (mobile, TR) | **{google_rank or 'N/A'}** |",
        f"| Google kaynak | {google_source or '—'} |",
        f"| Bing (mobile, TR) | {bing_rank or 'N/A'} |",
        f"| Hedef URL | {DEFAULT_TARGET} |",
        f"| Önceki Google kaydı | {prev_rank or '—'} ({prev_date or '—'}, {prev_source or '—'}) |",
        f"| Haftalık delta | {delta or '—'} |",
        "",
        "### Bing top 5 (referans)",
        "",
    ]
    for index, host in enumerate(bing_top[:5], start=1):
        lines.append(f"{index}. {host}")
    lines.extend(
        [
            "",
            "## GSC referans (son export)",
            "",
            "- `led ekran` avg position: **6.78** (2026-06-05, mobile aggregate)",
            "- Kaynak: `AGENT-HUB/DATA/gsc-performance-2026-06-05/Sorgular.csv`",
            "",
            "## CSV güncelleme",
            "",
            f"- `SERP-BASELINE.csv` eklenen satır: **{appended}**",
            "",
            "## Sonraki ölçüm",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-rank.py --google-mobile-rank <sıra>",
            "```",
            "",
            "Google otomatik taraması bulut IP'de engellenebilir; haftalık browser doğrulaması önerilir.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP sıra izleme ve baseline CSV güncelleme")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--target-url", default=DEFAULT_TARGET)
    parser.add_argument("--google-mobile-rank", type=int, help="Google TR mobile organik sıra")
    parser.add_argument("--google-notes", default="", help="Google ölçüm notları")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    captured_at = utc_now_iso()
    fields, _ = read_baseline()
    for col in CSV_FIELDS:
        if col not in fields:
            fields.append(col)

    bing_rank, bing_url, bing_top = check_bing_rank(args.query)
    rows: list[dict[str, str]] = []

    if args.google_mobile_rank is not None:
        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": args.query,
                "locale": DEFAULT_LOCALE,
                "device": "mobile",
                "search_engine": "google",
                "target_url": bing_url or args.target_url,
                "rank_position": str(args.google_mobile_rank),
                "source": "google_organic_browser_check",
                "notes": args.google_notes
                or f"Google TR mobile organik sıra; rakip #1 TR: ledeca.com (~5)",
            }
        )

    if bing_rank is not None:
        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": args.query,
                "locale": DEFAULT_LOCALE,
                "device": "mobile",
                "search_engine": "bing",
                "target_url": bing_url or args.target_url,
                "rank_position": str(bing_rank),
                "source": "bing_organic_check",
                "notes": f"Top5: {', '.join(bing_top[:5])}",
            }
        )

    if args.dry_run:
        for row in rows:
            print(row)
        return 0

    prev_google = latest_google_rank(args.query)
    appended = append_rows(rows, fields)
    weekly_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{week_start_label(datetime.now(timezone.utc))}.md"
    google_rank = str(args.google_mobile_rank) if args.google_mobile_rank is not None else None
    weekly_path.write_text(
        build_weekly_markdown(
            captured_at,
            args.query,
            google_rank,
            "google_organic_browser_check" if google_rank else None,
            bing_rank,
            bing_top,
            appended,
            prev_google,
        ),
        encoding="utf-8",
    )

    report_path = REPORTS_DIR / f"serp-check-{args.query.replace(' ', '-')}-{captured_at[:10]}.md"
    report_path.write_text(
        f"# SERP Check — {args.query}\n\n"
        f"- captured_at_utc: {captured_at}\n"
        f"- google_mobile_rank: {google_rank or 'N/A'}\n"
        f"- bing_mobile_rank: {bing_rank or 'N/A'}\n"
        f"- baseline_appended: {appended}\n",
        encoding="utf-8",
    )

    print(f"google_mobile_rank={google_rank}")
    print(f"bing_mobile_rank={bing_rank}")
    print(f"baseline_appended={appended}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
