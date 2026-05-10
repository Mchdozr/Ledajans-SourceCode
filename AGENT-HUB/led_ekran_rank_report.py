#!/usr/bin/env python3
"""ledajans.com için 'led ekran' sorgu sırası: Google CSE (varsa) veya DDG HTML proxy."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import unquote

ROOT = Path("/workspace")
OUT_DIR = ROOT / "AGENT-HUB" / "SERP-RANK"
HISTORY = OUT_DIR / "led-ekran-history.jsonl"
LATEST_MD = OUT_DIR / "led-ekran-latest.md"

KEYWORD = "led ekran"
TARGET_HOST = "ledajans.com"
UA = "Mozilla/5.0 (compatible; LEDAJANS-rank-snapshot/1.0; +https://ledajans.com)"


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _read_jsonl_last(path: Path) -> dict | None:
    if not path.exists():
        return None
    last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            continue
    return last


def _days_since_last_run(path: Path) -> float | None:
    row = _read_jsonl_last(path)
    if not row:
        return None
    try:
        then = dt.datetime.fromisoformat(row["captured_at_utc"].replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return None
    delta = _utc_now() - then.astimezone(dt.UTC)
    return delta.total_seconds() / 86400.0


def rank_ddg_html(keyword: str) -> tuple[int | None, list[str]]:
    q = urllib.parse.quote_plus(keyword)
    url = f"https://html.duckduckgo.com/html/?q={q}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", "replace")
    uddgs = re.findall(r"uddg=([^&\"]+)", html)
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in uddgs:
        u = unquote(raw)
        if u.startswith("http") and u not in seen:
            seen.add(u)
            ordered.append(u)
    rank = None
    for i, u in enumerate(ordered, start=1):
        if TARGET_HOST in u.lower():
            rank = i
            break
    return rank, ordered[:15]


def rank_google_cse(keyword: str, api_key: str, cx: str, max_scan: int = 100) -> tuple[int | None, str | None, list[str]]:
    try:
        import requests
    except ImportError:
        return None, "requests modülü yok", []

    top_links: list[str] = []
    for start in range(1, max_scan + 1, 10):
        params = {
            "key": api_key,
            "cx": cx,
            "q": keyword,
            "num": 10,
            "start": start,
            "hl": "tr",
            "gl": "tr",
            "cr": "countryTR",
        }
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=25,
        )
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:500]}", top_links
        data = r.json()
        items = data.get("items") or []
        if not items:
            break
        for idx, it in enumerate(items):
            abs_pos = start + idx
            link = (it.get("link") or "").strip()
            if link and len(top_links) < 15:
                top_links.append(link)
            if TARGET_HOST in link.lower():
                return abs_pos, None, top_links
    return None, "İlk 100 organik sonuçta eşleşme yok", top_links


def write_latest_md(
    *,
    captured: str,
    rank: int | None,
    source: str,
    detail: str,
    sample_urls: list[str],
) -> None:
    lines = [
        f"# LEDAJANS — «{KEYWORD}» sıra özeti",
        "",
        f"- **Ölçüm zamanı (UTC):** {captured}",
        f"- **Kaynak:** {source}",
        f"- **ledajans.com ilk görünüm sırası:** {rank if rank is not None else 'Bulunamadı (>liste derinliği veya eşleşme yok)'}",
        "",
        "## Not",
        detail,
        "",
        "## Örnek üst URL'ler (aynı ölçümde)",
    ]
    for u in sample_urls[:12]:
        lines.append(f"- {u}")
    LATEST_MD.parent.mkdir(parents=True, exist_ok=True)
    LATEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_history(row: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--min-days-between-runs",
        type=float,
        default=0,
        help="Son jsonl kaydından bu kadar gün geçmeden çık (0=her zaman çalış). Haftalık için 7 önerilir.",
    )
    args = p.parse_args()

    if args.min_days_between_runs > 0:
        prev = _days_since_last_run(HISTORY)
        if prev is not None and prev < args.min_days_between_runs:
            print(
                json.dumps(
                    {
                        "skipped": True,
                        "reason": "min_days_between_runs",
                        "days_since_last": round(prev, 3),
                        "min_required": args.min_days_between_runs,
                    },
                    ensure_ascii=False,
                )
            )
            return 0

    api_key = os.environ.get("GOOGLE_CSE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CSE_CX") or os.environ.get("GOOGLE_CSE_ID")

    captured = _utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")
    sample: list[str] = []
    rank: int | None
    source: str
    extra_note: str

    if api_key and cx:
        rank, err, sample = rank_google_cse(KEYWORD, api_key, cx)
        source = "google_custom_search_json_api"
        if rank is None:
            extra_note = (
                "Google Programmable Search Engine sonucu; "
                + (err or "bilinmeyen")
            )
        else:
            extra_note = "Google Programmable Search Engine (CSE) ile üretildi; sonuçlar Google web aramasıyla birebir aynı olmayabilir."
    else:
        rank, ordered = rank_ddg_html(KEYWORD)
        sample = ordered
        source = "duckduckgo_html_proxy"
        extra_note = (
            "Bu ölçüm DuckDuckGo HTML sonuç listesinden türetildi; **Google sırası değildir**. "
            "Gerçek Google sırası için ortam değişkenleri `GOOGLE_CSE_API_KEY` ve `GOOGLE_CSE_CX` "
            "(veya `GOOGLE_API_KEY` + `GOOGLE_CSE_ID`) tanımlayın."
        )

    row = {
        "captured_at_utc": captured,
        "keyword": KEYWORD,
        "target_host": TARGET_HOST,
        "rank_position": rank,
        "source": source,
    }
    append_history(row)
    write_latest_md(
        captured=captured,
        rank=rank,
        source=source,
        detail=extra_note,
        sample_urls=sample,
    )

    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as e:
        print(json.dumps({"error": "url_error", "message": str(e)}, ensure_ascii=False))
        raise SystemExit(1)
