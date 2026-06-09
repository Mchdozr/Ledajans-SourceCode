#!/usr/bin/env python3
"""Haftalık 'led ekran' SERP kontrolü — CSV baseline + haftalık özet."""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
DEFAULT_TARGET_URL = "https://ledajans.com/"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def read_baseline_fields() -> list[str]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def rows_for_query(query: str, device: str | None = None) -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    matches = [r for r in rows if r.get("query", "").lower() == query.lower()]
    if device:
        matches = [r for r in matches if r.get("device", "").lower() == device.lower()]
    return matches


def latest_row_for_query(query: str, device: str | None = None) -> dict[str, str] | None:
    matches = rows_for_query(query, device)
    return matches[-1] if matches else None


def previous_organic_row(query: str, device: str, before_utc: str) -> dict[str, str] | None:
    organic_sources = {"browser_serp_check", "manual_web_check", "chrome_headless"}
    matches = [
        r
        for r in rows_for_query(query, device)
        if r.get("captured_at_utc", "") < before_utc
        and r.get("source", "") in organic_sources
        and str(r.get("rank_position", "")).isdigit()
    ]
    return matches[-1] if matches else None


def append_baseline_row(row: dict[str, str]) -> None:
    fields = read_baseline_fields()
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writerow({key: row.get(key, "") for key in fields})


def fetch_google_html(device: str) -> str:
    if device == "mobile":
        ua = (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        )
    else:
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    params = {"q": QUERY, "hl": "tr", "gl": "tr", "num": "20", "gbv": "1"}
    url = "https://www.google.com/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": ua, "Accept-Language": "tr-TR,tr;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_chrome_html(device: str) -> str | None:
    chrome = "/usr/local/bin/google-chrome"
    if not Path(chrome).exists():
        return None
    ua_flag = (
        "--user-agent=Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
        if device == "mobile"
        else "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    params = {"q": QUERY, "hl": "tr", "gl": "tr", "num": "20"}
    url = "https://www.google.com/search?" + urllib.parse.urlencode(params)
    try:
        proc = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--virtual-time-budget=8000",
                ua_flag,
                f"--dump-dom={url}",
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    return proc.stdout


def extract_organic_rank(html: str) -> tuple[int | None, str | None, list[str]]:
    patterns = [
        r'href="(https?://[^"]+)"',
        r'href="/url\?q=([^"&]+)',
    ]
    urls: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, html):
            url = urllib.parse.unquote(match.group(1))
            if not url.startswith("http"):
                continue
            if any(x in url for x in ("google.", "gstatic.", "schema.org", "webcache")):
                continue
            urls.append(url.rstrip(".,;)"))

    ordered: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        ordered.append(url)

    rank: int | None = None
    target_url: str | None = None
    for index, url in enumerate(ordered, start=1):
        if TARGET_DOMAIN in url:
            rank = index
            target_url = url
            break

    domains = [re.sub(r"^https?://([^/]+).*$", r"\1", u) for u in ordered[:10]]
    return rank, target_url, domains


def check_device(device: str) -> dict[str, object]:
    html = fetch_chrome_html(device) or fetch_google_html(device)
    rank, target_url, top_domains = extract_organic_rank(html)
    return {
        "device": device,
        "rank_position": rank,
        "target_url": target_url or DEFAULT_TARGET_URL,
        "top_domains": top_domains,
        "method": "chrome_headless" if rank else "http_fallback",
        "html_has_target": TARGET_DOMAIN in html.lower(),
    }


