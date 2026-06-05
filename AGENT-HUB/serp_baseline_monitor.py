#!/usr/bin/env python3
"""SERP baseline: led ekran → ledajans.com. CSV satırı + haftalık özet."""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

HUB = Path("/workspace/AGENT-HUB")
CSV_PATH = HUB / "SERP-BASELINE.csv"
CSV_HEADERS = [
    "captured_at_utc",
    "query",
    "locale",
    "device",
    "search_engine",
    "target_url",
    "rank_position",
    "source",
    "notes",
]

DEFAULT_QUERY = "led ekran"
DEFAULT_DOMAIN = "ledajans.com"
DEFAULT_LOCALE = "tr-TR"
DEVICES = ("desktop", "mobile")


@dataclass
class SerpSnapshot:
    captured_at_utc: str
    query: str
    locale: str
    device: str
    search_engine: str
    target_url: str | None
    rank_position: int | None
    source: str
    notes: str
    top_domains: list[str]


def normalize_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def find_rank(urls: list[str], domain: str) -> tuple[int | None, str | None]:
    needle = domain.lower().removeprefix("www.")
    seen: set[str] = set()
    for raw in urls:
        host = normalize_domain(raw)
        if not host or host in seen:
            continue
        seen.add(host)
        if needle in host or host.endswith(needle):
            return len(seen), raw
    return None, None


def fetch_serpapi(query: str, api_key: str) -> tuple[list[str], str, str]:
    params = {
        "engine": "google",
        "q": query,
        "google_domain": "google.com.tr",
        "gl": "tr",
        "hl": "tr",
        "num": 100,
        "api_key": api_key,
    }
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    urls: list[str] = []
    for item in payload.get("organic_results", []):
        link = item.get("link") or ""
        if link.startswith("http"):
            urls.append(link)
    return urls, "google", "serpapi"


def fetch_ddg_html(query: str) -> tuple[list[str], str, str]:
    data = urllib.parse.urlencode({"q": query, "kl": "tr-tr", "s": "0"}).encode()
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-serp-baseline/1.0)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    raw = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    urls: list[str] = []
    for link in raw:
        if "duckduckgo.com/l/?uddg=" in link:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get(
                "uddg", [link]
            )[0]
            urls.append(urllib.parse.unquote(q))
        else:
            urls.append(link)
    if not urls:
        raise RuntimeError("DuckDuckGo HTML sonuç ayrıştırılamadı.")
    return urls, "duckduckgo", "ddg_html_tr"


def fetch_organic(query: str) -> tuple[list[str], str, str]:
    api_key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if api_key:
        return fetch_serpapi(query, api_key)
    return fetch_ddg_html(query)


def build_snapshots(
    query: str,
    domain: str,
    locale: str,
    urls: list[str],
    search_engine: str,
    source: str,
) -> list[SerpSnapshot]:
    rank, target_url = find_rank(urls, domain)
    top_domains = []
    seen: set[str] = set()
    for u in urls:
        host = normalize_domain(u)
        if host and host not in seen:
            seen.add(host)
            top_domains.append(host)
        if len(top_domains) >= 10:
            break

    now = datetime.now(UTC).replace(microsecond=0)
    captured = now.isoformat().replace("+00:00", "Z")
    base_note = ""
    if search_engine == "duckduckgo":
        base_note = (
            "Google TR doğrudan ölçümü datacenter IP engeli nedeniyle kullanılamadı; "
            "DuckDuckGo HTML (kl=tr-tr) organik proxy. Kesin Google için SERPAPI_API_KEY."
        )
    else:
        base_note = "SerpAPI google.com.tr organik sonuçları."

    snapshots: list[SerpSnapshot] = []
    for device in DEVICES:
        device_note = base_note
        if search_engine == "duckduckgo":
            device_note += f" Cihaz={device}; DDG HTML cihaz ayrımı yok, aynı liste."
        snapshots.append(
            SerpSnapshot(
                captured_at_utc=captured,
                query=query,
                locale=locale,
                device=device,
                search_engine=search_engine,
                target_url=target_url,
                rank_position=rank,
                source=source,
                notes=device_note,
                top_domains=top_domains,
            )
        )
    return snapshots


def ensure_csv_header() -> None:
    if CSV_PATH.exists():
        return
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=CSV_HEADERS).writeheader()


def append_csv(snapshots: list[SerpSnapshot]) -> None:
    ensure_csv_header()
    with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        for s in snapshots:
            writer.writerow(
                {
                    "captured_at_utc": s.captured_at_utc,
                    "query": s.query,
                    "locale": s.locale,
                    "device": s.device,
                    "search_engine": s.search_engine,
                    "target_url": s.target_url or "",
                    "rank_position": "" if s.rank_position is None else str(s.rank_position),
                    "source": s.source,
                    "notes": s.notes,
                }
            )


def read_csv_rows() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(UTC)
    except ValueError:
        return None


