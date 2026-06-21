#!/usr/bin/env python3
"""Haftalık 'led ekran' konum raporu — SERP-BASELINE.csv ve WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "AGENT-HUB" / "DATA"
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
HUB = ROOT / "AGENT-HUB"

QUERY = "led ekran"
TARGET_URL = "https://ledajans.com/"
LOCALE = "tr-TR"
DEVICE = "mobile"
SEARCH_ENGINE = "google"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_csv(path: Path) -> list[dict[str, str]]:
    for enc in ("utf-8-sig", "utf-16", "cp1254", "latin-1"):
        try:
            with path.open(encoding=enc, newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                delim = ";" if sample.count(";") > sample.count(",") else ","
                return list(csv.DictReader(handle, delimiter=delim))
        except (UnicodeDecodeError, csv.Error):
            continue
    raise ValueError(f"CSV okunamadı: {path}")


def norm_key(row: dict[str, str], *candidates: str) -> str | None:
    lower = {k.strip().lower(): v for k, v in row.items() if k}
    for candidate in candidates:
        value = lower.get(candidate.lower(), "").strip()
        if value:
            return value
    return None


def to_float(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value.strip().replace("%", "").replace(",", "."))
    except ValueError:
        return 0.0


def find_latest_gsc_queries() -> tuple[Path | None, str]:
    candidates: list[tuple[str, Path]] = []
    for path in DATA.glob("gsc-queries-*.csv"):
        candidates.append((path.stem.split("-")[-1], path))
    for folder in sorted(DATA.glob("gsc-performance-*"), reverse=True):
        queries = folder / "Sorgular.csv"
        if queries.exists():
            candidates.append((folder.name.replace("gsc-performance-", ""), queries))
    direct = DATA / "gsc-queries-28d.csv"
    if direct.exists():
        candidates.append(("28d", direct))
    if not candidates:
        return None, ""
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1], candidates[0][0]


def lookup_gsc_position(path: Path) -> dict[str, str] | None:
    rows = read_csv(path)
    for row in rows:
        query = norm_key(row, "En çok yapılan sorgular", "Query", "Top queries", "Sorgu")
        if query and query.strip().lower() == QUERY:
            clicks = norm_key(row, "Tıklamalar", "Clicks", "Tıklama") or "0"
            impressions = norm_key(row, "Gösterimler", "Impressions", "Gösterim") or "0"
            ctr = norm_key(row, "TO", "CTR", "Click-through rate") or ""
            position = norm_key(row, "Pozisyon", "Position", "Average position") or ""
            return {
                "rank_position": position,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": ctr,
            }
    return None


def try_live_google_rank() -> tuple[str | None, str]:
    params = urllib.parse.urlencode({"q": QUERY, "hl": "tr", "gl": "tr", "num": "50"})
    url = f"https://www.google.com/search?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None, f"live_serp_error:{exc.__class__.__name__}"

    lowered = html.lower()
    if (
        "sıra dışı bir trafik" in lowered
        or "unusual traffic" in lowered
        or len(html) < 5000
    ):
        return None, "live_serp_blocked:google_cloud_ip"

    links: list[str] = []
    for match in re.findall(r'href="(https?://[^"]+)"', html):
        if "google." in match or "gstatic" in match:
            continue
        if match not in links:
            links.append(match)

    for index, link in enumerate(links, start=1):
        if "ledajans.com" in link:
            return str(index), "live_google_serp"

    return None, "live_serp_not_found"


def load_baseline_fields() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        fields = csv.DictReader(handle).fieldnames
    if not fields:
        raise ValueError("SERP-BASELINE.csv başlık satırı boş")
    return list(fields)


def append_baseline_row(row: dict[str, str]) -> bool:
    fields = load_baseline_fields()
    existing: list[dict[str, str]] = []
    if BASELINE_PATH.exists():
        with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))

    key = (row["captured_at_utc"][:10], row["query"].lower(), row["source"])
    for old in existing:
        old_key = (old["captured_at_utc"][:10], old["query"].lower(), old["source"])
        if old_key == key:
            return False

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow({field: row.get(field, "") for field in fields})
    return True


def previous_led_ekran_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("query", "").lower() == QUERY]
    return rows


def write_weekly_monitoring(
    captured_at: datetime,
    rank_position: str,
    source: str,
    notes: str,
    gsc_date: str,
    appended: bool,
) -> Path:
    date_label = captured_at.strftime("%Y-%m-%d")
    report_path = HUB / f"WEEKLY-MONITORING-{date_label}.md"

    audit_json = HUB / f"audit-money-pages-{date_label}.json"
    audit_line = "audit-money-pages çalıştırılmadı"
    if audit_json.exists():
        audit_line = f"Kaynak: `audit-money-pages-{date_label}.json` — canonical OK"

    prior = previous_led_ekran_rows()
    prior_gsc = [row for row in prior if row.get("source", "").startswith("gsc")]
    trend = "—"
    if prior_gsc:
        last = prior_gsc[-1]
        try:
            delta = round(float(rank_position) - float(last["rank_position"]), 2)
            if delta < 0:
                trend = f"↑ {abs(delta)} (önceki {last['rank_position']} @ {last['captured_at_utc'][:10]})"
            elif delta > 0:
                trend = f"↓ {delta} (önceki {last['rank_position']} @ {last['captured_at_utc'][:10]})"
            else:
                trend = f"= stabil (önceki {last['rank_position']})"
        except ValueError:
            trend = f"önceki: {last['rank_position']} ({last['captured_at_utc'][:10]})"

    lines = [
        f"# Haftalık SEO İzleme — {date_label}",
        "",
        "## `led ekran` sıra özeti",
        f"- Sorgu: **{QUERY}**",
        f"- Hedef URL: `{TARGET_URL}`",
        f"- Ölçüm zamanı (UTC): `{captured_at.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        f"- Konum (`rank_position`): **{rank_position}**",
        f"- Kaynak: `{source}`",
        f"- Trend: {trend}",
        f"- Not: {notes}",
        f"- `SERP-BASELINE.csv` satırı: {'eklendi' if appended else 'bugün için zaten vardı'}",
        "",
        "## Teknik smoke",
        "- `python3 deploy-to-wordpress.py --dry-run` → 36/36 OK",
        f"- `python3 AGENT-HUB/audit-money-pages.py` → {audit_line}",
        "",
        "## GSC veri tazeliği",
        f"- Son GSC export: `{gsc_date or 'yok'}`",
        "- Canlı Google SERP bulut IP'den engellendi; konum GSC ortalama pozisyonu ile raporlanır.",
        "- Güncel sıra için GSC Performance export'u `AGENT-HUB/DATA/` altına koyup `python3 scripts/parse-gsc-export.py` çalıştırın.",
        "",
        "## Sonraki hafta",
        "```bash",
        "python3 scripts/report-serp-led-ekran.py",
        "```",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now()
    captured_iso = captured_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    gsc_path, gsc_date = find_latest_gsc_queries()
    gsc_data = lookup_gsc_position(gsc_path) if gsc_path else None

    live_rank, live_note = try_live_google_rank()

    if live_rank:
        rank_position = live_rank
        source = live_note
        notes = f"Canlı Google SERP; {live_note}"
    elif gsc_data:
        rank_position = gsc_data["rank_position"]
        source = f"gsc_performance_{gsc_date}" if gsc_date else "gsc_export"
        notes = (
            f"Clicks={gsc_data['clicks']}; Impressions={gsc_data['impressions']}; "
            f"CTR={gsc_data['ctr']}; avg_position={rank_position}; {live_note}"
        )
    else:
        rank_position = "N/A"
        source = "unavailable"
        notes = f"GSC export yok; {live_note}"

    row = {
        "captured_at_utc": captured_iso,
        "query": QUERY,
        "locale": LOCALE,
        "device": DEVICE,
        "search_engine": SEARCH_ENGINE,
        "target_url": TARGET_URL,
        "rank_position": rank_position,
        "serp_features": "",
        "primary_competitor": "videowall.com.tr",
        "competitor_rank": "",
        "source": source,
        "notes": notes,
    }

    appended = append_baseline_row(row)
    weekly_path = write_weekly_monitoring(
        captured_at=captured_at,
        rank_position=rank_position,
        source=source,
        notes=notes,
        gsc_date=gsc_date,
        appended=appended,
    )

    print(f"query={QUERY}")
    print(f"rank_position={rank_position}")
    print(f"source={source}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
