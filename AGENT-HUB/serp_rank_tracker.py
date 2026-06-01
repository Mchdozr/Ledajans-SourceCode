#!/usr/bin/env python3
"""Haftalık anahtar kelime sıra takibi — ledajans.com (varsayılan: led ekran)."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
RANKING_DIR = HUB / "RANKING"
HISTORY_FILE = RANKING_DIR / "history.jsonl"
LATEST_MD = RANKING_DIR / "latest.md"
WEEKLY_MD = RANKING_DIR / "weekly.md"
REPORTS = HUB / "REPORTS"

DEFAULT_KEYWORD = "led ekran"
DEFAULT_DOMAIN = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/led-ekran/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_url(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalize_domain(url_or_host: str) -> str:
    raw = url_or_host.strip().lower()
    if "://" in raw:
        raw = urlparse(raw).netloc
    return raw.removeprefix("www.")


def rank_from_serpapi(keyword: str, domain: str) -> dict[str, Any]:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        return {"ok": False, "reason": "SERPAPI_KEY tanımlı değil"}

    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": keyword,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "num": 100,
            "api_key": api_key,
        }
    )
    url = f"https://serpapi.com/search.json?{params}"
    try:
        payload = json.loads(fetch_url(url, timeout=40))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        return {"ok": False, "reason": f"SerpAPI hatası: {exc}"}

    organic = payload.get("organic_results") or []
    rank = None
    target_url = None
    top: list[dict[str, str]] = []
    for item in organic:
        link = item.get("link") or ""
        pos = item.get("position")
        if not link or pos is None:
            continue
        dom = normalize_domain(link)
        top.append({"position": int(pos), "domain": dom, "url": link})
        if rank is None and domain in dom:
            rank = int(pos)
            target_url = link

    return {
        "ok": True,
        "source": "serpapi_google_tr",
        "engine": "google",
        "rank": rank,
        "target_url": target_url,
        "top": top[:15],
        "note": None if rank else f"İlk 100 sonuçta {domain} bulunamadı",
    }


def rank_from_duckduckgo_html(keyword: str, domain: str) -> dict[str, Any]:
    q = urllib.parse.quote_plus(keyword)
    url = f"https://html.duckduckgo.com/html/?q={q}&kl=tr-tr"
    try:
        html = fetch_url(url)
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"ok": False, "reason": f"DuckDuckGo isteği başarısız: {exc}"}

    links: list[str] = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', html):
        links.append(m.group(1))
    if not links:
        for m in re.finditer(r"uddg=([^&\"]+)", html):
            links.append(urllib.parse.unquote(m.group(1)))

    rank = None
    target_url = None
    top: list[dict[str, str | int]] = []
    seen: set[str] = set()
    for raw in links:
        href = raw
        if href.startswith("//"):
            href = "https:" + href
        uddg_m = re.search(r"uddg=([^&\"]+)", href)
        if uddg_m:
            href = urllib.parse.unquote(uddg_m.group(1).replace("&amp;", "&"))
        if not href.startswith("http"):
            continue
        dom = normalize_domain(href)
        if dom in seen or "duckduckgo" in dom:
            continue
        seen.add(dom)
        pos = len(top) + 1
        top.append({"position": pos, "domain": dom, "url": href})
        if rank is None and domain in dom:
            rank = pos
            target_url = href

    if not top:
        return {"ok": False, "reason": "DuckDuckGo sonuç listesi parse edilemedi"}

    return {
        "ok": True,
        "source": "duckduckgo_html_tr",
        "engine": "duckduckgo",
        "rank": rank,
        "target_url": target_url,
        "top": top[:15],
        "note": (
            "Google/Bing datacenter engeli nedeniyle DuckDuckGo HTML proxy kullanıldı. "
            "Kesin Google sırası için SERPAPI_KEY ekleyin."
        ),
    }


def rank_from_bing_html(keyword: str, domain: str) -> dict[str, Any]:
    q = urllib.parse.quote_plus(keyword)
    url = f"https://www.bing.com/search?q={q}&cc=tr&setlang=tr-tr"
    try:
        html = fetch_url(url)
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"ok": False, "reason": f"Bing isteği başarısız: {exc}"}

    parts = re.split(r'<li class="b_algo"', html)
    blocks = parts[1:] if len(parts) > 1 else []
    rank = None
    target_url = None
    top: list[dict[str, str | int]] = []
    for block in blocks:
        label = re.search(r'aria-label="([^"]+)"', block)
        dom = normalize_domain(label.group(1)) if label else ""
        if not dom:
            cite = re.search(r"<cite[^>]*>([^<]+)", block)
            if cite:
                dom = normalize_domain(cite.group(1).split(" ›")[0])
        if not dom:
            continue
        pos = len(top) + 1
        link_m = re.search(r'<a[^>]+href="([^"]+)"', block)
        link = link_m.group(1) if link_m else ""
        top.append({"position": pos, "domain": dom, "url": link})
        if rank is None and domain in dom:
            rank = pos
            target_url = link or f"https://{dom}/"

    if not top:
        return {"ok": False, "reason": "Bing sonuç listesi parse edilemedi (CAPTCHA veya HTML değişimi)"}

    return {
        "ok": True,
        "source": "bing_html_tr",
        "engine": "bing",
        "rank": rank,
        "target_url": target_url,
        "top": top[:15],
        "note": (
            "Google datacenter CAPTCHA verdi; Bing organik sırası proxy olarak kullanıldı. "
            "Kesin Google sırası için SERPAPI_KEY ekleyin."
        ),
    }


def measure(keyword: str, domain: str) -> dict[str, Any]:
    captured_at = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    serpapi = rank_from_serpapi(keyword, domain)
    if serpapi.get("ok"):
        result = serpapi
    else:
        ddg = rank_from_duckduckgo_html(keyword, domain)
        result = ddg if ddg.get("ok") else rank_from_bing_html(keyword, domain)

    record: dict[str, Any] = {
        "captured_at_utc": captured_at,
        "keyword": keyword,
        "domain": domain,
        "locale": "tr-TR",
        "device_scope": "desktop",
        "rank_position": result.get("rank"),
        "target_url": result.get("target_url") or DEFAULT_TARGET_URL,
        "serp_source": result.get("source"),
        "search_engine": result.get("engine"),
        "measurement_note": result.get("note") or result.get("reason"),
        "top_organic": result.get("top") or [],
        "ok": bool(result.get("ok")),
    }
    if not record["ok"]:
        record["measurement_note"] = result.get("reason", "ölçüm başarısız")
    return record


def append_history(record: dict[str, Any]) -> None:
    RANKING_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_history(keyword: str | None = None) -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if keyword and row.get("keyword") != keyword:
            continue
        rows.append(row)
    return rows


def iso_week_key(iso_ts: str) -> str:
    day = dt.datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def build_weekly_summary(keyword: str, history: list[dict[str, Any]]) -> str:
    if not history:
        return "_Henüz geçmiş ölçüm yok._"

    by_week: dict[str, list[dict[str, Any]]] = {}
    for row in history:
        ts = row.get("captured_at_utc", "")
        if not ts:
            continue
        by_week.setdefault(iso_week_key(ts), []).append(row)

    lines = ["| Hafta | Ölçüm | Ort. sıra | Min | Max | Son | Kaynak |", "|---|---:|---:|---:|---:|---:|---|"]
    for week in sorted(by_week.keys(), reverse=True)[:8]:
        items = by_week[week]
        ranks = [r["rank_position"] for r in items if r.get("rank_position") is not None]
        if not ranks:
            lines.append(f"| {week} | {len(items)} | — | — | — | — | — |")
            continue
        avg = round(sum(ranks) / len(ranks), 1)
        last = items[-1]
        src = last.get("serp_source", "—")
        lines.append(
            f"| {week} | {len(items)} | {avg} | {min(ranks)} | {max(ranks)} | "
            f"{last.get('rank_position')} | {src} |"
        )
    return "\n".join(lines)


def write_latest_md(record: dict[str, Any], history: list[dict[str, Any]]) -> None:
    rank = record.get("rank_position")
    rank_text = str(rank) if rank is not None else "İlk 10–15 sonuçta görünmedi"
    prev = None
    for row in reversed(history[:-1]):
        if row.get("rank_position") is not None:
            prev = row["rank_position"]
            break
    delta = ""
    if rank is not None and prev is not None:
        diff = prev - rank
        if diff > 0:
            delta = f" (önceki ölçüme göre **{diff} sıra yükseldi**)"
        elif diff < 0:
            delta = f" (önceki ölçüme göre **{-diff} sıra düştü**)"
        else:
            delta = " (önceki ölçümle aynı)"

    top_lines = []
    for item in record.get("top_organic") or []:
        top_lines.append(f"- {item['position']}. {item['domain']}")

    body = f"""# Sıralama Raporu — {record['keyword']}

