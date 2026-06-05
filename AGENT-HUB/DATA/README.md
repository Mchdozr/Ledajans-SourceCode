# GSC Ham Veri Klasörü

Bu klasöre Search Console export dosyalarını koyun. Agent otomatik okur:

```powershell
python scripts/parse-gsc-export.py
```

## Beklenen dosya adları

| Dosya | GSC yolu | Zorunlu |
|-------|----------|---------|
| `gsc-queries-28d.csv` | Performans → Sorgular → Dışa aktar (Son 28 gün) | Evet |
| `gsc-pages-28d.csv` | Performans → Sayfalar → Dışa aktar | Evet |
| `gsc-indexing-pages.csv` | Dizin oluşturma → Sayfalar → Dışa aktar | Önerilir |
| `gsc-coverage-2026-06-05/` (Coverage ZIP) | Özet grafik CSV — **URL listesi değil** | İstatistik only |

**Coverage ZIP** (`ledajans.com-Coverage-*.zip`) içinde `Önemli sorunlar.csv` sadece neden + adet verir. URL triage için: **Sayfa indeksleme** → *Tarandı - şu anda dizine eklenmiş değil* satırına tıkla → **Dışa aktar** (URL sütunlu CSV).

Tarih aralığı: **Son 28 gün**, ülke: **Türkiye** (varsa), cihaz: tümü veya ayrı mobil/masaüstü.

## GSC kullanıcı erişimi (alternatif)

Cursor tarayıcısı şu hesapla açılıyor: **mucahid.ozer.5@gmail.com**

Search Console → Ayarlar → Kullanıcılar ve izinler → Kullanıcı ekle → **Tam** yetki.
