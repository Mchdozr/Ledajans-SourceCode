#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü: SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
DEVICES = ("mobile", "desktop")
MAX_RESULTS = 20
DDG_LITE_URL = "https://lite.duckduckgo.com/lite/"
USER_AGENT = "Mozilla/5.0 (compatible; LEDAJANS-SERP/1.0)"

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


@dataclass
class SerpSnapshot:
    rank_position: int | str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""
    serp_features: str = ""
    result_urls: list[str] | None = None


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    return f"{host}{path}"


def domain_from_url(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def find_rank(urls: list[str], domain: str = TARGET_DOMAIN) -> tuple[int | str, str]:
    for index, url in enumerate(urls, start=1):
        if domain in domain_from_url(url):
            return index, url
    return "not_in_top20", ""


def http_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    method: str = "GET",
    timeout: int = 25,
) -> dict:
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_serper(query: str, device: str) -> SerpSnapshot | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None

    payload = json.dumps(
        {
            "q": query,
            "gl": "tr",
            "hl": "tr",
            "num": MAX_RESULTS,
            "device": device,
        }
    ).encode("utf-8")
    body = http_json(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        data=payload,
        method="POST",
    )
    organic = body.get("organic") or []
    urls = [item.get("link", "") for item in organic if item.get("link")]
    rank, matched = find_rank(urls)
    competitor = ""
    competitor_rank = ""
    if urls:
        competitor = domain_from_url(urls[0])
        competitor_rank = "1" if rank != 1 else ""
    notes = f"Serper organic={len(urls)}"
    if matched:
        notes += f"; matched_url={matched}"
    return SerpSnapshot(
        rank_position=rank,
        source="serper_api",
        notes=notes,
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
        result_urls=urls,
    )


def fetch_serpapi(query: str, device: str) -> SerpSnapshot | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None

    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": query,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "num": MAX_RESULTS,
            "device": device,
            "api_key": api_key,
        }
    )
    body = http_json(f"https://serpapi.com/search.json?{params}")
    organic = body.get("organic_results") or []
    urls = [item.get("link", "") for item in organic if item.get("link")]
    rank, matched = find_rank(urls)
    competitor = domain_from_url(urls[0]) if urls else ""
    competitor_rank = "1" if urls and rank != 1 else ""
    notes = f"SerpAPI organic={len(urls)}"
    if matched:
        notes += f"; matched_url={matched}"
    return SerpSnapshot(
        rank_position=rank,
        source="serpapi",
        notes=notes,
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
        result_urls=urls,
    )


def fetch_ddg_lite(query: str, *, retries: int = 3) -> SerpSnapshot:
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            url = DDG_LITE_URL + "?" + urllib.parse.urlencode({"q": query})
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=25) as response:
                html = response.read().decode("utf-8", errors="replace")

            encoded_urls = re.findall(r"uddg=([^&\"]+)", html)
            urls: list[str] = []
            seen: set[str] = set()
            for encoded in encoded_urls:
                decoded = urllib.parse.unquote(encoded)
                key = normalize_url(decoded)
                if key in seen:
                    continue
                seen.add(key)
                urls.append(decoded)
                if len(urls) >= MAX_RESULTS:
                    break

            rank, matched = find_rank(urls)
            competitor = domain_from_url(urls[0]) if urls else ""
            competitor_rank = "1" if urls and rank != 1 else ""
            notes = f"DDG lite proxy organic={len(urls)}; attempt={attempt}"
            if matched:
                notes += f"; matched_url={matched}"
            return SerpSnapshot(
                rank_position=rank,
                source="ddg_lite_proxy",
                notes=notes,
                primary_competitor=competitor,
                competitor_rank=competitor_rank,
                result_urls=urls,
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(2 ** attempt)

    return SerpSnapshot(
        rank_position="error",
        source="ddg_lite_proxy",
        notes=f"DDG fetch failed after {retries} attempts: {last_error}",
    )


def gsc_fallback_rank() -> SerpSnapshot | None:
    """Son bilinen GSC avg_position değerini yedek olarak kullan."""
    if not BASELINE_PATH.exists():
        return None

    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in reversed(rows):
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("source", "").startswith("gsc_performance")
            and row.get("rank_position")
        ):
            return SerpSnapshot(
                rank_position=row["rank_position"],
                source="gsc_fallback",
                notes=(
                    "Canlı SERP kaynağı başarısız; son GSC avg_position kullanıldı "
                    f"({row.get('captured_at_utc', '')})"
                ),
                primary_competitor=row.get("primary_competitor", ""),
            )
    return None


