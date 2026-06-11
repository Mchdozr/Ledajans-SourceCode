#!/usr/bin/env python3
"""SERP ölçümünü SERP-BASELINE.csv'ye ekler ve haftalık özeti günceller."""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
WEEKLY_DIR = ROOT / "AGENT-HUB"

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


def read_baseline() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_row(row: dict[str, str]) -> None:
    exists = BASELINE_PATH.exists()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def latest_led_ekran_rows(rows: list[dict[str, str]], limit: int = 5) -> list[dict[str, str]]:
    matches = [row for row in rows if row.get("query", "").strip().lower() == "led ekran"]
    matches.sort(key=lambda item: item.get("captured_at_utc", ""), reverse=True)
    return matches[:limit]


def update_weekly_summary(
    captured_at: str,
    rank_position: str,
    target_url: str,
    source: str,
    notes: str,
    history: list[dict[str, str]],
) -> Path:
    date_part = captured_at[:10]
    weekly_path = WEEKLY_DIR / f"WEEKLY-MONITORING-{date_part}.md"

    history_lines = []
    for row in history:
        history_lines.append(
            f"| {row.get('captured_at_utc', '')[:10]} | {row.get('source', '')} | "
            f"{row.get('rank_position', '')} | {row.get('target_url', '')} |"
        )

    content = f"""# Haftalık SEO İzleme — {date_part}

## SERP — `led ekran` (Google, tr-TR, mobile)

| Alan | Değer |
|------|-------|
| Ölçüm UTC | {captured_at} |
| Sıra | **{rank_position}** |
| Hedef URL | {target_url} |
| Kaynak | {source} |
| Not | {notes} |

### Son ölçümler (led ekran)

| Tarih | Kaynak | Sıra | URL |
|-------|--------|-----:|-----|
{chr(10).join(history_lines) if history_lines else "| — | — | — | — |"}

## Smoke / teknik (önceki hafta ile aynı komutlar)

```bash
cd /workspace
python3 deploy-to-wordpress.py --dry-run
python3 AGENT-HUB/audit-money-pages.py
```

## Sonraki ölçüm

Cron: günlük 06:00 UTC — `python3 AGENT-HUB/record-serp-check.py ...`

Haftalık kayıt: bu dosya (`WEEKLY-MONITORING-{date_part}.md`) + `SERP-BASELINE.csv`.
"""
    weekly_path.write_text(content, encoding="utf-8")
    return weekly_path


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP ölçümünü baseline CSV'ye işler.")
    parser.add_argument("--query", default="led ekran")
    parser.add_argument("--locale", default="tr-TR")
    parser.add_argument("--device", default="mobile", choices=["mobile", "desktop"])
    parser.add_argument("--search-engine", default="google")
    parser.add_argument("--target-url", default="https://ledajans.com/")
    parser.add_argument("--rank-position", required=True)
    parser.add_argument("--source", default="google_serp_browser")
    parser.add_argument("--notes", default="")
    parser.add_argument("--primary-competitor", default="")
    parser.add_argument("--competitor-rank", default="")
    parser.add_argument("--serp-features", default="")
    parser.add_argument("--captured-at", default="")
    parser.add_argument("--skip-weekly", action="store_true")
    args = parser.parse_args()

    captured_at = args.captured_at or utc_now_iso()
    row = {
        "captured_at_utc": captured_at,
        "query": args.query,
        "locale": args.locale,
        "device": args.device,
        "search_engine": args.search_engine,
        "target_url": args.target_url,
        "rank_position": args.rank_position,
        "serp_features": args.serp_features,
        "primary_competitor": args.primary_competitor,
        "competitor_rank": args.competitor_rank,
        "source": args.source,
        "notes": args.notes,
    }

    existing = read_baseline()
    duplicate = any(
        r.get("captured_at_utc") == captured_at
        and r.get("query", "").lower() == args.query.lower()
        and r.get("source") == args.source
        and r.get("device") == args.device
        for r in existing
    )
    if duplicate:
        print("skip_duplicate=1")
        return 0

    append_row(row)
    print(f"baseline_appended=1 query={args.query} rank={args.rank_position}")

    if not args.skip_weekly:
        history = latest_led_ekran_rows(existing + [row])
        weekly_path = update_weekly_summary(
            captured_at=captured_at,
            rank_position=args.rank_position,
            target_url=args.target_url,
            source=args.source,
            notes=args.notes or "—",
            history=history,
        )
        print(f"weekly_updated={weekly_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