def load_json_report(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_row(
    captured_at: str,
    device: str,
    rank_position: int | str | None,
    target_url: str,
    source: str,
    notes: str,
    serp_features: str = "",
    primary_competitor: str = "",
) -> dict[str, str]:
    return {
        "captured_at_utc": captured_at,
        "query": QUERY,
        "locale": LOCALE,
        "device": device,
        "search_engine": SEARCH_ENGINE,
        "target_url": target_url,
        "rank_position": "" if rank_position is None else str(rank_position),
        "serp_features": serp_features,
        "primary_competitor": primary_competitor,
        "competitor_rank": "",
        "source": source,
        "notes": notes,
    }


def update_weekly_report(
    captured_at: str,
    results: list[dict[str, object]],
    previous: dict[str, str] | None,
) -> Path:
    report_path = ROOT / "AGENT-HUB" / f"WEEKLY-MONITORING-{today_iso()}.md"
    mobile = next((r for r in results if r["device"] == "mobile"), results[0])
    desktop = next((r for r in results if r["device"] == "desktop"), None)

    prev_at = previous.get("captured_at_utc", "—") if previous else "—"
    mobile_rank = mobile.get("rank_position", "N/A")
    prev_serp = previous_organic_row(QUERY, "mobile", captured_at)
    prev_serp_pos = prev_serp.get("rank_position", "") if prev_serp else ""
    prev_gsc = previous.get("rank_position", "N/A") if previous else "N/A"
    delta = "—"
    if prev_serp_pos and str(prev_serp_pos).isdigit() and mobile_rank not in (None, "", "N/A"):
        delta_val = int(mobile_rank) - int(prev_serp_pos)
        delta = f"{delta_val:+d} (önceki organik: {prev_serp_pos})"
    elif prev_gsc not in ("", "N/A", "pending"):
        delta = (
            f"canlı organik #{mobile_rank}; GSC avg_position önceki: {prev_gsc} "
            "(farklı metrik — karşılaştırma bilgilendirme amaçlı)"
        )

    lines = [
        f"# Haftalık SEO İzleme — {today_iso()}",
        "",
        "## SERP — `led ekran`",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        f"- Mobil organik sıra: **{mobile_rank}** (`{mobile.get('target_url', DEFAULT_TARGET_URL)}`)",
    ]
    if desktop and desktop.get("rank_position") not in (None, ""):
        lines.append(
            f"- Masaüstü organik sıra: **{desktop.get('rank_position')}** "
            f"(`{desktop.get('target_url', DEFAULT_TARGET_URL)}`)"
        )
    else:
        lines.append("- Masaüstü organik sıra: bu turda doğrulanamadı (yalnızca mobil snapshot)")
    lines.extend(
        [
        f"- Önceki GSC kaydı: `{prev_at}` → avg_position `{prev_gsc}`",
        f"- Haftalık delta (mobil organik): {delta}",
            f"- Kaynak: `{mobile.get('source', 'serp_check')}`",
            "",
            "### İlk 5 organik domain (mobil)",
            "",
        ]
    )
    top5 = mobile.get("top_domains") or mobile.get("top5_domains") or []
    if top5:
        for index, domain in enumerate(top5[:5], start=1):
            lines.append(f"{index}. {domain}")
    else:
        lines.append("- (çekimde domain listesi alınamadı)")

    lines.extend(
        [
            "",
            "## SERP baseline",
            "",
            f"- Yeni satır(lar): `AGENT-HUB/SERP-BASELINE.csv`",
            f"- Komut: `python3 AGENT-HUB/serp-check-led-ekran.py`",
            "",
            "## Açık aksiyonlar",
            "",
            "- GSC Performance export ile avg_position doğrulaması (son: 6.78 @ 2026-06-05)",
            "- Haftalık smoke: `powershell -File scripts/run-weekly-seo-check.ps1`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/serp-check-led-ekran.py",
            "```",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Haftalık led ekran SERP kontrolü")
    parser.add_argument("--device", choices=["mobile", "desktop", "both"], default="both")
    parser.add_argument("--rank", type=int, help="Manuel organik sıra (mobil)")
    parser.add_argument("--desktop-rank", type=int, help="Manuel organik sıra (desktop)")
    parser.add_argument("--target-url", default=DEFAULT_TARGET_URL)
    parser.add_argument("--json-report", type=Path, default=ROOT / "serp-position-report.json")
    parser.add_argument("--source", default="browser_serp_check")
    parser.add_argument("--notes", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    captured_at = utc_now_iso()
    previous = latest_row_for_query(QUERY, "mobile")
    devices = ["mobile", "desktop"] if args.device == "both" else [args.device]
    json_report = load_json_report(args.json_report)

    results: list[dict[str, object]] = []
    rows: list[dict[str, str]] = []

    for device in devices:
        manual_rank = args.rank if device == "mobile" else args.desktop_rank
        if manual_rank is not None:
            result = {
                "device": device,
                "rank_position": manual_rank,
                "target_url": args.target_url,
                "top_domains": [],
                "source": args.source,
            }
        elif json_report and json_report.get("device") == device:
            result = {
                "device": device,
                "rank_position": json_report.get("rank_position"),
                "target_url": json_report.get("target_url", args.target_url),
                "top_domains": json_report.get("top5_domains", []),
                "serp_features": ", ".join(json_report.get("serp_features", [])),
                "source": args.source,
                "notes_extra": json_report.get("notes", ""),
            }
        else:
            checked = check_device(device)
            result = {
                "device": device,
                "rank_position": checked["rank_position"],
                "target_url": checked["target_url"],
                "top_domains": checked["top_domains"],
                "source": "chrome_headless" if checked["rank_position"] else "http_fallback_unverified",
                "notes_extra": (
                    "Otomatik HTTP/headless çekimde sıra doğrulanamadı; tarayıcı kontrolü önerilir."
                    if not checked["rank_position"]
                    else f"Top domains: {', '.join(checked['top_domains'][:5])}"
                ),
            }

        notes_parts = [args.notes, str(result.get("notes_extra", "")).strip()]
        notes = "; ".join(part for part in notes_parts if part)
        if not notes:
            notes = f"Organik SERP snapshot ({device})"

        primary = ""
        tops = result.get("top_domains") or []
        if tops:
            for domain in tops:
                if TARGET_DOMAIN not in str(domain):
                    primary = str(domain)
                    break

        rank_value = result.get("rank_position")
        if rank_value in (None, "") and manual_rank is None and not (
            json_report and json_report.get("device") == device
        ):
            continue

        row = build_row(
            captured_at=captured_at,
            device=device,
            rank_position=rank_value,
            target_url=str(result.get("target_url", args.target_url)),
            source=str(result.get("source", args.source)),
            notes=notes,
            serp_features=str(result.get("serp_features", "")),
            primary_competitor=primary,
        )
        results.append({**result, "source": row["source"]})
        rows.append(row)

    if args.dry_run:
        print(json.dumps({"captured_at": captured_at, "results": results, "rows": rows}, indent=2))
        return 0

    for row in rows:
        append_baseline_row(row)

    report_path = update_weekly_report(captured_at, results, previous)
    mobile_rank = next((r.get("rank_position") for r in results if r["device"] == "mobile"), "N/A")
    print(f"led_ekran_mobile_rank={mobile_rank}")
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
