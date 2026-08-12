#!/usr/bin/env python3
"""QA + Risk gectiyse T1/T2 uygulama komutlarini calistir."""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from coalition_common import (  # noqa: E402
    deploy_locked,
    extract_apply_commands,
    hub_dir,
)
from telegram_gate import (  # noqa: E402
    approval_required,
    format_pending_summary,
    get_approved_commands,
    is_apply_approved,
    mark_apply_done,
    queue_apply_approval,
)
from telegram_notify import send_message  # noqa: E402


def run_command(command: str, dry_run: bool) -> int:
    parts = shlex.split(command, posix=True)
    if not parts:
        return 0

    script = parts[0].lower()
    if script.endswith(".py") and not script.endswith("deploy-to-wordpress.py"):
        # Relative script path → python3
        if script.endswith("publish-blog-post.py"):
            blog_path = parts[1] if len(parts) > 1 else ""
            args = [sys.executable, str(ROOT / "scripts/publish-blog-post.py"), blog_path]
            if dry_run:
                args.append("--dry-run")
            elif "--publish" in parts:
                args.append("--publish")
        elif script.endswith("install-mobile-perf-plugin.py"):
            args = [sys.executable, str(ROOT / "scripts/install-mobile-perf-plugin.py")]
            if dry_run:
                args.append("--dry-run")
        else:
            script_path = ROOT / parts[0] if not Path(parts[0]).is_absolute() else Path(parts[0])
            args = [sys.executable, str(script_path), *parts[1:]]
            if dry_run and "--dry-run" not in args:
                args.append("--dry-run")
    elif script.endswith("deploy-to-wordpress.py"):
        args = [sys.executable, str(ROOT / "deploy-to-wordpress.py")]
        if dry_run:
            args.append("--dry-run")
        if "--blog-only" in parts:
            args.append("--blog-only")
    else:
        args = parts

    print(f"-> {' '.join(args)}")
    return subprocess.call(args, cwd=str(ROOT))


def write_apply_report(results: list[dict], dry_run: bool) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = hub_dir() / "REPORTS" / f"{today}-coalition-apply.md"
    lines = [
        f"# Coalition Apply - {today}",
        "",
        f"- Mod: {'dry-run' if dry_run else 'live'}",
        f"- Komut sayisi: {len(results)}",
        "",
        "## Sonuclar",
    ]
    for item in results:
        status = "OK" if item["exit_code"] == 0 else f"FAIL({item['exit_code']})"
        lines.append(
            f"- [{item['tier']}] {status} — {item['command']} (kaynak: {item['source']})"
        )
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")


def request_telegram_approval(commands: list[dict]) -> None:
    queue_apply_approval(commands)
    send_message(
        "LEDAJANS — ONAY GEREKIYOR\n"
        "Sitede henuz bir sey degismedi.\n\n"
        + format_pending_summary()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="LEDAJANS koalisyon uygulama")
    parser.add_argument("--dry-run", action="store_true", help="Canli deploy yapma")
    parser.add_argument("--force", action="store_true", help="Deploy kilidini yoksay")
    parser.add_argument(
        "--skip-telegram-gate",
        action="store_true",
        help="Telegram insan onayini atla",
    )
    args = parser.parse_args()

    locked, reason = deploy_locked()
    if locked and not args.force:
        print(f"Deploy kilidi aktif: {reason}")
        return 2

    report_commands = extract_apply_commands()

    # Dry-run: rapor APPLY + Telegram kuyrugu
    if args.dry_run:
        if not report_commands:
            print("Uygulanacak [APPLY:T1/T2] komutu yok.")
            return 0
        results: list[dict] = []
        for item in report_commands:
            code = run_command(item["command"], dry_run=True)
            results.append({**item, "exit_code": code})
        write_apply_report(results, True)
        if approval_required() and not args.skip_telegram_gate:
            request_telegram_approval(report_commands)
            print("Telegram onay istegi gonderildi (/onay 2, /red 1, /onay hepsi)")
        return 0

    # Canli: once Telegram onayli maddeler (raporda APPLY kalmasa bile)
    commands: list[dict] = []
    if approval_required() and not args.skip_telegram_gate:
        ok, why = is_apply_approved()
        if not ok:
            print(f"Telegram kapisi: {why}")
            if "Bekleyen onay yok" in why and report_commands:
                request_telegram_approval(report_commands)
            return 3
        commands = get_approved_commands()
        if not commands:
            print("Onayli madde yok.")
            return 3
        print(f"Telegram onayli {len(commands)} madde uygulanacak.")
    else:
        commands = report_commands
        if not commands:
            print("Uygulanacak [APPLY:T1/T2] komutu yok.")
            return 0

    results = []
    for item in commands:
        code = run_command(item["command"], dry_run=False)
        results.append({**item, "exit_code": code})
        if code != 0:
            write_apply_report(results, False)
            return code

    write_apply_report(results, False)
    mark_apply_done()
    n = len(results)
    send_message(f"LEDAJANS: canli APPLY tamamlandi ({n} madde).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
