#!/usr/bin/env python3
"""Koalisyon döngüsü: keşif, uygulama hazırlığı veya kapanış."""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from coalition_common import (  # noqa: E402
    check_keyword_alarms,
    deploy_locked,
    hub_dir,
    repo_root,
    write_coalition_status,
)


def run_script(rel_path: str, *args: str) -> int:
    cmd = [sys.executable, str(ROOT / rel_path), *args]
    print(f"-> {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(ROOT))


def find_latest_gsc_export() -> Path | None:
    data_dir = hub_dir() / "DATA"
    if not data_dir.exists():
        return None
    candidates = sorted(data_dir.glob("gsc-performance-*/Sorgular.csv"), reverse=True)
    return candidates[0] if candidates else None


def maybe_update_serp_baseline() -> None:
    if find_latest_gsc_export():
        run_script("scripts/update-serp-baseline-from-gsc.py")


def write_cycle_report(phase: str, alarms: list[dict], locked: bool, reason: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = hub_dir() / "REPORTS" / f"{today}-coalition-cycle.md"
    lines = [
        f"# Coalition Cycle - {today} ({phase})",
        "",
        f"- Deploy kilidi: {'EVET' if locked else 'HAYIR'}",
        f"- Kilit nedeni: {reason or '-'}",
        f"- Alarm sayısı: {len(alarms)}",
        "",
        "## Alarmlar",
    ]
    if alarms:
        for alarm in alarms[:20]:
            lines.append(f"- [{alarm.get('tier')}] {alarm.get('query', alarm.get('category'))}: {alarm.get('reason')}")
    else:
        lines.append("- Alarm yok.")
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapor: {report}")


def main() -> int:
    parser = argparse.ArgumentParser(description="LEDAJANS koalisyon döngüsü")
    parser.add_argument(
        "--phase",
        choices=["discover", "apply-prep", "close"],
        default="discover",
        help="Tur fazı",
    )
    args = parser.parse_args()

    print(f"Koalisyon turu: {args.phase} | repo: {repo_root()}")

    if args.phase == "discover":
        maybe_update_serp_baseline()
        run_script("AGENT-HUB/auto_orchestrator.py")
        run_script("AGENT-HUB/live_dashboard.py")

    alarms = check_keyword_alarms()
    locked, reason = deploy_locked()
    status_path = write_coalition_status(
        phase=args.phase,
        alarms=alarms,
        deploy_locked_flag=locked,
        deploy_lock_reason=reason,
    )
    write_cycle_report(args.phase, alarms, locked, reason)

    print(f"Durum: {status_path}")
    print(f"Alarmlar: {len(alarms)} | Deploy kilidi: {locked}")
    if locked:
        print(f"Kilit nedeni: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
