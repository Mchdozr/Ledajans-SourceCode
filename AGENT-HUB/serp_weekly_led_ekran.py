#!/usr/bin/env python3
"""
Haftalık 'led ekran' sorgusunda ledajans.com organik sırası (DuckDuckGo Lite, kl=tr-tr).

Google Türkiye ile aynı sonuç listesi garanti edilmez; GSC veya resmi rank API ile doğrulama önerilir.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "AGENT-HUB" / "REPORTS" / "serp-led-ekran-weekly-log.md"
DDG_LITE = "https://lite.duckduckgo.com/lite/"
KEYWORD = "led ekran"
TARGET_HOST = "ledajans.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_ddg_result_urls() -> list[str]:
    body = urllib.parse.urlencode({"q": KEYWORD, "kl": "tr-tr"}).encode()
    req = urllib.request.Request(
        DDG_LITE,
        data=body,
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    return re.findall(
        r'<a rel="nofollow" href="(https?://[^"]+)" class=\'result-link\'>',
        html,
    )


def rank_for_target(urls: list[str], host: str) -> tuple[int | None, str | None]:
    host_l = host.lower()
    for i, raw in enumerate(urls, start=1):
        try:
            netloc = urllib.parse.urlparse(raw).netloc.lower()
        except ValueError:
            continue
        if netloc == host_l or netloc.endswith("." + host_l):
            return i, raw
    return None, None


def iso_week_id(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def log_already_has_week(log_text: str, week_id: str) -> bool:
    return f"| {week_id} |" in log_text


def ensure_log_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Haftalık SERP — led ekran → ledajans.com\n\n"
        "Ölçüm: DuckDuckGo Lite, bölge `tr-tr`. Google sıralaması farklı olabilir.\n\n"
        "| ISO Hafta | Tarih (UTC) | Sıra | URL |\n"
        "|-------------|-------------|------|-----|\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bu hafta için zaten kayıt olsa bile yeni satır ekle.",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    week_id = iso_week_id(now)
    stamp = now.strftime("%Y-%m-%d %H:%M")

    urls = fetch_ddg_result_urls()
    if not urls:
        print("SERP_ERR: sonuç URL listesi boş", file=sys.stderr)
        return 2

    pos, hit_url = rank_for_target(urls, TARGET_HOST)
    ensure_log_header(LOG_PATH)
    existing = LOG_PATH.read_text(encoding="utf-8")
    if not args.force and log_already_has_week(existing, week_id):
        print(f"SKIP: {week_id} için kayıt zaten var ({LOG_PATH})")
        print(f"INFO: son ölçüm sırası (tekrar hesaplandı): {pos}")
        return 0

    rank_disp = str(pos) if pos is not None else "— (ilk 10'da yok)"
    url_disp = hit_url or "—"
    line = f"| {week_id} | {stamp} | {rank_disp} | {url_disp} |\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)

    print(f"KEYWORD={KEYWORD!r} ENGINE=duckduckgo_lite kl=tr-tr WEEK={week_id}")
    print(f"RANK={pos} URL={hit_url}")
    print(f"LOG={LOG_PATH}")
    return 0 if pos is not None else 3


if __name__ == "__main__":
    raise SystemExit(main())
