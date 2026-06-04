#!/usr/bin/env python3
"""Google SERP baseline capture for ledajans.com — appends AGENT-HUB/SERP-BASELINE.csv."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

WORKSPACE = Path("/workspace")
CSV_PATH = WORKSPACE / "AGENT-HUB" / "SERP-BASELINE.csv"
FIELDS = [
    "captured_at_utc",
    "query",
    "locale",
    "device",
    "search_engine",
    "target_url",
    "rank_position",
    "source",
    "notes",
]

DEFAULT_QUERY = "led ekran"
DEFAULT_LOCALE = "tr-TR"
DEFAULT_TARGET_HOST = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_host(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def find_rank_in_serper(
    query: str,
    device: str,
    target_host: str,
    api_key: str,
) -> tuple[int | None, str | None, str]:
    payload: dict[str, Any] = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": 100,
    }
    if device == "mobile":
        payload["device"] = "mobile"
    resp = requests.post(
        "https://google.serper.dev/search",
        json=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        timeout=45,
    )
    resp.raise_for_status()
    data = resp.json()
    organic = data.get("organic") or []
    for idx, item in enumerate(organic, start=1):
        link = item.get("link") or ""
        if target_host in normalize_host(link):
            return idx, link, "serper.dev"
    return None, None, "serper.dev"


def append_row(row: dict[str, str]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0
    with CSV_PATH.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in FIELDS})


def capture(
    query: str,
    locale: str,
    device: str,
    target_host: str,
    notes_extra: str = "",
) -> dict[str, str]:
    captured_at = utc_now_iso()
    rank: int | str | None = None
    target_url = ""
    source = ""
    notes_parts: list[str] = []

    api_key = os.environ.get("SERPER_API_KEY") or os.environ.get("SERPAPI_API_KEY")
    if api_key:
        try:
            rank_val, url_val, source = find_rank_in_serper(
                query, device, target_host, api_key
            )
            rank = rank_val if rank_val is not None else ">100"
            target_url = url_val or ""
            if rank_val is None:
                notes_parts.append("ledajans.com ilk 100 organik sonuçta yok")
        except requests.RequestException as exc:
            rank = "BLOCKED"
            source = "serper.dev"
            notes_parts.append(f"API hatası: {exc}")
    else:
        rank = "BLOCKED"
        source = "none"
        notes_parts.append(
            "SERPER_API_KEY veya SERPAPI_API_KEY tanımlı değil; "
            "bulut IP Google CAPTCHA veriyor — otomasyon secret ekleyin veya "
            "AGENT-HUB/SERP-BASELINE.csv satırını browser capture ile güncelleyin"
        )

    if notes_extra:
        notes_parts.append(notes_extra)

    return {
        "captured_at_utc": captured_at,
        "query": query,
        "locale": locale,
        "device": device,
        "search_engine": "google",
        "target_url": target_url or DEFAULT_TARGET_URL,
        "rank_position": str(rank) if rank is not None else "",
        "source": source,
        "notes": "; ".join(notes_parts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP baseline CSV capture")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--locale", default=DEFAULT_LOCALE)
    parser.add_argument(
        "--device",
        choices=("mobile", "desktop", "both"),
        default="both",
    )
    parser.add_argument("--target-host", default=DEFAULT_TARGET_HOST)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--manual-rank",
        type=int,
        default=None,
        help="Browser doğrulaması sonrası rank (ör. 2)",
    )
    parser.add_argument(
        "--manual-url",
        default="",
        help="Manuel capture hedef URL",
    )
    parser.add_argument(
        "--manual-source",
        default="google-organic-browser",
        help="Manuel capture kaynak etiketi",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    devices = ["mobile", "desktop"] if args.device == "both" else [args.device]
    rows: list[dict[str, str]] = []

    for device in devices:
        if args.manual_rank is not None:
            row = {
                "captured_at_utc": utc_now_iso(),
                "query": args.query,
                "locale": args.locale,
                "device": device,
                "search_engine": "google",
                "target_url": args.manual_url or DEFAULT_TARGET_URL,
                "rank_position": str(args.manual_rank),
                "source": args.manual_source,
                "notes": args.notes or "cursor browser capture; hl=tr gl=tr",
            }
        else:
            row = capture(
                args.query,
                args.locale,
                device,
                args.target_host,
                args.notes,
            )
        rows.append(row)

    for row in rows:
        print(
            f"{row['captured_at_utc']} | {row['device']} | "
            f"rank={row['rank_position']} | {row['target_url']} | {row['source']}"
        )
        if not args.dry_run:
            append_row(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
