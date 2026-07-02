#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus, unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
DATA_DIR = ROOT / "AGENT-HUB" / "DATA"

QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
DEVICES = ("mobile", "desktop")

UA = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_baseline() -> tuple[list[str], list[dict[str, str]]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def find_rank_in_results(results: list[dict[str, str]], domain: str) -> tuple[int | None, str]:
    for item in results:
        link = item.get("link", "")
        host = re.sub(r"^https?://(www\.)?", "", link).split("/")[0].lower()
        if domain in host:
            return int(item["position"]), link
    return None, ""


def fetch_serper(query: str, device: str, api_key: str) -> tuple[list[dict[str, str]], str]:
    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 50}
    if device == "mobile":
        payload["device"] = "mobile"
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    organic = response.json().get("organic", [])
    results = [
        {"position": str(i + 1), "link": row.get("link", "")}
        for i, row in enumerate(organic)
    ]
    return results, "serper_google"


def fetch_serpapi(query: str, device: str, api_key: str) -> tuple[list[dict[str, str]], str]:
    params = {
        "engine": "google",
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 50,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    response.raise_for_status()
    organic = response.json().get("organic_results", [])
    results = [
        {"position": str(row.get("position", i + 1)), "link": row.get("link", "")}
        for i, row in enumerate(organic)
    ]
    return results, "serpapi_google"


def fetch_ddg_html(query: str, device: str) -> tuple[list[dict[str, str]], str]:
    headers = {
        "User-Agent": UA[device],
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query, "kl": "tr-tr"},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', response.text)
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    rank = 0
    for href in links:
        if "uddg=" in href:
            url = unquote(re.search(r"uddg=([^&]+)", href).group(1))
        else:
            url = href
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
        if host in seen:
            continue
        seen.add(host)
        rank += 1
        results.append({"position": str(rank), "link": url})
    return results, "duckduckgo_html_proxy"


def fetch_gsc_if_fresh(query: str) -> tuple[float | None, str, str]:
    if not DATA_DIR.is_dir():
        return None, "", ""
    cutoff = datetime.now(UTC).date() - timedelta(days=7)
    best_date: datetime.date | None = None
    best_path: Path | None = None
    for folder in DATA_DIR.iterdir():
        if not folder.is_dir() or not folder.name.startswith("gsc-performance-"):
            continue
        date_part = folder.name.replace("gsc-performance-", "")
        try:
            folder_date = datetime.strptime(date_part, "%Y-%m-%d").date()
        except ValueError:
            continue
        if folder_date >= cutoff and (best_date is None or folder_date > best_date):
            queries_path = folder / "Sorgular.csv"
            if queries_path.is_file():
                best_date = folder_date
                best_path = queries_path
    if not best_path:
        return None, "", ""
    with best_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("En çok yapılan sorgular") or "").strip().lower()
            if name == query.lower():
                pos = (row.get("Pozisyon") or "").strip().replace(",", ".")
                try:
                    return float(pos), f"gsc_performance_{best_date}", best_path.parent.name
                except ValueError:
                    return None, "", ""
    return None, "", ""


def measure_device(query: str, device: str) -> dict[str, str]:
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()
    results: list[dict[str, str]] = []
    source = ""
    search_engine = "google"

    if serper_key:
        results, source = fetch_serper(query, device, serper_key)
    elif serpapi_key:
        results, source = fetch_serpapi(query, device, serpapi_key)
    else:
        results, source = fetch_ddg_html(query, device)
        search_engine = "duckduckgo_proxy"

    rank, url = find_rank_in_results(results, TARGET_DOMAIN)
    if not url:
        url = TARGET_URL

    primary_competitor = ""
    competitor_rank = ""
    if results:
        first = results[0]
        first_host = re.sub(r"^https?://(www\.)?", "", first.get("link", "")).split("/")[0]
        if TARGET_DOMAIN not in first_host.lower():
            primary_competitor = first_host
            competitor_rank = first.get("position", "")

    gsc_pos, gsc_source, gsc_folder = fetch_gsc_if_fresh(query)
    notes_parts = []
    if rank is None:
        notes_parts.append("Hedef domain ilk 50 sonuçta görünmedi")
    else:
        notes_parts.append(f"organic_rank={rank}")
    if source == "duckduckgo_html_proxy":
        notes_parts.append("Google organic proxy; SERPER_API_KEY ile kesin ölçüm önerilir")
    if gsc_pos is not None:
        notes_parts.append(f"GSC avg_position={gsc_pos} ({gsc_folder})")

    return {
        "query": query,
        "locale": LOCALE,
        "device": device,
        "search_engine": search_engine,
        "target_url": url,
        "rank_position": str(rank) if rank is not None else "not_found",
        "serp_features": "",
        "primary_competitor": primary_competitor,
        "competitor_rank": competitor_rank,
        "source": source if rank is not None or source else "unavailable",
        "notes": "; ".join(notes_parts),
        "gsc_position": str(gsc_pos) if gsc_pos is not None else "",
    }


