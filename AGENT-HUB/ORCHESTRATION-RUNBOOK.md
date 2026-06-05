# LEDAJANS Cloud Agent Orkestrasyon Runbook

## 1) Lider Agent Görevi
- `STATE.md` oku.
- `TASKS.md` içinden `pending` görevleri role göre parçala.
- Alt agent üret, her birine tek hedef ver.
- Çıktıları `REPORTS/` altında topla.
- Çakışma varsa karar ver, `TASKS.md` ve `DAILY-SUMMARY.md` güncelle.

## 2) Alt Agent Roller
- `tech-seo-agent`: crawl/index/sitemap/robots/canonical.
- `content-agent`: yeni içerik ve güncelleme.
- `internal-link-agent`: hub-spoke link grafiği.
- `gsc-agent`: URL inspection öncelik listesi.
- `serp-watch-agent`: rakip ve sorgu takibi.

## 3) Self-Spawn Protokolü
Lider agent şu koşullarda yeni alt agent açar:
- Bir görevde blokaj oluşursa.
- Mevcut rol seti görevi karşılamıyorsa.
- Zaman kritik ve paralel yürütme gerekiyorsa.

Yeni görev açma formatı (`TASKS.md`):
- [ ] [NEW:<rol>] <görev özeti> | owner:<agent> | due:<tarih>

## 4) Cloud Agent Prompt Şablonu
```text
Rolün: <rol>
Hedefin: <tek ve net hedef>
Bağlam Dosyaları:
- AGENT-HUB/STATE.md
- AGENT-HUB/TASKS.md
Kurallar:
1) Sadece verilen hedef üzerinde çalış.
2) Çıktıyı AGENT-HUB/REPORTS/<yyyy-mm-dd>-<rol>.md formatında yaz.
3) Blokajda lider için net aksiyon öner.
```

## 5) Günlük Çalışma Döngüsü
- 09:30 teknik sağlık kontrolü
- 13:00 içerik + iç link işleri
- 17:00 SERP + GSC değerlendirme
