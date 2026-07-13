#!/usr/bin/env python3
"""Indeks triage ozet — INDEXING-ACTION planindaki URL siniflarini raporla."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import os
from datetime import datetime, timezone

ACTION = AGENT_HUB / "docs" / "INDEXING-ACTION-2026-07-12.md"
TRIAGE = AGENT_HUB / "docs" / "INDEXING-TRIAGE-2026-06-05.md"
REPORT = AGENT_HUB / "REPORTS" / "index-triage-summary-latest.md"

SUMMARY = """# Indeks Triage Ozet — {ts}

Kaynak: INDEXING-TRIAGE-2026-06-05 (463 URL, 390 tarandi-indekslenmedi)

## Siniflar ve aksiyon

| Sinif | Ornek | Aksiyon | Arac |
|-------|-------|---------|------|
| Tag/attachment/tarih arsivi | /tag/, ?attachment_id= | noindex | RankMath toplu |
| Thin SEO sayfa | /rehber/ cakismasi | 301 veya 300+ kelime genislet | fix-rehber-flat-permalinks.py |
| Degerli long-tail | /pitch-led-nedir/ vb. | ic link + hub baglantisi | deploy-to-wordpress.py |
| Duplicate canonical | /izmir-led-ekran/ cakismasi | canonical duzelt | CANONICAL-REGISTRY.md |
| Para sayfa | /led-ekran/ hub | index, cornerstone | set-rankmath-cornerstone.py |

## Bu sprint tamamlanan

- robots.txt crawl butcesi kurallari (canli)
- Hub + para sayfa ic link kumesi
- 7 yeni landing (sehir + referans + seffaf + sahne kiralama)
- ic-link-haritasi guncellendi

## Sonraki olcum

1. GSC Coverage → "Tarandi, indekslenmedi" sayisi (2 haftada bir)
2. Yeni slug'lar icin URL Denetimi istegi
3. Dusuk degerli URL'ler icin RankMath noindex batch

Detay: {action}
"""


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = SUMMARY.format(ts=ts, action=os.path.basename(ACTION))
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"OK: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
