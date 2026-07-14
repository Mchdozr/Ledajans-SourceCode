# Depo yapısı

```
/workspace/
├── content/              # WordPress HTML widget ve sayfa içerikleri
│   ├── Anasayfa/
│   ├── Blog/
│   ├── Urunlerimiz/
│   ├── SEO-Icerik-Widgets/
│   └── ...
├── ops/                  # Sunucuya deploy edilen dosyalar
│   ├── robots.txt
│   ├── wordpress/        # mu-plugin, RankMath REST
│   └── nginx/            # Plesk/nginx 301 kuralları
├── data/                 # Referans veri ve baseline'lar
│   ├── blog-301.csv
│   └── baselines/        # Lighthouse CWV JSON
├── scripts/              # Python araçları
│   ├── lib/repo_paths.py # Ortak yol sabitleri
│   ├── deploy/           # Canlı WordPress deploy
│   ├── seo/              # RankMath, GSC, permalink
│   ├── verify/           # Canlı doğrulama
│   ├── monitor/          # CWV, haftalık SEO izleme
│   └── ops/              # WP REST teşhis, WP-CLI yardımcıları
├── AGENT-HUB/            # SEO agent orkestrasyonu
│   ├── docs/             # Runbook ve aksiyon planları
│   ├── DATA/             # GSC export CSV'leri
│   └── REPORTS/          # Agent raporları
├── Katalog/              # Baskı kataloğu (ayrı proje)
├── docs/                 # Operatör kılavuzları
├── deploy-to-wordpress.py
└── AGENTS.md
```

## Komut örnekleri

```bash
python3 deploy-to-wordpress.py --dry-run
python3 scripts/deploy/deploy-elementor-widgets.py --apply
python3 scripts/seo/set-rankmath-p0-meta.py --apply
python3 AGENT-HUB/auto_orchestrator.py
```
