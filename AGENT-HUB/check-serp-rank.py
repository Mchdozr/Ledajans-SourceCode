#!/usr/bin/env python3
"""Google SERP sırasını ölçer, SERP-BASELINE.csv ve haftalık özeti günceller."""
from __future__ import annotations

import csv
import subprocess
import sys
import time
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "AGENT-HUB" / "SERP-BASELINE.csv"
QUERY = "led ekran"
LOCALE = "tr-TR"
SEARCH_ENGINE = "google"
TARGET_DOMAIN = "ledajans.com"
TARGET_URL = "https://ledajans.com/"
SOURCE = "google_serp_headless_uc"
USER_AGENTS = {
    "mobile": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "desktop": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def ensure_dependencies() -> None:
    try:
        import undetected_chromedriver  # noqa: F401
        from selenium.webdriver.common.by import By  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "undetected-chromedriver", "selenium"]
        )


def chrome_major_version() -> int | None:
    try:
        out = subprocess.check_output(
            ["google-chrome", "--version"],
            text=True,
            stderr=subprocess.STDOUT,
        )
        token = out.strip().split()[-1].split(".")[0]
        return int(token)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None


def fetch_organic_results(device: str) -> list[tuple[str, str]]:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By

    search_url = (
        "https://www.google.com/search?"
        + urllib.parse.urlencode(
            {"q": QUERY, "hl": "tr", "gl": "tr", "num": "100", "pws": "0"}
        )
    )
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=tr-TR")
    options.add_argument(f"--user-agent={USER_AGENTS[device]}")
    if device == "mobile":
        options.add_argument("--window-size=412,915")

    version_main = chrome_major_version()
    driver = uc.Chrome(options=options, version_main=version_main)
    organic: list[tuple[str, str]] = []
    try:
        driver.set_page_load_timeout(60)
        driver.get(search_url)
        time.sleep(5)
        raw: list[tuple[str, str]] = []
        for heading in driver.find_elements(By.CSS_SELECTOR, "a h3, h3, [role='heading']"):
            title = heading.text.strip()
            if not title:
                continue
            try:
                link = heading.find_element(By.XPATH, "./ancestor::a[1]")
                href = link.get_attribute("href") or ""
            except Exception:
                continue
            if not href.startswith("http") or "google." in href:
                continue
            raw.append((href, title))

        seen: set[str] = set()
        for href, title in raw:
            if href in seen:
                continue
            seen.add(href)
            organic.append((href, title))
    finally:
        driver.quit()
    return organic


def find_rank(organic: list[tuple[str, str]]) -> tuple[int | None, str]:
    for index, (href, _title) in enumerate(organic, start=1):
        if TARGET_DOMAIN in href:
            return index, href
    return None, TARGET_URL


def read_baseline_fieldnames() -> list[str]:
    if not BASELINE_PATH.exists():
        return [
            "captured_at_utc",
            "query",
            "locale",
            "device",
            "search_engine",
            "target_url",
            "rank_position",
            "serp_features",
            "primary_competitor",
            "competitor_rank",
            "source",
            "notes",
        ]
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def append_baseline_rows(rows: list[dict[str, str]]) -> None:
    fieldnames = read_baseline_fieldnames()
    write_header = not BASELINE_PATH.exists() or BASELINE_PATH.stat().st_size == 0
    with BASELINE_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def previous_led_ekran_rows() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    with BASELINE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("query", "").lower() == QUERY]
    return rows[-4:]