def capture_device_rank(device: str, shared_ddg: SerpSnapshot | None = None) -> SerpSnapshot:
    for fetcher in (fetch_serper, fetch_serpapi):
        snapshot = fetcher(QUERY, device)
        if snapshot and snapshot.rank_position != "error":
            return snapshot

    if shared_ddg and shared_ddg.rank_position != "error":
        notes = shared_ddg.notes
        if device == "mobile":
            notes += "; mobile=ddg_desktop_snapshot"
        return SerpSnapshot(
            rank_position=shared_ddg.rank_position,
            source=shared_ddg.source,
            notes=notes,
            primary_competitor=shared_ddg.primary_competitor,
            competitor_rank=shared_ddg.competitor_rank,
            serp_features=shared_ddg.serp_features,
            result_urls=shared_ddg.result_urls,
        )

    ddg = fetch_ddg_lite(QUERY)
    if ddg.rank_position != "error":
        if device == "mobile":
            ddg.notes += "; mobile=ddg_desktop_snapshot"
        return ddg

    fallback = gsc_fallback_rank()
    if fallback:
        fallback.notes += f"; device={device}"
        return fallback

    return SerpSnapshot(
        rank_position="unavailable",
        source="none",
        notes=f"Tüm SERP kaynakları başarısız; device={device}",
    )


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    existing = read_baseline_rows()
    existing_keys = {
        (r.get("captured_at_utc", ""), r.get("query", "").lower(), r.get("device", ""), r.get("source", ""))
        for r in existing
    }

    to_write = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in existing_keys
    ]
    if not to_write:
        return 0

    file_exists = BASELINE_PATH.exists() and BASELINE_PATH.stat().st_size > 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for row in to_write:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return len(to_write)


def build_csv_rows(captured_at: str, snapshots: dict[str, SerpSnapshot]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for device in DEVICES:
        snap = snapshots[device]
        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": QUERY,
                "locale": LOCALE,
                "device": device,
                "search_engine": SEARCH_ENGINE,
                "target_url": TARGET_URL,
                "rank_position": str(snap.rank_position),
                "serp_features": snap.serp_features,
                "primary_competitor": snap.primary_competitor,
                "competitor_rank": snap.competitor_rank,
                "source": snap.source,
                "notes": snap.notes,
            }
        )
    return rows


def previous_weekly_rank(device: str = "desktop", *, before_capture: str | None = None) -> str:
    rows = read_baseline_rows()
    for row in reversed(rows):
        if before_capture and row.get("captured_at_utc", "") >= before_capture:
            continue
        if row.get("query", "").strip().lower() == QUERY and row.get("device") == device:
            return row.get("rank_position", "N/A")
    return "N/A"


def write_weekly_report(
    captured_at: str,
    snapshots: dict[str, SerpSnapshot],
    appended: int,
    prev_ranks: dict[str, str] | None = None,
) -> Path:
    report_date = captured_at[:10]
    report_path = HUB / f"WEEKLY-MONITORING-{report_date}.md"

    desktop = snapshots["desktop"]
    mobile = snapshots["mobile"]
    prev_desktop = (prev_ranks or {}).get("desktop", previous_weekly_rank("desktop", before_capture=captured_at))
    prev_mobile = (prev_ranks or {}).get("mobile", previous_weekly_rank("mobile", before_capture=captured_at))

    top5_lines = ""
    sample_urls = desktop.result_urls or mobile.result_urls or []
    if sample_urls:
        top5_lines = "\n".join(f"| {i} | {url} |" for i, url in enumerate(sample_urls[:5], start=1))
    else:
        top5_lines = "| — | Sonuç listesi alınamadı |"

    content = f"""# Haftalık SEO İzleme — {report_date}

## SERP: "led ekran" (ledajans.com)

| Alan | Değer |
|------|-------|
| Ölçüm UTC | {captured_at} |
| Locale | {LOCALE} |
| Arama motoru | Google (proxy/API) |
| Hedef URL | {TARGET_URL} |
| Desktop sıra | **{desktop.rank_position}** (önceki: {prev_desktop}) |
| Mobile sıra | **{mobile.rank_position}** (önceki: {prev_mobile}) |
| Veri kaynağı | {desktop.source} |
| Birincil rakip | {desktop.primary_competitor or '—'} |
| CSV eklenen satır | {appended} |

### Top 5 organic (snapshot)

| # | URL |
|---|-----|
{top5_lines}

### Notlar
- Desktop: {desktop.notes}
- Mobile: {mobile.notes}
- GSC `avg_position` ile canlı organic sıra farklı metriklerdir; ikisi birlikte izlenmeli.
- Son GSC avg_position (2026-06-05): **6.78** (`gsc_performance_2026-06-05`)

## Komutlar

```bash
cd /workspace
python3 AGENT-HUB/keyword_rank_weekly.py
```

Cron (automation): `0 6 * * *` UTC → `AGENT-HUB/run-keyword-rank-weekly.sh`

## Sonraki hafta
- `SERP-BASELINE.csv` trendini kontrol et
- GSC Performance export ile avg_position doğrula
- `python3 AGENT-HUB/audit-money-pages.py`
"""
    report_path.write_text(content, encoding="utf-8")
    return report_path


def main() -> int:
    captured_at = utc_now_iso()
    prev_ranks = {
        device: previous_weekly_rank(device)
        for device in DEVICES
    }
    shared_ddg = fetch_ddg_lite(QUERY)
    snapshots = {device: capture_device_rank(device, shared_ddg) for device in DEVICES}
    rows = build_csv_rows(captured_at, snapshots)
    appended = append_baseline_rows(rows)
    report_path = write_weekly_report(captured_at, snapshots, appended, prev_ranks)

    print(f"query={QUERY}")
    print(f"captured_at_utc={captured_at}")
    print(f"desktop_rank={snapshots['desktop'].rank_position}")
    print(f"mobile_rank={snapshots['mobile'].rank_position}")
    print(f"source={snapshots['desktop'].source}")
    print(f"primary_competitor={snapshots['desktop'].primary_competitor}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")

    if snapshots["desktop"].rank_position in {"error", "unavailable"}:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
