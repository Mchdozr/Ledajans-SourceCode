#!/usr/bin/env python3
"""Haftalık SERP sıra takibi — ledajans.com için 'led ekran' (tr-TR)."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

HUB = Path("/workspace/AGENT-HUB")
DATA_DIR = HUB / "data"
HISTORY_FILE = DATA_DIR / "serp-led-ekran-history.jsonl"
REPORTS = HUB / "REPORTS"
LATEST_SNAPSHOT = DATA_DIR / "serp-led-ekran-latest.json"

TARGET_DOMAIN = "ledajans.com"
KEYWORD = "led ekran"
LOCALE = "tr-TR"
TR_TZ = ZoneInfo("Europe/Istanbul")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
}


@dataclass
class SourceResult:
    source: str
    rank: int | None
    target_url: str | None
    results_count: int
    top_domains: list[str]
    error: str | None = None


@dataclass
class Snapshot:
    captured_at_utc: str
    keyword: str
    locale: str
    target_domain: str
    sources: list[SourceResult]
    primary_rank: int | None
    primary_source: str | None
    week_id: str


def normalize_domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def dedupe_results(links: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: list[str] = []
    out: list[tuple[str, str]] = []
    for domain, url in links:
        if not domain or domain in seen:
            continue
        seen.append(domain)
        out.append((domain, url))
    return out


def find_rank(results: list[tuple[str, str]]) -> tuple[int | None, str | None]:
    for idx, (domain, url) in enumerate(results, start=1):
        if TARGET_DOMAIN in domain:
            return idx, url
    return None, None


def fetch_startpage() -> SourceResult:
    try:
        resp = requests.get(
            "https://www.startpage.com/sp/search",
            params={"query": KEYWORD, "language": "turkish", "region": "tr-tr"},
            headers=HEADERS,
            timeout=45,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return SourceResult("startpage_google_proxy", None, None, 0, [], str(exc))

    soup = BeautifulSoup(resp.text, "lxml")
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not href.startswith("http") or "startpage.com" in href:
            continue
        domain = normalize_domain(href)
        if domain not in [d for d, _ in links]:
            links.append((domain, href))

    results = dedupe_results(links)
    rank, url = find_rank(results)
    return SourceResult(
        "startpage_google_proxy",
        rank,
        url,
        len(results),
        [d for d, _ in results[:15]],
    )


def fetch_duckduckgo() -> SourceResult:
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": KEYWORD, "kl": "tr-tr"},
            headers=HEADERS,
            timeout=45,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return SourceResult("duckduckgo_html", None, None, 0, [], str(exc))

    soup = BeautifulSoup(resp.text, "lxml")
    links: list[tuple[str, str]] = []
    for anchor in soup.select("a.result__a"):
        href = anchor.get("href", "")
        if "uddg=" in href:
            match = re.search(r"uddg=([^&]+)", href)
            if match:
                href = unquote(match.group(1))
        if not href.startswith("http"):
            continue
        domain = normalize_domain(href)
        if domain not in [d for d, _ in links]:
            links.append((domain, href))

    results = dedupe_results(links)
    rank, url = find_rank(results)
    return SourceResult(
        "duckduckgo_html",
        rank,
        url,
        len(results),
        [d for d, _ in results[:15]],
    )


def iso_week_id(when: datetime) -> str:
    year, week, _ = when.isocalendar()
    return f"{year}-W{week:02d}"


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    rows: list[dict] = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def append_history(snapshot: Snapshot) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(snapshot), ensure_ascii=False) + "\n")


def week_ago_snapshot(history: list[dict], week_id: str) -> dict | None:
    if not history:
        return None
    current_year, current_week = week_id.split("-W")
    current_week = int(current_week)
    for row in reversed(history):
        row_week = row.get("week_id", "")
        if row_week == week_id:
            continue
        try:
            _, prev_week = row_week.split("-W")
            if row_week.startswith(current_year) and int(prev_week) < current_week:
                return row
            if row_week < week_id:
                return row
        except ValueError:
            continue
    return history[-1] if len(history) == 1 else None


def build_snapshot(sources: list[SourceResult]) -> Snapshot:
    now = datetime.now(UTC)
    primary = next((s for s in sources if s.rank is not None), None)
    if primary is None:
        primary = sources[0] if sources else None
    return Snapshot(
        captured_at_utc=now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        keyword=KEYWORD,
        locale=LOCALE,
        target_domain=TARGET_DOMAIN,
        sources=sources,
        primary_rank=primary.rank if primary else None,
        primary_source=primary.source if primary else None,
        week_id=iso_week_id(now.astimezone(TR_TZ)),
    )


def format_rank(rank: int | None) -> str:
    if rank is None:
        return "İlk 100 içinde görünmüyor"
    if rank == 1:
        return "1. sırada"
    return f"{rank}. sırada"


def delta_text(current: int | None, previous: int | None) -> str:
    if previous is None:
        return "İlk ölçüm — haftalık karşılaştırma bir sonraki çalıştırmada oluşacak"
    if current is None:
        return f"Önceki hafta {previous}. sıradaydı; bu hafta ilk 100 içinde görünmüyor"
    diff = previous - current
    if diff == 0:
        return "Değişim yok (önceki haftayla aynı)"
    if diff > 0:
        return f"{diff} sıra yükseldi (önceki: {previous} → şimdi: {current})"
    return f"{abs(diff)} sıra düştü (önceki: {previous} → şimdi: {current})"


def write_weekly_report(snapshot: Snapshot, history: list[dict]) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / f"{snapshot.week_id}-serp-led-ekran-weekly.md"
    prev = week_ago_snapshot(history, snapshot.week_id)
    prev_rank = prev.get("primary_rank") if prev else None

    tr_now = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M TR")
    lines = [
        f"# SERP Haftalık Rapor — «{KEYWORD}»",
        "",
        f"- Rapor haftası: **{snapshot.week_id}**",
        f"- Ölçüm zamanı: {tr_now} ({snapshot.captured_at_utc})",
        f"- Hedef site: **{TARGET_DOMAIN}**",
        f"- Locale: {LOCALE}",
        "",
        "## Özet",
        "",
        f"- **Birincil sıra (Google proxy / Startpage):** {format_rank(snapshot.primary_rank)}",
    ]
    if snapshot.primary_rank and snapshot.sources:
        primary_src = next(s for s in snapshot.sources if s.source == snapshot.primary_source)
        if primary_src and primary_src.target_url:
            lines.append(f"- Sıralanan URL: {primary_src.target_url}")
    lines.extend(
        [
            f"- **Haftalık değişim:** {delta_text(snapshot.primary_rank, prev_rank)}",
            "",
            "## Kaynak detayı",
            "",
            "| Kaynak | Sıra | Sonuç sayısı | Not |",
            "|---|---:|---:|---|",
        ]
    )
    for src in snapshot.sources:
        note = "—" if not src.error else src.error
        lines.append(
            f"| {src.source} | {src.rank if src.rank is not None else '—'} | {src.results_count} | {note} |"
        )

    lines.extend(["", "## İlk 10 rakip (Startpage)", ""])
    startpage = next((s for s in snapshot.sources if s.source == "startpage_google_proxy"), None)
    if startpage and startpage.top_domains:
        for idx, domain in enumerate(startpage.top_domains[:10], start=1):
            mark = " ← **ledajans**" if TARGET_DOMAIN in domain else ""
            lines.append(f"{idx}. {domain}{mark}")
    else:
        lines.append("- Startpage sonucu alınamadı.")

    lines.extend(
        [
            "",
            "## Metodoloji",
            "",
            "- Birincil ölçüm: [Startpage](https://www.startpage.com/) (`region=tr-tr`, `language=turkish`) — Google sonuçlarına yakın proxy.",
            "- Doğrulama: DuckDuckGo HTML (`kl=tr-tr`).",
            "- Resmi Google Search Console / rank tracker API kullanılmıyor; kişiselleştirme ve SERP özellikleri (reklam, snippet) sonucu değiştirebilir.",
            "- Otomasyon: `python3 AGENT-HUB/serp_rank_tracker.py` (cron ile haftalık özet + günlük snapshot).",
            "",
            "## Geçmiş ölçümler",
            "",
        ]
    )
    recent = history[-8:]
    if recent:
        lines.append("| Hafta | UTC zaman | Birincil sıra | Kaynak |")
        lines.append("|---|---|---:|---|")
        for row in recent:
            lines.append(
                f"| {row.get('week_id', '—')} | {row.get('captured_at_utc', '—')} "
                f"| {row.get('primary_rank', '—')} | {row.get('primary_source', '—')} |"
            )
    else:
        lines.append("- İlk ölçüm; geçmiş satır yok.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def write_daily_snapshot_markdown(snapshot: Snapshot) -> Path:
    date_prefix = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    path = REPORTS / f"{date_prefix}-serp-led-ekran.md"
    startpage = next((s for s in snapshot.sources if s.source == "startpage_google_proxy"), None)
    ddg = next((s for s in snapshot.sources if s.source == "duckduckgo_html"), None)
    content = f"""# SERP Snapshot — «{KEYWORD}» — {date_prefix}

