#!/usr/bin/env python3
"""GSC Performance export'u SERP baseline ve kısa rapora işler."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "AGENT-HUB" / "DATA" / "gsc-performance-2026-06-05"
QUERIES_PATH = DATA_DIR / "Sorgular.csv"
PAGES_PATH = DATA_DIR / "Sayfa sayısı.csv"
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
PRIORITIZED_PATH = ROOT / "AGENT-HUB" / "DATA" / "gsc-queries-prioritized-2026-06-05.csv"
REPORT_PATH = ROOT / "AGENT-HUB" / "REPORTS" / "2026-06-05-gsc-performance.md"
CAPTURED_AT = "2026-06-05T14:21:00Z"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value.strip().replace("%", "").replace(",", "."))
    except ValueError:
        return 0.0


def main() -> int:
    queries = read_csv(QUERIES_PATH)
    pages = read_csv(PAGES_PATH)
    q_by_name = {row["En çok yapılan sorgular"].strip().lower(): row for row in queries}

    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        baseline_rows = list(reader)

    latest_by_query: dict[str, dict[str, str]] = {}
    for row in baseline_rows:
        query = row["query"].strip().lower()
        if query and query not in latest_by_query:
            latest_by_query[query] = row

    new_rows: list[dict[str, str]] = []
    for query, old in latest_by_query.items():
        gsc_row = q_by_name.get(query)
        if not gsc_row:
            continue
        clicks = int(to_float(gsc_row.get("Tıklamalar")))
        impressions = int(to_float(gsc_row.get("Gösterimler")))
        ctr = gsc_row.get("TO", "").strip()
        position = gsc_row.get("Pozisyon", "").strip()

        new = dict(old)
        new.update(
            {
                "captured_at_utc": CAPTURED_AT,
                "rank_position": position,
                "source": "gsc_performance_2026-06-05",
                "notes": f"Clicks={clicks}; Impressions={impressions}; CTR={ctr}; avg_position={position}",
            }
        )
        new_rows.append(new)

    existing_keys = {(r["captured_at_utc"], r["query"].lower(), r["source"]) for r in baseline_rows}
    append_rows = [
        row
        for row in new_rows
        if (row["captured_at_utc"], row["query"].lower(), row["source"]) not in existing_keys
    ]

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for row in append_rows:
            writer.writerow({key: row.get(key, "") for key in fields})

    led_terms = ("led", "ekran", "rental", "kiralama", "fiyat", "panel", "cob", "rgb", "indoor", "outdoor")
    selected: list[dict[str, object]] = []
    for row in queries:
        query = row["En çok yapılan sorgular"].strip()
        if not any(term in query.lower() for term in led_terms):
            continue
        clicks = int(to_float(row.get("Tıklamalar")))
        impressions = int(to_float(row.get("Gösterimler")))
        ctr = to_float(row.get("TO"))
        position = to_float(row.get("Pozisyon"))
        score = round(clicks * 3 + impressions * 0.04 + max(0, 30 - position) * 2 + ctr, 2)
        selected.append(
            {
                "query": query,
                "clicks": clicks,
                "impressions": impressions,
                "ctr_pct": ctr,
                "position": position,
                "priority_score": score,
            }
        )
    selected.sort(key=lambda item: float(item["priority_score"]), reverse=True)

    with PRIORITIZED_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["query", "clicks", "impressions", "ctr_pct", "position", "priority_score"],
        )
        writer.writeheader()
        writer.writerows(selected)

    lines = [
        "# GSC Performance — 2026-06-05",
        "",
        "- Kaynak klasör: `AGENT-HUB/DATA/gsc-performance-2026-06-05/`",
        f"- Sorgu satırı: {len(queries)}",
        f"- Sayfa satırı: {len(pages)}",
        f"- `SERP-BASELINE.csv` eklenen satır: {len(append_rows)}",
        "- Öncelik dosyası: `AGENT-HUB/DATA/gsc-queries-prioritized-2026-06-05.csv`",
        "",
        "## Hedef Sorgular",
        "",
        "| Sorgu | Tıklama | Gösterim | CTR | Pozisyon |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in new_rows:
        gsc_row = q_by_name[row["query"].lower()]
        lines.append(
            f"| {row['query']} | {gsc_row['Tıklamalar']} | {gsc_row['Gösterimler']} | "
            f"{gsc_row['TO']} | {gsc_row['Pozisyon']} |"
        )

    lines.extend(
        [
            "",
            "## En İyi Sayfalar",
            "",
            "| Sayfa | Tıklama | Gösterim | CTR | Pozisyon |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in pages[:15]:
        lines.append(
            f"| {row['En alakalı sayfalar']} | {row['Tıklamalar']} | {row['Gösterimler']} | "
            f"{row['TO']} | {row['Pozisyon']} |"
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"baseline_appended={len(append_rows)}")
    print(f"prioritized_rows={len(selected)}")
    print(f"report={REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
