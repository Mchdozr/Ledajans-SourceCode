# AGENTS.md

## Overview

This repository is a content staging and deployment pipeline for the **ledajans.com** WordPress site (a Turkish B2B LED screen manufacturer). It contains:

- **HTML content/widget snippets** organized by website sections (Homepage, Products, Blog, Contact, etc.)
- **SEO optimization assets** — Lighthouse audits, structured data schemas, RankMath meta scripts
- **Deployment scripts** — `deploy-to-wordpress.py` (REST API), `deploy-wp-cli.sh` (WP-CLI)
- **WordPress performance plugin** — `wordpress-mobil-hiz-patch.php`
- **AI-driven SEO orchestration** — `AGENT-HUB/` with Python scripts for coordinating SEO analysis agents

There is **no build step, no package.json, no compiled application**. The codebase is static HTML + Python tooling.

## Cursor Cloud specific instructions

### Runtime Requirements

- **Python 3.12+** with `requests` package (pre-installed in the Cloud VM).
- No Node.js, no Docker, no database required.

### Key Scripts

| Script | Purpose | How to Run |
|---|---|---|
| `deploy-to-wordpress.py` | Deploy HTML content to WordPress REST API | `python3 deploy-to-wordpress.py --dry-run` (safe test) |
| `AGENT-HUB/auto_orchestrator.py` | SEO agent orchestration — reads reports, updates TASKS.md | `python3 AGENT-HUB/auto_orchestrator.py` |
| `AGENT-HUB/live_dashboard.py` | Generates `DASHBOARD.md` and `DASHBOARD.html` from report data | `python3 AGENT-HUB/live_dashboard.py` |
| `AGENT-HUB/run-auto-orchestrator.sh` | Loop wrapper for orchestrator (runs every 20 min) | `bash AGENT-HUB/run-auto-orchestrator.sh` |
| `AGENT-HUB/run-live-dashboard.sh` | Loop wrapper for dashboard (refreshes every 20s) | `bash AGENT-HUB/run-live-dashboard.sh` |
| `AGENT-HUB/serp_baseline_monitor.py` | SERP baseline CSV + haftalık özet (`led ekran`) | `python3 AGENT-HUB/serp_baseline_monitor.py` |
| `AGENT-HUB/run-serp-monitor.sh` | Cron wrapper for SERP monitor | `bash AGENT-HUB/run-serp-monitor.sh` |

### Running Background Services

Start orchestrator and dashboard in tmux:

```bash
tmux new-session -d -s orchestrator 'bash /workspace/AGENT-HUB/run-auto-orchestrator.sh'
tmux new-session -d -s live-dashboard 'bash /workspace/AGENT-HUB/run-live-dashboard.sh'
```

To view the HTML dashboard: `python3 -m http.server 8080 --directory /workspace/AGENT-HUB` then open `http://localhost:8080/DASHBOARD.html`.

### Important Caveats

- `deploy-to-wordpress.py` has hardcoded WordPress credentials. It will fail with HTTP 403 unless valid WP Application Passwords are configured. Use `--dry-run` flag to test without deploying.
- The orchestrator reads report files from `AGENT-HUB/REPORTS/` and is a no-op if report signatures haven't changed since last run.
- All Python scripts use hardcoded paths rooted at `/workspace`. They must be run from the repository root.

### Linting and Testing

There are no automated test suites or lint configurations in this repo. To validate Python scripts, run them directly and check exit codes:

```bash
python3 AGENT-HUB/auto_orchestrator.py && echo "OK"
python3 AGENT-HUB/live_dashboard.py && echo "OK"
python3 deploy-to-wordpress.py --dry-run
```
