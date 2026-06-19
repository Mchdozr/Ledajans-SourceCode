#!/usr/bin/env python3
"""Google SERP ölçümü → SERP-BASELINE.csv + haftalık özet."""
from __future__ import annotations

import argparse
import csv
import html as htmlmod
import re
import subprocess
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
AGENT_HUB = ROOT / "AGENT-HUB"

USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

DEFAULT_QUERIES = ("led ekran",)
SKIP_DOMAINS = (
    "google.",
    "gstatic.",
    "youtube.com",
    "schema.org",
    "webcache",
    "accounts.google",
    "support.google",
    "maps.google",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def extract_organic(page_html: str) -> list[str]:
    patterns = (
        r'<a[^>]+href="(https?://[^"]+)"[^>]*><h3',
        r"/url\?q=(https?://[^&\"]+)",
        r"&amp;url=(https?://[^&\"]+)",
        r"&url=(https?://[^&\"]+)",
    )
    urls: list[str] = []
    for pattern in patterns:
        urls.extend(re.findall(pattern, page_html))

    organic: list[str] = []
    seen: set[str] = set()
    for raw in urls:
        url = htmlmod.unescape(urllib.parse.unquote(raw.split("#")[0]))
        if any(skip in url for skip in SKIP_DOMAINS) or url in seen:
            continue
        seen.add(url)
        organic.append(url)
    return organic


def fetch_google_serp(query: str, device: str, profile_dir: Path, timeout_sec: int) -> list[str]:
    params = {
        "q": query,
        "hl": "tr",
        "gl": "tr",
        "num": "30",
        "pws": "0",
    }
    if device == "mobile":
        params["udm"] = "14"

    search_url = "https://www.google.com/search?" + urllib.parse.urlencode(params)
    profile_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        output_path = Path(tmp.name)

    chrome_cmd = " ".join(
        [
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile_dir}",
            "--virtual-time-budget=15000",
            shlex_quote(f"--user-agent={USER_AGENTS[device]}"),
            "--dump-dom",
            shlex_quote(search_url),
        ]
    )
    shell_cmd = f"timeout {timeout_sec} {chrome_cmd} > {shlex_quote(str(output_path))} 2>/dev/null"
    subprocess.run(shell_cmd, shell=True, check=False)

    if not output_path.exists() or output_path.stat().st_size == 0:
        return []

    page_html = output_path.read_text(encoding="utf-8", errors="replace")
    output_path.unlink(missing_ok=True)
    return extract_organic(page_html)


def shlex_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def find_rank(organic: list[str], target_domain: str) -> tuple[int | None, str]:
    for index, url in enumerate(organic, start=1):
        if target_domain in url:
            return index, url
    return None, ""


