#!/usr/bin/env python3
"""Lighthouse CWV ölçümü — mobil medyan + desktop gate + rapor."""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import AGENT_HUB, DATA_BASELINES, ROOT

DEFAULT_URLS = [
    "https://ledajans.com/",
    "https://ledajans.com/led-ekran/",
    "https://ledajans.com/ic-mekan-led-ekran/",
    "https://ledajans.com/dis-mekan-led-ekran/",
]

MOBILE_TARGETS = {"perf": 0.80, "lcp_ms": 2500, "tbt_ms": 200, "cls": 0.1}
DESKTOP_GATES = {"perf": 0.90, "lcp_ms": 1500, "tbt_ms": 50, "cls": 0.1}

METRIC_KEYS = {
    "perf": ("categories", "performance", "score"),
    "lcp_ms": ("audits", "largest-contentful-paint", "numericValue"),
    "tbt_ms": ("audits", "total-blocking-time", "numericValue"),
    "cls": ("audits", "cumulative-layout-shift", "numericValue"),
    "fcp_ms": ("audits", "first-contentful-paint", "numericValue"),
    "si_ms": ("audits", "speed-index", "numericValue"),
}


def _get_nested(data: dict, path: tuple[str, ...]):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def extract_metrics(report: dict) -> dict:
    out: dict[str, float | None] = {}
    for name, path in METRIC_KEYS.items():
        val = _get_nested(report, path)
        out[name] = float(val) if val is not None else None
    return out


def median_metrics(runs: list[dict]) -> dict:
    keys = list(METRIC_KEYS.keys())
    med: dict[str, float | None] = {}
    for k in keys:
        vals = [r[k] for r in runs if r.get(k) is not None]
        med[k] = statistics.median(vals) if vals else None
    return med


def run_lighthouse(url: str, form_factor: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx",
        "--yes",
        "lighthouse",
        url,
        "--only-categories=performance",
        "--output=json",
        f"--output-path={out_path}",
        "--quiet",
        "--chrome-flags=--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-extensions",
    ]
    if form_factor == "mobile":
        cmd.append("--form-factor=mobile")
    else:
        cmd.extend(["--preset=desktop", "--form-factor=desktop"])

    env = os.environ.copy()
    env.setdefault("CHROME_PATH", "/usr/local/bin/google-chrome")
    print(f"  >> lighthouse {form_factor}: {url}")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300, env=env)
    if result.returncode != 0:
        print(result.stderr[-500:] if result.stderr else "lighthouse failed")
    return result.returncode


def gate_check(metrics: dict, gates: dict) -> tuple[bool, list[str]]:
    fails: list[str] = []
    perf = metrics.get("perf")
    if perf is not None and perf < gates["perf"]:
        fails.append(f"perf={perf:.2f} < {gates['perf']}")
    lcp = metrics.get("lcp_ms")
    if lcp is not None and lcp > gates["lcp_ms"]:
        fails.append(f"lcp={lcp:.0f}ms > {gates['lcp_ms']}ms")
    tbt = metrics.get("tbt_ms")
    if tbt is not None and tbt > gates["tbt_ms"]:
        fails.append(f"tbt={tbt:.0f}ms > {gates['tbt_ms']}ms")
    cls = metrics.get("cls")
    if cls is not None and cls > gates["cls"]:
        fails.append(f"cls={cls:.3f} > {gates['cls']}")
    return len(fails) == 0, fails


def fmt_metrics(m: dict) -> str:
    perf = m.get("perf")
    lcp = m.get("lcp_ms")
    tbt = m.get("tbt_ms")
    cls = m.get("cls")
    parts = [f"Perf={int(perf * 100) if perf else '?'}"]
    parts.append(f"LCP={lcp / 1000:.1f}s" if lcp else "LCP=?")
    parts.append(f"TBT={tbt:.0f}ms" if tbt else "TBT=?")
    parts.append(f"CLS={cls:.3f}" if cls is not None else "CLS=?")
    return " ".join(parts)


