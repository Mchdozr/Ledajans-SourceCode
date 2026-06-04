#!/usr/bin/env python3
"""Haftalık anahtar kelime sıra takibi (ledajans.com)."""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
DATA_DIR = HUB / "data"
HISTORY_FILE = DATA_DIR / "serp-history.json"
LATEST_FILE = HUB / "LATEST-RANK.md"
STATE_FILE = DATA_DIR / "serp-tracker-state.json"

DOMAIN = "ledajans.com"
LOCALE = "tr-tr"
DEFAULT_KEYWORDS = ["led ekran"]

EXCLUDE_HOSTS = {
    "wikipedia.org",
    "google.com",
    "google.com.tr",
    "youtube.com",
    "pinterest.com",
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "hepsiburada.com",
    "trendyol.com",
    "n11.com",
    "amazon.com",
    "amazon.com.tr",
    "alibaba.com",
    "sahibinden.com",
}


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def host_of(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_excluded(url: str) -> bool:
    host = host_of(url)
    return any(host == ex or host.endswith("." + ex) for ex in EXCLUDE_HOSTS)


def fetch_serpapi(keyword: str, api_key: str) -> list[dict[str, str]]:
    import urllib.parse
    import urllib.request

    params = urllib.parse.urlencode(
        {
            "engine": "google",
            "q": keyword,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "num": 50,
            "api_key": api_key,
        }
    )
    url = f"https://serpapi.com/search.json?{params}"
    with urllib.request.urlopen(url, timeout=45) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    rows: list[dict[str, str]] = []
    for item in payload.get("organic_results", []):
        link = item.get("link") or ""
        if link.startswith("http"):
            rows.append({"href": link, "title": item.get("title") or ""})
    return rows


def fetch_ddgs(keyword: str) -> list[dict[str, str]]:
    from ddgs import DDGS

    return list(DDGS().text(keyword, region=LOCALE, max_results=40, backend="auto"))


def filter_commercial(results: list[dict[str, str]]) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    for row in results:
        url = row.get("href") or ""
        if not url.startswith("http"):
            continue
        if is_excluded(url):
            continue
        filtered.append(row)
    return filtered


def rank_for_domain(results: list[dict[str, str]], domain: str = DOMAIN) -> tuple[int | None, str | None, list[dict[str, str]]]:
    best_pos: int | None = None
    best_url: str | None = None
    top: list[dict[str, str]] = []
    for i, row in enumerate(results, 1):
        url = row.get("href") or ""
        title = row.get("title") or ""
        top.append({"position": i, "url": url, "title": title, "host": host_of(url)})
        if domain in url.lower():
            if best_pos is None or i < best_pos:
                best_pos = i
                best_url = url
    return best_pos, best_url, top


def measure_keyword(keyword: str) -> dict:
    source = "ddgs-auto-commercial-filter"
    raw: list[dict[str, str]]
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if api_key:
        try:
            raw = fetch_serpapi(keyword, api_key)
            source = "serpapi-google-tr"
        except Exception as exc:  # noqa: BLE001
            raw = fetch_ddgs(keyword)
            source = f"ddgs-auto-commercial-filter (serpapi-fallback: {exc})"
    else:
        raw = fetch_ddgs(keyword)

    filtered = filter_commercial(raw)
    position, target_url, top = rank_for_domain(filtered)
    return {
        "keyword": keyword,
        "position": position,
        "target_url": target_url,
        "source": source,
        "locale": LOCALE,
        "domain": DOMAIN,
        "captured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "top_competitors": top[:10],
        "not_found": position is None,
    }


def append_history(snapshot: dict) -> dict:
    history = read_json(HISTORY_FILE, {"snapshots": []})
    history.setdefault("snapshots", []).append(snapshot)
    write_json(HISTORY_FILE, history)
    return history


def previous_snapshot(keyword: str) -> dict | None:
    history = read_json(HISTORY_FILE, {"snapshots": []})
    matches = [s for s in history.get("snapshots", []) if s.get("keyword") == keyword]
    if len(matches) < 2:
        return None
    return matches[-2]


def delta_text(current: int | None, previous: int | None) -> str:
    if current is None or previous is None:
        return "N/A"
    diff = previous - current
    if diff > 0:
        return f"+{diff} (yükseldi)"
    if diff < 0:
        return f"{diff} (düştü)"
    return "0 (değişmedi)"


def render_latest(snapshot: dict) -> str:
    kw = snapshot["keyword"]
    pos = snapshot.get("position")
    pos_txt = str(pos) if pos is not None else "50+ / bulunamadı"
    prev = previous_snapshot(kw)
    prev_pos = prev.get("position") if prev else None
    lines = [
        "# Ledajans — Güncel Anahtar Kelime Sırası",
        "",
        f"**Son ölçüm (UTC):** {snapshot['captured_at_utc']}",
        f"**Anahtar kelime:** `{kw}`",
        f"**Sıra:** **{pos_txt}**",
        f"**URL:** {snapshot.get('target_url') or '—'}",
        f"**Kaynak:** {snapshot['source']}",
        f"**Haftalık değişim:** {delta_text(pos, prev_pos)}",
        "",
        "## İlk 10 rakip (ticari filtre)",
        "",
        "| Sıra | Domain | Başlık |",
        "| --- | --- | --- |",
    ]
    for row in snapshot.get("top_competitors", [])[:10]:
        title = re.sub(r"\|", "/", row.get("title") or "")
        lines.append(f"| {row['position']} | {row['host']} | {title[:60]} |")
    lines.extend(
        [
            "",
            "## Not",
            "",
            "- Google doğrudan ölçümü için ortam değişkeni `SERPAPI_KEY` tanımlanabilir.",
            "- `ddgs` yedek kaynağında wiki/pazar yeri sonuçları filtrelenir; Google SERP ile birebir aynı olmayabilir.",
            "",
        ]
    )
    return "\n".join(lines)


def render_weekly_report(snapshots: list[dict]) -> str:
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# SERP Watch Report - {date}",
        "",
        "## Keyword Set",
    ]
    for s in snapshots:
        pos = s.get("position")
        pos_txt = str(pos) if pos is not None else "N/A"
        lines.append(
            f"- anahtar kelime: {s['keyword']} | mevcut sıra: {pos_txt} | "
            f"hedef URL: {s.get('target_url') or 'N/A'} | kaynak: {s['source']}"
        )
    lines.extend(["", "## Baseline Positions"])
    for s in snapshots:
        prev = previous_snapshot(s["keyword"])
        prev_pos = prev.get("position") if prev else None
        pos = s.get("position")
        pos_txt = str(pos) if pos is not None else "N/A"
        lines.append(
            f"- anahtar kelime: {s['keyword']} | mevcut sıra: {pos_txt} | "
            f"önceki: {prev_pos if prev_pos is not None else 'N/A'} | "
            f"değişim: {delta_text(pos, prev_pos)} | not: otomatik ölçüm"
        )
    lines.extend(["", "## Competitor Delta", ""])
    for s in snapshots:
        top = s.get("top_competitors") or []
        leader = top[0] if top else {}
        lines.append(
            f"- anahtar kelime: {s['keyword']} | lider domain: {leader.get('host', 'N/A')} | "
            f"ledajans sırası: {s.get('position') or 'N/A'}"
        )
    lines.extend(
        [
            "",
            "## Volatility Notes",
            f"- Ölçüm zamanı (UTC): {snapshots[0]['captured_at_utc'] if snapshots else 'N/A'}",
            "- Haftalık cadence: `serp_rank_tracker.py --weekly-report`",
            "",
        ]
    )
    return "\n".join(lines)


