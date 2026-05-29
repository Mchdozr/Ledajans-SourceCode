#!/usr/bin/env python3
"""Haftalık Google SERP sıra takibi — ledajans.com / led ekran."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

HUB = Path("/workspace/AGENT-HUB")
DATA_DIR = HUB / "data"
REPORTS = HUB / "REPORTS"
HISTORY_FILE = DATA_DIR / "serp-rank-history.json"

DEFAULT_KEYWORD = "led ekran"
DEFAULT_DOMAIN = "ledajans.com"
DEFAULT_LOCALE = "tr-TR"
DEFAULT_DEVICE = "desktop"


@dataclass
class OrganicResult:
    rank: int
    url: str
    domain: str
    title: str


@dataclass
class Measurement:
    date: str
    captured_at_utc: str
    keyword: str
    locale: str
    device: str
    search_engine: str
    serp_source: str
    rank_position: int | None
    target_url: str | None
    target_domain: str
    in_top_100: bool
    top_10: list[dict[str, str | int]]
    delta_vs_previous: int | None
    note: str


def normalize_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return host.removeprefix("www.")


def fetch_via_serpapi(keyword: str, api_key: str) -> tuple[list[OrganicResult], str]:
    params = {
        "engine": "google",
        "q": keyword,
        "google_domain": "google.com.tr",
        "gl": "tr",
        "hl": "tr",
        "num": 100,
        "api_key": api_key,
    }
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    organic: list[OrganicResult] = []
    seen: set[str] = set()
    for item in payload.get("organic_results", []):
        link = item.get("link") or ""
        domain = normalize_domain(link)
        if not domain or domain in seen:
            continue
        seen.add(domain)
        organic.append(
            OrganicResult(
                rank=len(organic) + 1,
                url=link,
                domain=domain,
                title=(item.get("title") or "")[:120],
            )
        )
    return organic, "serpapi"


def fetch_via_startpage(keyword: str) -> tuple[list[OrganicResult], str]:
    url = f"https://www.startpage.com/sp/search?query={quote(keyword)}&language=tr"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=45)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    organic: list[OrganicResult] = []
    seen: set[str] = set()
    for block in soup.select("div.result"):
        anchor = block.select_one("a.result-link") or block.select_one("a[href^='http']")
        if not anchor:
            continue
        href = (anchor.get("href") or "").strip()
        if not href.startswith("http"):
            continue
        domain = normalize_domain(href)
        if not domain or domain in seen:
            continue
        seen.add(domain)
        title_el = block.select_one("h2") or block.select_one("p.w-gl__title")
        title = title_el.get_text(strip=True) if title_el else anchor.get_text(strip=True)
        organic.append(
            OrganicResult(
                rank=len(organic) + 1,
                url=href,
                domain=domain,
                title=title[:120],
            )
        )
    if not organic:
        raise RuntimeError("Startpage sonuç ayrıştırılamadı (HTML yapısı değişmiş olabilir).")
    return organic, "startpage"


def fetch_organic(keyword: str) -> tuple[list[OrganicResult], str]:
    api_key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if api_key:
        return fetch_via_serpapi(keyword, api_key)
    return fetch_via_startpage(keyword)


def find_target(organic: list[OrganicResult], domain: str) -> tuple[int | None, str | None]:
    needle = domain.lower().removeprefix("www.")
    for row in organic:
        if needle in row.domain or row.domain.endswith(needle):
            return row.rank, row.url
    return None, None


def load_history() -> dict:
    if not HISTORY_FILE.exists():
        return {"keyword": DEFAULT_KEYWORD, "target_domain": DEFAULT_DOMAIN, "measurements": []}
    return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))


def save_history(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def previous_rank(history: dict, keyword: str) -> int | None:
    matches = [
        m["rank_position"]
        for m in history.get("measurements", [])
        if m.get("keyword") == keyword and isinstance(m.get("rank_position"), int)
    ]
    return matches[-1] if matches else None


def build_measurement(
    keyword: str,
    domain: str,
    locale: str,
    device: str,
    organic: list[OrganicResult],
    source: str,
    prev_rank: int | None,
) -> Measurement:
    rank, target_url = find_target(organic, domain)
    delta = None
    if rank is not None and prev_rank is not None:
        delta = prev_rank - rank
    note = ""
    if source == "startpage":
        note = (
            "Startpage üzerinden Google proxy; gerçek Google TR SERP ile küçük farklar olabilir. "
            "Kesin ölçüm için SERPAPI_API_KEY tanımlayın."
        )
    now = datetime.now(UTC)
    return Measurement(
        date=now.strftime("%Y-%m-%d"),
        captured_at_utc=now.isoformat(timespec="seconds"),
        keyword=keyword,
        locale=locale,
        device=device,
        search_engine="google",
        serp_source=source,
        rank_position=rank,
        target_url=target_url,
        target_domain=domain,
        in_top_100=rank is not None,
        top_10=[asdict(r) for r in organic[:10]],
        delta_vs_previous=delta,
        note=note,
    )


def render_report(m: Measurement) -> str:
    rank_text = str(m.rank_position) if m.rank_position is not None else "100+"
    delta_line = ""
    if m.delta_vs_previous is not None:
        if m.delta_vs_previous > 0:
            delta_line = f"- Haftalık değişim: **{m.delta_vs_previous} sıra yükseldi** (önceki → şimdi)"
        elif m.delta_vs_previous < 0:
            delta_line = f"- Haftalık değişim: **{abs(m.delta_vs_previous)} sıra düştü**"
        else:
            delta_line = "- Haftalık değişim: değişmedi"
    else:
        delta_line = "- Haftalık değişim: ilk ölçüm (karşılaştırma yok)"

    lines = [
        f"# Haftalık SERP Raporu — {m.keyword}",
        "",
        f"- Tarih (UTC): {m.captured_at_utc}",
        f"- Site: **{m.target_domain}**",
        f"- Anahtar kelime: **{m.keyword}**",
        f"- Organik sıra: **{rank_text}**",
        f"- Hedef URL: {m.target_url or '—'}",
        f"- Kaynak: `{m.serp_source}` | Locale: `{m.locale}` | Cihaz: `{m.device}`",
        delta_line,
        "",
        "## İlk 10 organik sonuç",
        "",
        "| Sıra | Domain | Başlık |",
        "|---:|---|---|",
    ]
    for row in m.top_10:
        mark = " **← LEDAJANS**" if m.target_domain in str(row.get("domain", "")) else ""
        title = re.sub(r"\|", "/", str(row.get("title", "")))[:70]
        lines.append(f"| {row['rank']} | {row['domain']} | {title}{mark} |")
    lines.extend(["", "## Not", "", m.note or "—", ""])
    return "\n".join(lines)


def report_path_for(date_str: str) -> Path:
    slug = DEFAULT_KEYWORD.replace(" ", "-")
    return REPORTS / f"{date_str}-serp-weekly-{slug}.md"


def run(keyword: str, domain: str, locale: str, device: str, dry_run: bool) -> Measurement:
    history = load_history()
    prev = previous_rank(history, keyword)
    organic, source = fetch_organic(keyword)
    measurement = build_measurement(keyword, domain, locale, device, organic, source, prev)

    if dry_run:
        print(json.dumps(asdict(measurement), ensure_ascii=False, indent=2))
        return measurement

    history["keyword"] = keyword
    history["target_domain"] = domain
    history.setdefault("measurements", []).append(asdict(measurement))
    save_history(history)

    report = render_report(measurement)
    path = report_path_for(measurement.date)
    REPORTS.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")

    latest = HUB / "SERP-RANK-LATEST.md"
    latest.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nKayıt: {HISTORY_FILE}")
    print(f"Rapor: {path}")
    return measurement


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="led ekran haftalık SERP sıra raporu")
    parser.add_argument("--keyword", default=DEFAULT_KEYWORD)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--locale", default=DEFAULT_LOCALE)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        m = run(args.keyword, args.domain, args.locale, args.device, args.dry_run)
    except Exception as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1

    if m.rank_position is None:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
