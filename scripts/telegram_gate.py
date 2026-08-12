#!/usr/bin/env python3
"""Telegram insan kapisi — onay/red ve emir kuyrugu.

Dosya: AGENT-HUB/.telegram-gate.json
"""
from __future__ import annotations

import json
import os
import re
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
                "n": i,
                "tier": c.get("tier", ""),
                "command": c.get("command", ""),
                "summary": c.get("summary", ""),
                "pages": c.get("pages", ""),
                "visual": c.get("visual", ""),
                "risk": c.get("risk", ""),
                "source": c.get("source", ""),
                "decision": "pending",  # pending | approved | rejected
            }
            for i, c in enumerate(commands, start=1)
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
    if pending.get("status") in ("awaiting_approval", "partial", "approved"):
        return pending
    return None


def _refresh_batch_status(pending: dict) -> None:
    cmds = pending.get("commands") or []
    if not cmds:
        pending["status"] = "rejected"
        return
    decisions = [c.get("decision", "pending") for c in cmds]
    if all(d == "pending" for d in decisions):
        pending["status"] = "awaiting_approval"
    elif all(d != "pending" for d in decisions):
        pending["status"] = (
            "approved" if any(d == "approved" for d in decisions) else "rejected"
        )
    else:
        pending["status"] = "partial"  # bazilari kararlasti
    pending["decided_at"] = _now()
    pending["decided_by"] = "telegram"


def parse_item_numbers(arg: str, total: int) -> tuple[list[int] | None, str]:
    """arg: '' / hepsi / all / 2 / 1,3 / 1-3 → index list (1-based) veya None=hepsi."""
    raw = (arg or "").strip().lower()
    if raw in ("", "hepsi", "hepsi.", "all", "tumu", "tümü", "*"):
        return None, "hepsi"
    nums: set[int] = set()
    for token in re.split(r"[,\s]+", raw):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, _, b = token.partition("-")
            try:
                start, end = int(a), int(b)
            except ValueError:
                return [], f"Gecersiz aralik: {token}"
            for n in range(min(start, end), max(start, end) + 1):
                nums.add(n)
        else:
            try:
                nums.add(int(token))
            except ValueError:
                return [], f"Gecersiz madde no: {token}"
    invalid = [n for n in nums if n < 1 or n > total]
    if invalid:
        return [], f"Olmayan madde: {invalid} (1-{total})"
    return sorted(nums), ""


def set_apply_decision(
    decision: str,
    arg: str = "",
) -> tuple[bool, str]:
    """decision: approved | rejected. arg: madde no (2 veya 1,3) veya hepsi."""
    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending:
        return False, "Onay bekleyen paket yok"
    if pending.get("status") == "applied":
        return False, "Bu paket zaten uygulandi"

    cmds = pending.get("commands") or []
    if not cmds:
        return False, "Pakette madde yok"

    # Eski kayitlarda decision yoksa ekle
    for i, c in enumerate(cmds, start=1):
        c.setdefault("n", i)
        c.setdefault("decision", "pending")

    indices, err = parse_item_numbers(arg, len(cmds))
    if err and indices == []:
        return False, err

    targets = range(1, len(cmds) + 1) if indices is None else indices
    changed = []
    for n in targets:
        cmds[n - 1]["decision"] = decision
        changed.append(str(n))

    _refresh_batch_status(pending)
    pending["commands"] = cmds
    gate["pending_apply"] = pending
    save_gate(gate)

    label = "ONAY" if decision == "approved" else "RED"
    return True, f"{label} → madde {', '.join(changed)} | paket: {pending['status']}"


def is_apply_approved() -> tuple[bool, str]:
    """Canli apply icin en az 1 onayli madde var mi?"""
    if not approval_required():
        return True, "Telegram onay kapisi kapali"

    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending:
        return False, "Bekleyen onay yok — once kuyruk olusturun"
    if pending.get("status") == "rejected":
        return False, f"Reddedildi: {pending.get('id')}"
    if pending.get("status") == "applied":
        return False, f"Zaten uygulandi: {pending.get('id')}"

    cmds = pending.get("commands") or []
    # Eski kayit: paket seviyesi onay, madde decision yok
    if pending.get("status") == "approved" and cmds and all(
        "decision" not in c for c in cmds
    ):
        return True, f"Paket onayli (eski format): {pending.get('id')}"

    approved = [c for c in cmds if c.get("decision") == "approved"]
    if approved:
        return True, f"{len(approved)} madde onayli ({pending.get('id')})"
    return (
        False,
        "Henuz onayli madde yok — ornek: /onay 2 veya /onay hepsi",
    )


