#!/usr/bin/env python3
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import html
import re
from zoneinfo import ZoneInfo


HUB = Path(__file__).resolve().parent
REPORTS = HUB / "REPORTS"
DASHBOARD = HUB / "DASHBOARD.md"
DASHBOARD_HTML = HUB / "DASHBOARD.html"
TASKS = HUB / "TASKS.md"
MASTER_PLAN = HUB / "MASTER-PLAN.md"
LOG_FILE = HUB / "auto-orchestrator.log"

ROLES = ["tech-seo", "gsc", "content", "internal-link", "serp-watch"]
TR_TZ = ZoneInfo("Europe/Istanbul")


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def tail_lines(path: Path, max_lines: int = 12) -> list[str]:
    content = read(path).splitlines()
    return content[-max_lines:] if content else []


def role_report_path(role: str) -> Path:
    date_prefix = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    return REPORTS / f"{date_prefix}-{role}.md"


def role_status(role: str) -> tuple[str, str, str]:
    path = role_report_path(role)
    if not path.exists():
        return ("YOK", "-", "-")
    text = read(path)
    blockers = text.count("[BLOCKER]")
    last_update = datetime.fromtimestamp(path.stat().st_mtime, TR_TZ).strftime("%H:%M:%S TR")
    if "Brainstorm Round -" in text or "Cross-Review Update -" in text:
        phase = "aktif"
    elif "Execution Update -" in text:
        phase = "icra"
    else:
        phase = "bekliyor"
    return (phase, str(blockers), last_update)


def extract_latest_dialogues(role: str, max_items: int = 2) -> list[str]:
    path = role_report_path(role)
    if not path.exists():
        return []

    lines = read(path).splitlines()
    latest_start = -1
    for idx, line in enumerate(lines):
        if line.startswith("## Brainstorm Round -") or line.startswith("## Cross-Review Update -"):
            latest_start = idx
    if latest_start == -1:
        for idx, line in enumerate(lines):
            if line.startswith("## Execution Update -"):
                latest_start = idx
    if latest_start == -1:
        return []

    block = lines[latest_start:]
    dialogues: list[str] = []
    for line in block:
        stripped = line.strip()
        if stripped.startswith("- "):
            msg = re.sub(r"\s+", " ", stripped[2:]).strip()
            if msg:
                dialogues.append(msg)
        if len(dialogues) >= max_items:
            break
    return dialogues


def role_interaction_metrics(role: str) -> tuple[int, bool, bool]:
    path = role_report_path(role)
    if not path.exists():
        return (0, False, False)

    lines = read(path).splitlines()
    latest_start = -1
    for idx, line in enumerate(lines):
        if line.startswith("## Brainstorm Round -") or line.startswith("## Cross-Review Update -"):
            latest_start = idx

    if latest_start == -1:
        return (0, False, False)

    block = lines[latest_start:]
    interaction_count = 0
    has_objection = False
    has_proposed = False
    for line in block:
        stripped = line.strip().lower()
        if stripped.startswith("- "):
            interaction_count += 1
        if "itiraz" in stripped or "disagree" in stripped or "objection" in stripped:
            has_objection = True
        if "proposed changes" in stripped:
            has_proposed = True
    return (interaction_count, has_objection, has_proposed)


def is_recently_active(role: str, seconds: int = 300) -> bool:
    path = role_report_path(role)
    if not path.exists():
        return False
    age = datetime.now(UTC).timestamp() - path.stat().st_mtime
    return age <= seconds


