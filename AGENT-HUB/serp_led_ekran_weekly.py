#!/usr/bin/env python3
"""
ledajans.com için 'led ekran' Google (tr) organik sıra anlık görüntüsü.

Bulut/datacenter IP'lerinden doğrudan Google HTML çekimi genelde 403/CAPTCHA
ürettiği için varsayılan kaynak SerpAPI'dir (https://serpapi.com).

Kullanım:
  export SERPAPI_API_KEY="..."   # zorunlu (canlı sıra için)
  python3 AGENT-HUB/serp_led_ekran_weekly.py

Haftalık cron örneği (Pazartesi 09:00 Europe/Istanbul):
  0 9 * * 1 cd /workspace && python3 AGENT-HUB/serp_led_ekran_weekly.py >>/tmp/serp-led-ekran.log 2>&1
"""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import requests

HUB = Path("/workspace/AGENT-HUB")
OUT_JSONL = HUB / "REPORTS" / "serp-led-ekran-weekly.jsonl"
OUT_MD = HUB / "REPORTS" / "serp-led-ekran-weekly-latest.md"
TARGET_HOST = "ledajans.com"
QUERY = "led ekran"
SERPAPI_URL = "https://serpapi.com/search.json"


def fetch_serpapi_rank(api_key: str) -> tuple[int | None, str | None, list[dict]]:
    params = {
        "engine": "google",
        "q": QUERY,
        "hl": "tr",
        "gl": "tr",
        "google_domain": "google.com.tr",
        "num": "100",
        "api_key": api_key,
    }
    r = requests.get(SERPAPI_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    organic = data.get("organic_results") or []
    for i, item in enumerate(organic, start=1):
        link = (item.get("link") or "").lower()
        if TARGET_HOST in link:
            return i, item.get("link"), organic[:10]
    return None, None, organic[:10]


def main() -> int:
    api_key = (os.environ.get("SERPAPI_API_KEY") or "").strip()
    captured = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    record: dict = {
        "captured_at_utc": captured,
        "query": QUERY,
        "target_host": TARGET_HOST,
        "source": "serpapi_google",
        "locale": "hl=tr&gl=tr&google_domain=google.com.tr",
        "rank": None,
        "matched_url": None,
        "error": None,
        "top_sample": None,
    }

    if not api_key:
        record["error"] = "SERPAPI_API_KEY tanımlı değil; canlı sıra çekilmedi."
    else:
        try:
            rank, url, top = fetch_serpapi_rank(api_key)
            record["rank"] = rank
            record["matched_url"] = url
            record["top_sample"] = [
                {"position": j + 1, "link": (top[j] or {}).get("link")}
                for j in range(min(5, len(top)))
            ]
        except requests.HTTPError as e:
            record["error"] = f"HTTP {e.response.status_code if e.response else '?'}: {e}"
        except Exception as e:  # noqa: BLE001
            record["error"] = str(e)

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    rank = record["rank"]
    err = record["error"]
    lines = [
        "# led ekran — ledajans.com SERP özeti",
        "",
        f"- **Ölçüm zamanı (UTC):** {captured}",
        f"- **Sorgu:** `{QUERY}`",
        f"- **Kaynak:** SerpAPI → Google (`google.com.tr`, tr)",
        "",
    ]
    if rank is not None:
        lines.append(f"- **İlk eşleşen organik sıra:** **{rank}**")
        if record.get("matched_url"):
            lines.append(f"- **URL:** {record['matched_url']}")
    elif err:
        lines.append(f"- **Durum:** {err}")
    else:
        lines.append("- **Durum:** İlk 100 organik sonuçta ledajans.com bulunamadı.")

    lines.append("")
    lines.append("Not: GSC'deki “ortalama konum” ile klasik “kaçıncı sıra” birebir aynı değildir.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if not err or "tanımlı değil" in err else 1


if __name__ == "__main__":
    sys.exit(main())
