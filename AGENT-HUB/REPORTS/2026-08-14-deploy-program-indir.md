# Deploy: Program İndir — 2026-08-14

**URL:** https://ledajans.com/program-indir/  
**Page ID:** 786  
**Onay:** kullanıcı — rehber kaldır + canlı güncelle

## Yapılanlar
- `uzak-masaustu.html` boşaltıldı (`program-guide` / 3 adım kaldırıldı)
- Elementor widget’lar güncellendi (`scripts/deploy-program-indir.py` → `ledajans/v1/hero-widget` + purge)

| Widget | Dosya |
|--------|--------|
| 25682f9 | hero-banner.html |
| 997a1eb | indirme-dosyalari.html |
| 46ed6aa | uzak-masaustu.html (boş) |
| 553ceb0 | satis-kanallari.html (Inwelt + Sesajans) |

## Doğrulama (canlı)
- `program-guide-container`: yok
- `pi-picker` / yeni indirme hub: var
- `inwelt.com.tr` + `sesajans.com.tr`: var
- eski `program-indir-section`: yok

## Rollback
WP revision veya önceki widget HTML yedeklerinden `hero-widget` ile geri yaz.
