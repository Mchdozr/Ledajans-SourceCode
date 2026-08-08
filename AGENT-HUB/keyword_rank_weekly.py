#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING raporu."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
TARGET_DOMAIN = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"

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

UA_MOBILE = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)
UA_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class RankResult:
    rank_position: str
    target_url: str
    source: str
    notes: str
    primary_competitor: str = ""
    competitor_rank: str = ""
    serp_features: str = ""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def weekly_report_path(captured_at: str) -> Path:
    date_str = captured_at[:10]
    return ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_str}.md"


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def find_target_rank(organic_urls: list[str], domain: str = TARGET_DOMAIN) -> tuple[str | None, str | None]:
    for index, url in enumerate(organic_urls, start=1):
        if domain in url.lower():
            return str(index), url
    return None, None


def first_competitor(organic_urls: list[str]) -> tuple[str, str]:
    for index, url in enumerate(organic_urls, start=1):
        if TARGET_DOMAIN not in url.lower():
            parsed = urllib.parse.urlparse(url)
            host = parsed.netloc or url
            return host, str(index)
    return "", ""


def fetch_serper(query: str, device: str, api_key: str) -> RankResult | None:
    payload = {"q": query, "gl": "tr", "hl": "tr", "num": 20}
    if device == "mobile":
        payload["device"] = "mobile"
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if response.status_code != 200:
        return None
    data = response.json()
    organic_urls = [item.get("link", "") for item in data.get("organic", []) if item.get("link")]
    rank, target_url = find_target_rank(organic_urls)
    competitor, competitor_rank = first_competitor(organic_urls)
    features = []
    if data.get("answerBox"):
        features.append("answer_box")
    if data.get("peopleAlsoAsk"):
        features.append("paa")
    if data.get("localResults"):
        features.append("local_pack")
    notes = "Serper Google organic snapshot"
    if not rank:
        notes += "; target domain not in top 20"
        rank = "20+"
        target_url = DEFAULT_TARGET_URL
    return RankResult(
        rank_position=rank,
        target_url=target_url or DEFAULT_TARGET_URL,
        source="serper_api",
        notes=notes,
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
        serp_features="|".join(features),
    )


def fetch_serpapi(query: str, device: str, api_key: str) -> RankResult | None:
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
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    if response.status_code != 200:
        return None
    data = response.json()
    organic_urls = [item.get("link", "") for item in data.get("organic_results", []) if item.get("link")]
    rank, target_url = find_target_rank(organic_urls)
    competitor, competitor_rank = first_competitor(organic_urls)
    notes = "SerpAPI Google organic snapshot"
    if not rank:
        notes += "; target domain not in top 20"
        rank = "20+"
        target_url = DEFAULT_TARGET_URL
    return RankResult(
        rank_position=rank,
        target_url=target_url or DEFAULT_TARGET_URL,
        source="serpapi",
        notes=notes,
        primary_competitor=competitor,
        competitor_rank=competitor_rank,
    )


def fetch_google_headless(query: str, user_agent: str) -> tuple[list[str], str]:
    params = urllib.parse.urlencode({"q": query, "hl": "tr", "gl": "tr", "num": "20", "pws": "0"})
    search_url = f"https://www.google.com/search?{params}"
    temp_html = Path("/tmp/ledajans_google_serp.html")
    command = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--virtual-time-budget=15000",
        f"--user-agent={user_agent}",
        "--dump-dom",
        search_url,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=50,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return [], f"headless chrome failed: {exc}"

    html = completed.stdout or ""
    if not html and temp_html.exists():
        html = temp_html.read_text(encoding="utf-8", errors="ignore")

    if re.search(r"captcha|unusual traffic|recaptcha|sorry", html, re.I):
        return [], "google CAPTCHA / blocked"

    links: list[str] = []
    for match in re.finditer(r"/url\?q=(https?://[^&\"]+)", html):
        url = urllib.parse.unquote(match.group(1))
        if "google." not in url:
            links.append(url)

    seen: set[str] = set()
    organic: list[str] = []
    for url in links:
        if url not in seen:
            seen.add(url)
            organic.append(url)
    note = "Google headless organic parse"
    if not organic:
        note = "google headless returned no organic links"
    return organic, note


def fetch_ddg_html(query: str) -> tuple[list[str], str]:
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query, "kl": "tr-tr"},
        headers={"User-Agent": UA_DESKTOP},
        timeout=30,
    )
    if response.status_code != 200:
        return [], f"ddg http {response.status_code}"

    soup = BeautifulSoup(response.text, "html.parser")
    organic = [anchor.get("href", "") for anchor in soup.select("a.result__a") if anchor.get("href")]
    return organic, "DDG HTML proxy (Google değil — CAPTCHA fallback referansı)"


