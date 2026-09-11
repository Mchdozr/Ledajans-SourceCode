#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from coalition_common import (  # noqa: E402
    check_keyword_alarms,
    deploy_locked,
    extract_feedback_state,
    write_coalition_status,
)

HUB = ROOT / "AGENT-HUB"
REPORTS = HUB / "REPORTS"
STATE_FILE = HUB / ".auto-orchestrator-state.json"
MASTER_PLAN = HUB / "MASTER-PLAN.md"
TASKS = HUB / "TASKS.md"
BLOCKER_ALERT = HUB / "BLOCKER-ALERT.md"
KEYWORD_GUARD = HUB / "KEYWORD-GUARD.json"


ROLE_TO_TASK_ID = {
    "tech-seo": "P-001",
    "gsc": "P-002",
    "content": "P-003",
    "internal-link": "P-004",
    "serp-watch": "P-005",
}


FEEDBACK_PATTERN = re.compile(
    r"\[TO:([a-z0-9-]+)\]\s*\[FB:([A-Za-z0-9_-]+)\]\s*(.+)",
    flags=re.IGNORECASE,
)
RESOLVED_PATTERN = re.compile(r"\[RESOLVED:([A-Za-z0-9_-]+)\]", flags=re.IGNORECASE)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def get_report_files() -> list[Path]:
    files = sorted(REPORTS.glob("*.md"))
    excluded = {"orchestrator"}
    filtered = []
    for file in files:
        name = file.stem
        if any(token in name for token in excluded):
            continue
        filtered.append(file)
    return filtered


def calc_signature(report_files: list[Path]) -> str:
    payload = []
    for file in report_files:
        stat = file.stat()
        payload.append(f"{file.name}:{stat.st_mtime_ns}:{stat.st_size}")
    if KEYWORD_GUARD.exists():
        stat = KEYWORD_GUARD.stat()
        payload.append(f"KEYWORD-GUARD.json:{stat.st_mtime_ns}:{stat.st_size}")
    raw = "|".join(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_signature": "", "last_run": ""}
    return json.loads(read_text(STATE_FILE))


def save_state(signature: str) -> None:
    data = {
        "last_signature": signature,
        "last_run": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
    }
    write_text(STATE_FILE, json.dumps(data, ensure_ascii=False, indent=2))


def extract_role(file: Path) -> str:
    stem = file.stem
    for role in sorted(ROLE_TO_TASK_ID.keys(), key=len, reverse=True):
        if stem.endswith(role):
            return role
    return stem.split("-")[-1]


def is_report_complete(content: str) -> bool:
    return "Bekleniyor." not in content


def update_tasks(completions: dict[str, bool], new_roles: list[str]) -> list[str]:
    tasks = read_text(TASKS)
    if not tasks:
        return []

    actions = []
    status_map = {
        "P-001": "Done" if completions.get("tech-seo") else "In Progress",
        "P-002": "Done" if completions.get("gsc") else "In Progress",
        "P-003": "Done" if completions.get("content") else "Queued (P0 sonrası)",
        "P-004": "Done" if completions.get("internal-link") else "Queued (P0 sonrası)",
        "P-005": "Done" if completions.get("serp-watch") else "Queued (P0 sonrası)",
    }

    new_tasks = tasks
    for task_id, status in status_map.items():
        pattern = (
            rf"^(\|\s*{task_id}\s*\|[^|\n]*\|[^|\n]*\|[^|\n]*\|)\s*([^|\n]+?)\s*(\|)\s*$"
        )
        new_tasks = re.sub(pattern, rf"\1 {status} \3", new_tasks, flags=re.MULTILINE)

    p0_done = completions.get("tech-seo") and completions.get("gsc")
    p1_done = all(
        completions.get(role)
        for role in ["content", "internal-link", "serp-watch"]
    )
    p006_status = "Done" if p1_done else ("In Progress" if p0_done else "Pending")
    new_tasks = re.sub(
        r"^(\|\s*P-006\s*\|[^|\n]*\|[^|\n]*\|[^|\n]*\|)\s*([^|\n]+?)\s*(\|)\s*$",
        rf"\1 {p006_status} \3",
        new_tasks,
        flags=re.MULTILINE,
    )

    if new_roles:
        marker = "## Auto Opened Tasks"
        if marker not in new_tasks:
            new_tasks += (
                f"\n\n{marker}\n\n| Etiket | Rol | Çıktı Dosyası | Durum |\n|---|---|---|---|\n"
            )
        for role in new_roles:
            date_prefix = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
            output_path = f"AGENT-HUB/REPORTS/{date_prefix}-{role}.md"
            row = (
                f"| [NEW:{role}] | {role} | `{output_path}` | "
                "Opened by auto-orchestrator |"
            )
            if row not in new_tasks:
                new_tasks += row + "\n"
                actions.append(f"Yeni rol açıldı: [NEW:{role}] -> {output_path}")

    if new_tasks != tasks:
        write_text(TASKS, new_tasks)
        actions.append("TASKS.md durumları güncellendi")
    return actions


def update_keyword_alarms(alarms: list[dict]) -> list[str]:
    if not alarms:
        return []

    tasks = read_text(TASKS)
    marker = "## Keyword Alarms"
    if marker in tasks:
        tasks = tasks.split(marker)[0].rstrip() + "\n"

    ts = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "",
        marker,
        "",
        f"Son güncelleme: {ts}",
        "",
        "| Tier | Sorgu/Kategori | Pozisyon | Durum |",
        "|---|---|---|---|",
    ]
    for alarm in alarms[:15]:
        label = alarm.get("query") or alarm.get("category", "-")
        lines.append(
            f"| {alarm.get('tier')} | {label} | {alarm.get('position')} | "
            f"Alarm — {alarm.get('reason')} |"
        )

    p0_count = sum(1 for a in alarms if a.get("tier") == "P0")
    if p0_count:
        lines.append("")
        lines.append(f"- [ALARM:P0] {p0_count} P0 alarm aktif — P-016 sprint öncelikli")

    updated = tasks.rstrip() + "\n" + "\n".join(lines) + "\n"
    write_text(TASKS, updated)
    return [f"Keyword alarm tablosu güncellendi ({len(alarms)} alarm)"]


