#!/usr/bin/env python3
"""Telegram komut dinleyici — onay/red/emir.

Kullanim:
  python3 scripts/telegram_bot_poll.py           # tek tur
  python3 scripts/telegram_bot_poll.py --loop    # surekli (30sn)

Komutlar (sadece TELEGRAM_CHAT_ID):
  /yardim  /durum  /bekleyen  /alarm
  /onay    /red
  /emir <metin>
  /uygula  (onayliysa coalition-apply calistirir)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from telegram_gate import (  # noqa: E402
    add_order,
    format_pending_summary,
    is_apply_approved,
    load_gate,
    load_offset,
    save_offset,
    set_apply_decision,
)
from telegram_notify import build_coalition_message, send_message, telegram_config  # noqa: E402


HELP = """LEDAJANS komutlari:
/yardim — bu liste
/durum — koalisyon ozeti
/bekleyen — onay bekleyen APPLY (madde durumlari)
/alarm — durum + alarmlar
/onay 2 — sadece 2. maddeyi onayla
/red 1 — sadece 1. maddeyi reddet
/onay 1,3 — secili maddeleri onayla
/onay hepsi — hepsini onayla
/red hepsi — hepsini reddet
/uygula — sadece ONAYLI maddeleri canli uygula
/emir <metin> — ajanlara emir birak

Sadece senin chat'inden komut kabul edilir."""


def api_get(token: str, method: str, params: dict | None = None) -> dict:
    qs = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"https://api.telegram.org/bot{token}/{method}{qs}"
    with urllib.request.urlopen(url, timeout=35) as resp:
        return json.loads(resp.read().decode("utf-8"))


def handle_command(text: str) -> str:
    raw = text.strip()
    if not raw.startswith("/"):
        return "Komut / ile baslamali. /yardim"

    # /cmd@BotName args
    parts = raw.split(maxsplit=1)
    cmd = parts[0].split("@", 1)[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/yardim", "/help", "/start"):
        return HELP

    if cmd in ("/durum", "/status", "/alarm"):
        return build_coalition_message()

    if cmd in ("/bekleyen", "/pending"):
        return format_pending_summary()

    if cmd in ("/onay", "/approve", "/evet"):
        ok, msg = set_apply_decision("approved", arg)
        if not ok:
            return f"Olmadi: {msg}"
        return (
            f"ONAYLANDI\n{msg}\n\n"
            f"{format_pending_summary()}\n\n"
            "Canli uygulama: /uygula (sadece ONAYLI maddeler)"
        )

    if cmd in ("/red", "/reject", "/hayir"):
        ok, msg = set_apply_decision("rejected", arg)
        if not ok:
            return f"Olmadi: {msg}"
        return f"REDDEDILDI\n{msg}\n\n{format_pending_summary()}"

    if cmd in ("/emir", "/order"):
        if not arg:
            return "Kullanim: /emir <metin>\nOrnek: /emir led ekran title kisalt"
        order = add_order(arg)
        return (
            f"Emir alindi: {order['id']}\n"
            f"{order['text']}\n\n"
            "ceo-orchestrator sonraki turda TELEGRAM-ORDERS.md okuyacak."
        )

    if cmd in ("/uygula", "/apply"):
        approved, reason = is_apply_approved()
        if not approved:
            return f"Uygulanamaz: {reason}"
        # Insan /uygula: FB kilidini as (--force). Telegram onayi zaten kapı.
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/coalition-apply.py"),
                "--force",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        out = (proc.stdout or "")[-1500:]
        err = (proc.stderr or "")[-500:]
        if proc.returncode == 0:
            return f"UYGULAMA OK\n{out}"
        return f"UYGULAMA HATA exit={proc.returncode}\n{out}\n{err}"

    return f"Bilinmeyen komut: {cmd}\n\n{HELP}"


def process_updates(once: bool) -> int:
    cfg = telegram_config()
    if not cfg:
        print("Telegram config yok")
        return 1
    token, allowed_chat = cfg
    offset = load_offset()

    while True:
        try:
            data = api_get(
                token,
                "getUpdates",
                {"offset": offset, "timeout": 25 if not once else 0},
            )
        except urllib.error.HTTPError as e:
            print(f"getUpdates HTTP {e.code}: {e.read()[:200]}")
            return 1
        except Exception as e:
            print(f"getUpdates hata: {e}")
            if once:
                return 1
            time.sleep(5)
            continue

        if not data.get("ok"):
            print(f"API not ok: {data}")
            return 1

        for upd in data.get("result") or []:
            offset = max(offset, int(upd["update_id"]) + 1)
            msg = upd.get("message") or upd.get("edited_message")
            if not msg:
                continue
            chat = msg.get("chat") or {}
            chat_id = str(chat.get("id", ""))
            if chat_id != str(allowed_chat):
                print(f"Yabanci chat yok sayildi: {chat_id}")
                continue
            text = (msg.get("text") or "").strip()
            if not text:
                continue
            print(f"Komut: {text[:80]}")
            reply = handle_command(text)
            send_message(reply)

        save_offset(offset)
        if once:
            return 0
        # long-poll already waited; small pause
        time.sleep(0.5)


def main() -> int:
    parser = argparse.ArgumentParser(description="LEDAJANS Telegram bot poll")
    parser.add_argument("--loop", action="store_true", help="Surekli dinle")
    parser.add_argument(
        "--announce",
        action="store_true",
        help="Bot hazir mesaji gonder",
    )
    args = parser.parse_args()

    if args.announce:
        send_message("LEDAJANS bot hazir.\n" + HELP)

    return process_updates(once=not args.loop)


if __name__ == "__main__":
    raise SystemExit(main())
