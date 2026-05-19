#!/usr/bin/env python3
"""
ledajans.com için 'led ekran' anahtar kelimesinde organik sıra özeti.

Önemli: Google arama sonuçları bu ortamda güvenilir biçimde çekilemediği için
varsayılan kaynak DuckDuckGo HTML organik listesidir (Google ile birebir aynı değildir).
Google sırası için Search Console veya imzalı bir rank tracker kullanın.
"""
from __future__ import annotations

import datetime as dt
import re
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path("/workspace")
REPORT = ROOT / "AGENT-HUB" / "REPORTS" / "SERP-haftalik-led-ekran-ledajans.md"

KEYWORD = "led ekran"
DOMAIN = "ledajans.com"
ENGINE_LABEL = "DuckDuckGo HTML (organik, Google değildir)"

ROW_RE = re.compile(
    r"^\|\s*(?P<week>\d{4}-W\d{2})\s*\|\s*(?P<stamp>[^|]+)\|\s*(?P<rank>[^|]+)\|\s*(?P<url>[^|]+)\|\s*$"
)


def _fetch_ddg_links(query: str) -> list[str]:
    body = urllib.parse.urlencode({"q": query, "b": ""}).encode("utf-8")
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    raw = re.findall(r'class="result__a"[^>]+href="([^"]+)"', html)
    out: list[str] = []
    for href in raw:
        u = unescape(href)
        if "uddg=" in u:
            parsed = urllib.parse.urlparse(u)
            qs = urllib.parse.parse_qs(parsed.query)
            if "uddg" in qs:
                u = urllib.parse.unquote(qs["uddg"][0])
        out.append(u)
    return out


def _best_position(links: list[str], domain: str) -> tuple[str, str]:
    dom = domain.lower()
    for i, url in enumerate(links, start=1):
        if dom in url.lower():
            return str(i), url
    return "100+", f"(ilk {len(links)} sonuçta {DOMAIN} yok)"


def _iso_week_id(d: dt.datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _header() -> str:
    return "\n".join(
        [
            "# SERP — led ekran → ledajans.com (haftalık iz)",
            "",
            f"- **Ölçüm kaynağı:** {ENGINE_LABEL}",
            "- **Google uyarısı:** Bu tablo Google sırasını garanti etmez; GSC / rank tracker ile doğrulayın.",
            "- **Güncelleme kuralı:** Aynı ISO hafta içinde ilgili satır güncellenir; yeni haftada yeni satır eklenir.",
            "",
            "| ISO hafta | Son ölçüm (UTC) | Sıra | İlk eşleşen URL |",
            "| --- | --- | --- | --- |",
        ]
    )


def _parse_rows(text: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        rows.append(
            (
                m.group("week").strip(),
                m.group("stamp").strip(),
                m.group("rank").strip(),
                m.group("url").strip(),
            )
        )
    return rows


def _upsert(rows: list[tuple[str, str, str, str]], week: str, stamp: str, rank: str, url: str) -> list[tuple[str, str, str, str]]:
    out = [r for r in rows if r[0] != week]
    out.append((week, stamp, rank, url))
    out.sort(key=lambda r: (r[0]))
    return out


def _render(rows: list[tuple[str, str, str, str]]) -> str:
    lines = [_header()]
    for w, s, r, u in rows:
        lines.append(f"| {w} | {s} | {r} | {u} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    links = _fetch_ddg_links(KEYWORD)
    rank, url = _best_position(links, DOMAIN)
    now = dt.datetime.now(dt.UTC)
    stamp = now.strftime("%Y-%m-%d %H:%M")
    week = _iso_week_id(now)

    print(f"week={week} rank={rank} url={url}")

    existing: list[tuple[str, str, str, str]] = []
    if REPORT.exists():
        existing = _parse_rows(REPORT.read_text(encoding="utf-8"))

    merged = _upsert(existing, week, stamp, rank, url)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(_render(merged), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
