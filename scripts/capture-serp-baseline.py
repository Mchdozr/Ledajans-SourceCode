#!/usr/bin/env python3
"""Haftalık SERP snapshot: led ekran → SERP-BASELINE.csv + WEEKLY-MONITORING."""
from __future__ import annotations

import csv
import re
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
TARGET_HOST = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
LOCALE = "tr-TR"
DEVICE = "mobile"
MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)

CSV_FIELDS = [
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


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": MOBILE_UA,
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def decode_redirect_url(link: str) -> str:
    if link.startswith("//"):
        link = "https:" + link
    parsed = urllib.parse.urlparse(link)
    if "duckduckgo.com" in parsed.netloc and parsed.path == "/l/":
        target = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return urllib.parse.unquote(target)
    if "r.search.yahoo.com" in parsed.netloc:
        match = re.search(r"RU=(https[^/&]+)", link, re.IGNORECASE)
        if match:
            return urllib.parse.unquote(match.group(1))
    return link


def extract_domains(links: list[str]) -> list[str]:
    domains: list[str] = []
    for link in links:
        host = urllib.parse.urlparse(link).netloc.lower().removeprefix("www.")
        if host and host not in domains:
            domains.append(host)
    return domains


def rank_for_target(links: list[str]) -> int | None:
    for index, link in enumerate(links, start=1):
        if TARGET_HOST in link:
            return index
    return None


def rank_on_duckduckgo(query: str) -> tuple[int | None, list[str], str]:
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query) + "&kl=tr-tr"
    html = fetch(url)
    raw_links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', html)
    links = [decode_redirect_url(link) for link in raw_links]
    rank = rank_for_target(links)
    return rank, extract_domains(links)[:5], "duckduckgo_organic_mobile"


def rank_on_yahoo(query: str) -> tuple[int | None, list[str], str]:
    url = "https://search.yahoo.com/search?p=" + urllib.parse.quote(query) + "&vc=tr"
    html = fetch(url)
    raw_links = re.findall(r'<h3[^>]*><a[^>]+href="(https?://[^"]+)"', html)
    links = [decode_redirect_url(link) for link in raw_links if "scout.yahoo.com" not in link]
    rank = rank_for_target(links)
    return rank, extract_domains(links)[:5], "yahoo_bing_index_mobile"


def rank_on_google(query: str) -> tuple[int | None, str]:
    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote(query)
        + "&hl=tr&gl=tr&num=30"
    )
    try:
        html = fetch(url)
    except Exception as exc:  # noqa: BLE001
        return None, f"google_fetch_error:{exc.__class__.__name__}"

    blocked_markers = (
        "sıra dışı",
        "unusual traffic",
        "captcha",
        "enablejs",
    )
    if any(marker in html.lower() for marker in blocked_markers):
        return None, "google_blocked_captcha"

    links: list[str] = []
    for match in re.finditer(r'href="(https?://[^"#]+)"', html):
        link = match.group(1)
        if "google." in link or "gstatic" in link:
            continue
        if link not in links:
            links.append(link)

    for index, link in enumerate(links, start=1):
        if TARGET_HOST in link:
            return index, "google_organic_mobile"
    return None, "google_not_found_top30"


def read_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_google_gsc_position(rows: list[dict[str, str]]) -> str | None:
    for row in reversed(rows):
        if (
            row.get("query", "").strip().lower() == QUERY
            and row.get("search_engine", "").strip().lower() == "google"
            and row.get("source", "").startswith("gsc_performance")
            and row.get("rank_position")
        ):
            return row["rank_position"].strip()
    return None