def append_baseline(rows: list[dict[str, str]], captured_at: str) -> int:
    fields, existing = read_baseline()
    existing_keys = {
        (r["captured_at_utc"], r["query"].lower(), r["device"], r["source"])
        for r in existing
    }
    appended = 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for row in rows:
            key = (captured_at, row["query"].lower(), row["device"], row["source"])
            if key in existing_keys:
                continue
            out = {field: "" for field in fields}
            out.update({k: v for k, v in row.items() if k in fields})
            out["captured_at_utc"] = captured_at
            writer.writerow(out)
            appended += 1
    return appended


def previous_rank_for_query(query: str, device: str, source: str | None = None) -> dict[str, str] | None:
    _, rows = read_baseline()
    matches = [
        r
        for r in rows
        if r.get("query", "").lower() == query.lower() and r.get("device") == device
    ]
    if source:
        same_source = [r for r in matches if r.get("source") == source]
        if same_source:
            matches = same_source
    if not matches:
        return None
    matches.sort(key=lambda r: r.get("captured_at_utc", ""), reverse=True)
    return matches[0]


def update_weekly_monitoring(
    captured_at: str,
    measurements: list[dict[str, str]],
    previous_ranks: dict[str, dict[str, str] | None],
) -> Path:
    run_date = captured_at[:10]
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{run_date}.md"

    lines = [
        f"# Haftalık SEO İzleme — {run_date}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        "",
        "| Cihaz | Motor | Sıra | Hedef URL | Kaynak | Not |",
        "|---|---|---:|---|---|---|",
    ]
    for m in measurements:
        lines.append(
            f"| {m['device']} | {m['search_engine']} | {m['rank_position']} | "
            f"{m['target_url']} | {m['source']} | {m['notes']} |"
        )

    lines.extend(["", "## Önceki ölçümle fark", ""])
    for m in measurements:
        prev = previous_ranks.get(m["device"])
        if prev is None:
            any_prev = previous_rank_for_query(m["query"], m["device"])
            if any_prev:
                delta = (
                    f"ilk {m['source']} ölçümü; önceki kayıt "
                    f"({any_prev.get('source')}): {any_prev.get('rank_position')}"
                )
            else:
                delta = "ilk kayıt"
        elif prev.get("rank_position") == m["rank_position"]:
            delta = f"değişmedi ({m['rank_position']})"
        else:
            delta = f"{prev.get('rank_position')} → {m['rank_position']} ({prev.get('source')})"
        lines.append(f"- **{m['device']}**: {delta}")

    gsc_notes = [m["gsc_position"] for m in measurements if m.get("gsc_position")]
    if gsc_notes:
        lines.extend(
            [
                "",
                "## GSC (≤7 gün taze export)",
                "",
                f"- Ortalama pozisyon: **{gsc_notes[0]}** (site geneli; organic SERP ile birebir değil)",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## GSC",
                "",
                "- Son 7 günde taze Performance export yok; panelden export sonrası "
                "`scripts/update-serp-baseline-from-gsc.py` ile güncellenebilir.",
            ]
        )

    lines.extend(
        [
            "",
            "## Sonraki çalıştırma",
            "",
            "```bash",
            "cd /workspace && python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
            "",
            "Cron: `0 6 * * *` (UTC) — `AGENT-HUB/run-keyword-rank-weekly.sh`",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    captured_at = utc_now_iso()
    measurements = [measure_device(QUERY, device) for device in DEVICES]
    previous = {
        m["device"]: previous_rank_for_query(QUERY, m["device"], m["source"])
        for m in measurements
    }
    appended = append_baseline(measurements, captured_at)
    weekly_path = update_weekly_monitoring(captured_at, measurements, previous)

    print(f"captured_at_utc={captured_at}")
    for m in measurements:
        print(
            f"query={m['query']} device={m['device']} rank={m['rank_position']} "
            f"source={m['source']} url={m['target_url']}"
        )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