**Tarih (UTC):** {record['captured_at_utc']}  
**Site:** {record['domain']}  
**Anahtar kelime:** {record['keyword']}  
**Sıra:** **{rank_text}**{delta}  
**Hedef URL:** {record.get('target_url') or DEFAULT_TARGET_URL}  
**Kaynak:** {record.get('serp_source')} ({record.get('search_engine')})  
**Locale:** {record.get('locale')} · **Cihaz:** {record.get('device_scope')}

## Not
{record.get('measurement_note') or '—'}

## İlk 10–15 organik sonuç
{chr(10).join(top_lines) if top_lines else '_Sonuç listesi alınamadı._'}

## Haftalık özet
{build_weekly_summary(record['keyword'], history)}
"""
    LATEST_MD.write_text(body, encoding="utf-8")


def write_weekly_md(keyword: str, history: list[dict[str, Any]]) -> None:
    now = dt.datetime.now(dt.UTC)
    week = iso_week_key(now.isoformat())
    week_rows = [r for r in history if iso_week_key(r.get("captured_at_utc", "")) == week]
    ranks = [r["rank_position"] for r in week_rows if r.get("rank_position") is not None]
    current = week_rows[-1] if week_rows else (history[-1] if history else None)

    body = f"""# Haftalık Sıralama — {keyword}

