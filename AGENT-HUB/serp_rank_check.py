#!/usr/bin/env python3
"""Google (veya yedek kaynak) üzerinden anahtar kelime sıra takibi — ledajans.com."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus, unquote

import requests

HUB = Path("/workspace/AGENT-HUB")
DATA_DIR = HUB / "data"
HISTORY_FILE = DATA_DIR / "serp-rank-history.jsonl"
LATEST_FILE = HUB / "SERP-RANK-LATEST.md"
REPORTS = HUB / "REPORTS"

TARGET_DOMAIN = "ledajans.com"
DEFAULT_KEYWORD = "led ekran"
LOCALE = "tr-TR"
COUNTRY = "tr"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def domain_from_url(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url.split("?")[0]).split("/")[0].lower()


def unique_organic(results: list[tuple[str, str]]) -> list[tuple[int, str, str]]:
    seen: set[str] = set()
    out: list[tuple[int, str, str]] = []
    for url, title in results:
        dom = domain_from_url(url)
        if not dom or dom in seen:
            continue
        skip = ("google.", "gstatic", "youtube.com/redirect", "accounts.google")
        if any(s in dom for s in skip):
            continue
        seen.add(dom)
        out.append((len(out) + 1, dom, url))
    return out


def fetch_serper(keyword: str, num: int = 50) -> tuple[str, list[tuple[str, str]]]:
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return ("unconfigured", [])

    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": keyword, "gl": COUNTRY, "hl": "tr", "num": num},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    organic = [(item.get("link", ""), item.get("title", "")) for item in data.get("organic", [])]
    return ("google_serper", organic)


def fetch_duckduckgo(keyword: str, retries: int = 3) -> tuple[str, list[tuple[str, str]]]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(keyword)}&kl=tr-tr"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    }
    last_html = ""
    for attempt in range(retries):
        if attempt:
            time.sleep(2 * attempt)
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        last_html = resp.text
        pairs: list[tuple[str, str]] = []
        for m in re.finditer(r'uddg=([^&"]+)', last_html):
            pairs.append((unquote(m.group(1)), ""))
        if pairs:
            return ("duckduckgo_html_tr", pairs)
    return ("duckduckgo_html_tr", [])


def find_position(ranked: list[tuple[int, str, str]], domain: str = TARGET_DOMAIN) -> int | None:
    for pos, dom, _ in ranked:
        if domain in dom:
            return pos
    return None


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    rows: list[dict] = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def append_history(record: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def week_start(dt: datetime) -> datetime:
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def previous_week_snapshot(history: list[dict], keyword: str) -> dict | None:
    now = datetime.now(UTC)
    this_monday = week_start(now)
    prev_monday = this_monday - timedelta(days=7)
    candidates = [
        r
        for r in history
        if r.get("keyword") == keyword
        and prev_monday <= datetime.fromisoformat(r["captured_at_utc"]) < this_monday
    ]
    return candidates[-1] if candidates else None


def parse_ddg_html(html: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for m in re.finditer(r'uddg=([^&"]+)', html):
        pairs.append((unquote(m.group(1)), ""))
    return pairs


def run_check(keyword: str, num: int = 50, snapshot_html: Path | None = None) -> dict:
    source = "duckduckgo_html_tr"
    raw: list[tuple[str, str]] = []
    notes: list[str] = []

    if snapshot_html and snapshot_html.exists():
        raw = parse_ddg_html(snapshot_html.read_text(encoding="utf-8", errors="ignore"))
        source = "duckduckgo_html_snapshot"
        notes.append(f"Ölçüm HTML anlık görüntüsünden: {snapshot_html}")

    if raw:
        ranked = unique_organic(raw)[:num]
        position = find_position(ranked)
        captured = datetime.now(UTC).isoformat(timespec="seconds")
        target_url = next((u for _, d, u in ranked if TARGET_DOMAIN in d), "")
        return _build_record(keyword, source, ranked, position, target_url, captured, notes, num)

    try:
        serper_source, serper_raw = fetch_serper(keyword, num=num)
        if serper_raw:
            source = serper_source
            raw = serper_raw
        else:
            notes.append(
                "SERPER_API_KEY tanımlı değil veya boş; DuckDuckGo HTML (tr-tr) yedek kaynak kullanıldı."
            )
            source, raw = fetch_duckduckgo(keyword)
    except requests.RequestException as exc:
        notes.append(f"Serper hatası: {exc}; DuckDuckGo deneniyor.")
        source, raw = fetch_duckduckgo(keyword)

    ranked = unique_organic(raw)[:num]
    position = find_position(ranked)
    captured = datetime.now(UTC).isoformat(timespec="seconds")
    target_url = next((u for _, d, u in ranked if TARGET_DOMAIN in d), "")

    if not ranked:
        notes.append(
            "SERP çekimi başarısız (bot koruması). SERPER_API_KEY ile Google ölçümü önerilir."
        )

    return _build_record(keyword, source, ranked, position, target_url, captured, notes, num)


def _build_record(
    keyword: str,
    source: str,
    ranked: list[tuple[int, str, str]],
    position: int | None,
    target_url: str,
    captured: str,
    notes: list[str],
    num: int,
) -> dict:
    return {
        "keyword": keyword,
        "target_domain": TARGET_DOMAIN,
        "target_url": target_url,
        "rank_position": position,
        "rank_label": str(position) if position else (f">{len(ranked)}" if ranked else "ölçülemedi"),
        "locale": LOCALE,
        "country": COUNTRY,
        "device_scope": "desktop_proxy",
        "search_engine": "google" if source == "google_serper" else "duckduckgo",
        "serp_source": source,
        "captured_at_utc": captured,
        "top_results": [{"position": p, "domain": d, "url": u} for p, d, u in ranked[:15]],
        "notes": notes,
        "measurement_ok": bool(ranked and position),
    }


def format_latest_md(record: dict, weekly: dict | None = None) -> str:
    lines = [
        "# SERP Sıra Özeti — ledajans.com",
        "",
        f"- Son ölçüm (UTC): **{record['captured_at_utc']}**",
        f"- Anahtar kelime: **{record['keyword']}**",
        f"- Kaynak: `{record['serp_source']}` ({record['search_engine']})",
        f"- ledajans.com sırası: **{record['rank_label']}**",
    ]
    if record.get("target_url"):
        lines.append(f"- Hedef URL: {record['target_url']}")
    if record.get("notes"):
        lines.append(f"- Not: {' '.join(record['notes'])}")
    if weekly:
        prev_rank = weekly.get("prev_rank") or "—"
        prev_date = weekly.get("prev_date") or "—"
        lines.extend(
            [
                "",
                "## Haftalık değişim",
                f"- Önceki hafta sırası: **{prev_rank}** ({prev_date})",
                f"- Bu hafta sırası: **{weekly.get('curr_rank', '—')}**",
                f"- Delta: **{weekly.get('delta', '—')}**",
            ]
        )
    lines.extend(["", "## İlk 10 sonuç", ""])
    for item in record.get("top_results", [])[:10]:
        mark = " ← **LEDAJANS**" if TARGET_DOMAIN in item["domain"] else ""
        lines.append(f"{item['position']}. {item['domain']}{mark}")
    lines.append("")
    lines.extend(
        [
            "",
            "> **Google TR:** Cloud IP'lerde doğrudan Google SERP genelde CAPTCHA verir. "
            "Kesin Google sırası için Automation secret olarak `SERPER_API_KEY` tanımlayın "
            "(https://serper.dev). DuckDuckGo TR sonuçları yaklaşık gösterge niteliğindedir.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_serp_watch_report(record: dict, weekly: dict | None) -> Path:
    date_prefix = datetime.now(UTC).strftime("%Y-%m-%d")
    path = REPORTS / f"{date_prefix}-serp-watch.md"
    rank = record["rank_label"]
    prev = weekly or {}
    content = f"""# SERP Watch Report - {date_prefix}

