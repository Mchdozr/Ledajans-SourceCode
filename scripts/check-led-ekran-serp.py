#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
DEVICE = "mobile"
SEARCH_ENGINE = "google"
TARGET_URL = "https://ledajans.com/"
GSC_FALLBACK_DIR = ROOT / "AGENT-HUB" / "DATA" / "gsc-performance-2026-06-05"
GSC_QUERIES = GSC_FALLBACK_DIR / "Sorgular.csv"

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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_utc() -> str:
    return utc_now().strftime("%Y-%m-%d")


def weekly_monitoring_path() -> Path:
    return ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{today_utc()}.md"


def normalize_domain(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url.lower()).rstrip("/")


def is_ledajans(url: str) -> bool:
    return normalize_domain(url).startswith("ledajans.com")


JUNK_DOMAINS = (
    "wikipedia.org",
    "reddit.com",
    "pinterest.",
    "microsoft.com",
    "support.microsoft",
    "techcommunity.microsoft",
)


def is_relevant_result(url: str) -> bool:
    domain = normalize_domain(url)
    if any(j in domain for j in JUNK_DOMAINS):
        return False
    return True


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return CSV_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or CSV_FIELDS)
        return fields, list(reader)


def already_logged_today(source: str) -> bool:
    _, rows = read_baseline_rows()
    day = today_utc()
    for row in rows:
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("source", "") == source
            and row.get("captured_at_utc", "").startswith(day)
        ):
            return True
    return False


def append_baseline_row(row: dict[str, str]) -> None:
    fields, _ = read_baseline_rows()
    exists = BASELINE_PATH.exists()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fields})


