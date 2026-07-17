#!/usr/bin/env python3
"""Haftalık/günlük 'led ekran' SERP ölçümü → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_HOST = "ledajans.com"
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


def captured_at_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def week_file_date() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def read_baseline() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def append_baseline(rows: list[dict[str, str]]) -> int:
    existing = read_baseline()
    keys = {
        (r.get("captured_at_utc", ""), r.get("query", "").lower(), r.get("device", ""), r.get("source", ""))
        for r in existing
    }
    to_write = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in keys
    ]
    if not to_write:
        return 0
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_write:
            writer.writerow({key: row.get(key, "") for key in CSV_FIELDS})
    return len(to_write)


def normalize_host(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def find_rank(results: list[tuple[int, str]], host: str = TARGET_HOST) -> tuple[int | None, str]:
    for pos, url in results:
        if normalize_host(url) == host or host in normalize_host(url):
            return pos, url
    return None, ""


def top_competitor(results: list[tuple[int, str]]) -> tuple[str, int]:
    for pos, url in results:
        host = normalize_host(url)
        if host != TARGET_HOST and "ledajans.com" not in host:
            return host, pos
    return "", 0


def ddg_organic(query: str) -> list[tuple[int, str]]:
    url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query, "kl": "tr-tr"})
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-SERP/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    links: list[str] = []
    for encoded in re.findall(r"uddg=([^&\"]+)", html):
        links.append(urllib.parse.unquote(encoded))
    return [(i + 1, link) for i, link in enumerate(links)]


def serper_organic(query: str, device: str) -> list[tuple[int, str]]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return []
    payload = json.dumps(
        {
            "q": query,
            "gl": "tr",
            "hl": "tr",
            "num": 20,
            "device": device,
        }
    ).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    organic = data.get("organic") or []
    return [(i + 1, item.get("link", "")) for i, item in enumerate(organic) if item.get("link")]


def serpapi_organic(query: str, device: str) -> list[tuple[int, str]]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return []
    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "device": device,
            "num": 20,
            "api_key": api_key,
        }
    )
    req = urllib.request.Request(f"https://serpapi.com/search.json?{params}")
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
    organic = data.get("organic_results") or []
    return [(i + 1, item.get("link", "")) for i, item in enumerate(organic) if item.get("link")]


def gsc_fallback_position() -> tuple[str, str]:
    rows = read_baseline()
    for row in reversed(rows):
        if row.get("query", "").lower() == QUERY and row.get("source", "").startswith("gsc_"):
            return row.get("rank_position", "N/A"), row.get("source", "gsc_fallback")
    return "N/A", "gsc_fallback"


def measure_device(device: str) -> dict[str, str]:
    sources = [
        ("serper_google_tr", lambda: serper_organic(QUERY, device)),
        ("serpapi_google_tr", lambda: serpapi_organic(QUERY, device)),
        ("ddg_lite_proxy_tr", lambda: ddg_organic(QUERY)),
    ]
    errors: list[str] = []
    for source_name, fetcher in sources:
        try:
            results = fetcher()
            if not results:
                continue
            rank, matched_url = find_rank(results)
            competitor, competitor_rank = top_competitor(results)
            if rank is None:
                errors.append(f"{source_name}: hedef URL ilk {len(results)} sonuçta yok")
                continue
            return {
                "rank_position": str(rank),
                "target_url": matched_url or TARGET_URL,
                "source": source_name,
                "primary_competitor": competitor,
                "competitor_rank": str(competitor_rank) if competitor_rank else "",
                "notes": f"organic_top={len(results)}; competitor={competitor}@{competitor_rank}",
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            errors.append(f"{source_name}: {exc}")
    position, source = gsc_fallback_position()
    return {
        "rank_position": position,
        "target_url": TARGET_URL,
        "source": source,
        "primary_competitor": "",
        "competitor_rank": "",
        "notes": "live_serp_unavailable; " + "; ".join(errors) if errors else "live_serp_unavailable",
    }


def build_rows(timestamp: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for device in DEVICES:
        measured = measure_device(device)
        rows.append(
            {
                "captured_at_utc": timestamp,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": measured["target_url"],
                "rank_position": measured["rank_position"],
                "serp_features": "",
                "primary_competitor": measured["primary_competitor"],
                "competitor_rank": measured["competitor_rank"],
                "source": measured["source"],
                "notes": measured["notes"],
            }
        )
    return rows


def parse_numeric_rank(value: str) -> float | None:
    value = (value or "").strip().lower()
    if not value or value in {"n/a", "pending", "top3", "top5", "top10", "top20"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def led_ekran_history() -> list[dict[str, str]]:
  history = [
      row
      for row in read_baseline()
      if row.get("query", "").lower() == QUERY and row.get("target_url", "").rstrip("/") in {TARGET_URL.rstrip("/"), ""}
  ]
  return sorted(history, key=lambda r: r.get("captured_at_utc", ""))


def weekly_summary_md(timestamp: str, new_rows: list[dict[str, str]]) -> str:
    history = led_ekran_history()
    mobile_row = next((r for r in new_rows if r["device"] == "mobile"), {})
    desktop_row = next((r for r in new_rows if r["device"] == "desktop"), {})
    prior = [r for r in history if r.get("captured_at_utc", "") < timestamp]
    prior_mobile = next((r for r in reversed(prior) if r.get("device") == "mobile"), None)
    prior_desktop = next((r for r in reversed(prior) if r.get("device") == "desktop"), None)

    def delta(current: str, previous: dict[str, str] | None) -> str:
        if not previous:
            return "ilk ölçüm"
        cur = parse_numeric_rank(current)
        prev = parse_numeric_rank(previous.get("rank_position", ""))
        if cur is None or prev is None:
            return "karşılaştırılamaz"
        diff = prev - cur
        if diff > 0:
            return f"↑ {diff:.0f} sıra iyileşme (önceki: {prev})"
        if diff < 0:
            return f"↓ {abs(diff):.0f} sıra düşüş (önceki: {prev})"
        return "stabil"

    lines = [
        f"# Haftalık SEO İzleme — {week_file_date()}",
        "",
        "## SERP — `led ekran`",
        "",
        f"- Ölçüm UTC: `{timestamp}`",
        f"- Mobil sıra: **{mobile_row.get('rank_position', 'N/A')}** ({mobile_row.get('source', '')}) — {delta(mobile_row.get('rank_position', ''), prior_mobile)}",
        f"- Masaüstü sıra: **{desktop_row.get('rank_position', 'N/A')}** ({desktop_row.get('source', '')}) — {delta(desktop_row.get('rank_position', ''), prior_desktop)}",
        f"- Hedef URL: {mobile_row.get('target_url', TARGET_URL)}",
        "",
        "| captured_at_utc | device | rank | source | competitor |",
        "|---|---|---:|---|---|",
    ]
    for row in history[-8:]:
        lines.append(
            f"| {row.get('captured_at_utc', '')} | {row.get('device', '')} | "
            f"{row.get('rank_position', '')} | {row.get('source', '')} | "
            f"{row.get('primary_competitor', '')} |"
        )
    lines.extend(
        [
            "",
            "## Kayıt",
            f"- `SERP-BASELINE.csv` yeni satır: {len(new_rows)}",
            "- Script: `python3 AGENT-HUB/keyword_rank_weekly.py`",
            "- Cron: `0 6 * * *` UTC",
            "",
            "## Not",
            "- Canlı organic sıra ile GSC `avg_position` farklı metriklerdir.",
            "- `SERPER_API_KEY` veya `SERPAPI_KEY` tanımlıysa Google TR organic önceliklidir; aksi halde DDG lite proxy kullanılır.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_weekly_summary(timestamp: str, new_rows: list[dict[str, str]]) -> Path:
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{week_file_date()}.md"
    path.write_text(weekly_summary_md(timestamp, new_rows), encoding="utf-8")
    return path


def main() -> int:
    timestamp = captured_at_utc()
    rows = build_rows(timestamp)
    appended = append_baseline(rows)
    weekly_path = write_weekly_summary(timestamp, rows)

    for row in rows:
        print(
            f"{row['device']}: rank={row['rank_position']} source={row['source']} url={row['target_url']}"
        )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