def activity_indicator(phase: str, role: str) -> str:
    tick = datetime.now(TR_TZ).second
    active = (tick // 2 + len(role)) % 3
    if phase == "aktif":
        return ["🟢", "🟡", "🟢"][active]
    if phase == "icra":
        return "🟠"
    return "⚪"


def build_dashboard() -> str:
    now = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S TR")
    lines: list[str] = []
    lines.append("# AGENT LIVE DASHBOARD")
    lines.append("")
    lines.append(f"- Son yenileme: **{now}**")
    lines.append("- Mod: report-only (commit/push yok)")
    lines.append("")
    lines.append("## Rol Durumları")
    lines.append("")
    lines.append("| Rol | Faz | Blocker Sayısı | Son Rapor Güncelleme |")
    lines.append("|---|---|---:|---|")
    for role in ROLES:
        phase, blockers, last_update = role_status(role)
        icon = activity_indicator(phase, role)
        lines.append(f"| {icon} {role} | {phase} | {blockers} | {last_update} |")
    lines.append("")
    lines.append("## Ajanlar Arası Canlı Diyalog Akışı")
    lines.append("")
    any_dialogue = False
    for role in ROLES:
        messages = extract_latest_dialogues(role, max_items=2)
        if not messages:
            continue
        any_dialogue = True
        for msg in messages:
            lines.append(f"- **{role}**: {msg}")
    if not any_dialogue:
        lines.append("- Henüz yeni diyalog satırı yok.")
    lines.append("")
    lines.append("## Hızlı Dosya Kısayolları")
    lines.append("")
    lines.append("- TASKS: `AGENT-HUB/TASKS.md`")
    lines.append("- MASTER PLAN: `AGENT-HUB/MASTER-PLAN.md`")
    lines.append("- DAILY SUMMARY: `AGENT-HUB/DAILY-SUMMARY.md`")
    lines.append("")
    lines.append("## Orchestrator Son Log Satırları")
    lines.append("")
    for item in tail_lines(LOG_FILE, 10):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Not")
    lines.append("- Canlı akışı terminalde izlemek için: `tmux -f /exec-daemon/tmux.portal.conf attach -t live-dashboard`")
    lines.append("- Zengin panel: `AGENT-HUB/DASHBOARD.html`")
    return "\n".join(lines) + "\n"


def build_dashboard_html() -> str:
    now = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S TR")
    cards = []
    for role in ROLES:
        phase, blockers, last_update = role_status(role)
        indicator = activity_indicator(phase, role)
        color = "#22c55e" if phase == "aktif" else ("#f59e0b" if phase == "icra" else "#64748b")
        cards.append(
            f"""
            <div class="card">
              <div class="card-head">
                <span class="dot" style="background:{color};"></span>
                <h3>{indicator} {html.escape(role)}</h3>
              </div>
              <p><b>Faz:</b> {html.escape(phase)}</p>
              <p><b>Blocker:</b> {html.escape(blockers)}</p>
              <p><b>Son update:</b> {html.escape(last_update)}</p>
            </div>
            """
        )

    feed = []
    for role in ROLES:
        for msg in extract_latest_dialogues(role, max_items=3):
            feed.append(f"<li><span class='role'>{html.escape(role)}</span> {html.escape(msg)}</li>")
    if not feed:
        feed.append("<li><span class='role'>system</span> Yeni diyalog satırı bekleniyor.</li>")

    logs = [f"<li>{html.escape(item)}</li>" for item in tail_lines(LOG_FILE, 8)]
    if not logs:
        logs.append("<li>Log bekleniyor...</li>")

    arena_agents = []
    for idx, role in enumerate(ROLES):
        phase, blockers, _ = role_status(role)
        interaction_count, has_objection, has_proposed = role_interaction_metrics(role)
        recent = is_recently_active(role, seconds=420)

        # Hareket yalnız etkileşim varsa açılır; aksi halde idle kalır.
        mood = "idle"
        if interaction_count > 0 and has_proposed and recent:
            mood = "sending"
        elif interaction_count > 0 and recent:
            mood = "talking"
        if has_objection and recent:
            mood = "debating"
        if blockers != "-" and blockers.isdigit() and int(blockers) >= 8 and recent:
            mood = "alert"

        arena_agents.append(
            f"""
            <div class="agent sprite {mood}" style="--i:{idx};">
              <div class="name">{html.escape(role)}</div>
              <div class="body"></div>
            </div>
            """
        )

    return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="5" />
  <title>Agent Live Dashboard</title>
  <style>
    body {{ background:#0b1020; color:#e5e7eb; font-family:Inter,Arial,sans-serif; margin:0; }}
    .wrap {{ max-width:1200px; margin:20px auto; padding:0 16px; }}
    h1 {{ margin:0 0 4px; }}
    .meta {{ color:#94a3b8; margin-bottom:16px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin-bottom:16px; }}
    .card {{ background:#111827; border:1px solid #1f2937; border-radius:14px; padding:12px; }}
    .card-head {{ display:flex; align-items:center; gap:8px; }}
    .dot {{ width:10px; height:10px; border-radius:999px; box-shadow:0 0 10px currentColor; animation:pulse 1.6s infinite; }}
    .panel {{ background:#111827; border:1px solid #1f2937; border-radius:14px; padding:12px; margin-bottom:12px; }}
    ul {{ margin:8px 0 0; padding-left:18px; }}
    li {{ margin:6px 0; line-height:1.35; }}
    .role {{ color:#60a5fa; font-weight:700; margin-right:6px; }}
    .arena {{ position:relative; height:170px; border-radius:14px; background:linear-gradient(180deg,#0f172a,#111827); border:1px solid #1f2937; overflow:hidden; margin-bottom:12px; }}
    .arena::before {{ content:""; position:absolute; left:0; right:0; bottom:0; height:28px; background:#1e293b; }}
    .agent {{ position:absolute; bottom:22px; left:10px; animation-delay:calc(var(--i) * -1.1s); }}
    .agent .name {{ font-size:11px; color:#93c5fd; margin-bottom:4px; text-shadow:0 0 6px rgba(59,130,246,.6); }}
    .agent .body {{ width:18px; height:26px; border-radius:6px; background:#64748b; box-shadow:0 0 10px rgba(100,116,139,.5); border:1px solid rgba(255,255,255,.25); }}
    .agent.idle {{ animation:none; }}
    .agent.idle .body {{ background:#64748b; box-shadow:0 0 10px rgba(100,116,139,.5); }}
    .agent.talking .body {{ background:#22c55e; box-shadow:0 0 12px rgba(34,197,94,.7); }}
    .agent.sending .body {{ background:#38bdf8; box-shadow:0 0 12px rgba(56,189,248,.7); }}
    .agent.debating .body {{ background:#f59e0b; box-shadow:0 0 12px rgba(245,158,11,.7); }}
    .agent.alert .body {{ background:#ef4444; box-shadow:0 0 12px rgba(239,68,68,.8); }}
    .agent.talking {{ animation-name:bob; animation-duration:1.2s; animation-iteration-count:infinite; animation-timing-function:ease-in-out; }}
    .agent.sending {{ animation-name:walk,bob; animation-duration:8s,1s; animation-iteration-count:infinite,infinite; animation-timing-function:linear,ease-in-out; }}
    .agent.debating {{ animation-name:walk-fast,bob; animation-duration:5.5s,.7s; animation-iteration-count:infinite,infinite; animation-timing-function:linear,ease-in-out; }}
    .agent.alert {{ animation-name:walk-fast,bob; animation-duration:5s,.6s; animation-iteration-count:infinite,infinite; animation-timing-function:linear,ease-in-out; }}
    @keyframes pulse {{ 0% {{opacity:0.4}} 50% {{opacity:1}} 100% {{opacity:0.4}} }}
    @keyframes walk {{ 0% {{ transform:translateX(0px); }} 50% {{ transform:translateX(980px); }} 100% {{ transform:translateX(0px); }} }}
    @keyframes walk-fast {{ 0% {{ transform:translateX(0px); }} 50% {{ transform:translateX(980px); }} 100% {{ transform:translateX(0px); }} }}
    @keyframes bob {{ 0% {{ margin-bottom:0; }} 50% {{ margin-bottom:6px; }} 100% {{ margin-bottom:0; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Agent Live Dashboard</h1>
    <div class="meta">Son yenileme: {html.escape(now)} | Mod: report-only</div>
    <div class="grid">
      {''.join(cards)}
    </div>
    <div class="panel">
      <h2>Agent Arena (Canlı Hareket)</h2>
      <div class="arena">
        {''.join(arena_agents)}
      </div>
    </div>
    <div class="panel">
      <h2>Ajanlar Arası Sohbet Akışı</h2>
      <ul>{''.join(feed)}</ul>
    </div>
    <div class="panel">
      <h2>Orchestrator Son Loglar</h2>
      <ul>{''.join(logs)}</ul>
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    DASHBOARD.write_text(build_dashboard(), encoding="utf-8")
    DASHBOARD_HTML.write_text(build_dashboard_html(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
