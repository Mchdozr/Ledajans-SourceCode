#!/usr/bin/env python3
"""
Tekrarlanabilir 'led ekran' sıra snapshot'ı.

- Kaynak: Brave Search HTML (country=tr). Google ile birebir aynı değildir;
  Google konumu için GSC veya onaylı rank tracker gerekir.
- Çıktı: REPORTS/{tarih}-led-ekran-brave-snapshot.md + jsonl geçmişi.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/workspace")
HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
HISTORY = REPORTS / "led-ekran-brave-rank.jsonl"

QUERY = "led ekran"
TARGET_HOSTS = ("ledajans.com", "www.ledajans.com")
BRAVE_URL = (
    "https://search.brave.com/search?"
    + urllib.parse.urlencode({"q": QUERY, "country": "tr", "source": "web"})
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_brave_html() -> str:
    offline = os.environ.get("BRAVE_HTML_PATH", "").strip()
    if offline:
        return Path(offline).read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(
        BRAVE_URL,
        headers={
            "User-Agent": UA,
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        },
        method="GET",
    )
    last_err: Exception | None = None
    for attempt, delay in enumerate((0, 4, 16), start=1):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429 and attempt < 3:
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < 3:
                continue
            raise
    raise last_err  # pragma: no cover


def parse_ranked_netlocs(html: str) -> tuple[list[str], list[str]]:
    """site-name-wrapper bloklarından sıralı tekil netloc listesi + ham URL'ler."""
    parts = html.split("site-name-wrapper")
    raw_urls: list[str] = []
    for chunk in parts[1:]:
        m = re.search(r'href="(https?://[^"]+)"', chunk)
        if m:
            raw_urls.append(m.group(1))
    seen: set[str] = set()
    ranked: list[str] = []
    skip_if_sub = ("google.com", "gstatic.com", "youtube.com", "doubleclick.net")
    for u in raw_urls:
        netloc = urlparse(u).netloc.lower()
        if not netloc or netloc.endswith("brave.com"):
            continue
        if any(s in netloc for s in skip_if_sub):
            continue
        if netloc in seen:
            continue
        seen.add(netloc)
        ranked.append(netloc)
    return ranked, raw_urls


def rank_of_ledajans(ranked_netlocs: list[str]) -> int | None:
    for i, host in enumerate(ranked_netlocs, start=1):
        if host in TARGET_HOSTS or host.endswith(".ledajans.com"):
            return i
    return None


def write_snapshot_md(
    path: Path,
    *,
    captured_utc: str,
    ranked: list[str],
    position: int | None,
    error: str | None,
) -> None:
    lines = [
        f"# LED ekran — Brave Search (TR) snapshot — {captured_utc}",
        "",
        f"- **Sorgu:** `{QUERY}`",
        "- **Motor:** Brave Search (`country=tr`). **Google organik sıra değildir.**",
        "- **Yöntem:** `site-name-wrapper` içindeki ilk `href`, tekrarlayan `netloc` atlanır.",
        "",
    ]
    if error:
        lines.extend(["## Hata", "", f"```\n{error}\n```", ""])
    else:
        lines.extend(
            [
                "## Sonuç",
                "",
                f"- **ledajans.com tahmini sıra (Brave, tekil alan):** "
                f"{'**' + str(position) + '.**' if position else '_Bulunamadı_'}",
                "",
                "### İlk 15 tekil alan",
                "",
            ]
        )
        for i, h in enumerate(ranked[:15], start=1):
            lines.append(f"{i}. `{h}`")
        lines.append("")
    lines.extend(
        [
            "## Google için not",
            "",
            "Google `tr-TR` organik konum bu betikle ölçülmez. "
            "Search Console → Performans → sorgu `led ekran` → ortalama konum "
            "veya DataForSEO / SerpAPI gibi bir kaynak kullanın.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def append_history(record: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def weekly_summary_lines(now: dt.datetime) -> list[str]:
    if not HISTORY.exists():
        return ["Henüz geçmiş yok (`led-ekran-brave-rank.jsonl`)."]
    cutoff = now - dt.timedelta(days=7)
    rows: list[dict] = []
    for line in HISTORY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = r.get("captured_at_utc")
        if not ts:
            continue
        try:
            t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if t.replace(tzinfo=dt.timezone.utc) >= cutoff.replace(tzinfo=dt.timezone.utc):
            rows.append(r)
    if not rows:
        return ["Son 7 günde kayıt yok."]
    lines = ["| Tarih (UTC) | Brave sıra | Üst 5 alan |", "| --- | --- | --- |"]
    for r in sorted(rows, key=lambda x: x.get("captured_at_utc", "")):
        top5 = r.get("top5_netlocs") or []
        lines.append(
            f"| {r.get('captured_at_utc', '')} | {r.get('ledajans_rank_brave')} | "
            f"{', '.join(top5)} |"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weekly-md",
        action="store_true",
        help="Son 7 günü özetleyen markdown dosyası yaz (snapshot almaz).",
    )
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    date_slug = now.strftime("%Y-%m-%d")

    if args.weekly_md:
        REPORTS.mkdir(parents=True, exist_ok=True)
        wpath = REPORTS / f"{date_slug}-led-ekran-haftalik-brave-ozet.md"
        body = "\n".join(
            [
                f"# led ekran — haftalık Brave (TR) özet — {date_slug}",
                "",
                *weekly_summary_lines(now),
                "",
            ]
        )
        wpath.write_text(body, encoding="utf-8")
        print(f"Wrote {wpath}")
        return 0

    err: str | None = None
    ranked: list[str] = []
    try:
        html = fetch_brave_html()
        ranked, _ = parse_ranked_netlocs(html)
        pos = rank_of_ledajans(ranked)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        err = repr(e)
        pos = None

    captured = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    record = {
        "captured_at_utc": captured,
        "query": QUERY,
        "engine": "brave",
        "country": "tr",
        "ledajans_rank_brave": pos,
        "top5_netlocs": ranked[:5],
        "top15_netlocs": ranked[:15],
        "error": err,
    }
    append_history(record)

    md_path = REPORTS / f"{date_slug}-led-ekran-brave-snapshot.md"
    write_snapshot_md(md_path, captured_utc=captured, ranked=ranked, position=pos, error=err)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print(f"Wrote {md_path}")
    return 0 if not err else 1


if __name__ == "__main__":
    sys.exit(main())
