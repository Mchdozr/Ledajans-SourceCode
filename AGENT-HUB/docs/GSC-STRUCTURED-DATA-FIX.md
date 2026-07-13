# GSC Yapılandırılmış Veri Düzeltmesi

## Sorun neydi?

Google Search Console, Product rich result denetiminde bazı öğeleri geçersiz gösterdi:

- Ana sayfada 5 Product öğesi: `offers`, `review` veya `aggregateRating` alanı yoktu.
- `/dis-mekan-led-ekran/` sayfasında Product `offers.lowPrice` alanı eksikti.
- `review`, `aggregateRating`, `highPrice`, `offerCount` uyarıları kritik olmayan alanlardır; kritik hata `offers` veya `lowPrice` eksikliğidir.

## Repo tarafında ne düzeltildi?

- `SEO-Icerik-Widgets/schema/organization-schema.html`
  - `hasOfferCatalog.itemOffered` içindeki 5 genel katalog öğesi `Product` yerine `Service` yapıldı.
  - Bu, ana sayfada ürün fiyatı gerektirmeyen hizmet/kategori öğelerinin Product olarak algılanmasını engeller.

- `Urunlerimiz/Dis-Mekan-Led-Ekran/urun-ozellikleri.html`
- `Urunlerimiz/Ic-Mekan-Led-Ekran/urun-ozellikleri.html`
- `Urunlerimiz/Rental-Ekran/urun-ozellikleri.html`
  - `AggregateOffer` içine `lowPrice`, `highPrice`, `offerCount`, `availability`, `url` alanları eklendi.
  - LEDAJANS B2B proje fiyatları teklif bazlı olduğu için `lowPrice` ve `highPrice` geçici doğrulama değeri olarak `0` bırakıldı.

## WordPress tarafında ne güncellenecek?

1. Ana sayfada kullanılan global Organization schema snippet’i:
   - Kaynak: `SEO-Icerik-Widgets/schema/organization-schema.html`
   - WordPress’te schema/snippet nereye yapıştırıldıysa aynı içerikle güncelle.

2. Ürün sayfası HTML widget/snippet’leri:
   - Dış mekan: `Urunlerimiz/Dis-Mekan-Led-Ekran/urun-ozellikleri.html`
   - İç mekan: `Urunlerimiz/Ic-Mekan-Led-Ekran/urun-ozellikleri.html`
   - Rental: `Urunlerimiz/Rental-Ekran/urun-ozellikleri.html`
   - Elementor veya ilgili WordPress snippet alanında canlı içerikle değiştir.

3. Cache:
   - W3 Total Cache / site cache temizle.

## GSC tekrar test

1. Google Search Console → URL Inspection.
2. İlgili URL’yi test et:
   - `https://ledajans.com/`
   - `https://ledajans.com/dis-mekan-led-ekran/`
   - `https://ledajans.com/ic-mekan-led-ekran/`
   - `https://ledajans.com/rental-ekran/`
3. “Canlı URL’yi test et” sonrası Product hatasının kritik olmaktan çıktığını kontrol et.

## Beklenen sonuç

- Ana sayfadaki 5 Product hatası kalkmalı veya Product yerine hizmet/katalog olarak algılanmalı.
- Dış mekan / iç mekan / rental Product öğelerinde `lowPrice` eksikliği kalkmalı.
- `review` ve `aggregateRating` uyarıları kalabilir; bunlar isteğe bağlıdır.
