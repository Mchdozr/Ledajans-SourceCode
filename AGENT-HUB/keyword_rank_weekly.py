#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP ölçümü — SERP-BASELINE.csv + WEEKLY-MONITORING günceller."""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
TARGET_DOMAIN = "ledajans.com"
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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def domain_from(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def latest_gsc_position() -> tuple[str | None, str]:
    if not BASELINE_PATH.exists():
        return None, ""
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in reversed(rows):
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("source", "").startswith("gsc_performance")
        ):
            return row.get("rank_position"), row.get("source", "")
    return None, ""


def fetch_serper(query: str, device: str) -> dict | None:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None
    payload = json.dumps({"q": query, "gl": "tr", "hl": "tr", "num": 20}).encode()
    req = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    organic = []
    for item in data.get("organic", []):
        link = item.get("link", "")
        dom = domain_from(link)
        if dom:
            organic.append({"rank": len(organic) + 1, "domain": dom, "url": link})
    rank = next((o["rank"] for o in organic if TARGET_DOMAIN in o["domain"]), None)
    target_url = next((o["url"] for o in organic if TARGET_DOMAIN in o["domain"]), None)
    top = next((o for o in organic if TARGET_DOMAIN not in o["domain"]), None)
    return {
        "status": "ok",
        "rank": rank,
        "target_url": target_url or f"https://{TARGET_DOMAIN}/",
        "source": "serper_api",
        "top_competitor": top["domain"] if top else "",
        "top_competitor_rank": str(top["rank"]) if top else "",
        "top5": organic[:5],
        "notes": f"serper.dev {device}; top5={','.join(o['domain'] for o in organic[:5])}",
    }


def fetch_playwright_google(query: str, device: str) -> dict:
    from playwright.sync_api import sync_playwright

    is_mobile = device == "mobile"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            locale="tr-TR",
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                if is_mobile
                else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ),
            viewport={"width": 390, "height": 844} if is_mobile else {"width": 1366, "height": 900},
            is_mobile=is_mobile,
            has_touch=is_mobile,
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9"},
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        try:
            if device == "desktop":
                page.goto("https://www.google.com/?hl=tr&gl=tr", wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1500)
                for sel in ["button:has-text('Tümünü kabul et')", "button:has-text('Accept all')", "#L2AGLb"]:
                    try:
                        page.locator(sel).first.click(timeout=2000)
                        break
                    except Exception:
                        pass
                page.fill("textarea[name='q'], input[name='q']", query)
                page.keyboard.press("Enter")
            else:
                page.goto(
                    f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=tr&gl=tr",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
            page.wait_for_timeout(4000)
            if "sorry" in page.url:
                return {"status": "captcha", "source": "playwright_google"}
            links = page.eval_on_selector_all("div#search a[href^='http']", "els => els.map(e => e.href)")
            organic: list[dict] = []
            seen: set[str] = set()
            for href in links:
                if "google." in href or "youtube.com/results" in href:
                    continue
                dom = domain_from(href)
                if dom and dom not in seen:
                    seen.add(dom)
                    organic.append({"rank": len(organic) + 1, "domain": dom, "url": href})
            rank = next((o["rank"] for o in organic if TARGET_DOMAIN in o["domain"]), None)
            target_url = next((o["url"] for o in organic if TARGET_DOMAIN in o["domain"]), None)
            top = next((o for o in organic if TARGET_DOMAIN not in o["domain"]), None)
            return {
                "status": "ok",
                "rank": rank,
                "target_url": target_url or f"https://{TARGET_DOMAIN}/",
                "source": "playwright_google",
                "top_competitor": top["domain"] if top else "",
                "top_competitor_rank": str(top["rank"]) if top else "",
                "top5": organic[:5],
                "notes": f"organic top5={','.join(o['domain'] for o in organic[:5])}",
            }
        finally:
            browser.close()


def measure_device(device: str, captured_at: str) -> dict[str, str]:
    result = fetch_serper(QUERY, device)
    if not result or result.get("status") != "ok" or result.get("rank") is None:
        pw = fetch_playwright_google(QUERY, device)
        if pw.get("status") == "ok" and pw.get("rank") is not None:
            result = pw
        elif not result:
            result = pw

    gsc_pos, gsc_source = latest_gsc_position()
    rank = result.get("rank") if result else None
    source = (result or {}).get("source", "unavailable")
    notes = (result or {}).get("notes", "")

    if rank is None and gsc_pos:
        rank = gsc_pos
        source = f"gsc_fallback:{gsc_source or 'baseline'}"
        notes = f"Canlı SERP captcha/boş; GSC avg_position={gsc_pos} referans"

    if rank is None:
        rank = "N/A"
        notes = notes or "Ölçüm başarısız"

    prev_rows = []
    if BASELINE_PATH.exists():
        with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
            prev_rows = [
                r
                for r in csv.DictReader(f)
                if r.get("query", "").strip().lower() == QUERY and r.get("device") == device
            ]
    prev_rank = prev_rows[-1].get("rank_position") if prev_rows else None
    delta = ""
    if prev_rank and str(rank) not in ("N/A", "top3", "top5", "top10", "top20", "pending"):
        try:
            delta = f"; delta_vs_prev={float(rank) - float(prev_rank):+.2f}"
        except ValueError:
            pass

    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": (result or {}).get("target_url") or f"https://{TARGET_DOMAIN}/",
        "rank_position": str(rank),
        "serp_features": "",
        "primary_competitor": (result or {}).get("top_competitor", ""),
        "competitor_rank": (result or {}).get("top_competitor_rank", ""),
        "source": source,
        "notes": (notes + delta).strip("; "),
    }


