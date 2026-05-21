#!/usr/bin/env python3
"""led ekran sorgusu için ledajans.com organik sıra ölçümü (DuckDuckGo HTML).

Google SERP bu ortamda CAPTCHA/429 verdiği için doğrudan ölçülemez; bu betik
DuckDuckGo html.duckduckgo.com sonuçlarını ayrıştırır. Google sırası için
Search Console veya ücretli SERP API kullanılmalıdır.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from html import unescape
from pathlib import Path

HUB = Path("/workspace/AGENT-HUB")
DATA = HUB / "data"
REPORTS = HUB / "REPORTS"
JSONL = DATA / "serp-led-ekran-ledajans.jsonl"
LATEST_MD = REPORTS / "serp-led-ekran-ledajans-SON.md"
WEEKLY_MD = REPORTS / "serp-led-ekran-haftalik.md"

KEYWORD = "led ekran"
TARGET_HOST = "ledajans.com"
DDG_URL = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(KEYWORD)


def ddg_real_url(href: str) -> str:
    if not href:
        return ""
    href = unescape(href)
    if "uddg=" in href:
        m = re.search(r"uddg=([^&]+)", href)
        if m:
            return urllib.parse.unquote(m.group(1))
    if href.startswith("//"):
        return "https:" + href
    return href


def fetch_ddg_html() -> str:
    req = urllib.request.Request(
        DDG_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_first_ledajans_position(html: str) -> tuple[int | None, str]:
    """İlk organik sonuç sırası (1 tabanlı) ve eşleşen URL."""
    seen: set[str] = set()
    ordered: list[str] = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', html):
        raw = m.group(1)
        u = ddg_real_url(raw).lower().strip()
        if not u or u in seen:
            continue
        seen.add(u)
        ordered.append(u)

    for i, u in enumerate(ordered, start=1):
        if TARGET_HOST in u:
            return i, u
    return None, ""


def append_jsonl(record: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with JSONL.open("a", encoding="utf-8") as f:
        f.write(line)


def load_jsonl() -> list[dict]:
    if not JSONL.exists():
        return []
    out: list[dict] = []
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def rebuild_weekly(rows: list[dict]) -> str:
    """ISO hafta (Europe/Istanbul takvim günü) ile gruplanmış özet."""
    by_week: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for r in rows:
        try:
            dt = datetime.fromisoformat(r["ts_tr"])
        except (KeyError, ValueError):
            continue
        y, w, _ = dt.isocalendar()
        by_week[(y, w)].append(r)

    lines = [
        "# led ekran — haftalık sıra özeti (ledajans.com)",
        "",
        "> Kaynak: DuckDuckGo HTML organik liste. Google ile farklılık gösterebilir.",
        "",
    ]
    for (y, w) in sorted(by_week.keys(), reverse=True):
        items = sorted(by_week[(y, w)], key=lambda x: x.get("ts_tr", ""))
        poss = [x["position"] for x in items if x.get("position") is not None]
        if not poss:
            continue
        lines.append(f"## ISO hafta {y}-W{w:02d}")
        lines.append("")
        lines.append(f"- Ölçüm sayısı: {len(poss)}")
        lines.append(f"- Sıra aralığı: {min(poss)} – {max(poss)}")
        lines.append(f"- Son ölçüm: {items[-1].get('ts_tr', '?')} → **{items[-1].get('position', '?')}**")
        lines.append("")
    if len(lines) <= 4:
        lines.append("_Henüz haftalık kayıt yok._")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_latest(record: dict, position: int | None, matched: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    pos_txt = str(position) if position is not None else "İlk 10 organik sonuçta yok"
    body = "\n".join(
        [
            "# led ekran — ledajans.com sıra (son ölçüm)",
            "",
            "| Alan | Değer |",
            "|------|-------|",
            f"| Ölçüm zamanı (TR) | {record['ts_tr']} |",
            f"| Anahtar kelime | `{KEYWORD}` |",
            f"| Motor (proxy) | DuckDuckGo HTML |",
            f"| **Sıra** | **{pos_txt}** |",
            f"| Eşleşen URL | {matched or '—'} |",
            "",
            "## Google hakkında",
            "",
            "Bu depo ortamında Google arama sonuç sayfası otomatik çekilemedi "
            "(CAPTCHA / çok fazla istek). Resmi Google sırası için "
            "[Search Console](https://search.google.com/search-console) "
            "Performans raporuna bakın veya SERP API kullanın.",
            "",
            "## Haftalık takip",
            "",
            f"Geçmiş ve haftalık özet: [`serp-led-ekran-haftalik.md`](serp-led-ekran-haftalik.md) "
            f"(veri: [`data/serp-led-ekran-ledajans.jsonl`](../data/serp-led-ekran-ledajans.jsonl)).",
            "",
            "Cron veya otomasyon için:",
            "",
            "```bash",
            "cd /workspace && python3 AGENT-HUB/keyword_serp_led_ekran.py",
            "```",
            "",
        ]
    )
    LATEST_MD.write_text(body, encoding="utf-8")


def main() -> int:
    from zoneinfo import ZoneInfo

    tr = ZoneInfo("Europe/Istanbul")
    now_tr = datetime.now(tr)
    now_utc = datetime.now(UTC)
    ts_tr = now_tr.isoformat(timespec="seconds")
    ts_utc = now_utc.isoformat(timespec="seconds").replace("+00:00", "Z")

    try:
        html = fetch_ddg_html()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"HATA: DDG isteği başarısız: {e}")
        return 1

    position, matched = parse_first_ledajans_position(html)
    record = {
        "ts_utc": ts_utc,
        "ts_tr": ts_tr,
        "keyword": KEYWORD,
        "engine": "duckduckgo_html",
        "position": position,
        "matched_url": matched,
    }
    append_jsonl(record)
    write_latest(record, position, matched)

    all_rows = load_jsonl()
    WEEKLY_MD.write_text(rebuild_weekly(all_rows), encoding="utf-8")

    if position is not None:
        print(f"DDG organik sıra: {position} ({matched})")
    else:
        print("DDG: ledajans.com ilk sonuç sayfasında bulunamadı")
    print(f"Yazıldı: {LATEST_MD} , {WEEKLY_MD} , {JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
