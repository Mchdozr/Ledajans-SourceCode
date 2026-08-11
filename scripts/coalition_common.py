#!/usr/bin/env python3
"""Koalisyon döngüsü ortak yardımcılar."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

FEEDBACK_PATTERN = re.compile(
    r"\[TO:([a-z0-9-]+)\]\s*\[FB:([A-Za-z0-9_-]+)\]\s*(.+)",
    flags=re.IGNORECASE,
)
OBJECT_PATTERN = re.compile(
    r"\[TO:([a-z0-9-]+)\]\s*\[OBJECT:([A-Za-z0-9_-]+)\]\s*(.+)",
    flags=re.IGNORECASE,
)
RESOLVED_PATTERN = re.compile(r"\[RESOLVED:([A-Za-z0-9_-]+)\]", flags=re.IGNORECASE)
CEO_DECISION_PATTERN = re.compile(
    r"\[CEO-DECISION:([A-Za-z0-9_-]+)\]",
    flags=re.IGNORECASE,
)
APPLY_PATTERN = re.compile(r"\[APPLY:(T[12])\]\s*(.+)", flags=re.IGNORECASE)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def hub_dir() -> Path:
    return repo_root() / "AGENT-HUB"


def load_keyword_guard() -> dict:
    path = hub_dir() / "KEYWORD-GUARD.json"
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8")


def parse_rank(value: str) -> float | None:
    if not value or value.lower() in ("n/a", "pending"):
        return None
    mapping = {"top3": 3.0, "top5": 5.0, "top10": 10.0, "top20": 20.0}
    if value.lower() in mapping:
        return mapping[value.lower()]
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def load_serp_baseline() -> list[dict[str, str]]:
    path = hub_dir() / "SERP-BASELINE.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def latest_position_by_query(rows: list[dict[str, str]]) -> dict[str, float]:
    latest: dict[str, tuple[str, float]] = {}
    for row in rows:
        query = row.get("query", "").strip().lower()
        if not query:
            continue
        rank = parse_rank(row.get("rank_position", ""))
        if rank is None:
            continue
        captured = row.get("captured_at_utc", "")
        prev = latest.get(query)
        if prev is None or captured >= prev[0]:
            latest[query] = (captured, rank)
    return {q: v[1] for q, v in latest.items()}


def extract_feedback_state() -> tuple[int, set[str]]:
    reports = sorted((hub_dir() / "REPORTS").glob("*.md"))
    items: list[str] = []
    resolved: set[str] = set()
    for report in reports:
        content = read_text(report)
        for line in content.splitlines():
            m = FEEDBACK_PATTERN.search(line)
            if m:
                items.append(m.group(2).upper())
            o = OBJECT_PATTERN.search(line)
            if o:
                items.append(o.group(2).upper())
        resolved.update(RESOLVED_PATTERN.findall(content))
        resolved.update(CEO_DECISION_PATTERN.findall(content))
    open_count = len({fb for fb in items if fb not in resolved})
    return open_count, resolved


def deploy_locked() -> tuple[bool, str]:
    open_fb, _ = extract_feedback_state()
    if open_fb > 0:
        return True, f"Acik feedback: {open_fb}"

    blocker = read_text(hub_dir() / "BLOCKER-ALERT.md")
    if blocker.strip() and "BLOCKER ALERT" in blocker:
        return True, "BLOCKER-ALERT aktif"

    status_path = hub_dir() / ".coalition-status.json"
    if status_path.exists():
        data = json.loads(status_path.read_text(encoding="utf-8"))
        if data.get("deploy_locked"):
            return True, data.get("deploy_lock_reason", "status locked")

    return False, ""


def check_keyword_alarms() -> list[dict]:
    guard = load_keyword_guard()
    positions = latest_position_by_query(load_serp_baseline())
    alarms: list[dict] = []

    p0 = guard["p0_defense"]
    for query in p0["queries"]:
        pos = positions.get(query.lower())
        if pos is None:
            continue
        if query.lower() == "led ekran" and pos >= p0["serp_alarm_rank"]:
            alarms.append(
                {
                    "tier": "P0",
                    "query": query,
                    "position": pos,
                    "reason": f"pozisyon {pos} >= alarm {p0['serp_alarm_rank']}",
                }
            )
        elif pos > p0["gsc_target_position"] and query.lower().startswith("led ekran"):
            alarms.append(
                {
                    "tier": "P0",
                    "query": query,
                    "position": pos,
                    "reason": f"hedef {p0['gsc_target_position']} ustu: {pos}",
                }
            )

    for cat in guard["p1_categories"]:
        for query in cat["queries"]:
            pos = positions.get(query.lower())
            if pos is None:
                continue
            if pos > cat["gsc_target_position"]:
                alarms.append(
                    {
                        "tier": "P1",
                        "category": cat["name"],
                        "query": query,
                        "position": pos,
                        "reason": f"hedef {cat['gsc_target_position']} ustu: {pos}",
                    }
                )

    return alarms


def write_coalition_status(
    *,
    phase: str,
    alarms: list[dict],
    deploy_locked_flag: bool,
    deploy_lock_reason: str,
) -> Path:
    path = hub_dir() / ".coalition-status.json"
    open_fb, _ = extract_feedback_state()
    payload = {
        "phase": phase,
        "open_feedback_count": open_fb,
        "deploy_locked": deploy_locked_flag,
        "deploy_lock_reason": deploy_lock_reason,
        "alarms": alarms,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def extract_apply_commands() -> list[dict[str, str]]:
    reports = sorted((hub_dir() / "REPORTS").glob("*.md"))
    commands: list[dict[str, str]] = []
    seen: set[str] = set()
    for report in reversed(reports):
        for line in read_text(report).splitlines():
            m = APPLY_PATTERN.search(line)
            if not m:
                continue
            tier, cmd = m.group(1).upper(), m.group(2).strip()
            if cmd not in seen:
                seen.add(cmd)
                commands.append({"tier": tier, "command": cmd, "source": report.name})
    return commands
