#!/usr/bin/env python3
"""QA + Risk geçtiyse T1/T2 uygulama komutlarını çalıştır."""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from coalition_common import deploy_locked, extract_apply_commands, hub_dir  # noqa: E402


def run_command(command: str, dry_run: bool) -> int:
    parts = shlex.split(command, posix=False)
    if not parts:
        return 0

    script = parts[0].lower()
    if script.endswith("deploy-to-wordpress.py"):
        args = [sys.executable, str(ROOT / "deploy-to-wordpress.py")]
        if dry_run:
            args.append("--dry-run")
        if "--blog-only" in parts:
            args.append("--blog-only")
    elif script.endswith("publish-blog-post.py"):
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
        f"- Komut sayısı: {len(results)}",
        "",
        "## Sonuçlar",
    ]
    for item in results:
        status = "OK" if item["exit_code"] == 0 else f"FAIL({item['exit_code']})"
        lines.append(f"- [{item['tier']}] {status} — {item['command']} (kaynak: {item['source']})")
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="LEDAJANS koalisyon uygulama")
    parser.add_argument("--dry-run", action="store_true", help="Canlı deploy yapma")
    parser.add_argument("--force", action="store_true", help="Deploy kilidini yoksay (acil)")
    args = parser.parse_args()

    locked, reason = deploy_locked()
    if locked and not args.force:
        print(f"Deploy kilidi aktif: {reason}")
        return 2

    commands = extract_apply_commands()
    if not commands:
        print("Uygulanacak [APPLY:T1/T2] komutu yok.")
        return 0

    results: list[dict] = []
    for item in commands:
        code = run_command(item["command"], dry_run=args.dry_run)
        results.append({**item, "exit_code": code})
        if code != 0 and not args.dry_run:
            write_apply_report(results, args.dry_run)
            return code

    if not args.dry_run:
        smoke = subprocess.call(
            ["powershell", "-File", str(ROOT / "scripts/seo-smoke-test.ps1")],
            cwd=str(ROOT),
        )
        if smoke != 0:
            print(f"seo-smoke-test uyarı: exit {smoke}")

    write_apply_report(results, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
