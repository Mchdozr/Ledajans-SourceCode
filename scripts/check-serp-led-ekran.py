#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP snapshot'ını SERP-BASELINE.csv ve haftalık özete yazar."""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_URL = "https://ledajans.com/"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline_fields() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def latest_led_ekran_rows() -> dict[str, dict[str, str]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    latest: dict[str, dict[str, str]] = {}
    for row in reversed(rows):
        if row.get("query", "").strip().lower() != QUERY:
            continue
        device = row.get("device", "").strip().lower()
        if device and device not in latest:
            latest[device] = row
    return latest


def append_rows(
    fields: list[str],
    captured_at: str,
    mobile_rank: str,
    desktop_rank: str,
    target_url: str,
    source: str,
    notes: str,
    serp_features: str,
    dry_run: bool,
) -> list[dict[str, str]]:
    new_rows: list[dict[str, str]] = []
    for device, rank in (("mobile", mobile_rank), ("desktop", desktop_rank)):
        row = {field: "" for field in fields}
        row.update(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": target_url,
                "rank_position": rank,
                "serp_features": serp_features,
                "source": source,
                "notes": notes,
            }
        )
        new_rows.append(row)

    if dry_run:
        for row in new_rows:
            print(
                f"DRY_RUN append: device={row['device']} rank={row['rank_position']} "
                f"url={row['target_url']} source={row['source']}"
            )
        return new_rows

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        for row in new_rows:
            writer.writerow(row)
    return new_rows


def format_delta(device: str, new_rank: str, previous: dict[str, str] | None) -> str:
    if not previous:
        return f"- **{device}**: {new_rank} (önceki kayıt yok)"
    old_rank = previous.get("rank_position", "N/A")
    old_date = previous.get("captured_at_utc", "?")
    old_source = previous.get("source", "?")
    return (
        f"- **{device}**: {new_rank} (önceki: {old_rank} @ {old_date}, kaynak: {old_source})"
    )


def update_weekly_summary(
    report_date: str,
    captured_at: str,
    mobile_rank: str,
    desktop_rank: str,
    target_url: str,
    source: str,
    notes: str,
    previous: dict[str, dict[str, str]],
    dry_run: bool,
) -> Path:
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{report_date}.md"
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran (Google tr-TR)",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        f"- Hedef URL: `{target_url}`",
        f"- Kaynak: `{source}`",
        "",
        "### Sıra",
        format_delta("mobile", mobile_rank, previous.get("mobile")),
        format_delta("desktop", desktop_rank, previous.get("desktop")),
        "",
        "### Notlar",
        notes,
        "",
        "## Komut (sonraki hafta)",
        "",
        "```bash",
        "python3 scripts/check-serp-led-ekran.py \\",
        "  --mobile-rank <sıra> --desktop-rank <sıra> \\",
        "  --target-url https://ledajans.com/ \\",
        "  --source live_google_serp_check \\",
        '  --notes "Görseller + ilgili aramalar; ücretli reklam yok"',
        "```",
        "",
        "## Referans",
        "",
        "- Detay satırlar: `AGENT-HUB/SERP-BASELINE.csv`",
        "- Runbook: `AGENT-HUB/SEO-MONITORING-RUNBOOK.md`",
        "",
    ]
    content = "\n".join(lines)
    if dry_run:
        print(f"DRY_RUN weekly report -> {report_path}")
        print(content)
        return report_path

    report_path.write_text(content, encoding="utf-8")
    return report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="led ekran SERP baseline kaydı")
    parser.add_argument("--mobile-rank", required=True, help="Mobil organik sıra (sayı veya N/A)")
    parser.add_argument("--desktop-rank", required=True, help="Masaüstü organik sıra")
    parser.add_argument("--target-url", default=TARGET_URL)
    parser.add_argument("--source", default="live_google_serp_check")
    parser.add_argument("--notes", default="")
    parser.add_argument("--serp-features", default="")
    parser.add_argument("--report-date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--captured-at", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    captured_at = args.captured_at or utc_now_iso()
    fields = read_baseline_fields()
    previous = latest_led_ekran_rows()
    append_rows(
        fields=fields,
        captured_at=captured_at,
        mobile_rank=str(args.mobile_rank),
        desktop_rank=str(args.desktop_rank),
        target_url=args.target_url,
        source=args.source,
        notes=args.notes,
        serp_features=args.serp_features,
        dry_run=args.dry_run,
    )
    report_path = update_weekly_summary(
        report_date=args.report_date,
        captured_at=captured_at,
        mobile_rank=str(args.mobile_rank),
        desktop_rank=str(args.desktop_rank),
        target_url=args.target_url,
        source=args.source,
        notes=args.notes,
        previous=previous,
        dry_run=args.dry_run,
    )
    print(f"mobile_rank={args.mobile_rank}")
    print(f"desktop_rank={args.desktop_rank}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
