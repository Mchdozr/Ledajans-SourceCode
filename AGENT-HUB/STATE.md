# AGENT-HUB STATE

## Sprint
- Sprint: 2026-05 İlk Sprint / Tur-1
- Orchestrator: lider-orchestrator
- Öncelik Kuralı: teknik hata > indekslenme > içerik güncelleme > yeni içerik

## Hedef
- Ana hedef: ledajans.com için "led ekran" ve ticari alt anahtar kelimelerde sıralama artışı
- Kapsam: teknik SEO, indeksleme, içerik iyileştirme, iç linkleme, GSC doğrulama, SERP izleme

## Agent Rolleri
- tech-seo
- content
- internal-link
- gsc
- serp-watch

## Mevcut Durum
- AGENT-HUB yapısı bu sprint başlangıcında oluşturuldu.
- İlk tur görev dağıtımı aktif.
- 20 dakikalık otonom kontrol döngüsü çalışıyor.

## Çalışma Modu (Zorunlu)
- Rapor-odaklı mod: Sadece `AGENT-HUB/*.md` dosyalarına yaz.
- Alt agentlar ve orchestrator commit/push yapmaz.
- Kod değişiklikleri yalnızca `proposed changes` olarak raporlanır, uygulanmaz.

## Sürekli Worker Operasyon Modu (20dk)
- Model: ajanlar yalnız itiraz etmez; profesyonel web yönetim ekibi gibi uçtan uca operasyon yürütür.
- Her 20 dakikada her rol diğer raporları okuyup kendi raporunda şu 5 çıktıyı üretir:
  - `### Situation` (mevcut durum + risk)
  - `### Decision` (hangi karar alındı, neden)
  - `### Proposed Changes (No Apply)` (dosya bazlı teknik/ürünsel öneri)
  - `### QA/Validation` (başarı ölçümü ve kontrol listesi)
  - `### Handoff` (bir sonraki role net devir)
- Zaman standardı: tüm dashboard/rapor saatleri `TR (Europe/Istanbul)` formatında yazılır.
- Hedef: siteyi gerçek bir web ekibi disipliniyle yönetmek (planlama, uygulama tasarımı, kalite kontrol, izleme).
