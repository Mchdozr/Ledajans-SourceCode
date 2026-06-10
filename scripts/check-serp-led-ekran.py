#!/usr/bin/env python3
"""led ekran SERP izleme: ölçüm, SERP-BASELINE.csv ve haftalık özet güncelleme."""
from __future__ import annotations

import argparse
import csv
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote_plus, unquote

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
REPORTS_DIR = ROOT / "AGENT-HUB" / "REPORTS"
WEEKLY_DIR = ROOT / "AGENT-HUB"

QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
DEFAULT_TARGET = "https://ledajans.com/"

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

SKIP_DOMAINS = (
    "google.",
    "gstatic.",
    "youtube.com",
    "webcache",
    "schema.org",
    "accounts.google",
    "support.google",
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_baseline_row(row: dict[str, str]) -> bool:
    rows = read_baseline_rows()
    key = (row["captured_at_utc"][:10], row["query"].lower(), row["device"], row["source"])
    for existing in rows:
        existing_key = (
            existing["captured_at_utc"][:10],
            existing["query"].lower(),
            existing["device"],
            existing["source"],
        )
        if existing_key == key:
            return False

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in BASELINE_FIELDS})
    return True


def extract_organic_links(html: str) -> list[str]:
    links = re.findall(r"/url\?q=(https?://[^&\"]+)", html)
    organic: list[str] = []
    seen: set[str] = set()
    for raw in links:
        link = unquote(raw)
        if any(skip in link for skip in SKIP_DOMAINS):
            continue
        domain = re.sub(r"^https?://(www\.)?", "", link).split("/")[0].lower()
        if domain in seen:
            continue
        seen.add(domain)
        organic.append(link)
    return organic


