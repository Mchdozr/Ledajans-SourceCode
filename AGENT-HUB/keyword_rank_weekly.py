#!/usr/bin/env python3
"""Haftalık 'led ekran' Google SERP ölçümü → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import argparse
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
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
TARGET_URL = "https://ledajans.com/"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"

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


@dataclass
class SerpResult:
    rank: int | str | None
    target_url: str
    competitors: list[tuple[int, str]]
    source: str
    notes: str
    blocked: bool = False


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def weekly_monitoring_path(run_date: date | None = None) -> Path:
    d = run_date or datetime.now(UTC).date()
    return ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{d.isoformat()}.md"


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    if not BASELINE_PATH.exists():
        return BASELINE_FIELDS, []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or BASELINE_FIELDS)
        return fields, list(reader)


def row_exists(rows: list[dict[str, str]], captured_at: str, device: str, source: str) -> bool:
    day = captured_at[:10]
    for row in rows:
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("device", "") == device
            and row.get("source", "") == source
            and row.get("captured_at_utc", "").startswith(day)
        ):
            return True
    return False


def append_baseline_row(fields: list[str], row: dict[str, str]) -> None:
    exists = False
    if BASELINE_PATH.exists():
        with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
            exists = bool(f.read().strip())
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fields})


def parse_organic_domains(results: list[dict]) -> list[tuple[int, str, str]]:
    ranked: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for item in results:
        link = item.get("link") or item.get("url") or ""
        if not link:
            continue
        match = re.match(r"https?://(?:www\.)?([^/]+)", link)
        if not match:
            continue
        domain = match.group(1).lower()
        if domain in seen or "google." in domain:
            continue
        seen.add(domain)
        ranked.append((len(ranked) + 1, domain, link))
    return ranked


def find_ledajans(ranked: list[tuple[int, str, str]]) -> tuple[int | None, str]:
    for pos, domain, link in ranked:
        if "ledajans" in domain:
            return pos, link
    return None, TARGET_URL


def fetch_serper(device: str) -> SerpResult | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None

    payload = json.dumps(
        {
            "q": QUERY,
            "gl": "tr",
            "hl": "tr",
            "num": 30,
            "device": device,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        return SerpResult(
            rank=None,
            target_url=TARGET_URL,
            competitors=[],
            source="serper_api",
            notes=f"Serper hata: {exc}",
            blocked=True,
        )

    organic = data.get("organic") or []
    ranked = parse_organic_domains(organic)
    rank, url = find_ledajans(ranked)
    competitors = [(pos, dom) for pos, dom, _ in ranked[:5] if "ledajans" not in dom]
    primary, primary_rank = ("", "")
    if competitors:
        primary, primary_rank = competitors[0][1], str(competitors[0][0])
    top = ", ".join(f"{d}({p})" for p, d, _ in ranked[:5])
    return SerpResult(
        rank=rank if rank is not None else "not_in_top_30",
        target_url=url,
        competitors=competitors,
        source="serper_api",
        notes=f"Serper organic top5: {top}",
        blocked=rank is None,
    )


def fetch_serpapi(device: str) -> SerpResult | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None

    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": QUERY,
            "hl": "tr",
            "gl": "tr",
            "num": 30,
            "device": device,
            "api_key": api_key,
        }
    )
    url = f"https://serpapi.com/search.json?{params}"
    try:
        with urllib.request.urlopen(url, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        return SerpResult(
            rank=None,
            target_url=TARGET_URL,
            competitors=[],
            source="serpapi",
            notes=f"SerpAPI hata: {exc}",
            blocked=True,
        )

    organic = data.get("organic_results") or []
    ranked = parse_organic_domains(organic)
    rank, target = find_ledajans(ranked)
    competitors = [(pos, dom) for pos, dom, _ in ranked[:5] if "ledajans" not in dom]
    top = ", ".join(f"{d}({p})" for p, d, _ in ranked[:5])
    return SerpResult(
        rank=rank if rank is not None else "not_in_top_30",
        target_url=target,
        competitors=competitors,
        source="serpapi",
        notes=f"SerpAPI organic top5: {top}",
        blocked=rank is None,
    )


def fetch_uc_chrome(device: str) -> SerpResult:
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
    except ImportError:
        return SerpResult(
            rank=None,
            target_url=TARGET_URL,
            competitors=[],
            source="google_live_check",
            notes="undetected-chromedriver yüklü değil (pip install undetected-chromedriver)",
            blocked=True,
        )

    ranked: list[tuple[int, str, str]] = []
    blocked = True
    last_error = ""

    for attempt in range(1, 4):
        driver = None
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--lang=tr-TR")
        if device == "mobile":
            options.add_argument("--window-size=412,915")
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            )
        else:
            options.add_argument("--window-size=1366,900")
        try:
            driver = uc.Chrome(options=options, version_main=147)
            driver.get(
                f"https://www.google.com/search?q={urllib.parse.quote(QUERY)}&hl=tr&gl=tr&num=30"
            )
            time.sleep(7)
            if "sorry" in (driver.current_url or ""):
                last_error = "Google CAPTCHA/sorry"
                continue
            links = driver.find_elements(By.CSS_SELECTOR, "a h3")
            seen: set[str] = set()
            for h3 in links:
                anchor = h3.find_element(By.XPATH, "..")
                href = anchor.get_attribute("href") or ""
                match = re.match(r"https?://(?:www\.)?([^/]+)", href)
                if not match:
                    continue
                domain = match.group(1).lower()
                if domain in seen or "google." in domain:
                    continue
                seen.add(domain)
                ranked.append((len(ranked) + 1, domain, href))
            if ranked:
                blocked = False
                break
            last_error = "Sonuç parse edilemedi"
        except Exception as exc:  # noqa: BLE001 — dış tarayıcı hataları
            last_error = str(exc)
        finally:
            if driver is not None:
                driver.quit()
        time.sleep(4)

    if blocked:
        return SerpResult(
            rank="blocked",
            target_url=TARGET_URL,
            competitors=[],
            source="google_live_check",
            notes=f"Google canlı ölçüm başarısız: {last_error}. SERPER_API_KEY önerilir.",
            blocked=True,
        )

    rank, target = find_ledajans(ranked)
    competitors = [(pos, dom) for pos, dom, _ in ranked[:5] if "ledajans" not in dom]
    top = ", ".join(f"{d}({p})" for p, d, _ in ranked[:5])
    return SerpResult(
        rank=rank if rank is not None else "not_in_top_30",
        target_url=target,
        competitors=competitors,
        source="google_live_check",
        notes=f"Organic top5: {top}",
        blocked=False,
    )


def resolve_rank(device: str, manual_rank: int | None) -> SerpResult:
    if manual_rank is not None:
        return SerpResult(
            rank=manual_rank,
            target_url=TARGET_URL,
            competitors=[],
            source="manual_override",
            notes=f"CLI {'--mobile-rank' if device == 'mobile' else '--desktop-rank'} ile sağlandı",
        )

    for provider in (fetch_serper, fetch_serpapi):
        result = provider(device)
        if result is not None:
            if not result.blocked:
                return result

    live = fetch_uc_chrome(device)
    if not live.blocked:
        return live
    ddg = fetch_ddg_proxy(device)
    if ddg is not None:
        return ddg
    return live


def fetch_ddg_proxy(device: str) -> SerpResult | None:
    user_agent = (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        if device == "mobile"
        else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
    try:
        response = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": QUERY, "kl": "tr-tr"},
            headers={"User-Agent": user_agent},
            timeout=25,
        )
    except requests.RequestException as exc:
        return SerpResult(
            rank=None,
            target_url=TARGET_URL,
            competitors=[],
            source="ddg_html_proxy",
            notes=f"DuckDuckGo proxy hata: {exc}",
            blocked=True,
        )
    if response.status_code != 200:
        return None

    ranked: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', response.text):
        href = match.group(1)
        if "uddg=" in href:
            url = unquote(re.search(r"uddg=([^&\"]+)", href).group(1))
        else:
            url = href
        host = urlparse(url).netloc.lower()
        if "duckduckgo" in host or host in seen:
            continue
        seen.add(host)
        ranked.append((len(ranked) + 1, host, url))

    rank, target = find_ledajans(ranked)
    competitors = [(pos, dom) for pos, dom, _ in ranked[:5] if "ledajans" not in dom]
    top = ", ".join(f"{d}({p})" for p, d, _ in ranked[:5])
    return SerpResult(
        rank=rank if rank is not None else "not_in_top_10",
        target_url=target,
        competitors=competitors,
        source="ddg_html_proxy",
        notes=(
            f"DDG HTML proxy (Google değil); top5: {top}. "
            "Google CAPTCHA — SERPER_API_KEY ile doğrulayın."
        ),
        blocked=rank is None,
    )


def latest_gsc_position(rows: list[dict[str, str]]) -> str | None:
    for row in reversed(rows):
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("source", "").startswith("gsc_performance")
        ):
            return row.get("rank_position") or None
    return None


def build_baseline_row(captured_at: str, device: str, result: SerpResult) -> dict[str, str]:
    primary = ""
    primary_rank = ""
    if result.competitors:
        primary, primary_rank = result.competitors[0][1], str(result.competitors[0][0])
    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": result.target_url,
        "rank_position": str(result.rank) if result.rank is not None else "",
        "serp_features": "",
        "primary_competitor": primary,
        "competitor_rank": primary_rank,
        "source": result.source,
        "notes": result.notes,
    }


def previous_live_rank(rows: list[dict[str, str]], device: str) -> dict[str, str] | None:
    for row in reversed(rows):
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("device", "") == device
            and row.get("source", "") in {"google_live_check", "serper_api", "serpapi"}
            and row.get("rank_position", "") not in {"", "blocked", "unavailable"}
        ):
            return row
    return None


def write_weekly_summary(
    path: Path,
    captured_at: str,
    mobile: SerpResult,
    desktop: SerpResult,
    gsc_position: str | None,
    appended: int,
    existing: list[dict[str, str]],
) -> None:
    prev_mobile = previous_live_rank(existing, "mobile")
    prev_desktop = previous_live_rank(existing, "desktop")
    lines = [
        f"# Haftalık SEO İzleme — {path.stem.replace('WEEKLY-MONITORING-', '')}",
        "",
        "## SERP — `led ekran` (Google, tr-TR)",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        f"- Hedef URL: `{TARGET_URL}`",
        "",
        "| Cihaz | Sıra | Kaynak | Not |",
        "|-------|------|--------|-----|",
        f"| Mobil | **{mobile.rank}** | {mobile.source} | {mobile.notes} |",
        f"| Masaüstü | **{desktop.rank}** | {desktop.source} | {desktop.notes} |",
        "",
    ]
    if prev_mobile or prev_desktop:
        lines.extend(["## Önceki hafta karşılaştırma", ""])
        if prev_desktop:
            lines.append(
                f"- Masaüstü (önceki): **#{prev_desktop.get('rank_position')}** "
                f"({prev_desktop.get('captured_at_utc', '')[:10]})"
            )
        if prev_mobile:
            lines.append(
                f"- Mobil (önceki): **{prev_mobile.get('rank_position')}** "
                f"({prev_mobile.get('captured_at_utc', '')[:10]})"
            )
        lines.append("")
    if gsc_position:
        lines.extend(
            [
                "## GSC referans (ortalama pozisyon)",
                "",
                f"- Son kayıtlı GSC avg position: **{gsc_position}** (export 2026-06-05)",
                "- GSC avg ile canlı organic sıra farklı metriklerdir.",
                "",
            ]
        )

    lines.extend(
        [
            "## CSV",
            "",
            f"- `AGENT-HUB/SERP-BASELINE.csv` — bu çalışmada **{appended}** yeni satır",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            "Cron: `0 6 * * *` (günlük 06:00 UTC). CAPTCHA için `SERPER_API_KEY` ekleyin.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Haftalık led ekran SERP ölçümü")
    parser.add_argument("--mobile-rank", type=int, default=None, help="Doğrulanmış mobil sıra")
    parser.add_argument("--desktop-rank", type=int, default=None, help="Doğrulanmış masaüstü sıra")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (varsayılan: bugün UTC)")
    args = parser.parse_args()

    run_date = date.fromisoformat(args.date) if args.date else datetime.now(UTC).date()
    captured_at = utc_now_iso()
    fields, existing = read_baseline_rows()

    mobile = resolve_rank("mobile", args.mobile_rank)
    desktop = resolve_rank("desktop", args.desktop_rank)

    appended = 0
    for device, result in (("mobile", mobile), ("desktop", desktop)):
        if row_exists(existing, captured_at, device, result.source):
            continue
        row = build_baseline_row(captured_at, device, result)
        append_baseline_row(fields, row)
        existing.append(row)
        appended += 1

    gsc_position = latest_gsc_position(existing)
    summary_path = weekly_monitoring_path(run_date)
    write_weekly_summary(
        summary_path, captured_at, mobile, desktop, gsc_position, appended, existing
    )

    print(f"captured_at={captured_at}")
    print(f"mobile_rank={mobile.rank} source={mobile.source}")
    print(f"desktop_rank={desktop.rank} source={desktop.source}")
    print(f"baseline_appended={appended}")
    print(f"weekly_summary={summary_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
