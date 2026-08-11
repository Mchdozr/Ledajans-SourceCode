#!/usr/bin/env python3
"""Telegram bildirim — koalisyon ozeti / alarm / blocker.

.env:
  TELEGRAM_BOT_TOKEN=123:ABC...
  TELEGRAM_CHAT_ID=123456789

Kullanim:
  python3 scripts/telegram_notify.py --text "merhaba"
  python3 scripts/telegram_notify.py --coalition-status
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def telegram_config() -> tuple[str, str] | None:
    load_dotenv()
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat_id:
        return None
    if ":" not in token or token.startswith("YOUR"):
        return None
    return token, chat_id


def send_message(text: str, *, disable_preview: bool = True) -> bool:
    cfg = telegram_config()
    if not cfg:
        print("Telegram atlandi: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID yok veya gecersiz")
        return False
    token, chat_id = cfg
    # Telegram limit ~4096
    if len(text) > 4000:
        text = text[:3990] + "\n…"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true" if disable_preview else "false",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if not body.get("ok"):
            print(f"Telegram API hata: {body}")
            return False
        print("Telegram OK")
        return True
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:300]
        print(f"Telegram HTTP {e.code}: {err}")
        return False
    except Exception as e:
        print(f"Telegram hata: {type(e).__name__}: {e}")
        return False


def build_coalition_message() -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    from coalition_common import (  # noqa: E402
        check_keyword_alarms,
        deploy_locked,
        extract_feedback_state,
        hub_dir,
    )

    status_path = hub_dir() / ".coalition-status.json"
    phase = "-"
    if status_path.exists():
        data = json.loads(status_path.read_text(encoding="utf-8"))
        phase = data.get("phase", "-")

    alarms = check_keyword_alarms()
    locked, reason = deploy_locked()
    open_fb, _ = extract_feedback_state()
    p0 = [a for a in alarms if a.get("tier") == "P0"]
    p1 = [a for a in alarms if a.get("tier") == "P1"]

    lines = [
        "LEDAJANS Koalisyon",
        f"Faz: {phase}",
        f"Deploy kilidi: {'EVET' if locked else 'HAYIR'}"
        + (f" ({reason})" if reason else ""),
        f"Acik FB/OBJECT: {open_fb}",
        f"Alarm: P0={len(p0)} P1={len(p1)} (toplam {len(alarms)})",
    ]
    if alarms:
        lines.append("")
        lines.append("Oncelikli:")
        for a in alarms[:8]:
            label = a.get("query") or a.get("category")
            lines.append(f"- [{a.get('tier')}] {label}: {a.get('reason')}")
        if len(alarms) > 8:
            lines.append(f"… +{len(alarms) - 8} alarm")

    lines.append("")
    lines.append("Yapilacak: acik FB kapat → T1/T2 apply; P0 led ekran savunma")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="LEDAJANS Telegram bildirim")
    parser.add_argument("--text", help="Serbest metin gonder")
    parser.add_argument(
        "--coalition-status",
        action="store_true",
        help="Koalisyon ozeti gonder",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gondermeden metni yazdir",
    )
    args = parser.parse_args()

    if args.coalition_status:
        text = build_coalition_message()
    elif args.text:
        text = args.text
    else:
        parser.error("--text veya --coalition-status gerekli")

    if args.dry_run:
        print(text)
        return 0

    return 0 if send_message(text) else 1


if __name__ == "__main__":
    raise SystemExit(main())
