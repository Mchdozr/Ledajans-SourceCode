#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP konumu: SERP-BASELINE.csv + WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "AGENT-HUB"
BASELINE_PATH = HUB / "SERP-BASELINE.csv"
DATA_DIR = HUB / "DATA"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
PRIMARY_URL = "https://ledajans.com/"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
)
GSC_MAX_AGE_DAYS = 7


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_gsc_queries_dir() -> Path | None:
    candidates = sorted(DATA_DIR.glob("gsc-performance-*"), reverse=True)
    for folder in candidates:
        if (folder / "Sorgular.csv").is_file():
            return folder
    return None


def gsc_is_fresh(folder: Path) -> bool:
    export_date = folder.name.replace("gsc-performance-", "")
    try:
        captured = datetime.strptime(export_date, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return False
    return datetime.now(UTC) - captured <= timedelta(days=GSC_MAX_AGE_DAYS)


def gsc_snapshot(device: str) -> dict[str, str] | None:
    folder = latest_gsc_queries_dir()
    if not folder or not gsc_is_fresh(folder):
        return None
    rows = read_csv(folder / "Sorgular.csv")
    match = next(
        (row for row in rows if row.get("En çok yapılan sorgular", "").strip().lower() == QUERY),
        None,
    )
    if not match:
        return None
    position = match.get("Pozisyon", "").strip()
    clicks = match.get("Tıklamalar", "").strip()
    impressions = match.get("Gösterimler", "").strip()
    ctr = match.get("TO", "").strip()
    export_date = folder.name.replace("gsc-performance-", "")
    return {
        "rank_position": position,
        "target_url": PRIMARY_URL,
        "source": f"gsc_performance_{export_date}",
        "notes": (
            f"GSC ortalama pozisyon (export {export_date}); device={device}; "
            f"Clicks={clicks}; Impressions={impressions}; CTR={ctr}"
        ),
    }


def serper_rank(device: str) -> dict[str, str] | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {"q": QUERY, "gl": "tr", "hl": "tr", "num": 50}
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
    organic = response.json().get("organic") or []
    for index, item in enumerate(organic, start=1):
        link = (item.get("link") or "").strip()
        if TARGET_DOMAIN in link.lower():
            return {
                "rank_position": str(index),
                "target_url": link,
                "source": "serper_api",
                "notes": f"Google organic via Serper; device={device}; title={item.get('title', '')[:80]}",
            }
    return {
        "rank_position": "not_found_top50",
        "target_url": PRIMARY_URL,
        "source": "serper_api",
        "notes": f"Google organic via Serper; {TARGET_DOMAIN} ilk 50 sonuçta yok; device={device}",
    }


def serpapi_rank(device: str) -> dict[str, str] | None:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return None
    params = {
        "engine": "google",
        "q": QUERY,
        "hl": "tr",
        "gl": "tr",
        "num": 50,
        "api_key": api_key,
    }
    if device == "mobile":
        params["device"] = "mobile"
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    if response.status_code != 200:
        return None
    organic = response.json().get("organic_results") or []
    for index, item in enumerate(organic, start=1):
        link = (item.get("link") or "").strip()
        if TARGET_DOMAIN in link.lower():
            return {
                "rank_position": str(index),
                "target_url": link,
                "source": "serpapi",
                "notes": f"Google organic via SerpAPI; device={device}; title={item.get('title', '')[:80]}",
            }
    return {
        "rank_position": "not_found_top50",
        "target_url": PRIMARY_URL,
        "source": "serpapi",
        "notes": f"Google organic via SerpAPI; {TARGET_DOMAIN} ilk 50 sonuçta yok; device={device}",
    }


def ddg_proxy_rank(device: str) -> dict[str, str] | None:
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": QUERY, "kl": "tr-tr"},
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    if response.status_code != 200:
        return None
    links: list[str] = []
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', response.text):
        href = match.group(1)
        if "uddg=" in href:
            url = unquote(re.search(r"uddg=([^&\"]+)", href).group(1))
        else:
            url = href
        host = urlparse(url).netloc.lower()
        if "duckduckgo" in host:
            continue
        links.append(url)
    for index, url in enumerate(links, start=1):
        if TARGET_DOMAIN in url.lower():
            return {
                "rank_position": str(index),
                "target_url": url,
                "source": "ddg_html_proxy",
                "notes": (
                    f"DuckDuckGo HTML proxy (Google ile birebir değil); device={device}; "
                    "bulut IP Google SERP captcha veriyor — SERPER_API_KEY önerilir"
                ),
            }
    return {
        "rank_position": "not_found_top10",
        "target_url": PRIMARY_URL,
        "source": "ddg_html_proxy",
        "notes": f"DuckDuckGo proxy; {TARGET_DOMAIN} ilk 10 sonuçta yok; device={device}",
    }


def resolve_rank(device: str) -> dict[str, str]:
    for resolver in (serper_rank, serpapi_rank, gsc_snapshot, ddg_proxy_rank):
        result = resolver(device)
        if result:
            return result
    return {
        "rank_position": "unavailable",
        "target_url": PRIMARY_URL,
        "source": "unavailable",
        "notes": "SERP ölçümü başarısız; SERPER_API_KEY veya güncel GSC export gerekli",
    }


def append_baseline_rows(rows: list[dict[str, str]]) -> int:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        existing = list(reader)

    keys = {(r["captured_at_utc"], r["query"].lower(), r["device"], r["source"]) for r in existing}
    to_append = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in keys
    ]
    if not to_append:
        return 0

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        for row in to_append:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return len(to_append)


