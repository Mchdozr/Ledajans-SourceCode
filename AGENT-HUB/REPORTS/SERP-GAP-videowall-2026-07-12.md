# SERP Gap Analizi — videowall.com.tr vs ledajans.com

**Tarih:** 2026-07-12  
**Head-term:** `led ekran`  
**Baseline:** ledajans avg pos 6.78 (GSC 2026-06-05), trafik çoğunlukla `/`

## Rakip SERP snapshot (videowall.com.tr)

| Alan | videowall.com.tr | ledajans.com (deploy sonrası) | Gap |
|------|------------------|-------------------------------|-----|
| Title | "LED Ekran \| Fiyat ve Modeller" benzeri exact-match | "LED Ekran ve Fiyatları 2026 \| İç-Dış Mekan" | Kapatıldı |
| H1 | Head-term + ürün | "LED Ekran Çözümleri ve Fiyatları" | Kapatıldı |
| FAQ rich result | 3-5 SSS | Hub + para sayfa FAQPage JSON-LD | Kapatıldı |
| Product/Offer schema | Kısıtlı / teklif bazlı | Hub Product + AggregateOffer | Kapatıldı |
| Trust signals | Referans sayısı | Trust bar 25+ yıl, 2 yıl garanti | Kapatıldı |
| Mobil LCP | ~3-5s (tahmini) | 10.9s baseline → mu-plugin deploy | **Açık — GSC doğrula** |
| Backlink profili | Güçlü sektör linkleri | Orta | **Açık — Faz 7** |

## Önerilen aksiyonlar (öncelik)

1. `/led-ekran/` hub'ının GSC'de `led ekran` birincil URL olması (cannibalization kapanışı)
2. Mobil LCP < 4s — GSC Deneyim + Lighthouse yerel
3. Dış mekan head-term (`dış mekan led ekran` pos ~15) — SEO metin + Product schema paketi
4. Off-page: GBP + sektör dizinleri + rakip referring domain gap (Ahrefs)

## CTR hedefi

- Mevcut CTR 2.9% → hedef 6%+ (title A/B: fiyat + ücretsiz keşif + 25 yıl)
