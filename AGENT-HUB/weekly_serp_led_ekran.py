#!/usr/bin/env python3
"""Haftalık 'led ekran' sıra notu: JSONL günlüğe yazar ve SERP-LED-EKRAN-RAPOR.md üretir.

Google organik SERP bu VM IP'lerinde genelde CAPTCHA/429 verdiği için varsayılan
ölçüm **manuel GSC** (serp-led-ekran-manual.json) veya env ile yapılır.

Çalıştırma (repo kökü):
  python3 AGENT-HUB/weekly_serp_led_ekran.py
  python3 AGENT-HUB/weekly_serp_led_ekran.py --force
  LED_EKRAN_MANUAL_JSON='{"source":"GSC","average_position":11.2}' python3 AGENT-HUB/weekly_serp_led_ekran.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HUB = Path("/workspace/AGENT-HUB")
DATA = HUB / "data"
JSONL = DATA / "serp-led-ekran-weekly.jsonl"
MANUAL = DATA / "serp-led-ekran-manual.json"
REPORT = HUB / "SERP-LED-EKRAN-RAPOR.md"
TR = ZoneInfo("Europe/Istanbul")


def iso_week_key(d: datetime) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def last_jsonl_week() -> str | None:
    if not JSONL.exists():
        return None
    lines = [ln for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1]).get("iso_week")
    except json.JSONDecodeError:
        return None


def try_ddg_lite_position(query: str, domain: str) -> tuple[int | None, str]:
    """DuckDuckGo Lite; başarısızlık sık (anomaly). Dönüş: (sıra veya None, ham_not)."""
    url = "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LEDAJANS-weekly-serp/1.0; +https://ledajans.com)",
            "Accept-Language": "tr-TR,tr;q=0.9",
        },
        method="GET",
    )
    try:
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        return None, f"istek_hatasi:{e}"

    if "anomaly.js" in html or "anomaly" in html[:8000]:
        return None, "ddg_lite_anomaly"

    links = re.findall(r"class='result-link'[^>]*href='([^']+)'", html)
    decoded: list[str] = []
    for L in links:
        full = "https:" + L if L.startswith("//") else L
        if "uddg=" in full:
            q = urllib.parse.urlparse(full).query
            params = urllib.parse.parse_qs(q)
            uddg = params.get("uddg", [""])[0]
            decoded.append(urllib.parse.unquote(uddg) if uddg else full)
        else:
            decoded.append(full)

    dom = domain.lower().replace("www.", "")
    for i, u in enumerate(decoded, 1):
        if dom in u.lower():
            return i, "ddg_lite_ok"
    return None, f"ddg_lite_not_found parsed_n={len(decoded)}"


def load_manual() -> dict | None:
    raw = os.environ.get("LED_EKRAN_MANUAL_JSON")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"_error": "LED_EKRAN_MANUAL_JSON parse hatası"}
    if MANUAL.exists():
        try:
            return json.loads(MANUAL.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"_error": "serp-led-ekran-manual.json parse hatası"}
    return None


def build_record(now_tr: datetime) -> dict:
    manual = load_manual()
    ddg_pos, ddg_note = try_ddg_lite_position("led ekran", "ledajans.com")

    rec: dict = {
        "captured_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "captured_at_tr": now_tr.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "iso_week": iso_week_key(now_tr),
        "keyword": "led ekran",
        "target_domain": "ledajans.com",
    }

    if manual and not manual.get("_error"):
        rec["google_proxy"] = None
        rec["manual_gsc"] = {
            "source": manual.get("source"),
            "average_position": manual.get("average_position"),
            "best_url": manual.get("best_url"),
            "period": manual.get("period"),
            "notes": manual.get("notes"),
        }
        rec["primary_rank_report"] = manual.get("average_position")
        rec["rank_label_tr"] = (
            f"GSC ortalama konum: {manual.get('average_position')} "
            f"({manual.get('best_url', 'URL yok')})"
        )
    else:
        rec["manual_gsc"] = None
        if manual and manual.get("_error"):
            rec["manual_error"] = manual["_error"]
        if ddg_pos is not None:
            rec["google_proxy"] = {"engine": "duckduckgo_lite", "approx_organic_position": ddg_pos}
            rec["primary_rank_report"] = ddg_pos
            rec["rank_label_tr"] = (
                f"DuckDuckGo Lite (Google değil) tahmini sıra: {ddg_pos}. "
                "Kesin değer için GSC kullanın."
            )
        else:
            rec["google_proxy"] = None
            rec["primary_rank_report"] = None
            rec["rank_label_tr"] = (
                "Otomatik sıra alınamadı. "
                f"{ddg_note}. data/serp-led-ekran-manual.json ile GSC değeri girin."
            )

    return rec


def render_markdown(rows: list[dict]) -> str:
    lines = [
        "# LEDAJANS — «led ekran» sıra takibi",
        "",
        "**Önemli:** Google `google.com.tr` organik sırası veri merkezi IP’lerinden güvenilir şekilde otomatik okunamaz (CAPTCHA/429). "
        "Resmi metrik için [Google Search Console](https://search.google.com/search-console) "
        "→ Performans → sorgu `led ekran` → ortalama konum ve hedef URL kullanın.",
        "",
        "Bu dosya `AGENT-HUB/weekly_serp_led_ekran.py` tarafından güncellenir; haftada en fazla bir kayıt (aynı ISO hafta atlanır, `--force` ile yenilenir).",
        "",
        "## Manuel değer şablonu",
        "",
        f"`{MANUAL.relative_to(Path('/workspace'))}` dosyasını oluşturun (örnek: `{MANUAL.with_name('serp-led-ekran-manual.example.json').name}`).",
        "",
        "## Geçmiş",
        "",
        "| ISO Hafta | TR zaman | Birincil metrik | Not |",
        "|-----------|----------|-----------------|-----|",
    ]
    for r in reversed(rows[-24:]):
        lines.append(
            "| {iw} | {tr} | {pr} | {lb} |".format(
                iw=r.get("iso_week", ""),
                tr=r.get("captured_at_tr", ""),
                pr=r.get("primary_rank_report") if r.get("primary_rank_report") is not None else "—",
                lb=(r.get("rank_label_tr") or "")[:120].replace("|", "/"),
            )
        )
    lines.append("")
    lines.append("---")
    lines.append("*Otomatik üretim — serbest metin notları kısaltılmış olabilir.*")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Aynı ISO haftada bile yeni satır ekle")
    args = ap.parse_args()

    now_tr = datetime.now(TR)
    week = iso_week_key(now_tr)
    prev = last_jsonl_week()
    if prev == week and not args.force:
        print(f"Aynı ISO hafta ({week}); kayıt atlandı. Yinelemek için: --force")
        return 0

    DATA.mkdir(parents=True, exist_ok=True)
    rec = build_record(now_tr)
    with JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    rows: list[dict] = []
    if JSONL.exists():
        for ln in JSONL.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    REPORT.write_text(render_markdown(rows), encoding="utf-8")
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
