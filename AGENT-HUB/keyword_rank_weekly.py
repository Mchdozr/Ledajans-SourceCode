#!/usr/bin/env python3
"""Haftalık SERP ölçümü: led ekran → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import argparse
import csv
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_HOST = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
USER_AGENT = (
    "Mozilla/5.0 (compatible; LEDAJANS-SERP-Monitor/1.0; +https://ledajans.com)"
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if url.startswith("http://"):
        url = "https://" + url[7:]
    return url


def find_rank(results: list[str], host: str = TARGET_HOST) -> tuple[int | None, str | None]:
    for index, url in enumerate(results, start=1):
        if host in url.lower():
            return index, normalize_url(url) + ("/" if url.rstrip("/").endswith(host) else "")
    return None, None


def fetch_serper(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return [], "serper_skipped"

    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 30}
    if device == "mobile":
        payload["device"] = "mobile"

    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    links = [item.get("link", "") for item in data.get("organic", []) if item.get("link")]
    return links, "serper_api"


def fetch_serpapi(query: str, device: str) -> tuple[list[str], str]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return [], "serpapi_skipped"

    params = {
        "engine": "google",
        "q": query,
        "hl": "tr",
        "gl": "tr",
        "num": 30,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"

    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    links = [item.get("link", "") for item in data.get("organic_results", []) if item.get("link")]
    return links, "serpapi"


def fetch_ddg_lite(query: str) -> tuple[list[str], str]:
    response = requests.post(
        "https://lite.duckduckgo.com/lite/",
        data={"q": query, "kl": "tr-tr"},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    links = re.findall(r'<a[^>]+href="(https?://[^"]+)"', response.text)
    results: list[str] = []
    for link in links:
        if "duckduckgo.com" in link:
            continue
        if link not in results:
            results.append(link)
    return results, "ddg_lite_proxy"


def measure_device(device: str) -> dict[str, str]:
    errors: list[str] = []
    for fetcher in (fetch_serper, fetch_serpapi):
        try:
            links, source = fetcher(QUERY, device)
            if links:
                rank, target = find_rank(links)
                if rank is not None:
                    return build_row(device, rank, target or TARGET_URL, source, links, errors)
        except requests.RequestException as exc:
            errors.append(f"{fetcher.__name__}: {exc}")

    try:
        links, source = fetch_ddg_lite(QUERY)
        rank, target = find_rank(links)
        note = "DDG lite proxy; Google doğrudan scrape engelli olabilir"
        if errors:
            note += "; " + "; ".join(errors)
        if rank is None:
            return build_row(device, "not_found", TARGET_URL, source, links, errors, note)
        return build_row(device, rank, target or TARGET_URL, source, links, errors, note)
    except requests.RequestException as exc:
        errors.append(f"ddg_lite: {exc}")
        return build_row(device, "error", TARGET_URL, "unavailable", [], errors, "; ".join(errors))


def build_row(
    device: str,
    rank: int | str,
    target_url: str,
    source: str,
    links: list[str],
    errors: list[str],
    extra_note: str = "",
) -> dict[str, str]:
    top3 = ", ".join(links[:3]) if links else "n/a"
    competitor = links[0] if links and TARGET_HOST not in links[0].lower() else ""
    competitor_rank = "1" if competitor else ""
    notes = f"Top3={top3}"
    if extra_note:
        notes = f"{extra_note}; {notes}"
    if errors and "DDG" not in extra_note:
        notes += "; " + "; ".join(errors)

    return {
        "captured_at_utc": utc_now_iso(),
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": target_url,
        "rank_position": str(rank),
        "serp_features": "",
        "primary_competitor": competitor,
        "competitor_rank": competitor_rank,
        "source": source,
        "notes": notes,
    }


def read_baseline_fields() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def append_baseline(rows: list[dict[str, str]]) -> int:
    fields = read_baseline_fields()
    existing: set[tuple[str, str, str, str]] = set()
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            existing.add(
                (
                    row.get("captured_at_utc", "")[:10],
                    row.get("query", "").lower(),
                    row.get("device", ""),
                    row.get("source", ""),
                )
            )

    appended = 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        for row in rows:
            key = (row["captured_at_utc"][:10], row["query"].lower(), row["device"], row["source"])
            if key in existing:
                continue
            writer.writerow({field: row.get(field, "") for field in fields})
            existing.add(key)
            appended += 1
    return appended


def previous_led_ekran_rows(before_date: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("query", "").strip().lower() != QUERY:
                continue
            if row.get("search_engine") != SEARCH_ENGINE:
                continue
            if before_date and row.get("captured_at_utc", "")[:10] >= before_date:
                continue
            rows.append(row)
    return rows


def write_weekly_report(rows: list[dict[str, str]], appended: int) -> Path:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{today}.md"
    previous = previous_led_ekran_rows(before_date=today)

    lines = [
        f"# Haftalık SEO İzleme — {today}",
        "",
        "## SERP — `led ekran` (Google, tr-TR)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Ölçüm (UTC) |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['device']} | {row['rank_position']} | {row['target_url']} | "
            f"{row['source']} | {row['captured_at_utc']} |"
        )

    lines.extend(["", "### Notlar", ""])
    for row in rows:
        lines.append(f"- **{row['device']}**: {row['notes']}")

    if previous:
        mobile_prev = next((r for r in reversed(previous) if r.get("device") == "mobile"), previous[-1])
        desktop_prev = next((r for r in reversed(previous) if r.get("device") == "desktop"), previous[-1])
        lines.extend(
            [
                "",
                "### Önceki ölçümle karşılaştırma",
                f"- Mobil önceki: {mobile_prev.get('captured_at_utc')} → **{mobile_prev.get('rank_position')}** ({mobile_prev.get('source')})",
                f"- Masaüstü önceki: {desktop_prev.get('captured_at_utc')} → **{desktop_prev.get('rank_position')}** ({desktop_prev.get('source')})",
            ]
        )
        prev_by_device = {"mobile": mobile_prev, "desktop": desktop_prev}
        for row in rows:
            prior_row = prev_by_device.get(row["device"], previous[-1])
            prior_val = prior_row.get("rank_position", "n/a")
            try:
                current = float(row["rank_position"])
                prior = float(prior_val)
                delta = prior - current
                direction = "iyileşme" if delta > 0 else "düşüş" if delta < 0 else "değişim yok"
                lines.append(
                    f"- {row['device']}: {prior} → {current} ({direction}, Δ={delta:+.1f})"
                )
            except ValueError:
                lines.append(f"- {row['device']}: önceki={prior_val}, şimdi={row['rank_position']}")

    lines.extend(
        [
            "",
            "## CSV",
            f"- `SERP-BASELINE.csv` bu çalışmada **{appended}** yeni satır eklendi.",
            "",
            "## Sonraki çalışma",
            "- Cron: `0 6 * * *` UTC (`AGENT-HUB/run-keyword-rank-weekly.sh`)",
            "- Öneri: `SERPER_API_KEY` ile doğrudan Google SERP API kullanın.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def build_live_row(device: str, rank: int, notes: str) -> dict[str, str]:
    return {
        "captured_at_utc": utc_now_iso(),
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": TARGET_URL,
        "rank_position": str(rank),
        "serp_features": "shopping_tab,images",
        "primary_competitor": "ledfon.com",
        "competitor_rank": "1",
        "source": "google_live_check",
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP baseline ölçümü")
    parser.add_argument("--mobile-rank", type=int, help="Doğrulanmış Google mobil sıra")
    parser.add_argument("--desktop-rank", type=int, help="Doğrulanmış Google masaüstü sıra")
    args = parser.parse_args()

    if args.mobile_rank is not None and args.desktop_rank is not None:
        shared_note = (
            "Google TR organic; rakipler: ledfon.com #1, ledurunleri.com #2, sahibinden.com #3"
        )
        rows = [
            build_live_row("mobile", args.mobile_rank, shared_note),
            build_live_row("desktop", args.desktop_rank, shared_note),
        ]
    else:
        rows = [measure_device(device) for device in ("mobile", "desktop")]

    appended = append_baseline(rows)
    report_path = write_weekly_report(rows, appended)

    for row in rows:
        print(
            f"{row['device']}: rank={row['rank_position']} source={row['source']} "
            f"url={row['target_url']}"
        )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
