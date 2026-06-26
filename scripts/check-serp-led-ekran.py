#!/usr/bin/env python3
"""Google TR SERP snapshot: led ekran -> SERP-BASELINE.csv + haftalık özet."""
from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_URL = "https://ledajans.com/"
PRIMARY_COMPETITOR = "ledfon.com"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline() -> tuple[list[str], list[dict[str, str]]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def latest_led_ekran_row(rows: list[dict[str, str]], device: str) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("device", "").strip().lower() == device
        and row.get("target_url", "").strip().rstrip("/") == TARGET_URL.rstrip("/")
    ]
    return matches[-1] if matches else None


def parse_organic_links(html: str) -> list[str]:
    links: list[str] = []
    for href in re.findall(r'<a[^>]+href="([^"]+)"[^>]*><h3', html):
        if href.startswith("/url?"):
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("q", [""])[0]
            if parsed.startswith("http"):
                links.append(parsed)
        elif href.startswith("http"):
            links.append(href)

    seen: set[str] = set()
    organic: list[str] = []
    for link in links:
        if link not in seen:
            seen.add(link)
            organic.append(link)
    return organic


def parse_rank_value(value: str) -> int | None:
    cleaned = (value or "").strip().lower()
    if cleaned.isdigit():
        return int(cleaned)
    match = re.match(r"top(\d+)", cleaned)
    if match:
        return int(match.group(1))
    return None


def find_rank(organic: list[str], target: str) -> int | None:
    normalized = target.rstrip("/").lower()
    for index, url in enumerate(organic, start=1):
        if url.rstrip("/").lower() == normalized or normalized in url.rstrip("/").lower():
            return index
    return None


def try_playwright_serp(device: str) -> tuple[int | None, str, list[str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "playwright_not_installed", []

    mobile = device == "mobile"
    url = (
        "https://www.google.com.tr/search?"
        + urllib.parse.urlencode({"q": QUERY, "hl": "tr", "gl": "tr", "num": "30"})
    )
    viewport = {"width": 390, "height": 844} if mobile else {"width": 1366, "height": 900}
    user_agent = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        if mobile
        else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, args=["--no-sandbox"])
        context = browser.new_context(locale="tr-TR", user_agent=user_agent, viewport=viewport)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(4000)
        html = page.content()
        browser.close()

    lowered = html.lower()
    if "captcha" in lowered or "unusual traffic" in lowered or "sıra dışı" in lowered:
        return None, "google_captcha_blocked", []

    organic = parse_organic_links(html)
    rank = find_rank(organic, TARGET_URL)
    return rank, "playwright_google_tr", organic[:10]


def append_baseline_row(
    fields: list[str],
    *,
    captured_at: str,
    device: str,
    rank_position: str | int,
    source: str,
    notes: str,
) -> None:
    row = {key: "" for key in fields}
    row.update(
        {
            "captured_at_utc": captured_at,
            "query": QUERY,
            "locale": LOCALE,
            "device": device,
            "search_engine": SEARCH_ENGINE,
            "target_url": TARGET_URL,
            "rank_position": str(rank_position),
            "primary_competitor": PRIMARY_COMPETITOR,
            "source": source,
            "notes": notes,
        }
    )
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writerow({key: row.get(key, "") for key in fields})


def write_weekly_summary(
    captured_at: str,
    device: str,
    rank_position: str | int,
    source: str,
    notes: str,
    previous: dict[str, str] | None,
) -> Path:
    date_label = captured_at[:10]
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_label}.md"
    prev_rank = previous.get("rank_position") if previous else "N/A"
    prev_date = (previous or {}).get("captured_at_utc", "N/A")[:10]
    delta = "ilk kayıt"
    prev_numeric = parse_rank_value(str(prev_rank))
    current_numeric = parse_rank_value(str(rank_position))
    if previous and prev_numeric is not None and current_numeric is not None:
        delta_value = current_numeric - prev_numeric
        if delta_value < 0:
            delta = f"↑ {abs(delta_value)} sıra iyileşme"
        elif delta_value > 0:
            delta = f"↓ {delta_value} sıra düşüş"
        else:
            delta = "değişmedi"

    content = f"""# Haftalık SEO İzleme — {date_label}

## SERP: `led ekran` (Google TR)

| Alan | Değer |
|------|-------|
| Sıra | **{rank_position}** |
| Hedef URL | `{TARGET_URL}` |
| Cihaz | {device} |
| Locale | {LOCALE} |
| Kaynak | `{source}` |
| Ölçüm UTC | {captured_at} |
| Önceki sıra | {prev_rank} ({prev_date}) |
| Haftalık delta | {delta} |

### Notlar
- {notes}
- `/led-ekran/` alt sayfası top-10 organikte ayrı görünmüyor (ana sayfa sıralanıyor).
- Birincil rakip (top-10): `{PRIMARY_COMPETITOR}`

## Sonraki hafta
```bash
python3 scripts/check-serp-led-ekran.py
```

Google CAPTCHA engellerse tarayıcı doğrulaması ile `--rank` geçin:
```bash
python3 scripts/check-serp-led-ekran.py --rank 1 --device desktop --source manual_web_check
```
"""
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="led ekran SERP snapshot")
    parser.add_argument("--device", choices=["desktop", "mobile"], default="desktop")
    parser.add_argument("--rank", type=int, help="Doğrulanmış organik sıra (CAPTCHA fallback)")
    parser.add_argument("--source", default="", help="Veri kaynağı etiketi")
    parser.add_argument("--notes", default="", help="Ek not")
    parser.add_argument("--skip-weekly", action="store_true")
    args = parser.parse_args()

    captured_at = utc_now_iso()
    fields, rows = read_baseline()
    if not fields:
        print("SERP-BASELINE.csv başlık satırı bulunamadı", file=sys.stderr)
        return 1

    duplicate_key = (captured_at[:10], QUERY, args.device, args.source or "auto")
    for row in rows:
        same_day = row.get("captured_at_utc", "")[:10] == duplicate_key[0]
        same_query = row.get("query", "").strip().lower() == QUERY
        same_device = row.get("device", "") == args.device
        same_source = row.get("source", "") == (args.source or "auto")
        if same_day and same_query and same_device and same_source and args.rank is None:
            print(f"skip_duplicate day={duplicate_key[0]} device={args.device}")
            return 0

    organic_preview: list[str] = []
    source = args.source
    rank = args.rank
    notes = args.notes

    if rank is None:
        rank, source, organic_preview = try_playwright_serp(args.device)
        if rank is None:
            if source == "google_captcha_blocked":
                print("google_captcha_blocked: --rank ile manuel doğrulama gerekli", file=sys.stderr)
                return 2
            print(f"rank_not_found source={source}", file=sys.stderr)
            return 2
        notes = (
            notes
            or f"Otomatik SERP çekimi; top10={[urllib.parse.urlparse(u).netloc for u in organic_preview]}"
        )
    else:
        source = source or "manual_web_check"
        notes = notes or "Manuel/tarayıcı doğrulaması ile kaydedildi"

    previous = latest_led_ekran_row(rows, args.device)
    append_baseline_row(
        fields,
        captured_at=captured_at,
        device=args.device,
        rank_position=rank,
        source=source,
        notes=notes,
    )

    weekly_path = None
    if not args.skip_weekly:
        weekly_path = write_weekly_summary(captured_at, args.device, rank, source, notes, previous)

    print(f"rank={rank} device={args.device} source={source}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    if weekly_path:
        print(f"weekly={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
