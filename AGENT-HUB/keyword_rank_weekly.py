#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP sırası ölçümü — SERP-BASELINE.csv + haftalık özet."""
from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_HOST = "ledajans.com"

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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def http_get_json(url: str, headers: dict[str, str], payload: dict | None = None) -> dict | None:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}{path}"


def host_from_url(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def find_rank(organic: list[dict[str, str]]) -> tuple[int | None, str | None, str, str]:
    for index, item in enumerate(organic, start=1):
        link = item.get("link") or item.get("url") or ""
        if TARGET_HOST in host_from_url(link):
            competitor = organic[0].get("link") or organic[0].get("url") or ""
            comp_host = host_from_url(competitor)
            comp_rank = "1" if index != 1 else ("2" if len(organic) > 1 else "")
            primary = comp_host if index != 1 else (host_from_url(organic[1]["link"]) if len(organic) > 1 else "")
            return index, normalize_url(link), primary, comp_rank
    return None, None, "", ""


def fetch_serper(device: str) -> tuple[int | None, str | None, str, str, str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {
        "q": QUERY,
        "gl": "tr",
        "hl": "tr",
        "num": 20,
    }
    if device == "mobile":
        payload["device"] = "mobile"
    body = http_get_json(
        "https://google.serper.dev/search",
        {"X-API-KEY": api_key, "Content-Type": "application/json"},
        payload,
    )
    if not body:
        return None
    organic = body.get("organic") or []
    rank, target_url, primary, comp_rank = find_rank(organic)
    if rank is None:
        return None
    return rank, target_url, primary, comp_rank, "serper_api"


def fetch_serpapi(device: str) -> tuple[int | None, str | None, str, str, str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = {
        "engine": "google",
        "q": QUERY,
        "google_domain": "google.com.tr",
        "gl": "tr",
        "hl": "tr",
        "num": "20",
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    body = http_get_json(url, {"User-Agent": "LEDAJANS-SERP/1.0"})
    if not body:
        return None
    organic = body.get("organic_results") or []
    normalized = [{"link": item.get("link", "")} for item in organic]
    rank, target_url, primary, comp_rank = find_rank(normalized)
    if rank is None:
        return None
    return rank, target_url, primary, comp_rank, "serpapi"


def fetch_ddg_lite(device: str) -> tuple[int | None, str | None, str, str, str] | None:
    user_agent = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
        if device == "mobile"
        else "Mozilla/5.0 (compatible; LEDAJANS-SERP/1.0)"
    )
    url = "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(QUERY)
    for attempt in range(3):
        if attempt:
            time.sleep(12 * attempt)
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode("utf-8", errors="replace")
        except urllib.error.URLError:
            continue
        links = [urllib.parse.unquote(match) for match in re.findall(r"uddg=([^&\"]+)", html)]
        if not links:
            continue
        organic = [{"link": link} for link in links]
        rank, target_url, primary, comp_rank = find_rank(organic)
        if rank is None:
            continue
        return rank, target_url, primary, comp_rank, "ddg_lite_proxy"
    return None


def fetch_gsc_fallback() -> tuple[str, str]:
    if not BASELINE_PATH.exists():
        return "", ""
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in reversed(rows):
        if row.get("query", "").strip().lower() == QUERY and row.get("source", "").startswith("gsc"):
            return row.get("rank_position", ""), row.get("source", "gsc_fallback")
    return "", ""


def measure_device(device: str, desktop_snapshot: dict[str, str] | None = None) -> dict[str, str]:
    if device == "mobile":
        time.sleep(15)
    for fetcher in (fetch_serper, fetch_serpapi, fetch_ddg_lite):
        result = fetcher(device)
        if result:
            rank, target_url, primary, comp_rank, source = result
            return {
                "device": device,
                "rank_position": str(rank),
                "target_url": target_url or f"https://{TARGET_HOST}/",
                "primary_competitor": primary,
                "competitor_rank": comp_rank,
                "source": source,
                "notes": f"Organic sıra; {source}; device={device}",
            }

    if device == "mobile" and desktop_snapshot and desktop_snapshot.get("source") == "ddg_lite_proxy":
        return {
            "device": device,
            "rank_position": desktop_snapshot["rank_position"],
            "target_url": desktop_snapshot["target_url"],
            "primary_competitor": desktop_snapshot.get("primary_competitor", ""),
            "competitor_rank": desktop_snapshot.get("competitor_rank", ""),
            "source": "ddg_lite_proxy",
            "notes": "Mobile DDG rate-limit; aynı snapshot desktop ölçümünden devralındı",
        }

    gsc_rank, gsc_source = fetch_gsc_fallback()
    return {
        "device": device,
        "rank_position": gsc_rank or "N/A",
        "target_url": f"https://{TARGET_HOST}/",
        "primary_competitor": "",
        "competitor_rank": "",
        "source": gsc_source or "gsc_fallback",
        "notes": "Canlı SERP alınamadı; son GSC avg_position kullanıldı",
    }


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_rows(captured_at: str, measurements: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for measurement in measurements:
        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": measurement["device"],
                "search_engine": SEARCH_ENGINE,
                "target_url": measurement["target_url"],
                "rank_position": measurement["rank_position"],
                "serp_features": "",
                "primary_competitor": measurement["primary_competitor"],
                "competitor_rank": measurement["competitor_rank"],
                "source": measurement["source"],
                "notes": measurement["notes"],
            }
        )

    file_exists = BASELINE_PATH.exists() and BASELINE_PATH.stat().st_size > 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return rows


def previous_led_ekran_row(rows: list[dict[str, str]], device: str) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY and row.get("device") == device
    ]
    return matches[-1] if matches else None


def delta_text(current: str, previous: str | None) -> str:
    if not previous or previous in {"", "N/A", "pending", "top3", "top5", "top10", "top20"}:
        return "önceki: " + (previous or "yok")
    try:
        cur = float(current)
        prev = float(previous)
    except ValueError:
        return f"önceki: {previous}"
    diff = prev - cur
    if diff > 0:
        return f"↑ {diff:.1f} sıra (önceki {prev})"
    if diff < 0:
        return f"↓ {abs(diff):.1f} sıra (önceki {prev})"
    return f"→ sabit (önceki {prev})"


def write_weekly_summary(captured_at: str, measurements: list[dict[str, str]], prior_rows: list[dict[str, str]]) -> Path:
    date_label = captured_at[:10]
    path = HUB / f"WEEKLY-MONITORING-{date_label}.md"
    desktop = next(item for item in measurements if item["device"] == "desktop")
    mobile = next(item for item in measurements if item["device"] == "mobile")
    prev_desktop = previous_led_ekran_row(prior_rows, "desktop")
    prev_mobile = previous_led_ekran_row(prior_rows, "mobile")

    lines = [
        f"# Haftalık SEO İzleme — {date_label}",
        "",
        "## SERP — `led ekran` (tr-TR, Google)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Değişim |",
        "|-------|-----:|-----------|--------|---------|",
        f"| desktop | {desktop['rank_position']} | {desktop['target_url']} | {desktop['source']} | "
        f"{delta_text(desktop['rank_position'], (prev_desktop or {}).get('rank_position'))} |",
        f"| mobile | {mobile['rank_position']} | {mobile['target_url']} | {mobile['source']} | "
        f"{delta_text(mobile['rank_position'], (prev_mobile or {}).get('rank_position'))} |",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Birincil rakip (desktop): `{desktop.get('primary_competitor') or '—'}` "
        f"(rakip sıra: {desktop.get('competitor_rank') or '—'})",
        f"- CSV güncellendi: `AGENT-HUB/SERP-BASELINE.csv` (+{len(measurements)} satır)",
        "",
        "## Notlar",
        "- Canlı organic sıra ile GSC `avg_position` farklı metriklerdir; trend için aynı kaynağı karşılaştırın.",
        "- API anahtarı yoksa DuckDuckGo lite proxy kullanılır (Google SERP yaklaşık proxy).",
        "",
        "## Sonraki çalıştırma",
        "```bash",
        "python3 AGENT-HUB/keyword_rank_weekly.py",
        "```",
        "",
        "Cron/automation: `0 6 * * *` UTC (`AGENT-HUB/run-keyword-rank-weekly.sh`).",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    captured_at = utc_now_iso()
    prior_rows = read_baseline_rows()
    desktop = measure_device("desktop")
    mobile = measure_device("mobile", desktop_snapshot=desktop)
    measurements = [desktop, mobile]
    appended = append_baseline_rows(captured_at, measurements)
    weekly_path = write_weekly_summary(captured_at, measurements, prior_rows)

    for row in appended:
        print(
            f"{row['device']}: rank={row['rank_position']} url={row['target_url']} source={row['source']}"
        )
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    print(f"baseline_rows={len(appended)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