def measure_device(
    device: str,
    *,
    manual_rank: str | None,
    manual_target_url: str | None,
    manual_notes: str | None,
) -> RankResult:
    if manual_rank:
        return RankResult(
            rank_position=manual_rank,
            target_url=manual_target_url or DEFAULT_TARGET_URL,
            source="manual_override",
            notes=manual_notes or "CLI override",
        )

    serper_key = os.getenv("SERPER_API_KEY", "").strip()
    if serper_key:
        result = fetch_serper(QUERY, device, serper_key)
        if result:
            return result

    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
    if serpapi_key:
        result = fetch_serpapi(QUERY, device, serpapi_key)
        if result:
            return result

    user_agent = UA_MOBILE if device == "mobile" else UA_DESKTOP
    organic, google_note = fetch_google_headless(QUERY, user_agent)
    if organic:
        rank, target_url = find_target_rank(organic)
        competitor, competitor_rank = first_competitor(organic)
        if rank:
            return RankResult(
                rank_position=rank,
                target_url=target_url or DEFAULT_TARGET_URL,
                source="google_headless",
                notes=google_note,
                primary_competitor=competitor,
                competitor_rank=competitor_rank,
            )

    organic, ddg_note = fetch_ddg_html(QUERY)
    rank, target_url = find_target_rank(organic)
    competitor, competitor_rank = first_competitor(organic)
    if rank:
        return RankResult(
            rank_position=rank,
            target_url=target_url or DEFAULT_TARGET_URL,
            source="ddg_html_proxy",
            notes=f"{google_note}; {ddg_note}",
            primary_competitor=competitor,
            competitor_rank=competitor_rank,
        )

    return RankResult(
        rank_position="blocked",
        target_url=DEFAULT_TARGET_URL,
        source="google_live_check",
        notes=f"{google_note}; {ddg_note}; ölçüm başarısız",
    )


def row_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row["captured_at_utc"][:10],
        row["query"].lower(),
        row["device"],
        row["source"],
    )


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    existing = read_baseline_rows()
    existing_keys = {row_key(row) for row in existing}
    to_append = [row for row in rows if row_key(row) not in existing_keys]

    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for row in to_append:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return len(to_append)


def latest_gsc_led_ekran() -> dict[str, str] | None:
    for row in read_baseline_rows():
        if row.get("query", "").lower() == QUERY and row.get("source", "").startswith("gsc_performance"):
            return row
    return None


def build_weekly_markdown(
    captured_at: str,
    mobile: RankResult,
    desktop: RankResult,
    appended: int,
) -> str:
    gsc = latest_gsc_led_ekran()
    gsc_line = "GSC avg_position kaydı yok."
    if gsc:
        gsc_line = (
            f"Son GSC export ({gsc.get('captured_at_utc', '')[:10]}): "
            f"avg_position={gsc.get('rank_position', 'N/A')} — {gsc.get('notes', '')}"
        )

    lines = [
        f"# Haftalık SEO İzleme — {captured_at[:10]}",
        "",
        "## SERP — `led ekran` (tr-TR, Google hedef)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Not |",
        "|---|---:|---|---|---|",
        f"| mobile | {mobile.rank_position} | {mobile.target_url} | {mobile.source} | {mobile.notes} |",
        f"| desktop | {desktop.rank_position} | {desktop.target_url} | {desktop.source} | {desktop.notes} |",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- `SERP-BASELINE.csv` yeni satır: **{appended}**",
        f"- Referans (GSC): {gsc_line}",
        "",
        "## Yorum",
        "",
    ]

    if mobile.source == "ddg_html_proxy" or desktop.source == "ddg_html_proxy":
        lines.append(
            "- Cloud IP Google CAPTCHA nedeniyle canlı Google organic parse bloklandı; "
            "DDG HTML proxy referans sırası raporlandı. Kesin Google sırası için `SERPER_API_KEY` "
            "veya GSC Performance export önerilir."
        )
    elif mobile.source.startswith("gsc") or desktop.source.startswith("gsc"):
        lines.append("- Sıra GSC ortalama pozisyonundan alındı (canlı SERP değil).")
    else:
        lines.append("- Canlı organic ölçüm tamamlandı.")

    lines.extend(
        [
            "",
            "## Tekrar çalıştırma",
            "",
            "```bash",
            "cd /workspace && python3 AGENT-HUB/keyword_rank_weekly.py",
            "```",
            "",
            "Manuel doğrulama:",
            "",
            "```bash",
            "python3 AGENT-HUB/keyword_rank_weekly.py --mobile-rank 3 --desktop-rank 3",
            "```",
            "",
            "## Sonraki hafta",
            "",
            "- Cron (UTC): `0 6 * * 1` veya automation `0 6 * * *`",
            "- Komut: `bash AGENT-HUB/run-keyword-rank-weekly.sh`",
        ]
    )
    return "\n".join(lines) + "\n"


def result_to_row(captured_at: str, device: str, result: RankResult) -> dict[str, str]:
    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": result.target_url,
        "rank_position": result.rank_position,
        "serp_features": result.serp_features,
        "primary_competitor": result.primary_competitor,
        "competitor_rank": result.competitor_rank,
        "source": result.source,
        "notes": result.notes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Haftalık led ekran SERP ölçümü")
    parser.add_argument("--mobile-rank", help="Manuel mobil sıra (ör. 3 veya top5)")
    parser.add_argument("--desktop-rank", help="Manuel desktop sıra")
    parser.add_argument("--target-url", default=DEFAULT_TARGET_URL, help="Hedef URL")
    parser.add_argument("--notes", default="", help="Manuel not")
    parser.add_argument("--dry-run", action="store_true", help="CSV/MD yazmadan sonucu yazdır")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    captured_at = utc_now_iso()

    mobile = measure_device(
        "mobile",
        manual_rank=args.mobile_rank,
        manual_target_url=args.target_url,
        manual_notes=args.notes or None,
    )
    desktop = measure_device(
        "desktop",
        manual_rank=args.desktop_rank,
        manual_target_url=args.target_url,
        manual_notes=args.notes or None,
    )

    payload = {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "mobile": mobile.__dict__,
        "desktop": desktop.__dict__,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0

    rows = [
        result_to_row(captured_at, "mobile", mobile),
        result_to_row(captured_at, "desktop", desktop),
    ]
    appended = append_baseline_rows(rows)
    report_path = weekly_report_path(captured_at)
    report_path.write_text(
        build_weekly_markdown(captured_at, mobile, desktop, appended),
        encoding="utf-8",
    )
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
