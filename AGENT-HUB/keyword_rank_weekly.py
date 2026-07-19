#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — CSV + haftalık özet dosyası."""
from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
GSC_QUERIES_PATH = HUB / "DATA" / "gsc-performance-2026-06-05" / "Sorgular.csv"

QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
DEVICES = ("mobile", "desktop")

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

USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    return f"{host}{path}"


def find_rank(links: list[str], domain: str = TARGET_DOMAIN) -> tuple[int | None, str | None]:
    for index, link in enumerate(links, start=1):
        if domain in link.lower():
            return index, link
    return None, None


def find_competitor(links: list[str], skip_domain: str = TARGET_DOMAIN) -> tuple[str | None, int | None]:
    for index, link in enumerate(links, start=1):
        host = urllib.parse.urlparse(link).netloc.lower().removeprefix("www.")
        if skip_domain not in host:
            return link, index
    return None, None


def fetch_serper(query: str, device: str) -> list[str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None

    payload = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
    }
    if device == "mobile":
        payload["device"] = "mobile"

    request = urllib.request.Request(
        "https://google.serper.dev/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENTS[device],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None

    links: list[str] = []
    for item in data.get("organic", []):
        link = item.get("link")
        if link:
            links.append(link)
    return links or None


def fetch_serpapi(query: str, device: str) -> list[str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None

    params = {
        "engine": "google",
        "q": query,
        "google_domain": "google.com.tr",
        "gl": "tr",
        "hl": "tr",
        "num": "20",
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"

    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENTS[device]})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None

    links = [item.get("link") for item in data.get("organic_results", []) if item.get("link")]
    return links or None


def fetch_duckduckgo(query: str, device: str, retries: int = 3) -> list[str] | None:
    url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query, "kl": "tr-tr"})
    for attempt in range(retries):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENTS[device]})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                html = response.read().decode("utf-8", errors="replace")
            links = [urllib.parse.unquote(match) for match in re.findall(r"uddg=([^&\"]+)", html)]
            if links:
                return links
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2**attempt)
    return None


def fetch_gsc_avg_position(query: str) -> float | None:
    if not GSC_QUERIES_PATH.exists():
        return None
    with GSC_QUERIES_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("En çok yapılan sorgular", "").strip().lower() == query.lower():
                try:
                    return float(str(row.get("Pozisyon", "")).replace(",", "."))
                except ValueError:
                    return None
    return None


def measure_device(
    device: str,
    shared_ddg_links: list[str] | None = None,
    desktop_ddg_links: list[str] | None = None,
) -> dict[str, object]:
    source = ""
    links: list[str] | None = None

    for provider, fetcher in (
        ("serper_api", lambda: fetch_serper(QUERY, device)),
        ("serpapi", lambda: fetch_serpapi(QUERY, device)),
    ):
        links = fetcher()
        if links:
            source = provider
            break

    if not links and shared_ddg_links:
        links = shared_ddg_links
        source = "duckduckgo_lite_proxy"
    if not links:
        links = fetch_duckduckgo(QUERY, device)
        if links:
            source = "duckduckgo_lite_proxy"

    rank, matched_url = find_rank(links or [])
    competitor_url, competitor_rank = find_competitor(links or [])

    if rank is None and links and source == "duckduckgo_lite_proxy":
        links = fetch_duckduckgo(QUERY, device)
        if links:
            rank, matched_url = find_rank(links)
            competitor_url, competitor_rank = find_competitor(links or [])

    inherited_mobile_snapshot = False
    if rank is None and device == "mobile" and desktop_ddg_links:
        links = desktop_ddg_links
        source = "duckduckgo_lite_proxy"
        rank, matched_url = find_rank(links)
        competitor_url, competitor_rank = find_competitor(links or [])
        inherited_mobile_snapshot = True

    notes_parts: list[str] = []
    if source == "duckduckgo_lite_proxy":
        notes_parts.append("DDG lite Google TR proxy; canlı organic yaklaşık gösterge")
    if inherited_mobile_snapshot:
        notes_parts.append("Mobil DDG başarısız; desktop SERP snapshot devralındı")
    if rank is None:
        gsc_position = fetch_gsc_avg_position(QUERY)
        if gsc_position is not None:
            source = source or "gsc_fallback"
            notes_parts.append(f"Organic bulunamadı; GSC avg_position={gsc_position}")
            return {
                "device": device,
                "rank_position": gsc_position,
                "target_url": TARGET_URL,
                "source": source,
                "primary_competitor": competitor_url or "",
                "competitor_rank": competitor_rank or "",
                "notes": "; ".join(notes_parts),
            }
        notes_parts.append("SERP çekilemedi")
        return {
            "device": device,
            "rank_position": "N/A",
            "target_url": TARGET_URL,
            "source": source or "unavailable",
            "primary_competitor": "",
            "competitor_rank": "",
            "notes": "; ".join(notes_parts),
        }

    if matched_url and normalize_url(matched_url) != normalize_url(TARGET_URL):
        notes_parts.append(f"Eşleşen URL: {matched_url}")
    if competitor_url:
        notes_parts.append(f"Rakip #1: {urllib.parse.urlparse(competitor_url).netloc}")

    return {
        "device": device,
        "rank_position": rank,
        "target_url": matched_url or TARGET_URL,
        "source": source,
        "primary_competitor": competitor_url or "",
        "competitor_rank": competitor_rank or "",
        "notes": "; ".join(notes_parts) if notes_parts else "Organic SERP ölçümü",
    }


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_rows(rows: list[dict[str, str]]) -> None:
    existing = read_baseline_rows()
    fieldnames = CSV_FIELDS
    if existing:
        fieldnames = list(existing[0].keys())

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def previous_led_ekran_rows(before_captured_at: str | None = None) -> list[dict[str, str]]:
    rows = [
        row
        for row in read_baseline_rows()
        if row.get("query", "").strip().lower() == QUERY
        and row.get("target_url", "").startswith("https://ledajans.com/")
        and row.get("rank_position", "") not in {"", "pending", "top3", "top5", "top10", "top20"}
        and (before_captured_at is None or row.get("captured_at_utc", "") != before_captured_at)
    ]
    rows.sort(key=lambda row: row.get("captured_at_utc", ""), reverse=True)
    return rows