def write_weekly_summary(
    captured_at: str,
    measurements: list[dict[str, object]],
    weekly_path: Path,
) -> None:
    prior = previous_led_ekran_rows()
    prior_mobile = next(
        (row for row in reversed(prior) if row.get("device") == "mobile"),
        None,
    )
    prior_desktop = next(
        (row for row in reversed(prior) if row.get("device") == "desktop"),
        None,
    )
    mobile = next(item for item in measurements if item["device"] == "mobile")
    desktop = next(item for item in measurements if item["device"] == "desktop")

    def delta(current: int | None, previous: dict[str, str] | None) -> str:
        if current is None:
            return "ölçülemedi"
        if not previous:
            return "ilk ölçüm"
        try:
            old = float(str(previous.get("rank_position", "")).replace("top", ""))
        except ValueError:
            return f"önceki={previous.get('rank_position', 'N/A')}"
        diff = old - current
        if diff > 0:
            return f"↑ {diff:.0f} sıra (önceki {previous.get('rank_position')})"
        if diff < 0:
            return f"↓ {abs(diff):.0f} sıra (önceki {previous.get('rank_position')})"
        return f"stabil (önceki {previous.get('rank_position')})"

    lines = [
        f"# Haftalık SEO İzleme — {weekly_path.stem.replace('WEEKLY-MONITORING-', '')}",
        "",
        "## SERP — led ekran",
        "",
        f"- Ölçüm UTC: `{captured_at}`",
        f"- Kaynak: `{SOURCE}` (Google, `hl=tr`, `gl=tr`, organik sonuçlar)",
        "",
        "| Cihaz | Sıra | Hedef URL | Haftalık delta |",
        "|---|---:|---|---|",
        (
            f"| mobile | {mobile['rank_position']} | {mobile['target_url']} | "
            f"{delta(int(mobile['rank_position']), prior_mobile)} |"
        ),
        (
            f"| desktop | {desktop['rank_position']} | {desktop['target_url']} | "
            f"{delta(int(desktop['rank_position']), prior_desktop)} |"
        ),
        "",
        "### Üst 5 organik (mobile)",
        "",
    ]
    for index, (href, title) in enumerate(mobile["top_results"][:5], start=1):
        mark = " **" if TARGET_DOMAIN in href else ""
        lines.append(f"{index}. {title} — {href}{mark}")
    lines.extend(
        [
            "",
            "## Kayıt",
            "",
            f"- `AGENT-HUB/SERP-BASELINE.csv` satır eklendi: {len(measurements)}",
            "- Komut: `python3 AGENT-HUB/check-serp-rank.py`",
            "",
            "## Sonraki hafta",
            "",
            "```bash",
            "python3 AGENT-HUB/check-serp-rank.py",
            "```",
        ]
    )
    weekly_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dependencies()
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    weekly_name = f"WEEKLY-MONITORING-{datetime.now(UTC).date().isoformat()}.md"
    weekly_path = ROOT / "AGENT-HUB" / weekly_name

    measurements: list[dict[str, object]] = []
    csv_rows: list[dict[str, str]] = []

    for device in ("mobile", "desktop"):
        organic = fetch_organic_results(device)
        rank, matched_url = find_rank(organic)
        rank_text = str(rank) if rank is not None else "not_in_top"
        top_result = organic[0][0] if organic else ""
        competitor_url = next(
            (href for href, _title in organic if TARGET_DOMAIN not in href),
            "",
        )
        notes = (
            f"Organic results={len(organic)}; "
            f"top_result={top_result or 'N/A'}; "
            f"capture=google_headless_{device}"
        )
        row = {
            "captured_at_utc": captured_at,
            "query": QUERY,
            "locale": LOCALE,
            "device": device,
            "search_engine": SEARCH_ENGINE,
            "target_url": matched_url,
            "rank_position": rank_text,
            "serp_features": "",
            "primary_competitor": competitor_url.replace("https://", "").split("/")[0],
            "competitor_rank": "1" if competitor_url else "",
            "source": SOURCE,
            "notes": notes,
        }
        csv_rows.append(row)
        measurements.append(
            {
                "device": device,
                "rank_position": rank if rank is not None else "not_in_top",
                "target_url": matched_url,
                "top_results": organic,
            }
        )
        print(f"{device}: rank={rank_text} url={matched_url}")

    append_baseline_rows(csv_rows)
    write_weekly_summary(captured_at, measurements, weekly_path)
    print(f"baseline={BASELINE_PATH.relative_to(ROOT)}")
    print(f"weekly={weekly_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
