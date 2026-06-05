#!/usr/bin/env python3
"""GSC failing URL CSV'sini HTTP/canonical/title olarak siniflandirir."""
from __future__ import annotations

import csv
import html
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

DEFAULT_INPUT = Path(r"AGENT-HUB\DATA\gsc-coverage-drilldown-2026-06-05\Tablo.csv")

PRODUCT_TERMS = re.compile(
    r"led|ekran|panel|kontrol|receiver|guc|kaynak|rgb|nova|hd-|serit|omru|tamir|indir",
    re.I,
)
LOW_VALUE_TERMS = re.compile(r"/en/|/de/|/case/?$|firma-bilgilerimiz|our-company|kontakt|contact", re.I)


def extract(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.I | re.S)
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""


def classify(url: str, status: int, final_url: str, title: str, canonical: str, robots: str) -> tuple[str, str]:
    path = urlparse(final_url).path.lower()
    if status >= 500:
        return "TEKNIK HATA", "5xx; index icin once sunucu hatasi cozulmeli"
    if status == 404:
        return "TEKNIK HATA", "404; trafik/geri link varsa 301, degilse normal"
    if status in (301, 302) or final_url.rstrip("/") != url.rstrip("/"):
        return "NORMAL", "yonlendirme; hedef URL indexlenmeli"
    if "noindex" in robots.lower():
        return "NORMAL", "noindex bilincli ise indexlenmemeli"
    if canonical and canonical.rstrip("/") != final_url.rstrip("/"):
        return "NORMAL", "canonical baska URL'yi isaret ediyor"
    if LOW_VALUE_TERMS.search(path):
        return "DUSUK ONCELIK", "kurumsal/dil/case sayfasi; ticari SEO katkisi dusuk"
    if PRODUCT_TERMS.search(path + " " + title):
        return "YARARLI", "urun/rehber niyeti var; kalite ve ic linkle indexlenmeli"
    return "KONTROL", "manuel niyet kontrolu gerekli"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="GSC URL CSV yolu")
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"CSV yok: {input_path}")
        return 1

    rows = list(csv.DictReader(input_path.open(encoding="utf-8-sig")))
    print(f"CSV satir: {len(rows)}")

    buckets: dict[str, list[dict[str, str]]] = {}
    session = requests.Session()
    session.headers.update({"User-Agent": "LEDAJANS-Index-Audit/1.0"})

    for row in rows:
        url = row.get("URL", "").strip()
        if not url:
            continue
        try:
            response = session.get(url, timeout=args.timeout, allow_redirects=True)
            text = response.text[:250000]
            title = extract(r"<title[^>]*>(.*?)</title>", text)
            canonical = extract(r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)", text)
            robots = extract(r"<meta[^>]+name=[\"']robots[\"'][^>]+content=[\"']([^\"']+)", text)
            verdict, reason = classify(url, response.status_code, response.url, title, canonical, robots)
            item = {
                "url": url,
                "status": str(response.status_code),
                "final": response.url,
                "title": title,
                "canonical": canonical,
                "robots": robots,
                "reason": reason,
            }
        except Exception as exc:
            verdict = "TEKNIK HATA"
            item = {"url": url, "status": "ERR", "final": "", "title": "", "canonical": "", "robots": "", "reason": str(exc)}
        buckets.setdefault(verdict, []).append(item)

    for verdict in ("YARARLI", "KONTROL", "DUSUK ONCELIK", "NORMAL", "TEKNIK HATA"):
        items = buckets.get(verdict, [])
        print(f"\n## {verdict} ({len(items)})")
        for item in items:
            print(f"- {item['url']} [{item['status']}]")
            if item["title"]:
                print(f"  title: {item['title'][:110]}")
            print(f"  not: {item['reason']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