def get_approved_commands() -> list[dict]:
    """Uygulanacak (onayli) maddeler."""
    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending:
        return []
    cmds = pending.get("commands") or []
    # Eski format: status=approved ve decision yok → hepsi
    if pending.get("status") == "approved" and cmds and all(
        "decision" not in c for c in cmds
    ):
        return list(cmds)
    return [c for c in cmds if c.get("decision") == "approved"]


def mark_apply_done() -> None:
    gate = load_gate()
    pending = gate.get("pending_apply")
    if not pending:
        return
    cmds = pending.get("commands") or []
    for c in cmds:
        if c.get("decision") == "approved":
            c["decision"] = "applied"
    pending["commands"] = cmds
    if any(c.get("decision") == "pending" for c in cmds):
        pending["status"] = "partial"
        gate["pending_apply"] = pending
    else:
        pending["status"] = "applied"
        pending["applied_at"] = _now()
        # Arsivle; /bekleyen artik bos kalsin
        hist = gate.get("apply_history") or []
        hist.insert(0, pending)
        gate["apply_history"] = hist[:20]
        gate["pending_apply"] = None
        gate["last_apply"] = {
            "id": pending.get("id"),
            "applied_at": pending.get("applied_at"),
            "summary": ", ".join(
                c.get("summary", "")[:60]
                for c in cmds
                if c.get("decision") == "applied"
            ),
        }
    save_gate(gate)


def format_pending_summary() -> str:
    gate = load_gate()
    pending = gate.get("pending_apply")

    # Sadece gercekten bekleyen / uygulanabilir paket
    if not pending or pending.get("status") in ("applied", "rejected", None):
        last = gate.get("last_apply") or {}
        lines = [
            "LEDAJANS — BEKLEYEN YOK",
            "",
            "Simdi onay bekleyen degisiklik yok.",
            "Ajanlar yeni APPLY uretince Telegram'a ONAY GEREKIYOR gelir.",
        ]
        if last.get("id"):
            lines.extend(
                [
                    "",
                    f"Son uygulanan: {last.get('id')}",
                    f"Zaman: {last.get('applied_at', '—')}",
                    f"Ozet: {last.get('summary') or '—'}",
                ]
            )
        return "\n".join(lines)

    status = pending.get("status", "")
    status_tr = {
        "awaiting_approval": "Senin onayin bekleniyor (madde sec)",
        "partial": "Kismi karar verildi — kalan maddeler bekliyor",
        "approved": "Secilenler onayli — /uygula ile uygula",
    }.get(status, status)

    cmds = pending.get("commands") or []
    dec_tr = {
        "pending": "bekliyor",
        "approved": "ONAYLI",
        "rejected": "RED",
        "applied": "uygulandi",
    }

    lines = [
        "LEDAJANS — BEKLEYEN DEGISIKLIK",
        f"Kod: {pending.get('id')}",
        f"Durum: {status_tr}",
        f"Madde: {len(cmds)}",
        "",
        "Sitede ne degisecek:",
    ]
    for c in cmds:
        n = c.get("n", "?")
        d = dec_tr.get(c.get("decision", "pending"), c.get("decision"))
        lines.append(f"{n}) [{c.get('tier', '?')}] [{d}] {c.get('summary', 'Guncelleme')}")
        lines.append(f"   Sayfa: {c.get('pages', '—')}")
        lines.append(f"   Gorunur etki: {c.get('visual', '—')}")
        lines.append(f"   Risk: {c.get('risk', '—')}")
        lines.append("")

    lines.extend(
        [
            "Tek tek karar ver:",
            "/onay 2        → sadece 2. maddeyi onayla",
            "/red 1         → sadece 1. maddeyi reddet",
            "/onay 2,3      → 2 ve 3'u onayla",
            "/onay hepsi    → hepsini onayla",
            "/red hepsi     → hepsini reddet",
            "/uygula        → onayladiklarini uygula",
        ]
    )
    return "\n".join(lines)


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
