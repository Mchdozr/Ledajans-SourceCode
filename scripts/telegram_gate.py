#!/usr/bin/env python3
"""Telegram insan kapisi — onay/red ve emir kuyrugu.

Dosya: AGENT-HUB/.telegram-gate.json
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "AGENT-HUB" / ".telegram-gate.json"
OFFSET_PATH = ROOT / "AGENT-HUB" / ".telegram-offset.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def approval_required() -> bool:
    """Canli apply icin Telegram onayi zorunlu mu?"""
    load_dotenv()
    flag = (os.environ.get("TELEGRAM_REQUIRE_APPROVAL") or "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return False
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    return bool(token and chat and ":" in token)


def default_gate() -> dict:
    return {
        "pending_apply": None,
        "orders": [],
        "updated_at": _now(),
    }


def load_gate() -> dict:
    if not GATE_PATH.exists():
        return default_gate()
    try:
        data = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_gate()
    if "orders" not in data:
        data["orders"] = []
    return data


def save_gate(data: dict) -> None:
    data["updated_at"] = _now()
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_offset() -> int:
    if not OFFSET_PATH.exists():
        return 0
    try:
        return int(json.loads(OFFSET_PATH.read_text(encoding="utf-8")).get("offset", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return 0


def save_offset(offset: int) -> None:
    OFFSET_PATH.write_text(
        json.dumps({"offset": offset}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def queue_apply_approval(commands: list[dict], *, phase: str = "apply-prep") -> dict:
    """Bekleyen APPLY listesini kuyruga al; yeni id uret."""
    gate = load_gate()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    item = {
        "id": f"APP-{stamp}",
        "phase": phase,
        "status": "awaiting_approval",
        "created_at": _now(),
        "decided_at": None,
        "commands": [
            {
                "tier": c.get("tier", ""),
                "command": c.get("command", ""),
                "summary": c.get("summary", ""),
                "pages": c.get("pages", ""),
                "visual": c.get("visual", ""),
                "risk": c.get("risk", ""),
                "source": c.get("source", ""),
            }
            for c in commands
        ],
    }
    gate["pending_apply"] = item
    save_gate(gate)
    return item


def get_pending_apply() -> dict | None:
    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending:
        return None
    if pending.get("status") == "awaiting_approval":
        return pending
    return None


def is_apply_approved() -> tuple[bool, str]:
    """Canli apply icin onay var mi?"""
    if not approval_required():
        return True, "Telegram onay kapisi kapali"

    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending:
        return False, "Bekleyen onay yok — once kuyruk olusturun"
    status = pending.get("status")
    if status == "approved":
        return True, f"Onayli: {pending.get('id')}"
    if status == "rejected":
        return False, f"Reddedildi: {pending.get('id')}"
    if status == "awaiting_approval":
        return False, f"Onay bekleniyor: {pending.get('id')} — Telegram: /onay veya /red"
    if status == "applied":
        return False, f"Zaten uygulandi: {pending.get('id')}"
    return False, f"Bilinmeyen durum: {status}"


def set_apply_decision(decision: str) -> tuple[bool, str]:
    """decision: approved | rejected"""
    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending or pending.get("status") != "awaiting_approval":
        return False, "Onay bekleyen APPLY yok"
    pending["status"] = decision
    pending["decided_at"] = _now()
    pending["decided_by"] = "telegram"
    gate["pending_apply"] = pending
    save_gate(gate)
    return True, f"{pending['id']} → {decision}"


def mark_apply_done() -> None:
    gate = load_gate()
    pending = gate.get("pending_apply")
    if pending and pending.get("status") == "approved":
        pending["status"] = "applied"
        pending["applied_at"] = _now()
        gate["pending_apply"] = pending
        save_gate(gate)


def add_order(text: str) -> dict:
    gate = load_gate()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    order = {
        "id": f"ORD-{stamp}",
        "text": text.strip(),
        "status": "open",
        "created_at": _now(),
    }
    orders = gate.get("orders") or []
    orders.insert(0, order)
    gate["orders"] = orders[:50]
    save_gate(gate)
    # Ajanlarin okumasi icin markdown
    orders_md = ROOT / "AGENT-HUB" / "TELEGRAM-ORDERS.md"
    lines = [
        "# Telegram Emirleri",
        "",
        "ceo-orchestrator her turda acik emirleri okur.",
        "",
    ]
    for o in gate["orders"][:20]:
        lines.append(
            f"- `{o['id']}` [{o['status']}] {o['created_at']}: {o['text']}"
        )
    lines.append("")
    orders_md.write_text("\n".join(lines), encoding="utf-8")
    return order


def format_pending_summary() -> str:
    from coalition_common import format_apply_human_list

    pending = load_gate().get("pending_apply")
    if not pending:
        return "Bekleyen onay yok."

    status = pending.get("status", "")
    status_tr = {
        "awaiting_approval": "Senin onayin bekleniyor",
        "approved": "Onayladin — henuz uygulanmadi (/uygula veya sonraki tur)",
        "rejected": "Reddettin — uygulanmayacak",
        "applied": "Uygulandi",
    }.get(status, status)

    cmds = pending.get("commands") or []
    lines = [
        "LEDAJANS — BEKLEYEN DEGISIKLIK",
        f"Kod: {pending.get('id')}",
        f"Durum: {status_tr}",
        f"Madde: {len(cmds)}",
        "",
        "Sitede ne degisecek:",
        format_apply_human_list(cmds),
        "",
        "Kararin:",
        "/onay  — bunlari uygula",
        "/red   — hicbirini uygulama",
    ]
    return "\n".join(lines)