- Hedef: **{TARGET_DOMAIN}**
- Google proxy (Startpage): **{format_rank(startpage.rank if startpage else None)}**
- DuckDuckGo: **{format_rank(ddg.rank if ddg else None)}**
- Haftalık rapor: `AGENT-HUB/REPORTS/{snapshot.week_id}-serp-led-ekran-weekly.md`

## Hızlı sonuç

ledajans.com, «{KEYWORD}» aramasında Startpage (tr-TR) ölçümünde **{format_rank(snapshot.primary_rank)}**.
"""
    path.write_text(content, encoding="utf-8")
    return path


def run(write_report: bool = True) -> int:
    sources = [fetch_startpage(), fetch_duckduckgo()]
    snapshot = build_snapshot(sources)
    history = load_history()
    append_history(snapshot)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_SNAPSHOT.write_text(
        json.dumps(asdict(snapshot), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if write_report:
        weekly = write_weekly_report(snapshot, history)
        daily = write_daily_snapshot_markdown(snapshot)
        print(f"primary_rank={snapshot.primary_rank}")
        print(f"weekly_report={weekly}")
        print(f"daily_snapshot={daily}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="led ekran SERP sıra takibi")
    parser.add_argument("--no-report", action="store_true", help="Yalnızca history kaydı")
    args = parser.parse_args()
    return run(write_report=not args.no_report)


if __name__ == "__main__":
    raise SystemExit(main())