def append_baseline(rows: list[dict[str, str]]) -> int:
    existing: list[dict[str, str]] = []
    if BASELINE_PATH.exists():
        with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    keys = {(r["captured_at_utc"], r["query"], r["device"], r["source"]) for r in existing}
    to_add = [r for r in rows if (r["captured_at_utc"], r["query"], r["device"], r["source"]) not in keys]
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BASELINE_FIELDS)
        for row in to_add:
            writer.writerow({k: row.get(k, "") for k in BASELINE_FIELDS})
    return len(to_add)


def write_weekly_summary(captured_at: str, rows: list[dict[str, str]]) -> Path:
    date_str = captured_at[:10]
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_str}.md"
    desktop = next((r for r in rows if r["device"] == "desktop"), None)
    mobile = next((r for r in rows if r["device"] == "mobile"), None)

    lines = [
        f"# Haftalık SEO İzleme — {date_str}",
        "",
        "## SERP — led ekran (tr-TR, Google)",
        "",
        "| Cihaz | Sıra | Hedef URL | Kaynak | Not |",
        "|-------|-----:|-----------|--------|-----|",
    ]
    for r in (desktop, mobile):
        if r:
            lines.append(
                f"| {r['device']} | **{r['rank_position']}** | {r['target_url']} | {r['source']} | {r['notes']} |"
            )

    lines.extend(
        [
            "",
            "## Trend (son ölçümler)",
            "",
        ]
    )
    history: list[dict[str, str]] = []
    if BASELINE_PATH.exists():
        with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
            history = [
                r
                for r in csv.DictReader(f)
                if r.get("query", "").strip().lower() == QUERY and r.get("device") == "desktop"
            ]
    for r in history[-5:]:
        lines.append(f"- {r['captured_at_utc']}: desktop **{r['rank_position']}** ({r['source']})")

    lines.extend(
        [
            "",
            "## Sonraki çalıştırma",
            "",
            "```bash",
            "bash AGENT-HUB/run-keyword-rank-weekly.sh",
            "```",
            "",
            f"_Otomatik ölçüm: {captured_at}_",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    captured_at = utc_now_iso()
    rows = [measure_device("desktop", captured_at), measure_device("mobile", captured_at)]
    added = append_baseline(rows)
    weekly_path = write_weekly_summary(captured_at, rows)

    for row in rows:
        print(
            f"{row['device']}: rank={row['rank_position']} url={row['target_url']} source={row['source']}"
        )
    print(f"baseline_appended={added}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
