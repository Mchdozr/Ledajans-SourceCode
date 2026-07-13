# AGENTS.md

## Overview

LEDAJANS WordPress içerik staging ve deploy deposu. Yapı için `REPO-STRUCTURE.md`.

| Klasör | İçerik |
|--------|--------|
| `content/` | HTML widget ve sayfa snippet'leri |
| `ops/` | robots.txt, mu-plugin, nginx kuralları |
| `data/` | blog-301.csv, Lighthouse baseline JSON |
| `scripts/` | Deploy, SEO, doğrulama betikleri |
| `AGENT-HUB/` | SEO agent orkestrasyonu |

## Cursor Cloud

- Python 3.12+, `requests`
- Komutlar repo kökünden: `cd /workspace`

### Ana komutlar

```bash
python3 deploy-to-wordpress.py --dry-run
python3 scripts/deploy/deploy-elementor-widgets.py --apply
python3 scripts/seo/set-rankmath-p0-meta.py --apply
python3 AGENT-HUB/auto_orchestrator.py && echo OK
python3 AGENT-HUB/live_dashboard.py && echo OK
```

### Arka plan servisleri

```bash
tmux new-session -d -s orchestrator 'bash /workspace/AGENT-HUB/run-auto-orchestrator.sh'
tmux new-session -d -s live-dashboard 'bash /workspace/AGENT-HUB/run-live-dashboard.sh'
```

Dashboard: `python3 -m http.server 8080 --directory /workspace/AGENT-HUB`

### Notlar

- `.env` ile WP kimlik bilgisi; canlı deploy için geçerli Application Password gerekir
- Orchestrator: `AGENT-HUB/REPORTS/` imzası değişmediyse no-op
- mu-plugin: `ops/wordpress/mobil-hiz-patch.php`
