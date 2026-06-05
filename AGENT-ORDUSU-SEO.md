# LEDAJANS Agent Ordusu (Cloud + Otomasyon)

Bu kurulum ile her gün SEO operasyonunu yarı-otonom yürütürsün:
- Lider agent işleri dağıtır
- Alt agentlar paralel çalışır
- Çıktılar ortak dosyalara yazılır
- Gerekirse lider agent yeni agent görevi açar

## 1) Lider Agent Prompt (Cursor Cloud)

Yeni Cloud Agent aç ve aşağıdaki promptu ver:

```text
Sen LEDAJANS SEO Orkestratörüsün.

Hedef:
- ledajans.com için "led ekran" ve ilişkili ticari anahtar kelimelerde görünürlük/artış.
- Teknik SEO + içerik + iç link + GSC takip + haftalık raporlama.

Çalışma Kuralları:
1) Her döngü başında AGENT-HUB/STATE.md dosyasını oku.
2) AGENT-HUB/TASKS.md içinde pending olan görevleri alt agentlara dağıt.
3) Her alt agent çıktısını AGENT-HUB/REPORTS/<tarih>-<agent>.md dosyasına yazdır.
4) Çakışan önerilerde öncelik sırası: Teknik hata > indekslenme > içerik güncelleme > yeni içerik.
5) İhtiyaç halinde kendin yeni alt agent görevleri oluştur (content, tech-seo, internal-linking, serp-watch, schema-fix).
6) Gün sonu AGENT-HUB/DAILY-SUMMARY.md güncelle.
7) Asla mevcut çalışan sayfaları kıracak toplu işlem yapma; önce dry-run ve doğrulama üret.
```

## 2) Alt Agent Rol Seti

- `tech-seo-agent`: sitemap, canonicals, redirect, robots, schema hataları.
- `content-agent`: yeni long-tail sayfalar ve mevcut içerik refresh.
- `internal-link-agent`: hub-spoke link optimizasyonu.
- `gsc-agent`: index coverage, query trend, URL inspection öncelik listesi.
- `serp-watch-agent`: rakip kıyas ve fırsat keyword listesi.

## 3) Ortak Dosya Yapısı

- `AGENT-HUB/STATE.md`: mevcut durum, darboğazlar, son kararlar
- `AGENT-HUB/TASKS.md`: görev kuyruğu
- `AGENT-HUB/REPORTS/`: agent raporları
- `AGENT-HUB/DAILY-SUMMARY.md`: günlük özet

## 4) Operasyon Döngüsü (Önerilen)

- Sabah: Teknik sağlık kontrolü + GSC kontrol
- Öğlen: İçerik güncelleme + iç link revizyon
- Akşam: SERP fark analizi + ertesi gün task üretimi