def read_baseline_rows() -> tuple[list[str], list[dict[str, str]]]:
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def append_baseline_rows(rows: list[dict[str, str]], fields: list[str]) -> int:
    existing = {
        (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"])
        for row in read_baseline_rows()[1]
    }
    to_write = [
        row
        for row in rows
        if (row["captured_at_utc"], row["query"].lower(), row["device"], row["source"]) not in existing
    ]
    if not to_write:
        return 0

    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        for row in to_write:
            writer.writerow({field: row.get(field, "") for field in fields})
    return len(to_write)


def previous_row_for_device(
    rows: list[dict[str, str]], device: str, exclude_at: str
) -> dict[str, str] | None:
    matches = [
        row
        for row in rows
        if row.get("query", "").strip().lower() == "led ekran"
        and row.get("device") == device
        and row.get("captured_at_utc") != exclude_at
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda row: row.get("captured_at_utc", ""), reverse=True)[0]


def format_delta(current: str, previous: str | None) -> str:
    if not previous:
        return "önceki ölçüm yok"
    try:
        current_value = float(current)
        previous_value = float(previous)
    except ValueError:
        return f"{previous} → {current}"
    diff = previous_value - current_value
    if diff > 0:
        return f"{previous_value} → {current_value} (↑{diff:.2f})"
    if diff < 0:
        return f"{previous_value} → {current_value} (↓{abs(diff):.2f})"
    return f"{previous_value} → {current_value} (sabit)"


def update_weekly_monitoring(
    captured_at: str,
    measurements: list[dict[str, str]],
    baseline_rows: list[dict[str, str]],
) -> Path:
    report_date = captured_at[:10]
    report_path = AGENT_HUB / f"WEEKLY-MONITORING-{report_date}.md"
    lines = [
        f"# Haftalık SEO İzleme — {report_date}",
        "",
        "## SERP — `led ekran`",
        "",
        f"- Ölçüm zamanı (UTC): `{captured_at}`",
        "- Kaynak: `AGENT-HUB/check-serp-baseline.py` (Google headless, tr-TR)",
        "",
        "| Cihaz | Hedef URL | Sıra | Not |",
        "|---|---|---:|---|",
    ]
    for row in measurements:
        lines.append(
            f"| {row['device']} | {row['target_url'] or '—'} | **{row['rank_position']}** | {row['notes']} |"
        )

    lines.extend(["", "## Haftalık delta", ""])
    for device in ("mobile", "desktop"):
        current = next((row for row in measurements if row["device"] == device), None)
        prior = previous_row_for_device(baseline_rows, device, captured_at)
        if not current:
            continue
        prior_rank = prior.get("rank_position") if prior else None
        prior_source = prior.get("source", "") if prior else ""
        lines.append(
            f"- **{device}:** {format_delta(current['rank_position'], prior_rank)}"
            + (f" (önceki kaynak: `{prior_source}`)" if prior_source else "")
        )

    gsc_prior = next(
        (
            row
            for row in sorted(baseline_rows, key=lambda row: row.get("captured_at_utc", ""), reverse=True)
            if row.get("query", "").strip().lower() == "led ekran"
            and row.get("device") == "mobile"
            and row.get("source", "").startswith("gsc_")
        ),
        None,
    )
    if gsc_prior:
        lines.append(
            f"- **GSC ort. pozisyon (referans):** {gsc_prior.get('rank_position', '—')} "
            f"(`{gsc_prior.get('captured_at_utc', '')}`) — canlı SERP ile doğrudan karşılaştırılmaz"
        )

    lines.extend(
        [
            "",
            "## Sonraki ölçüm",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-baseline.py",
            "```",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def measure_query(
    query: str,
    target_domain: str,
    devices: tuple[str, ...],
    captured_at: str,
    timeout_sec: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for device in devices:
        profile_dir = Path(tempfile.gettempdir()) / f"ledajans-serp-{device}-{captured_at.replace(':', '')}"
        organic = fetch_google_serp(query, device, profile_dir, timeout_sec)
        rank, target_url = find_rank(organic, target_domain)
        competitor = organic[1].split("/")[2] if len(organic) > 1 and rank == 1 else ""
        if len(organic) > 1 and rank and rank > 1:
            competitor = organic[0].split("/")[2]

        rows.append(
            {
                "captured_at_utc": captured_at,
                "query": query,
                "locale": "tr-TR",
                "device": device,
                "search_engine": "google",
                "target_url": target_url or f"https://{target_domain}/",
                "rank_position": str(rank) if rank is not None else "not_found",
                "serp_features": "",
                "primary_competitor": competitor,
                "competitor_rank": "2" if rank == 1 and competitor else "",
                "source": "manual_web_check_headless",
                "notes": (
                    f"Organic sonuç={len(organic)}; "
                    f"hedef={'bulundu' if rank else 'ilk 30da yok'}"
                ),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="SERP baseline ölçümü")
    parser.add_argument("--query", action="append", default=list(DEFAULT_QUERIES))
    parser.add_argument("--target-domain", default="ledajans.com")
    parser.add_argument("--device", action="append", choices=("mobile", "desktop"))
    parser.add_argument("--timeout", type=int, default=40)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    devices = tuple(args.device or ("mobile", "desktop"))
    captured_at = utc_now()
    all_rows: list[dict[str, str]] = []

    for query in args.query:
        all_rows.extend(
            measure_query(query, args.target_domain, devices, captured_at, args.timeout)
        )

    for row in all_rows:
        print(
            f"{row['device']}\t{row['query']}\t"
            f"rank={row['rank_position']}\t{row['target_url']}"
        )

    if args.dry_run:
        print("dry_run=1")
        return 0

    fields, baseline_rows = read_baseline_rows()
    appended = append_baseline_rows(all_rows, fields)
    report_path = update_weekly_monitoring(captured_at, all_rows, baseline_rows)
    print(f"baseline_appended={appended}")
    print(f"weekly_report={report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