## Özet — {record['keyword']}

| Alan | Değer |
|------|-------|
| Anahtar kelime | {record['keyword']} |
| ledajans.com sırası | **{rank}** |
| Kaynak | {record['serp_source']} |
| Locale | {LOCALE} |
| Ölçüm zamanı (UTC) | {record['captured_at_utc']} |
| Hedef URL | {record.get('target_url') or '—'} |

## Haftalık delta

- Önceki hafta: {prev.get('prev_rank', 'veri yok')} ({prev.get('prev_date', '—')})
- Bu hafta: {prev.get('curr_rank', rank)}
- Değişim: {prev.get('delta', 'ilk ölçüm')}

## Keyword Set

- anahtar kelime: {record['keyword']} | mevcut sıra: {rank} | kaynak: {record['serp_source']} | not: Otomatik ölçüm (serp_rank_check.py).

## Baseline Positions

- anahtar kelime: {record['keyword']} | mevcut sıra: {rank} | target_url: {record.get('target_url') or 'N/A'} | locale: {LOCALE} | device: desktop_proxy

## Top 10 SERP

"""
    for item in record.get("top_results", [])[:10]:
        mark = " **← LEDAJANS**" if TARGET_DOMAIN in item["domain"] else ""
        content += f"- #{item['position']} {item['domain']}{mark}\n"

    if record.get("notes"):
        content += f"\n## Notlar\n\n" + "\n".join(f"- {n}" for n in record["notes"]) + "\n"

    path.write_text(content, encoding="utf-8")
    return path


def write_weekly_report(record: dict, weekly: dict) -> Path:
    iso_year, iso_week, _ = datetime.now(UTC).isocalendar()
    path = REPORTS / f"{iso_year}-W{iso_week:02d}-serp-rank-weekly.md"
    lines = [
        f"# Haftalık SERP Raporu — {record['keyword']}",
        "",
        f"- Hafta: **{iso_year}-W{iso_week:02d}**",
        f"- Domain: **ledajans.com**",
        f"- Ölçüm: {record['captured_at_utc']} UTC",
        f"- Kaynak: `{record['serp_source']}`",
        "",
        "## Sıra",
        "",
        "| Metrik | Değer |",
        "|--------|-------|",
        f"| Bu hafta | **{weekly.get('curr_rank', record['rank_label'])}** |",
        f"| Geçen hafta | {weekly.get('prev_rank', '—')} |",
        f"| Değişim | {weekly.get('delta', '—')} |",
        "",
        "## İlk 10",
        "",
    ]
    for item in record.get("top_results", [])[:10]:
        mark = " ← LEDAJANS" if TARGET_DOMAIN in item["domain"] else ""
        lines.append(f"{item['position']}. {item['domain']}{mark}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def compute_weekly_delta(history: list[dict], record: dict) -> dict:
    prev = previous_week_snapshot(history, record["keyword"])
    curr_rank = record["rank_position"]
    curr_label = record["rank_label"]
    if not prev:
        return {
            "prev_rank": None,
            "prev_date": None,
            "curr_rank": curr_label,
            "delta": "ilk haftalık ölçüm",
        }
    prev_rank = prev.get("rank_position")
    prev_label = prev.get("rank_label", str(prev_rank) if prev_rank else ">?")
    if prev_rank and curr_rank:
        diff = prev_rank - curr_rank
        if diff > 0:
            delta = f"↑ {diff} sıra iyileşme"
        elif diff < 0:
            delta = f"↓ {abs(diff)} sıra düşüş"
        else:
            delta = "değişmedi"
    else:
        delta = "karşılaştırılamadı (önceki veya güncel ölçüm sınır dışı)"
    return {
        "prev_rank": prev_label,
        "prev_date": prev.get("captured_at_utc", "")[:10],
        "curr_rank": curr_label,
        "delta": delta,
    }


def should_emit_weekly(force: bool) -> bool:
    if force:
        return True
    return datetime.now(UTC).weekday() == 0  # Pazartesi


def main() -> int:
    parser = argparse.ArgumentParser(description="ledajans.com SERP sıra kontrolü")
    parser.add_argument("--keyword", default=DEFAULT_KEYWORD)
    parser.add_argument("--num", type=int, default=50)
    parser.add_argument("--weekly", action="store_true", help="Haftalık rapor dosyası üret")
    parser.add_argument("--no-history", action="store_true", help="Geçmişe yazma")
    parser.add_argument(
        "--snapshot-html",
        type=Path,
        default=None,
        help="DDG HTML anlık görüntüsünden ölçüm (bot engeli durumunda)",
    )
    args = parser.parse_args()

    record = run_check(args.keyword, num=args.num, snapshot_html=args.snapshot_html)
    history = load_history() if not args.no_history else []
    weekly = compute_weekly_delta(history, record)

    if not args.no_history:
        append_history(record)

    LATEST_FILE.write_text(format_latest_md(record, weekly), encoding="utf-8")
    report_path = write_serp_watch_report(record, weekly)

    weekly_path = None
    if should_emit_weekly(args.weekly):
        weekly_path = write_weekly_report(record, weekly)

    print(f"keyword={record['keyword']}")
    print(f"rank={record['rank_label']}")
    print(f"source={record['serp_source']}")
    print(f"latest={LATEST_FILE}")
    print(f"report={report_path}")
    if weekly_path:
        print(f"weekly={weekly_path}")
    print(f"delta={weekly.get('delta')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
