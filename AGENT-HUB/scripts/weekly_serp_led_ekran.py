#!/usr/bin/env python3
"""Haftalık 'led ekran' Google sırası kaydı (repo: ledajans.com).

Otomatik SERP kazıma veri merkezi IP'lerinde genelde engellenir; sıra değeri için:
  - Ortam: LEDAJANS_LED_EKRAN_GOOGLE_RANK (örn. 4 veya 12.3 GSC ortalaması)
  - Dosya: AGENT-HUB/REPORTS/serp-led-ekran-manual.json (örnek: serp-led-ekran-manual.example.json)

Aynı ISO haftada ikinci kez yazmaz; --force ile yeniden eklenir.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/workspace")
REPORTS = WORKSPACE / "AGENT-HUB" / "REPORTS"
LOG = REPORTS / "serp-led-ekran-weekly-log.md"
MANUAL = REPORTS / "serp-led-ekran-manual.json"
ENV_KEY = "LEDAJANS_LED_EKRAN_GOOGLE_RANK"


def _iso_week(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _last_logged_week(content: str) -> str | None:
    rows = [ln for ln in content.splitlines() if ln.startswith("| ") and "ISO hafta" not in ln and "---" not in ln]
    if not rows:
        return None
    last = rows[-1]
    m = re.match(r"\|\s*([^|]+)\|", last)
    return m.group(1).strip() if m else None


def _resolve_rank() -> tuple[str, str]:
    env = os.environ.get(ENV_KEY, "").strip()
    if env:
        return env, "env"
    if MANUAL.is_file():
        try:
            data = json.loads(MANUAL.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "N/A", "manual_json_hatali"
        pos = data.get("google_avg_position")
        if pos is None:
            return "N/A", "manual_json_bos"
        return str(pos), data.get("source", "manual_json")
    return "N/A", "otomatik_olcum_yok"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="Bu hafta için ikinci satır ekle")
    args = p.parse_args()

    now = datetime.now(timezone.utc)
    week = _iso_week(now)
    rank, source = _resolve_rank()
    note_tr = (
        "Veri merkezi çıkışlı ham SERP çekimi Google/Bing/Yandex tarafında bot doğrulamasına takıldı; "
        "kesin sıra için Search Console (sorgu: led ekran) ortalama konumunu kullanın."
    )
    if rank != "N/A" and source != "otomatik_olcum_yok":
        note_tr = "Manuel veya ortam değişkeni ile girildi; doğrulama: GSC / rank tracker önerilir."

    REPORTS.mkdir(parents=True, exist_ok=True)
    header = (
        "# led ekran — haftalık sıra günlüğü (ledajans.com)\n\n"
        "Kolonlar: ISO hafta, ölçüm UTC tarihi, anahtar kelime, raporlanan değer, kaynak, not.\n\n"
        "| ISO hafta | Tarih (UTC) | Anahtar kelime | Değer | Kaynak | Not |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    )

    if not LOG.is_file():
        LOG.write_text(header, encoding="utf-8")

    body = LOG.read_text(encoding="utf-8")
    if not body.lstrip().startswith("#"):
        body = header + body

    last_w = _last_logged_week(body)
    if last_w == week and not args.force:
        print(f"OK: Bu ISO hafta ({week}) zaten kayıtlı; atlanıyor. --force ile tekrar ekleyin.")
        return 0

    row = (
        f"| {week} | {now.strftime('%Y-%m-%d %H:%M')} | led ekran | {rank} | {source} | {note_tr} |\n"
    )
    if not body.endswith("\n"):
        body += "\n"
    LOG.write_text(body + row, encoding="utf-8")
    print(f"OK: {LOG.relative_to(WORKSPACE)} güncellendi ({week}, değer={rank}, kaynak={source}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
