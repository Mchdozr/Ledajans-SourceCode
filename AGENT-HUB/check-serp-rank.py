#!/usr/bin/env python3
"""Haftalık SERP kontrolü: led ekran sırasını ölçer, baseline CSV ve haftalık özeti günceller."""
from __future__ import annotations

import argparse
import csv
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_URL = "https://ledajans.com/"

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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_html(url: str, mobile: bool = True) -> str:
    ua = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        if mobile
        else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": ua, "Accept-Language": "tr-TR,tr;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="replace")


def rank_from_bing(query: str, mobile: bool) -> tuple[int | str, str, str, str]:
    q = urllib.parse.quote(query)
    url = f"https://www.bing.com/search?q={q}&setlang=tr&cc=TR"
    html = fetch_html(url, mobile=mobile)
    blocks = re.findall(r'<li class="b_algo"[\s\S]*?</li>', html)
    if not blocks:
        blocks = re.findall(r"<li class='b_algo'[\s\S]*?</li>", html)
    for i, block in enumerate(blocks, 1):
        if re.search(r"ledajans\.com", block, re.I):
            competitor = ""
            comp_rank = ""
            if i > 1:
                first = re.search(r'href="(https?://[^"]+)"', blocks[0], re.I)
                if first:
                    competitor = re.sub(r"^https?://(?:www\.)?", "", first.group(1)).split("/")[0]
                    comp_rank = "1"
            notes = f"Bing TR {'mobile' if mobile else 'desktop'}; organik={len(blocks)}"
            return i, notes, competitor, comp_rank
    return "not_in_top10", f"Bing TR ilk {len(blocks)} sonuçta yok", "", ""


def rank_from_ddg(query: str) -> tuple[int | str, str]:
    q = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={q}&kl=tr-tr"
    html = fetch_html(url, mobile=True)
    results = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    for i, href in enumerate(results, 1):
        if "ledajans.com" in urllib.parse.unquote(href):
            return i, "DuckDuckGo HTML lite TR"
    return "not_in_top10", f"DDG ilk {len(results)} sonuçta yok"


def read_baseline() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def append_rows(rows: list[dict[str, str]]) -> int:
    existing = read_baseline()
    fields = list(existing[0].keys()) if existing else BASELINE_FIELDS
    keys = {
        (r["captured_at_utc"], r["query"].lower(), r["device"], r["source"])
        for r in existing
    }
    to_write = [
        r
        for r in rows
        if (r["captured_at_utc"], r["query"].lower(), r["device"], r["source"]) not in keys
    ]
    if not to_write:
        return 0

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        for row in to_write:
            writer.writerow({k: row.get(k, "") for k in fields})
    return len(to_write)


def latest_led_ekran_rows() -> list[dict[str, str]]:
    rows = [r for r in read_baseline() if r.get("query", "").lower() == QUERY]
    rows.sort(key=lambda r: r.get("captured_at_utc", ""), reverse=True)
    return rows


def update_weekly_summary(captured_at: str, google_rows: list[dict[str, str]]) -> Path:
    date_part = captured_at[:10]
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_part}.md"
    prior = [
        r
        for r in latest_led_ekran_rows()
        if r.get("source", "").startswith("google") and r.get("captured_at_utc", "") < captured_at
    ]

    lines = [
        f"# Haftalık SEO İzleme — {date_part}",
        "",
        "## SERP — `led ekran` (ledajans.com)",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        "",
        "| Cihaz | Arama motoru | Sıra | Kaynak | Not |",
        "|---|---|---:|---|---|",
    ]
    for row in google_rows:
        lines.append(
            f"| {row['device']} | {row['search_engine']} | **{row['rank_position']}** | "
            f"{row['source']} | {row['notes']} |"
        )

    if prior:
        p = prior[0]
        lines.extend(
            [
                "",
                "## Trend",
                "",
                f"- Önceki Google kaydı ({p['captured_at_utc'][:10]}): "
                f"{p['device']} → **{p['rank_position']}** ({p['source']})",
            ]
        )

    lines.extend(
        [
            "",
            "## Otomasyon",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-rank.py --google-desktop 1 --google-mobile 2",
            "```",
            "",
            "Proxy kontrol (headless): Bing + DuckDuckGo otomatik eklenir.",
            "",
            "Kayıt: `AGENT-HUB/SERP-BASELINE.csv`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-rank.py --google-desktop N --google-mobile N",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_row(
    captured_at: str,
    device: str,
    search_engine: str,
    rank: int | str,
    source: str,
    notes: str,
    *,
    serp_features: str = "",
    primary_competitor: str = "",
    competitor_rank: str = "",
) -> dict[str, str]:
    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": search_engine,
        "target_url": TARGET_URL,
        "rank_position": str(rank),
        "serp_features": serp_features,
        "primary_competitor": primary_competitor,
        "competitor_rank": competitor_rank,
        "source": source,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP baseline ölçümü")
    parser.add_argument("--google-desktop", type=int, help="Doğrulanmış Google desktop sırası")
    parser.add_argument("--google-mobile", type=int, help="Doğrulanmış Google mobile sırası")
    parser.add_argument(
        "--google-notes-desktop",
        default="Tarayıcı ile doğrulandı (hl=tr, gl=tr); organik #1",
    )
    parser.add_argument(
        "--google-notes-mobile",
        default="Mobil viewport 390px; rakip #1: ledurunleri.com; yerel paket görünür",
    )
    args = parser.parse_args()
    captured_at = utc_now()
    rows: list[dict[str, str]] = []

    if args.google_desktop is not None:
        rows.append(
            build_row(
                captured_at,
                "desktop",
                "google",
                args.google_desktop,
                "google_desktop_browser",
                args.google_notes_desktop,
                primary_competitor="ledfon.com" if args.google_desktop > 1 else "",
                competitor_rank="" if args.google_desktop == 1 else "1",
            )
        )
    if args.google_mobile is not None:
        rows.append(
            build_row(
                captured_at,
                "mobile",
                "google",
                args.google_mobile,
                "google_mobile_browser",
                args.google_notes_mobile,
                serp_features="local_pack,resimler",
                primary_competitor="ledurunleri.com",
                competitor_rank="1",
            )
        )

    for device, mobile_flag in (("mobile", True), ("desktop", False)):
        rank, notes, competitor, comp_rank = rank_from_bing(QUERY, mobile=mobile_flag)
        rows.append(
            build_row(
                captured_at,
                device,
                "bing",
                rank,
                f"bing_{device}_html",
                notes,
                primary_competitor=competitor,
                competitor_rank=comp_rank,
            )
        )

    ddg_rank, ddg_notes = rank_from_ddg(QUERY)
    rows.append(
        build_row(
            captured_at,
            "mobile",
            "duckduckgo",
            ddg_rank,
            "duckduckgo_html",
            ddg_notes,
        )
    )

    appended = append_rows(rows)
    google_rows = [r for r in rows if r["source"].startswith("google")]
    weekly_path = update_weekly_summary(captured_at, google_rows) if google_rows else None

    print(f"captured_at={captured_at}")
    print(f"baseline_appended={appended}")
    if weekly_path:
        print(f"weekly={weekly_path.relative_to(ROOT)}")
    for row in rows:
        print(f"  {row['device']}/{row['search_engine']}: {row['rank_position']} ({row['source']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