def append_baseline_row(row: dict[str, str]) -> None:
    exists = BASELINE_PATH.exists()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_weekly_monitoring(
    captured_at: datetime,
    proxy_rank: int | None,
    proxy_source: str,
    google_rank: int | None,
    prior_gsc: str | None,
    competitors: list[str],
) -> Path:
    date_str = captured_at.strftime("%Y-%m-%d")
    path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{date_str}.md"
    prior_note = prior_gsc or "kayıt yok"
    delta = "n/a"
    if proxy_rank is not None and prior_gsc:
        try:
            delta = f"{proxy_rank - float(prior_gsc):+.2f} ({proxy_source} vs son GSC avg)"
        except ValueError:
            delta = "n/a"

    lines = [
        f"# Haftalık SEO İzleme — {date_str}",
        "",
        "## SERP — `led ekran`",
        "",
        f"- Ölçüm UTC: `{captured_at.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        f"- Hedef URL: `{TARGET_URL}`",
        f"- Locale / cihaz: `{LOCALE}` / `{DEVICE}`",
        f"- Proxy organik sıra ({proxy_source}): **{proxy_rank if proxy_rank is not None else 'bulunamadı'}**",
        f"- Google canlı organik sıra: **{google_rank if google_rank is not None else 'ölçülemedi (CAPTCHA/IP)'}**",
        f"- Son GSC avg position (Google): **{prior_note}**",
        f"- Delta notu: {delta}",
        "",
        f"### İlk 5 rakip domain ({proxy_source})",
        "",
    ]
    if competitors:
        for index, domain in enumerate(competitors, start=1):
            lines.append(f"{index}. `{domain}`")
    else:
        lines.append("- Veri yok")

    lines.extend(
        [
            "",
            "## Kayıt",
            "",
            f"- CSV: `AGENT-HUB/SERP-BASELINE.csv` (yeni satır eklendi)",
            "- Komut: `python3 scripts/capture-serp-baseline.py`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 scripts/capture-serp-baseline.py",
            "powershell -File scripts/run-weekly-seo-check.ps1",
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    captured_at = datetime.now(UTC).replace(microsecond=0)
    captured_at_str = captured_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    proxy_rank: int | None = None
    proxy_source = "unavailable"
    competitors: list[str] = []
    for probe in (rank_on_duckduckgo, rank_on_yahoo):
        candidate_rank, candidate_domains, candidate_source = probe(QUERY)
        if candidate_rank is not None:
            proxy_rank = candidate_rank
            proxy_source = candidate_source
            competitors = candidate_domains
            break
        if candidate_domains and not competitors:
            competitors = candidate_domains
            proxy_source = candidate_source

    google_rank, google_status = rank_on_google(QUERY)
    prior_rows = read_baseline_rows()
    prior_gsc = latest_google_gsc_position(prior_rows)

    primary_competitor = next((d for d in competitors if TARGET_HOST not in d), competitors[0] if competitors else "")
    competitor_rank = "2" if proxy_rank == 1 and len(competitors) > 1 else ""

    if google_rank is not None:
        rank_position = str(google_rank)
        search_engine = "google"
        source = google_status
        notes = (
            f"Google organik snapshot; proxy rank={proxy_rank or 'n/a'} ({proxy_source}); "
            f"son GSC avg={prior_gsc or 'n/a'}"
        )
    elif proxy_rank is not None:
        rank_position = str(proxy_rank)
        search_engine = "google"
        source = f"proxy_{proxy_source}_google_blocked"
        notes = (
            f"Google canlı ölçüm engellendi ({google_status}); "
            f"proxy rank={proxy_rank} via {proxy_source}; son GSC avg={prior_gsc or 'n/a'}; "
            f"rakipler={', '.join(competitors[:3])}"
        )
    else:
        rank_position = prior_gsc or "unavailable"
        search_engine = "google"
        source = "fallback_gsc_or_unavailable"
        notes = (
            f"Canlı SERP alınamadı (google={google_status}, proxy=fail); "
            f"son bilinen GSC avg={prior_gsc or 'yok'}"
        )

    row = {
        "captured_at_utc": captured_at_str,
        "query": QUERY,
        "locale": LOCALE,
        "device": DEVICE,
        "search_engine": search_engine,
        "target_url": TARGET_URL,
        "rank_position": rank_position,
        "serp_features": "",
        "primary_competitor": primary_competitor,
        "competitor_rank": competitor_rank,
        "source": source,
        "notes": notes,
    }

    duplicate = any(
        r.get("query", "").strip().lower() == QUERY
        and r.get("captured_at_utc", "").startswith(captured_at.strftime("%Y-%m-%d"))
        for r in prior_rows
    )
    if not duplicate:
        append_baseline_row(row)

    weekly_path = write_weekly_monitoring(
        captured_at, proxy_rank, proxy_source, google_rank, prior_gsc, competitors
    )

    print(f"query={QUERY}")
    print(f"proxy_rank={proxy_rank}")
    print(f"proxy_source={proxy_source}")
    print(f"google_rank={google_rank}")
    print(f"recorded_rank={rank_position}")
    print(f"source={source}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