def write_report(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CWV Iteration Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Mobile (median of runs)",
        "",
        "| URL | Perf | LCP | TBT | CLS |",
        "|-----|------|-----|-----|-----|",
    ]
    for row in payload["mobile"]:
        m = row["metrics"]
        perf = int(m["perf"] * 100) if m.get("perf") else "?"
        lcp = f"{m['lcp_ms'] / 1000:.1f}s" if m.get("lcp_ms") else "?"
        tbt = f"{m['tbt_ms']:.0f}ms" if m.get("tbt_ms") else "?"
        cls = f"{m['cls']:.3f}" if m.get("cls") is not None else "?"
        lines.append(f"| {row['url']} | {perf} | {lcp} | {tbt} | {cls} |")

    lines.extend(["", "## Desktop gate", ""])
    for row in payload["desktop"]:
        m = row["metrics"]
        ok, fails = gate_check(m, DESKTOP_GATES)
        status = "PASS" if ok else "FAIL: " + "; ".join(fails)
        lines.append(f"- {row['url']}: {status}")

    home_mobile = next((r for r in payload["mobile"] if r["url"].rstrip("/") == "https://ledajans.com"), None)
    if home_mobile:
        ok, fails = gate_check(home_mobile["metrics"], MOBILE_TARGETS)
        lines.extend(["", "## Mobile target (homepage)", ""])
        lines.append(f"- {'PASS' if ok else 'FAIL: ' + '; '.join(fails)}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", dest="urls", help="URL (tekrarlanabilir)")
    parser.add_argument("--mobile-runs", type=int, default=3)
    parser.add_argument("--desktop-runs", type=int, default=1)
    parser.add_argument("--label", default="", help="Dosya etiketi (örn. pre, iter1)")
    parser.add_argument("--homepage-only", action="store_true")
    args = parser.parse_args()

    urls = args.urls or DEFAULT_URLS
    if args.homepage_only:
        urls = ["https://ledajans.com/"]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    label = args.label or "live"
    tag = f"{stamp}-{label}"

    payload: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": tag,
        "mobile": [],
        "desktop": [],
    }

    for url in urls:
        mobile_runs: list[dict] = []
        for i in range(args.mobile_runs):
            out = DATA_BASELINES / f"audit-mobile-{tag}-{i}.json"
            rc = run_lighthouse(url, "mobile", out)
            if rc == 0 and out.is_file():
                with out.open(encoding="utf-8") as f:
                    mobile_runs.append(extract_metrics(json.load(f)))
            time.sleep(2)
        if mobile_runs:
            med = median_metrics(mobile_runs)
            payload["mobile"].append({"url": url, "metrics": med, "runs": mobile_runs})
            print(f"  mobile median {url}: {fmt_metrics(med)}")

        desktop_runs: list[dict] = []
        slug = url.replace("https://ledajans.com", "").strip("/") or "home"
        for i in range(args.desktop_runs):
            out = DATA_BASELINES / f"audit-desktop-{tag}-{slug}-{i}.json"
            rc = run_lighthouse(url, "desktop", out)
            if rc == 0 and out.is_file():
                with out.open(encoding="utf-8") as f:
                    desktop_runs.append(extract_metrics(json.load(f)))
            time.sleep(2)
        if desktop_runs:
            med = median_metrics(desktop_runs)
            payload["desktop"].append({"url": url, "metrics": med, "runs": desktop_runs})
            ok, fails = gate_check(med, DESKTOP_GATES)
            print(f"  desktop {url}: {fmt_metrics(med)} [{'OK' if ok else 'FAIL'}]")

    summary_path = DATA_BASELINES / f"cwv-summary-{tag}.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    report_path = AGENT_HUB / "REPORTS" / "cwv-iteration-latest.md"
    write_report(payload, report_path)
    print(f"\nOK: {summary_path}")
    print(f"OK: {report_path}")

    home = next((r for r in payload["mobile"] if "ledajans.com/" == r["url"] or r["url"] == "https://ledajans.com/"), None)
    if home:
        ok, _ = gate_check(home["metrics"], MOBILE_TARGETS)
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