def try_playwright_serp(device: str) -> tuple[int | None, str | None, str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, None, "playwright kurulu değil"

    mobile = device == "mobile"
    user_agent = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        if mobile
        else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
    url = (
        f"https://www.google.com/search?q={quote_plus(QUERY)}"
        f"&hl=tr&gl=tr&num=50&pws=0"
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(user_agent=user_agent, locale="tr-TR")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        body = page.inner_text("body")
        if "sıra dışı bir trafik" in body or "unusual traffic" in body.lower():
            browser.close()
            return None, None, "Google CAPTCHA / unusual traffic"

        results = page.evaluate(
            """() => {
              const out = [];
              document.querySelectorAll('a[href]').forEach((anchor) => {
                const href = anchor.href;
                if (!href.startsWith('http') || href.includes('google.com')) return;
                const heading = anchor.querySelector('h3');
                if (heading) out.push(href);
              });
              return out;
            }"""
        )
        browser.close()

    organic: list[str] = []
    seen: set[str] = set()
    for link in results:
        domain = re.sub(r"^https?://(www\.)?", "", link).split("/")[0].lower()
        if domain in seen:
            continue
        seen.add(domain)
        organic.append(link)

    for index, link in enumerate(organic, start=1):
        if "ledajans.com" in link:
            return index, link, f"playwright_{device}; organic={len(organic)}"
    return None, None, f"ledajans.com ilk {len(organic)} sonuçta yok; playwright_{device}"


def latest_gsc_position() -> tuple[str | None, str]:
    data_dir = ROOT / "AGENT-HUB" / "DATA"
    gsc_dirs = sorted(data_dir.glob("gsc-performance-*"), reverse=True)
    for folder in gsc_dirs:
        queries_path = folder / "Sorgular.csv"
        if not queries_path.exists():
            continue
        with queries_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("En çok yapılan sorgular", "").strip().lower() == QUERY:
                    position = row.get("Pozisyon", "").strip()
                    clicks = row.get("Tıklamalar", "")
                    impressions = row.get("Gösterimler", "")
                    ctr = row.get("TO", "")
                    return position, (
                        f"GSC avg_position={position}; "
                        f"Clicks={clicks}; Impressions={impressions}; CTR={ctr}; "
                        f"export={folder.name}"
                    )
    snapshot = data_dir / "gsc-queries-snapshot-2026-06-05.csv"
    if snapshot.exists():
        with snapshot.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("query", "").strip().lower() == QUERY:
                    return row.get("position"), f"GSC snapshot position={row.get('position')}"
    return None, "GSC verisi bulunamadı"


def history_for_query(days: int = 14) -> list[dict[str, str]]:
    rows = read_baseline_rows()
    filtered = [row for row in rows if row.get("query", "").strip().lower() == QUERY]
    filtered.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    return filtered[:days]


def build_weekly_markdown(captured_at: str, measurements: list[dict[str, str]]) -> str:
    today = captured_at[:10]
    history = history_for_query(30)
    gsc_pos, gsc_note = latest_gsc_position()

    lines = [
        f"# Haftalık SEO İzleme — {today}",
        "",
        "## SERP: led ekran",
        "",
    ]

    for row in measurements:
        lines.append(
            f"- **{row['device']}** | sıra: **{row['rank_position']}** | "
            f"URL: `{row['target_url']}` | kaynak: `{row['source']}`"
        )
        if row.get("notes"):
            lines.append(f"  - Not: {row['notes']}")

    lines.extend(
        [
            "",
            "## Trend (SERP-BASELINE)",
            "",
            "| Tarih | Cihaz | Sıra | Kaynak |",
            "|---|---|---:|---|",
        ]
    )
    for row in history[:8]:
        lines.append(
            f"| {row.get('captured_at_utc', '')[:10]} | "
            f"{row.get('device', '')} | {row.get('rank_position', '')} | "
            f"{row.get('source', '')} |"
        )

    lines.extend(
        [
            "",
            "## GSC karşılaştırma",
            "",
            f"- Son GSC ortalama pozisyon (`led ekran`): **{gsc_pos or 'N/A'}**",
            f"- Not: {gsc_note}",
            "",
            "## Sonraki çalıştırma",
            "",
            "```bash",
            "cd /workspace && python3 scripts/check-serp-led-ekran.py",
            "```",
            "",
            f"- Son ölçüm: `{captured_at}`",
            f"- Detay rapor: `AGENT-HUB/REPORTS/led-ekran-serp-position-{today}.md` (varsa)",
        ]
    )
    return "\n".join(lines) + "\n"


def write_weekly_markdown(captured_at: str, measurements: list[dict[str, str]]) -> Path:
    today = captured_at[:10]
    path = WEEKLY_DIR / f"WEEKLY-MONITORING-{today}.md"
    path.write_text(build_weekly_markdown(captured_at, measurements), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="led ekran SERP izleme ve baseline güncelleme")
    parser.add_argument("--rank", type=int, help="Manuel organik sıra (ör. 1)")
    parser.add_argument("--target-url", default=DEFAULT_TARGET, help="Sıralanan ledajans URL")
    parser.add_argument("--device", choices=("mobile", "desktop", "both"), default="both")
    parser.add_argument("--source", default="google_serp_check", help="Kaynak etiketi")
    parser.add_argument("--notes", default="", help="Ek not")
    parser.add_argument("--skip-playwright", action="store_true", help="Otomatik SERP taramasını atla")
    parser.add_argument("--dry-run", action="store_true", help="CSV/MD yazmadan sonucu göster")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    captured_at = utc_now_iso()
    devices = ["mobile", "desktop"] if args.device == "both" else [args.device]
    measurements: list[dict[str, str]] = []

    for device in devices:
        rank: int | str | None = args.rank
        target_url = args.target_url
        source = args.source
        notes = args.notes

        if rank is None and not args.skip_playwright:
            auto_rank, auto_url, probe_note = try_playwright_serp(device)
            if auto_rank is not None:
                rank = auto_rank
                target_url = auto_url or target_url
                source = f"playwright_{device}"
                notes = probe_note if not notes else f"{notes}; {probe_note}"
            elif not notes:
                notes = probe_note

        if rank is None:
            gsc_pos, gsc_note = latest_gsc_position()
            if gsc_pos:
                rank = gsc_pos
                source = "gsc_fallback"
                notes = gsc_note if not notes else f"{notes}; {gsc_note}"
            else:
                rank = "N/A"
                source = "unavailable"
                notes = notes or "SERP ve GSC verisi alınamadı"

        row = {
            "captured_at_utc": captured_at,
            "query": QUERY,
            "locale": LOCALE,
            "device": device,
            "search_engine": SEARCH_ENGINE,
            "target_url": target_url,
            "rank_position": str(rank),
            "serp_features": "",
            "primary_competitor": "ledfon.com" if str(rank) == "1" else "videowall.com.tr",
            "competitor_rank": "2" if str(rank) == "1" else "",
            "source": source,
            "notes": notes,
        }
        measurements.append(row)

    if args.dry_run:
        for row in measurements:
            print(row)
        return 0

    appended = 0
    for row in measurements:
        if write_baseline_row(row):
            appended += 1
            print(f"appended: {row['device']} rank={row['rank_position']} source={row['source']}")
        else:
            print(f"skipped duplicate: {row['device']} ({row['source']})")

    weekly_path = write_weekly_markdown(captured_at, measurements)
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    print(f"baseline_appended={appended}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