def update_deploy_lock_status() -> list[str]:
    locked, reason = deploy_locked()
    open_fb, _ = extract_feedback_state()
    alarms = check_keyword_alarms()
    write_coalition_status(
        phase="orchestrator",
        alarms=alarms,
        deploy_locked_flag=locked,
        deploy_lock_reason=reason,
    )
    actions = [f"Deploy kilidi: {'EVET' if locked else 'HAYIR'}"]
    if locked:
        actions.append(f"Kilit nedeni: {reason}")
    actions.append(f"Açık FB: {open_fb}")
    return actions


def update_master_plan(changed_files: list[str], actions: list[str]) -> None:
    content = read_text(MASTER_PLAN)
    if not content:
        return
    marker = "## Auto Update Log"
    if marker not in content:
        content += f"\n\n{marker}\n"
    ts = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    changed = ", ".join(changed_files) if changed_files else "-"
    action_text = "; ".join(actions) if actions else "Değişiklik algılandı, no-op"
    content += f"\n- {ts} | Raporlar: {changed} | Aksiyon: {action_text}"
    write_text(MASTER_PLAN, content + "\n")


def write_blocker_if_needed(blockers: list[str]) -> None:
    if not blockers:
        return
    ts = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# BLOCKER ALERT - {ts}",
        "",
        "Aşağıdaki kritik blokajlar raporlarda tespit edildi:",
    ]
    for blocker in blockers:
        lines.append(f"- {blocker}")
    lines.append("")
    lines.append("Onay gerektiren durum: robots/canonical/noindex canlı müdahalesi.")
    write_text(BLOCKER_ALERT, "\n".join(lines))