**ISO hafta:** {week}  
**Bu hafta ölçüm sayısı:** {len(week_rows)}  
**Güncel sıra:** {current.get('rank_position') if current else '—'}  
**Kaynak:** {current.get('serp_source') if current else '—'}

{build_weekly_summary(keyword, history)}

_Günlük cron ile yeni satır eklenir; haftalık tablo otomatik güncellenir._
"""
    WEEKLY_MD.write_text(body, encoding="utf-8")


def write_serp_watch_report(record: dict[str, Any]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    day = record["captured_at_utc"][:10]
    path = REPORTS / f"{day}-serp-watch.md"
    rank = record.get("rank_position")
    rank_s = str(rank) if rank is not None else "N/A"
    note = record.get("measurement_note") or "otomatik ölçüm"
    content = f"""# SERP Watch Report - {day}

## Keyword Set
- anahtar kelime: {record['keyword']} | mevcut sıra: {rank_s} | hedef: {record.get('target_url')} | kaynak: {record.get('serp_source')} | not: {note}

## Baseline Positions
- anahtar kelime: {record['keyword']} | mevcut sıra: {rank_s} | locale: tr-TR | device: desktop | captured_at_utc: {record['captured_at_utc']} | serp_source: {record.get('serp_source')}

## Competitor Delta
- (otomatik) İlk 3 rakip: {', '.join(item['domain'] for item in (record.get('top_organic') or [])[:3] if item.get('domain') != record['domain']) or '—'}

## Volatility Notes
- Haftalık özet: `AGENT-HUB/RANKING/weekly.md`
- Ham geçmiş: `AGENT-HUB/RANKING/history.jsonl`
"""
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    keyword = os.environ.get("RANK_KEYWORD", DEFAULT_KEYWORD).strip() or DEFAULT_KEYWORD
    domain = os.environ.get("RANK_DOMAIN", DEFAULT_DOMAIN).strip() or DEFAULT_DOMAIN

    record = measure(keyword, domain)
    history = load_history(keyword)
    append_history(record)
    history.append(record)

    write_latest_md(record, history)
    write_weekly_md(keyword, history)
    report_path = write_serp_watch_report(record)

    rank = record.get("rank_position")
    print(f"keyword={keyword} domain={domain} rank={rank} source={record.get('serp_source')}")
    print(f"latest={LATEST_MD}")
    print(f"weekly={WEEKLY_MD}")
    print(f"report={report_path}")
    return 0 if record.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