def should_write_weekly(state: dict, force: bool) -> bool:
    if force:
        return True
    last = state.get("last_weekly_report_utc")
    if not last:
        return True
    last_dt = datetime.fromisoformat(last)
    return (datetime.now(UTC) - last_dt).days >= 7


def run(keywords: list[str], weekly_report: bool, force_weekly: bool) -> int:
    snapshots = [measure_keyword(kw) for kw in keywords]
    for snap in snapshots:
        append_history(snap)

    primary = snapshots[0]
    write_text = LATEST_FILE.write_text
    write_text(render_latest(primary), encoding="utf-8")

    state = read_json(STATE_FILE, {})
    if weekly_report and should_write_weekly(state, force_weekly):
        report_path = REPORTS / f"{datetime.now(UTC).strftime('%Y-%m-%d')}-serp-watch.md"
        report_path.write_text(render_weekly_report(snapshots), encoding="utf-8")
        state["last_weekly_report_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
        write_json(STATE_FILE, state)

    pos = primary.get("position")
    print(f"keyword={primary['keyword']} position={pos} url={primary.get('target_url')}")
    print(f"source={primary['source']}")
    print(f"latest={LATEST_FILE}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ledajans SERP sıra takibi")
    parser.add_argument("--keyword", action="append", dest="keywords", help="Anahtar kelime (tekrarlanabilir)")
    parser.add_argument("--weekly-report", action="store_true", help="Haftalık rapor dosyası üret")
    parser.add_argument("--force-weekly", action="store_true", help="7 gün beklemeden haftalık rapor yaz")
    args = parser.parse_args()
    keywords = args.keywords or DEFAULT_KEYWORDS
    return run(keywords, weekly_report=args.weekly_report, force_weekly=args.force_weekly)


if __name__ == "__main__":
    raise SystemExit(main())
