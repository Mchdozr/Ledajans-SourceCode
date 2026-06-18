#!/usr/bin/env python3
"""Haftalık SERP kontrolü: led ekran sırasını ölçer, CSV ve haftalık özeti günceller."""
from __future__ import annotations

import csv
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_URL = "https://ledajans.com/"

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
)
DESKTOP_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)

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


def fetch_serp(query: str, user_agent: str) -> list[str]:
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query) + "&kl=tr-tr"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept-Language": "tr-TR,tr;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        html = response.read().decode("utf-8", errors="replace")

    links: list[str] = []
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', html):
        link = match.group(1)
        if "uddg=" in link:
            encoded = re.search(r"uddg=([^&]+)", link)
            if encoded:
                link = urllib.parse.unquote(encoded.group(1))
        if "duckduckgo.com/y.js" in link:
            continue
        links.append(link)
    return links


def rank_for_domain(links: list[str], domain: str) -> tuple[int | None, str | None, str | None, int | None]:
    position = 0
    seen: set[str] = set()
    target_rank: int | None = None
    target_url: str | None = None
    competitor: str | None = None
    competitor_rank: int | None = None

    for link in links:
        host = re.sub(r"^https?://(www\.)?", "", link).split("/")[0]
        if host in seen:
            continue
        seen.add(host)
        position += 1
        if domain in link and target_rank is None:
            target_rank = position
            target_url = link.split("?")[0]
        elif competitor is None and domain not in link:
            competitor = host
            competitor_rank = position

    return target_rank, target_url, competitor, competitor_rank


def read_baseline() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def previous_led_ekran_row(
    rows: list[dict[str, str]],
    device: str,
    *,
    organic_only: bool = False,
) -> dict[str, str] | None:
    organic_sources = {"manual_web_check", "ddg_html_google_proxy", "audit_2026-06-03"}
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("device", "").strip().lower() == device
        and row.get("target_url", "").startswith("https://ledajans.com")
        and (not organic_only or row.get("source", "") in organic_sources)
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda row: row.get("captured_at_utc", ""), reverse=True)[0]


def delta_note(current: int | None, previous: dict[str, str] | None) -> str:
    if current is None:
        return "ledajans.com ilk 10 organik sonuçta görünmedi"
    if previous is None:
        return f"Organik sıra: {current}"
    prev_raw = previous.get("rank_position", "").strip()
    if not prev_raw or prev_raw in {"pending", "top3", "top5", "top10", "top20"}:
        return f"Organik sıra: {current}; önceki kayıt: {prev_raw or 'yok'}"
    try:
        prev_val = float(prev_raw)
        change = prev_val - current
        if change > 0:
            direction = f"↑ {change:.1f} sıra iyileşme"
        elif change < 0:
            direction = f"↓ {abs(change):.1f} sıra düşüş"
        else:
            direction = "değişim yok"
        return f"Organik sıra: {current}; önceki: {prev_val}; {direction}"
    except ValueError:
        return f"Organik sıra: {current}; önceki kayıt: {prev_raw}"


def build_rows(captured_at: str, baseline_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for device, user_agent in (("mobile", MOBILE_UA), ("desktop", DESKTOP_UA)):
        links = fetch_serp(QUERY, user_agent)
        rank, found_url, competitor, competitor_rank = rank_for_domain(links, "ledajans.com")
        previous = previous_led_ekran_row(baseline_rows, device, organic_only=True)
        rank_value = "" if rank is None else str(rank)
        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": found_url or TARGET_URL,
                "rank_position": rank_value,
                "serp_features": "",
                "primary_competitor": competitor or "",
                "competitor_rank": "" if competitor_rank is None else str(competitor_rank),
                "source": "ddg_html_google_proxy",
                "notes": (
                    f"{delta_note(rank, previous)}; "
                    f"DDG HTML tr-TR organik proxy (Google doğrudan scrape engelli); "
                    f"sonuç_sayısı={len(links)}"
                ),
            }
        )
    return rows


def append_baseline(rows: list[dict[str, str]]) -> int:
    existing = read_baseline()
    existing_keys = {
        (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        for row in existing
    }
    to_append = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        not in existing_keys
    ]
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return len(to_append)


def write_weekly_report(captured_at: str, rows: list[dict[str, str]], baseline_rows: list[dict[str, str]]) -> Path:
    report_date = captured_at[:10]
    report_path = HUB / f"WEEKLY-MONITORING-{report_date}.md"
    mobile = next(row for row in rows if row["device"] == "mobile")
    desktop = next(row for row in rows if row["device"] == "desktop")
    prev_mobile = previous_led_ekran_row(baseline_rows, "mobile", organic_only=True)
    prev_gsc = next(
        (
            row
            for row in sorted(baseline_rows, key=lambda item: item.get("captured_at_utc", ""), reverse=True)
            if row.get("query", "").strip().lower() == QUERY and row.get("source", "").startswith("gsc_")
        ),
        None,
    )

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        "",
        "| Cihaz | Sıra | Hedef URL | Rakip | Rakip sıra | Kaynak |",
        "|---|---:|---|---|---:|---|",
        (
            f"| mobile | {mobile['rank_position'] or 'N/A'} | {mobile['target_url']} | "
            f"{mobile['primary_competitor'] or '-'} | {mobile['competitor_rank'] or '-'} | {mobile['source']} |"
        ),
        (
            f"| desktop | {desktop['rank_position'] or 'N/A'} | {desktop['target_url']} | "
            f"{desktop['primary_competitor'] or '-'} | {desktop['competitor_rank'] or '-'} | {desktop['source']} |"
        ),
        "",
        "### Notlar",
        f"- {mobile['notes']}",
        f"- {desktop['notes']}",
        "",
        "### Karşılaştırma",
    ]

    if prev_mobile:
        lines.append(
            f"- Önceki mobil kayıt ({prev_mobile.get('captured_at_utc')}): "
            f"sıra **{prev_mobile.get('rank_position')}**, kaynak `{prev_mobile.get('source')}`"
        )
    if prev_gsc:
        lines.append(
            f"- Son GSC ortalama pozisyon ({prev_gsc.get('captured_at_utc')}): "
            f"**{prev_gsc.get('rank_position')}** ({prev_gsc.get('notes', '').split(';')[0]})"
        )

    lines.extend(
        [
            "",
            "## Komut",
            "```bash",
            "python3 AGENT-HUB/check-serp-weekly.py",
            "```",
            "",
            "## Sonraki kontrol",
            "- Cron: `0 6 * * *` (günlük ölçüm, haftalık özet dosyası)",
            "- GSC export geldiğinde: `python3 scripts/update-serp-baseline-from-gsc.py`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    baseline_rows = read_baseline()
    rows = build_rows(captured_at, baseline_rows)
    appended = append_baseline(rows)
    report_path = write_weekly_report(captured_at, rows, baseline_rows)

    for row in rows:
        print(
            f"{row['device']}: rank={row['rank_position'] or 'N/A'} "
            f"competitor={row['primary_competitor']}@{row['competitor_rank']}"
        )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