def latest_baseline_row(device: str, *, before_captured_at: str | None = None) -> dict[str, str] | None:
    rows = read_csv(BASELINE_PATH)
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == QUERY
        and row.get("device", "").strip().lower() == device
        and row.get("target_url", "").strip().rstrip("/") == PRIMARY_URL.rstrip("/")
        and (before_captured_at is None or row.get("captured_at_utc", "") < before_captured_at)
    ]
    return matches[-1] if matches else None


def parse_rank_value(value: str) -> float | None:
    cleaned = (value or "").strip().lower()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        match = re.match(r"top(\d+)", cleaned)
        if match:
            return float(match.group(1))
    return None


def rank_delta(current: str, previous: dict[str, str] | None) -> str:
    if not previous:
        return "ilk kayıt"
    prev_value = parse_rank_value(previous.get("rank_position", ""))
    curr_value = parse_rank_value(current)
    if prev_value is None or curr_value is None:
        return "karşılaştırılamadı"
    diff = curr_value - prev_value
    if diff < 0:
        return f"↑ {abs(diff):.0f} sıra iyileşme"
    if diff > 0:
        return f"↓ {diff:.0f} sıra düşüş"
    return "değişmedi"


def load_audit_summary() -> tuple[int, int]:
    audits = sorted(HUB.glob("audit-money-pages-*.json"), reverse=True)
    if not audits:
        return 0, 0
    data = json.loads(audits[0].read_text(encoding="utf-8"))
    pages = data if isinstance(data, list) else data.get("pages") or []
    ok = sum(1 for page in pages if page.get("canonical_ok"))
    return len(pages), ok


def update_weekly_monitoring(captured_at: str, mobile: dict[str, str], desktop: dict[str, str]) -> Path:
    today = datetime.now(UTC).date()
    path = HUB / f"WEEKLY-MONITORING-{today.isoformat()}.md"
    pages_total, pages_ok = load_audit_summary()
    gsc_folder = latest_gsc_queries_dir()
    gsc_label = gsc_folder.name.replace("gsc-performance-", "") if gsc_folder else "yok"
    gsc_fresh = gsc_is_fresh(gsc_folder) if gsc_folder else False
    prev_mobile = latest_baseline_row("mobile", before_captured_at=captured_at)
    prev_desktop = latest_baseline_row("desktop", before_captured_at=captured_at)

    lines = [
        f"# Haftalık SEO İzleme — {today.isoformat()}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        f"- Mobil: sıra **{mobile['rank_position']}** | URL `{mobile['target_url']}` | kaynak `{mobile['source']}`",
        f"- Masaüstü: sıra **{desktop['rank_position']}** | URL `{desktop['target_url']}` | kaynak `{desktop['source']}`",
        f"- Mobil haftalık delta: {rank_delta(mobile['rank_position'], prev_mobile)}",
        f"- Masaüstü haftalık delta: {rank_delta(desktop['rank_position'], prev_desktop)}",
        f"- Satır eklendi: `AGENT-HUB/SERP-BASELINE.csv`",
        "",
        "### Notlar",
        f"- Mobil: {mobile['notes']}",
        f"- Masaüstü: {desktop['notes']}",
        "- Kesin Google SERP için ortam değişkeni: `SERPER_API_KEY` veya `SERPAPI_KEY`",
        "",
        "## Para sayfa (audit-money-pages.py)",
        f"- Son audit: **{pages_ok}/{pages_total}** canonical OK",
        "",
        "## GSC export",
        f"- Son klasör: `AGENT-HUB/DATA/gsc-performance-{gsc_label}/`",
        f"- GSC tazelik: {'güncel (≤7 gün)' if gsc_fresh else 'eski — yeni export gerekli'}",
        "- Yeni export geldiğinde `scripts/update-serp-baseline-from-gsc.py` ile toplu güncelle",
        "",
        "## Komutlar",
        "```bash",
        "cd /workspace",
        "python3 AGENT-HUB/keyword_rank_weekly.py",
        "python3 AGENT-HUB/audit-money-pages.py",
        "python3 deploy-to-wordpress.py --dry-run",
        "```",
        "",
        "## Sonraki hafta",
        "- `python3 AGENT-HUB/keyword_rank_weekly.py` (cron: `0 6 * * *` günlük 06:00 UTC)",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_row(captured_at: str, device: str, result: dict[str, str]) -> dict[str, str]:
    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": result["target_url"],
        "rank_position": result["rank_position"],
        "serp_features": "",
        "primary_competitor": "videowall.com.tr",
        "competitor_rank": "",
        "source": result["source"],
        "notes": result["notes"],
    }


def main() -> int:
    captured_at = utc_now_iso()
    prev_mobile = latest_baseline_row("mobile")
    prev_desktop = latest_baseline_row("desktop")
    mobile = resolve_rank("mobile")
    desktop = resolve_rank("desktop")
    rows = [
        build_row(captured_at, "mobile", mobile),
        build_row(captured_at, "desktop", desktop),
    ]
    appended = append_baseline_rows(rows)
    weekly_path = update_weekly_monitoring(captured_at, mobile, desktop)

    print(f"captured_at={captured_at}")
    print(f"mobile_rank={mobile['rank_position']} source={mobile['source']}")
    print(f"desktop_rank={desktop['rank_position']} source={desktop['source']}")
    if prev_mobile:
        print(f"mobile_delta={rank_delta(mobile['rank_position'], prev_mobile)}")
    if prev_desktop:
        print(f"desktop_delta={rank_delta(desktop['rank_position'], prev_desktop)}")
    print(f"baseline_appended={appended}")
    print(f"weekly_report={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