def fetch_serper(query: str) -> tuple[int | str, str, str, str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = json.dumps({"q": query, "gl": "tr", "hl": "tr", "num": 20}).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    organic = data.get("organic") or []
    for i, item in enumerate(organic, 1):
        link = item.get("link", "")
        if is_ledajans(link):
            competitor = organic[0].get("link", "") if organic else ""
            comp_rank = "1" if competitor and not is_ledajans(competitor) else ""
            return i, link, competitor, comp_rank
    return "not_in_top20", TARGET_URL, "", ""


def fetch_serpapi(query: str) -> tuple[int | str, str, str, str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = urllib.parse.urlencode(
        {"engine": "google", "q": query, "hl": "tr", "gl": "tr", "num": 20, "api_key": api_key}
    )
    with urllib.request.urlopen(f"https://serpapi.com/search.json?{params}", timeout=30) as resp:
        data = json.loads(resp.read().decode())
    organic = data.get("organic_results") or []
    for i, item in enumerate(organic, 1):
        link = item.get("link", "")
        if is_ledajans(link):
            competitor = organic[0].get("link", "") if organic else ""
            comp_rank = "1" if competitor and not is_ledajans(competitor) else ""
            return i, link, competitor, comp_rank
    return "not_in_top20", TARGET_URL, "", ""


def fetch_ddgs_proxy(query: str) -> tuple[int | str, str, str, str]:
    try:
        from ddgs import DDGS
    except ImportError:
        return "unavailable", TARGET_URL, "", "ddgs paketi yok; pip install ddgs"

    results = list(DDGS().text(query, region="tr-tr", max_results=20, backend="auto"))
    filtered = [
        r for r in results
        if r.get("href", "").startswith("http") and is_relevant_result(r["href"])
    ]
    for i, item in enumerate(filtered, 1):
        href = item.get("href", "")
        if is_ledajans(href):
            comp = ""
            comp_rank = ""
            for j, other in enumerate(filtered, 1):
                other_href = other.get("href", "")
                if not is_ledajans(other_href):
                    comp = other_href
                    comp_rank = str(j)
                    break
            return i, href, comp, comp_rank
    return "not_in_top20", TARGET_URL, "", ""


def fetch_gsc_fallback() -> tuple[str, str]:
    if not GSC_QUERIES.exists():
        return "N/A", "GSC export bulunamadı"
    with GSC_QUERIES.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            q = row.get("En çok yapılan sorgular", "").strip().lower()
            if q == QUERY:
                pos = row.get("Pozisyon", "N/A").strip()
                clicks = row.get("Tıklamalar", "")
                impressions = row.get("Gösterimler", "")
                ctr = row.get("TO", "")
                note = (
                    f"GSC avg_position={pos}; Clicks={clicks}; "
                    f"Impressions={impressions}; CTR={ctr}; export=2026-06-05"
                )
                return pos, note
    return "N/A", "GSC export içinde 'led ekran' bulunamadı"


def measure() -> dict[str, str]:
    captured = iso_utc()
    rank: int | str = "N/A"
    target = TARGET_URL
    source = "unavailable"
    notes = ""
    competitor = ""
    competitor_rank = ""

    for name, fetcher in (
        ("serper_google", lambda: fetch_serper(QUERY)),
        ("serpapi_google", lambda: fetch_serpapi(QUERY)),
    ):
        try:
            result = fetcher()
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            notes = f"{name} hata: {exc}"
            continue
        if result is None:
            continue
        rank, target, competitor, competitor_rank = result
        source = name
        notes = "Google SERP API canlı ölçüm"
        break

    if source == "unavailable":
        rank, target, competitor, competitor_rank = fetch_ddgs_proxy(QUERY)
        if rank != "unavailable":
            source = "ddgs_auto_tr_proxy"
            notes = (
                "Google canlı scrape engelli; ddgs auto backend organik proxy. "
                "GSC avg_position ile karşılaştırın."
            )

    if rank in ("unavailable", "N/A", "not_in_top20"):
        gsc_pos, gsc_note = fetch_gsc_fallback()
        if rank == "unavailable":
            rank = gsc_pos
            source = "gsc_performance_2026-06-05"
            notes = gsc_note
        else:
            notes = f"{notes}; GSC referans: {gsc_note}" if notes else gsc_note

    return {
        "captured_at_utc": captured,
        "query": QUERY,
        "locale": LOCALE,
        "device": DEVICE,
        "search_engine": SEARCH_ENGINE,
        "target_url": target,
        "rank_position": str(rank),
        "serp_features": "",
        "primary_competitor": competitor,
        "competitor_rank": competitor_rank,
        "source": source,
        "notes": notes,
    }


def previous_led_ekran_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in rows if r.get("query", "").strip().lower() == QUERY]


def update_weekly_monitoring(row: dict[str, str], history: list[dict[str, str]]) -> Path:
    path = weekly_monitoring_path()
    prev = history[-2] if len(history) >= 2 else None
    delta = ""
    if prev and str(row["rank_position"]).replace(".", "", 1).isdigit():
        try:
            cur = float(row["rank_position"])
            old = float(prev.get("rank_position", "nan"))
            if old == old:
                diff = old - cur
                if diff > 0:
                    delta = f"↑ {diff:.2f} pozisyon iyileşme"
                elif diff < 0:
                    delta = f"↓ {abs(diff):.2f} pozisyon düşüş"
                else:
                    delta = "→ değişim yok"
        except ValueError:
            pass

    lines = [
        f"# Haftalık SEO İzleme — {today_utc()}",
        "",
        "## SERP — led ekran",
        "",
        f"| Alan | Değer |",
        f"|------|-------|",
        f"| Ölçüm zamanı (UTC) | {row['captured_at_utc']} |",
        f"| Sorgu | {row['query']} |",
        f"| Locale / cihaz | {row['locale']} / {row['device']} |",
        f"| Arama motoru | {row['search_engine']} |",
        f"| Hedef URL | {row['target_url']} |",
        f"| **Sıra** | **{row['rank_position']}** |",
        f"| Kaynak | {row['source']} |",
        f"| Birincil rakip | {row['primary_competitor'] or '—'} |",
        f"| Rakip sırası | {row['competitor_rank'] or '—'} |",
        f"| Notlar | {row['notes']} |",
        "",
    ]
    if delta:
        lines.extend([f"**Haftalık delta (önceki ölçüme göre):** {delta}", ""])

    if history:
        lines.extend(["## Son ölçümler (led ekran)", "", "| Tarih | Sıra | Kaynak |", "|-------|-----:|--------|"])
        for h in history[-6:]:
            lines.append(
                f"| {h.get('captured_at_utc', '')[:10]} | {h.get('rank_position', '')} | {h.get('source', '')} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Otomasyon",
            "",
            "- Cron: `0 6 * * *` UTC (`scripts/check-led-ekran-serp.py`)",
            "- CSV: `AGENT-HUB/SERP-BASELINE.csv`",
            "- Google canlı için `SERPER_API_KEY` veya `SERPAPI_KEY` önerilir.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    row = measure()
    source = row["source"]

    if already_logged_today(source):
        print(f"skip: bugün için {source} kaydı mevcut")
        _, rows = read_baseline_rows()
        history = previous_led_ekran_rows(rows)
        update_weekly_monitoring(row, history)
        print(json.dumps(row, ensure_ascii=False))
        return 0

    append_baseline_row(row)
    _, rows = read_baseline_rows()
    history = previous_led_ekran_rows(rows)
    weekly_path = update_weekly_monitoring(row, history)

    print(f"rank={row['rank_position']} source={row['source']}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