def week_start(d: datetime) -> datetime:
    return (d - timedelta(days=d.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def update_weekly_summary(snapshots: list[SerpSnapshot], query: str) -> Path:
    now = datetime.now(UTC)
    path = HUB / f"WEEKLY-MONITORING-{now.strftime('%Y-%m-%d')}.md"
    rows = read_csv_rows()
    ws = week_start(now)
    week_rows = [
        r
        for r in rows
        if r.get("query") == query
        and (t := parse_utc(r.get("captured_at_utc", ""))) is not None
        and t >= ws
    ]

    def rank_line(device: str) -> str:
        for s in snapshots:
            if s.device == device:
                pos = "100+" if s.rank_position is None else str(s.rank_position)
                return (
                    f"| {device} | {pos} | {s.search_engine} | {s.source} | "
                    f"{s.target_url or '—'} |"
                )
        return f"| {device} | — | — | — | — |"

    history_lines = ["| UTC | Cihaz | Sıra | Motor | Kaynak |", "|---|---|---:|---|---|"]
    for r in week_rows[-14:]:
        history_lines.append(
            f"| {r.get('captured_at_utc', '')} | {r.get('device', '')} | "
            f"{r.get('rank_position') or '100+'} | {r.get('search_engine', '')} | "
            f"{r.get('source', '')} |"
        )

    prev_week_rows = [
        r
        for r in rows
        if r.get("query") == query
        and (t := parse_utc(r.get("captured_at_utc", ""))) is not None
        and week_start(t) == ws - timedelta(days=7)
    ]
    delta_note = "Önceki hafta verisi yok (ilk hafta)."
    if prev_week_rows and snapshots:
        def last_rank(device: str, data: list[dict[str, str]]) -> int | None:
            for r in reversed(data):
                if r.get("device") == device and r.get("rank_position", "").isdigit():
                    return int(r["rank_position"])
            return None

        d = snapshots[0].device
        cur = snapshots[0].rank_position
        prev = last_rank("desktop", prev_week_rows)
        if cur is not None and prev is not None:
            diff = prev - cur
            if diff > 0:
                delta_note = f"Geçen haftaya göre desktop **{diff} sıra yükseldi** ({prev} → {cur})."
            elif diff < 0:
                delta_note = f"Geçen haftaya göre desktop **{abs(diff)} sıra düştü** ({prev} → {cur})."
            else:
                delta_note = f"Geçen haftaya göre desktop sıra değişmedi ({cur})."

    top = snapshots[0].top_domains if snapshots else []
    top_table = ["| # | Domain |", "|---:|---|"]
    for i, dom in enumerate(top, 1):
        mark = " **← ledajans**" if DEFAULT_DOMAIN in dom else ""
        top_table.append(f"| {i} | {dom}{mark} |")

    body = "\n".join(
        [
            f"# Haftalık SERP İzleme — {query}",
            "",
            f"- Özet tarihi (UTC): `{now.isoformat(timespec='seconds').replace('+00:00', 'Z')}`",
            f"- Hafta başlangıcı (Pazartesi UTC): `{ws.date().isoformat()}`",
            f"- Hedef domain: **{DEFAULT_DOMAIN}**",
            "",
            "## Bu çalıştırma (led ekran)",
            "",
            "| Cihaz | Sıra | Motor | Kaynak | Hedef URL |",
            "|---|---:|---|---|---|",
            rank_line("desktop"),
            rank_line("mobile"),
            "",
            f"**Haftalık trend:** {delta_note}",
            "",
            "## Bu haftanın ölçüm geçmişi",
            "",
            *history_lines,
            "",
            "## İlk 10 domain (son ölçüm)",
            "",
            *top_table,
            "",
            "## Notlar",
            "",
            snapshots[0].notes if snapshots else "—",
            "",
            f"Ham veri: `{CSV_PATH.relative_to(Path('/workspace'))}`",
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")
    return path


def run(query: str, domain: str, locale: str, dry_run: bool) -> list[SerpSnapshot]:
    urls, search_engine, source = fetch_organic(query)
    snapshots = build_snapshots(query, domain, locale, urls, search_engine, source)
    if dry_run:
        for s in snapshots:
            print(
                f"{s.device}: rank={s.rank_position} engine={s.search_engine} "
                f"url={s.target_url}"
            )
        return snapshots
    append_csv(snapshots)
    weekly = update_weekly_summary(snapshots, query)
    desktop = next(s for s in snapshots if s.device == "desktop")
    rank_txt = desktop.rank_position if desktop.rank_position is not None else "100+"
    print(
        f'"{query}" → {domain}: sıra {rank_txt} ({desktop.search_engine}/{desktop.source})'
    )
    print(f"CSV: {CSV_PATH}")
    print(f"Haftalık özet: {weekly}")
    return snapshots


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SERP baseline CSV + haftalık özet")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--locale", default=DEFAULT_LOCALE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        snapshots = run(args.query, args.domain, args.locale, args.dry_run)
    except Exception as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    if not any(s.rank_position is not None for s in snapshots):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
