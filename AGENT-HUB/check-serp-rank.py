#!/usr/bin/env python3
"""Haftalık SERP sıra ölçümü: led ekran → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
WEEKLY_DIR = ROOT / "AGENT-HUB"

QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_URL = "https://ledajans.com/"
TARGET_DOMAIN = "ledajans.com"

USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
}

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


def week_start(d: datetime) -> datetime:
    return (d - timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def fetch_brave_serp(query: str, device: str) -> tuple[int | str, str, str, list[tuple[int, str]]]:
    """Brave Search HTML üzerinden organik sıra (Google doğrudan erişim engelli VM'lerde proxy)."""
    url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}&country=TR&source=web"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENTS[device],
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    all_urls = re.findall(r'href="(https?://[^"]+)"', html)
    organic: list[tuple[int, str]] = []
    seen_domains: set[str] = set()
    for href in all_urls:
        parsed = urllib.parse.urlparse(href)
        domain = parsed.netloc.lower().replace("www.", "")
        if not domain or "brave.com" in domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        clean = parsed._replace(query="", fragment="").geturl().rstrip("/")
        organic.append((len(organic) + 1, clean))

    led_match = next(((rank, url) for rank, url in organic if TARGET_DOMAIN in url), None)
    if led_match:
        rank, matched_url = led_match
        return rank, matched_url, "brave_search_proxy", organic[:10]

    return f">{len(organic)}", TARGET_URL, "brave_search_proxy", organic[:10]


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return BASELINE_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or BASELINE_FIELDS)
        return fields, list(reader)


def append_baseline_row(fields: list[str], row: dict[str, str]) -> None:
    exists = BASELINE_PATH.exists()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fields})


def latest_gsc_position(query: str) -> str | None:
    for row in reversed(read_baseline_rows()[1]):
        if row.get("query", "").lower() == query.lower() and row.get("source", "").startswith("gsc"):
            return row.get("rank_position") or None
    return None


def build_weekly_markdown(
    captured_at: datetime,
    measurements: list[dict[str, object]],
) -> str:
    week_label = week_start(captured_at).strftime("%Y-%m-%d")
    gsc_pos = latest_gsc_position(QUERY)
    lines = [
        f"# Haftalık SEO İzleme — {week_label}",
        "",
        f"Son ölçüm: `{captured_at.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        "",
        "## SERP — led ekran",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak |",
        "|-------|-----:|-----------|--------|",
    ]
    for item in measurements:
        lines.append(
            f"| {item['device']} | {item['rank']} | {item['url']} | {item['source']} |"
        )

    if gsc_pos:
        lines.extend(
            [
                "",
                f"**GSC ortalama pozisyon (son export):** {gsc_pos} — kaynak `gsc_performance`, "
                "tıklama ağırlıklı ortalama; canlı SERP sırasından farklı olabilir.",
            ]
        )

    current_ts = captured_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    prev_rows = [
        r
        for r in read_baseline_rows()[1]
        if r.get("query", "").lower() == QUERY.lower()
        and TARGET_DOMAIN in (r.get("target_url") or "")
        and r.get("device") == "mobile"
        and r.get("source") == "brave_search_proxy"
        and r.get("captured_at_utc") != current_ts
    ]
    mobile = next((m for m in measurements if m.get("device") == "mobile"), None)
    if prev_rows and mobile:
        last = prev_rows[-1]
        lines.extend(
            [
                "",
                "## Haftalık delta (mobile)",
                "",
                f"- Önceki ölçüm ({last.get('captured_at_utc', '?')}): sıra **{last.get('rank_position', '?')}**",
                f"- Bu ölçüm ({current_ts}): sıra **{mobile.get('rank', '?')}**",
            ]
        )

    lines.extend(
        [
            "",
            "## Komut",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-rank.py",
            "```",
            "",
            "## Notlar",
            "",
            "- Google doğrudan tarama bulut VM IP'lerinde CAPTCHA ile engellenir; "
              "ölçüm `brave_search_proxy` ile yapılır (TR locale, organik web sonuçları).",
            "- Kesin Google SERP doğrulaması için GSC Performance export veya yerel tarayıcı kontrolü önerilir.",
            "- Kayıtlar: `AGENT-HUB/SERP-BASELINE.csv`",
        ]
    )
    return "\n".join(lines) + "\n"


def update_weekly_monitoring(captured_at: datetime, measurements: list[dict[str, object]]) -> Path:
    week_file = WEEKLY_DIR / f"WEEKLY-MONITORING-{week_start(captured_at).strftime('%Y-%m-%d')}.md"
    week_file.write_text(build_weekly_markdown(captured_at, measurements), encoding="utf-8")
    return week_file


def measure_device(device: str, captured_at: datetime) -> dict[str, object]:
    rank, url, source, top10 = fetch_brave_serp(QUERY, device)
    competitor = ""
    competitor_rank = ""
    if top10:
        for r, u in top10:
            dom = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
            if TARGET_DOMAIN not in dom and competitor == "":
                competitor = dom
                competitor_rank = str(r)

    top_summary = "; ".join(f"{r}:{urllib.parse.urlparse(u).netloc}" for r, u in top10[:5])
    notes = (
        f"Brave proxy TR; top5={top_summary}. "
        "Google CAPTCHA on cloud VM; proxy approximates organic order."
    )

    row = {
        "captured_at_utc": captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": url if TARGET_DOMAIN in url else TARGET_URL,
        "rank_position": str(rank),
        "serp_features": "",
        "primary_competitor": competitor,
        "competitor_rank": competitor_rank,
        "source": source,
        "notes": notes,
    }
    return {
        "device": device,
        "rank": rank,
        "url": row["target_url"],
        "source": source,
        "row": row,
    }


def main() -> int:
    captured_at = datetime.now(UTC)
    fields, _ = read_baseline_rows()
    measurements: list[dict[str, object]] = []

    for device in ("mobile", "desktop"):
        try:
            result = measure_device(device, captured_at)
            measurements.append(result)
            append_baseline_row(fields, result["row"])
            print(
                f"{device}: rank={result['rank']} url={result['url']} source={result['source']}"
            )
        except urllib.error.HTTPError as exc:
            print(f"{device}: HTTP {exc.code} — atlandı", file=sys.stderr)
        if device == "mobile":
            time.sleep(2)

    if not measurements:
        print("Ölçüm alınamadı", file=sys.stderr)
        return 1

    weekly_path = update_weekly_monitoring(captured_at, measurements)
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