def format_rank_delta(current: object, previous: object | None) -> str:
    if previous is None:
        return "önceki ölçüm yok"
    try:
        current_value = float(current)
        previous_value = float(previous)
    except (TypeError, ValueError):
        return f"önceki={previous} → şimdi={current}"
    delta = previous_value - current_value
    if delta > 0:
        return f"↑ {abs(delta):.2f} sıra iyileşme (önceki {previous_value:g} → şimdi {current_value:g})"
    if delta < 0:
        return f"↓ {abs(delta):.2f} sıra düşüş (önceki {previous_value:g} → şimdi {current_value:g})"
    return f"stabil ({current_value:g})"


def write_weekly_summary(captured_at: str, measurements: list[dict[str, object]]) -> Path:
    report_date = captured_at[:10]
    report_path = HUB / f"WEEKLY-MONITORING-{report_date}.md"
    previous_rows = previous_led_ekran_rows(before_captured_at=captured_at)

    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Sorgu: **{QUERY}** | locale: `{LOCALE}` | arama motoru: `{SEARCH_ENGINE}`",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Not |",
        "|---|---:|---|---|---|",
    ]

    for item in measurements:
        lines.append(
            f"| {item['device']} | {item['rank_position']} | {item['target_url']} | "
            f"{item['source']} | {item['notes']} |"
        )

    lines.extend(["", "## Önceki ölçümle karşılaştırma", ""])
    for item in measurements:
        device = str(item["device"])
        prev = next((row for row in previous_rows if row.get("device") == device), None)
        prev_rank = prev.get("rank_position") if prev else None
        prev_at = prev.get("captured_at_utc", "—") if prev else "—"
        lines.append(
            f"- **{device}**: {format_rank_delta(item['rank_position'], prev_rank)} "
            f"(son kayıt: {prev_at})"
        )

    # GSC referans
    gsc_position = fetch_gsc_avg_position(QUERY)
    if gsc_position is not None:
        lines.extend(
            [
                "",
                "## GSC referans (son export)",
                "",
                f"- `led ekran` avg position: **{gsc_position}** (`gsc-performance-2026-06-05`)",
                "- Not: GSC avg position ile canlı organic sıra farklı metriklerdir.",
            ]
        )

    lines.extend(
        [
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    desktop_ddg = fetch_duckduckgo(QUERY, "desktop")
    mobile_ddg = fetch_duckduckgo(QUERY, "mobile")

    measurements: list[dict[str, object]] = []
    csv_rows: list[dict[str, str]] = []

    for device in DEVICES:
        shared = mobile_ddg if device == "mobile" else desktop_ddg
        result = measure_device(
            device,
            shared_ddg_links=shared,
            desktop_ddg_links=desktop_ddg,
        )
        measurements.append(result)
        csv_rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": str(result["device"]),
                "search_engine": SEARCH_ENGINE,
                "target_url": str(result["target_url"]),
                "rank_position": str(result["rank_position"]),
                "serp_features": "",
                "primary_competitor": str(result.get("primary_competitor", "")),
                "competitor_rank": str(result.get("competitor_rank", "")),
                "source": str(result["source"]),
                "notes": str(result["notes"]),
            }
        )

    append_baseline_rows(csv_rows)
    report_path = write_weekly_summary(captured_at, measurements)

    for item in measurements:
        print(
            f"{item['device']}: rank={item['rank_position']} source={item['source']} url={item['target_url']}"
        )
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
