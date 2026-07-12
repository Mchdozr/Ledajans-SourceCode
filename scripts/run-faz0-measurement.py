#!/usr/bin/env python3
"""Faz 0: canli olcum + SERP-BASELINE guncelleme (GSC API yok — teknik proxy)."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(ROOT, "AGENT-HUB", "SERP-BASELINE.csv")
AUDIT_JSON = os.path.join(ROOT, "AGENT-HUB", "audit-money-pages-2026-07-12.json")
REPORT = os.path.join(ROOT, "AGENT-HUB", "REPORTS", "2026-07-12-post-deploy-measurement.md")
CAPTURED = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

QUERIES = [
    ("led ekran", "https://ledajans.com/led-ekran/"),
    ("led ekran fiyatları", "https://ledajans.com/led-ekran/"),
    ("dış mekan led ekran", "https://ledajans.com/dis-mekan-led-ekran/"),
    ("iç mekan led ekran", "https://ledajans.com/ic-mekan-led-ekran/"),
    ("led ekran kiralama", "https://ledajans.com/rental-ekran/"),
]


def run_audit() -> dict:
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "AGENT-HUB", "audit-money-pages.py")],
        cwd=ROOT,
        check=False,
    )
    path = AUDIT_JSON
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def cannibalization_check() -> str:
    home = requests.get("https://ledajans.com/", timeout=30).text
    hub = requests.get("https://ledajans.com/led-ekran/", timeout=30).text
    home_led = "led ekran" in home.lower() and "led ekran üreticisi" in home.lower()
    hub_trust = "la-trust-bar" in hub or "25+" in hub
    hub_h1 = "LED Ekran Çözümleri ve Fiyatları" in hub
    notes = []
    notes.append(f"homepage_producer_focus={home_led}")
    notes.append(f"hub_trust_bar={hub_trust}")
    notes.append(f"hub_h1_ok={hub_h1}")
    return "; ".join(notes)


def append_baseline(rows: list[dict[str, str]]) -> None:
    with open(BASELINE, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
    with open(BASELINE, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def main() -> int:
    audit = run_audit()
    cann = cannibalization_check()
    hub = next((p for p in audit if p.get("label") == "LED ekran hub"), {})
    home = next((p for p in audit if p.get("label") == "Ana sayfa"), {})

    lines = [
        f"# Post-deploy olcum — {CAPTURED}",
        "",
        "## Cannibalization",
        cann,
        "",
        "## Money pages",
        f"- Homepage title: {home.get('title', 'n/a')}",
        f"- Hub title: {hub.get('title', 'n/a')}",
        f"- Hub H1: {hub.get('h1', 'n/a')}",
        "",
        "## CWV",
        "Lighthouse cloud ortaminda crash — baseline: audit-mobile-full.json (Perf 42, LCP 10.9s).",
        "Canli mu-plugin + GTM defer deploy edildi; GSC Deneyim raporu ile dogrula.",
        "",
        "## GSC",
        "Manuel: GSC → Performans → Sorgu filtre (led ekran) → 28 gun → avg position + CTR",
    ]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    new_rows = []
    for q, url in QUERIES:
        new_rows.append(
            {
                "captured_at_utc": CAPTURED,
                "query": q,
                "locale": "tr-TR",
                "device": "mobile",
                "search_engine": "google",
                "target_url": url,
                "rank_position": "pending_gsc",
                "serp_features": "",
                "primary_competitor": "videowall.com.tr",
                "competitor_rank": "",
                "source": "post-deploy-2026-07-12",
                "notes": f"Deploy sonrasi; {cann}; hub_title={hub.get('title','')[:60]}",
            }
        )
    append_baseline(new_rows)
    print(f"OK: {REPORT}")
    print(f"OK: {len(new_rows)} SERP-BASELINE satiri eklendi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