def ensure_new_role_reports(new_roles: list[str]) -> list[str]:
    actions: list[str] = []
    if not new_roles:
        return actions
    date_prefix = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    for role in new_roles:
        report_path = REPORTS / f"{date_prefix}-{role}.md"
        if report_path.exists():
            continue
        template = (
            f"# {role} Report - {date_prefix}\n\n"
            "## Assignment\n"
            f"- Rol: {role}\n"
            "- Durum: Assigned by auto-orchestrator\n"
            f"- Zorunlu çıktı yolu: `AGENT-HUB/REPORTS/{date_prefix}-{role}.md`\n\n"
            "## Findings\n"
            "- Bekleniyor.\n"
        )
        write_text(report_path, template)
        actions.append(f"Alt agent görevi yazıldı: {report_path.name}")
    return actions


def extract_feedback_items(report_files: list[Path]) -> tuple[list[dict], set[str]]:
    items: list[dict] = []
    resolved_ids: set[str] = set()
    for file in report_files:
        src_role = extract_role(file)
        content = read_text(file)
        for line in content.splitlines():
            m = FEEDBACK_PATTERN.search(line)
            if m:
                target_role = m.group(1).lower()
                fb_id = m.group(2).upper()
                detail = m.group(3).strip()
                items.append(
                    {
                        "id": fb_id,
                        "source": src_role,
                        "target": target_role,
                        "detail": detail,
                        "file": file.name,
                    }
                )
        for resolved in RESOLVED_PATTERN.findall(content):
            resolved_ids.add(resolved.upper())
    return items, resolved_ids


def update_feedback_queue(
    items: list[dict],
    resolved_ids: set[str],
) -> list[str]:
    tasks = read_text(TASKS)
    if not tasks:
        return []

    marker = "## Auto Feedback Queue"
    before = tasks
    if marker in tasks:
        tasks = tasks.split(marker)[0].rstrip() + "\n"

    lines = [
        "",
        f"{marker}",
        "",
        "| FB-ID | Kaynak Rol | Hedef Rol | Durum | Geri Bildirim | Kaynak Rapor |",
        "|---|---|---|---|---|---|",
    ]
    seen_ids: set[str] = set()
    for item in items:
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        status = "Closed" if item["id"] in resolved_ids else "Open"
        lines.append(
            f"| {item['id']} | {item['source']} | {item['target']} | {status} | "
            f"{item['detail']} | `{item['file']}` |"
        )
    if not seen_ids:
        lines.append("| - | - | - | - | Bekleyen feedback yok. | - |")

    updated = tasks.rstrip() + "\n" + "\n".join(lines) + "\n"
    actions: list[str] = []
    if updated != before:
        write_text(TASKS, updated)
        actions.append("Auto Feedback Queue güncellendi")
    return actions


def run() -> int:
    report_files = get_report_files()
    signature = calc_signature(report_files)
    state = load_state()
    if state.get("last_signature") == signature:
        actions = update_deploy_lock_status()
        if actions:
            update_master_plan([], actions)
        return 0

    completions: dict[str, bool] = {}
    new_roles: list[str] = []
    blockers: list[str] = []
    changed_files = [file.name for file in report_files]

    for file in report_files:
        content = read_text(file)
        role = extract_role(file)
        if role in ROLE_TO_TASK_ID:
            completions[role] = is_report_complete(content)

        for match in re.findall(r"\[NEW:([a-z0-9-]+)\]", content, flags=re.IGNORECASE):
            normalized = match.lower()
            if normalized not in new_roles:
                new_roles.append(normalized)

        if "[BLOCKER]" in content:
            blockers.append(f"{file.name}: [BLOCKER] etiketi bulundu")

    actions = update_tasks(completions, new_roles)
    actions.extend(ensure_new_role_reports(new_roles))
    feedback_items, resolved_ids = extract_feedback_items(report_files)
    actions.extend(update_feedback_queue(feedback_items, resolved_ids))

    alarms = check_keyword_alarms()
    actions.extend(update_keyword_alarms(alarms))
    actions.extend(update_deploy_lock_status())

    update_master_plan(changed_files, actions)
    write_blocker_if_needed(blockers)
    save_state(signature)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
