#!/usr/bin/env python3
"""Haftalık/günlük 'led ekran' SERP izleme — SERP-BASELINE.csv + haftalık özet."""
from __future__ import annotations

import csv
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
DATA_DIR = ROOT / "AGENT-HUB" / "DATA"
QUERY = "led ekran"
TARGET_URL = "https://ledajans.com/"
LOCALE = "tr-TR"
DEVICE = "mobile"
SEARCH_ENGINE = "google"

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

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_duckduckgo_lite_rank(query: str, target_host: str = "ledajans.com") -> tuple[int | None, list[str]]:
    response = requests.post(
        "https://lite.duckduckgo.com/lite/",
        data={"q": query, "kl": "tr-tr"},
        headers={"User-Agent": USER_AGENT, "Accept-Language": "tr-TR,tr;q=0.9"},
        timeout=25,
    )
    response.raise_for_status()
    urls: list[str] = []
    for match in re.finditer(r'<a rel="nofollow" href="([^"]+)"', response.text):
        url = match.group(1)
        if url.startswith("//"):
            url = f"https:{url}"
        if "duckduckgo.com" in url:
            continue
        if url not in urls:
            urls.append(url)

    rank: int | None = None
    for index, url in enumerate(urls, start=1):
        if target_host in url.lower():
            rank = index
            break
    return rank, urls


def latest_gsc_avg_position(query: str) -> tuple[str | None, str | None]:
    gsc_dirs = sorted(DATA_DIR.glob("gsc-performance-*"), reverse=True)
    for gsc_dir in gsc_dirs:
        queries_path = gsc_dir / "Sorgular.csv"
        if not queries_path.exists():
            continue
        with queries_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("En çok yapılan sorgular", "").strip().lower() == query.lower():
                    position = row.get("Pozisyon", "").strip()
                    clicks = row.get("Tıklamalar", "").strip()
                    impressions = row.get("Gösterimler", "").strip()
                    ctr = row.get("TO", "").strip()
                    export_tag = gsc_dir.name.replace("gsc-performance-", "")
                    notes = (
                        f"GSC avg_position={position}; Clicks={clicks}; "
                        f"Impressions={impressions}; CTR={ctr}; export={export_tag}"
                    )
                    return position or None, notes
    return None, None


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_row(row: dict[str, str]) -> bool:
    existing = read_baseline_rows()
    day_prefix = row["captured_at_utc"][:10]
    for existing_row in existing:
        if (
            existing_row.get("query", "").lower() == QUERY
            and existing_row.get("source", "") == row["source"]
            and existing_row.get("captured_at_utc", "").startswith(day_prefix)
        ):
            return False

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})
    return True


def build_weekly_markdown(
    captured_at: str,
    proxy_rank: int | None,
    competitors: list[str],
    gsc_position: str | None,
    gsc_notes: str | None,
    appended: bool,
) -> Path:
    date_label = captured_at[:10]
    weekly_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_label}.md"
    prior_rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").lower() == QUERY and row.get("rank_position", "").replace(".", "", 1).isdigit()
    ]
    prior_rows.sort(key=lambda row: row.get("captured_at_utc", ""))

    trend_lines: list[str] = []
    if prior_rows:
        for row in prior_rows[-5:]:
            trend_lines.append(
                f"- {row['captured_at_utc'][:10]}: pozisyon **{row['rank_position']}** "
                f"({row.get('source', 'n/a')})"
            )
    else:
        trend_lines.append("- İlk ölçüm kaydı")

    competitor_line = competitors[1] if len(competitors) > 1 else "n/a"
    rank_text = str(proxy_rank) if proxy_rank is not None else "bulunamadı"
    gsc_text = gsc_position if gsc_position else "güncel export yok"

    content = f"""# Haftalık SEO İzleme — {date_label}

## SERP — \"led ekran\"

| Alan | Değer |
|------|-------|
| Ölçüm UTC | {captured_at} |
| Hedef URL | {TARGET_URL} |
| Canlı organik proxy sırası (DDG lite TR) | **{rank_text}** |
| Google GSC ort. pozisyon (son export) | **{gsc_text}** |
| Birincil rakip (proxy #2) | {competitor_line} |
| CSV satırı eklendi | {"evet" if appended else "hayır (aynı gün kayıt var)"} |

### Not
Google SERP otomasyonu (headless/curl) bu ortamda engelleniyor. Canlı sıra için DuckDuckGo Lite TR organik sonuçları proxy olarak kullanılır; kesin Google sırası için GSC Performance export güncellenmelidir.

### Trend (son kayıtlar)
{chr(10).join(trend_lines)}

## Komutlar

```bash
python3 scripts/check-led-ekran-serp.py
python3 scripts/seo-smoke-test.ps1   # Windows
python3 AGENT-HUB/audit-money-pages.py
```

## Sonraki hafta
- GSC Performance export → `AGENT-HUB/DATA/gsc-performance-YYYY-MM-DD/`
- `python3 scripts/check-led-ekran-serp.py`
"""
    if gsc_notes:
        content += f"\n### GSC detay\n- {gsc_notes}\n"

    weekly_path.write_text(content, encoding="utf-8")
    return weekly_path


def main() -> int:
    captured_at = utc_now_iso()
    proxy_rank, competitors = fetch_duckduckgo_lite_rank(QUERY)
    gsc_position, gsc_notes = latest_gsc_avg_position(QUERY)

    note_parts = [
        f"DDG lite TR organik proxy sırası={proxy_rank if proxy_rank is not None else 'N/A'}",
    ]
    if gsc_position:
        note_parts.append(f"son GSC avg_position={gsc_position}")
    else:
        note_parts.append("GSC export güncel değil")

    row = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": DEVICE,
        "search_engine": SEARCH_ENGINE,
        "target_url": TARGET_URL,
        "rank_position": str(proxy_rank) if proxy_rank is not None else "N/A",
        "serp_features": "",
        "primary_competitor": competitors[1] if len(competitors) > 1 else "",
        "competitor_rank": "2" if len(competitors) > 1 else "",
        "source": "duckduckgo_lite_tr_proxy",
        "notes": "; ".join(note_parts),
    }

    appended = append_baseline_row(row)
    weekly_path = build_weekly_markdown(
        captured_at=captured_at,
        proxy_rank=proxy_rank,
        competitors=competitors,
        gsc_position=gsc_position,
        gsc_notes=gsc_notes,
        appended=appended,
    )

    print(f"query={QUERY}")
    print(f"proxy_rank={proxy_rank}")
    print(f"gsc_avg_position={gsc_position or 'n/a'}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        print(f"error: SERP fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
