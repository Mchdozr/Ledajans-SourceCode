# Visual-UX — Program İndir redesign

**Tarih:** 2026-08-14  
**URL:** https://ledajans.com/program-indir/  
**Kapsam:** `Teknik-Destek-Bilgi/Program-indir/*` (hero, rehber, indirme kartları)

## Viewport / UX Issues (önceki)
- Kartlarda sadece teknik dosya adı + turuncu buton; “bu ne?” yok
- Uzak masaüstü ikon bloğu indirme ile ilişkisiz, scroll uzatıyordu
- Marka seçimi yok → kullanıcı tüm listeyi kaydırmak zorundaydı

## Copy / Visual Fixes
- Hero: sade dil + “Markamı seç” CTA
- 3 adımlı rehber (seç → indir → kur)
- 6’lı görsel marka seçici + sticky arama; kategoriye tıklanınca sadece o marka görünür
- Her dosya kartı: ikon + tip rozeti + “Bu ne?” + net indirme butonu
- 16 indirme linki korundu (doğrulandı)

## QA Checklist
- [x] Colorlight filtresi → 5 kart, diğer kategoriler `display:none`
- [x] Tüm orijinal Drive / Nova / AnyDesk / Huidu URL’leri mevcut
- [ ] Canlı WP widget deploy (kullanıcı onayı gerekir)
- [ ] TF PowerLed URL’si Teknik Özellikler ile aynı (eski bug; ayrı kontrol)
