# LEDAJANS — Görünüm İyileştirme Planı

Tarih: 2026-11-17 · Kapsam: ana sayfa + üst menüdeki tüm başlık ve alt başlıklar (**19 sayfa**)
Yöntem: Her sayfaya canlıdan girildi; masaüstü (1440 px) ve mobil (390 px) ekran görüntüsü, DOM denetimi (başlıklar, yazı boyutu, dokunma hedefi, görsel, taşma) ve mobil Lighthouse (performans, erişilebilirlik, en iyi uygulamalar, SEO) alındı. Ham veri: `docs/gorunum-plani/olcum-*.json`. Görseller: aynı klasör.

> Bu belge **plan**dır; sitede hiçbir şey değiştirilmedi.

## 1. Kapsam: taranan sayfalar

| Menü | Sayfa |
|---|---|
| Anasayfa | `/` |
| Kurumsal | `/hakkimizda/` · `/sertifikalarimiz/` · `/firma-bilgilerimiz/` |
| Ürünlerimiz | `/led-ekran/` (hub) · `/cob-ekran/` · `/ic-mekan-led-ekran/` · `/dis-mekan-led-ekran/` · `/rental-ekran/` · `/ic-mekan-rgb-panel/` · `/dis-mekan-rgb-panel/` · `/kontrol-kartlari/` · `/guc-kaynaklari/` |
| Blog | `/blog/` |
| Teknik Destek & Bilgi | `/colorlight/` · `/huidu-processor-hdplayer-indir/` · `/program-indir/` · `/teknik-destek-videolari/` · Google Drive (→ `/program-indir/`'e yönleniyor) |
| İletişim | `/iletisim/` |
| Dil | Türkçe / English / Deutsch (`/en/`, `/de/` bu taramaya dahil değil) |

Ürün hub'ı (`/led-ekran/`) ve "Tüm ürünler" öğesi menüde yeni; export'taki eski menüde yok.

## 2. Genel değerlendirme

**Güçlü yanlar (korunacak):** Tek tip turuncu/lacivert marka dili, temiz tek `h1` (19/19 sayfada tam 1 tane), Kumbh Sans ile tutarlı başlık tipografisi, yatay taşma yok (0/19), mobil menü düzgün çalışıyor, masaüstü menü açılır listeleri temiz. Ana sayfa bölüm akışı (hero → sertifika → ürünler → projeler → SSS → yorumlar → blog) doğru kurgulanmış.

**Zayıf yanlar:** Sayfalar aynı "kabuğu" paylaşıyor ama içerikleri 5 farklı yöntemle yazılmış (Elementor HTML widget'ları, Tailwind benzeri satır içi CSS, tema bileşenleri). Bunun sonucu: tutarsız boşluk/yazı boyutu, düşük kontrast, küçük dokunma hedefleri ve mobilde ürün sayfalarının ilk ekranında ürün görünmemesi.

## 3. Ölçümler

### 3.1 Mobil Lighthouse (laboratuvar; sunucu yanıtı ~1.8 sn dahil)

| Skor | Aralık | Not |
|---|---|---|
| Erişilebilirlik | **85–100** | En düşük: `/ic-mekan-led-ekran/` 85, `/rental-ekran/` 86, `/ic-mekan-rgb-panel/` 86, `/dis-mekan-led-ekran/` 87 |
| En iyi uygulamalar | 75–96 | `/rental-ekran/` ve `/iletisim/` 75 |
| SEO | 92–100 | (92: robots.txt denetimi, geçici görünüyor) |
| Performans | 54–77 | Plan kapsamı dışı; ayrı iş (bkz. §8) |

### 3.2 Tüm sitede tekrarlayan sorunlar

| # | Sorun | Etki | Kanıt |
|---|---|---|---|
| S1 | **Marka turuncusu (#F46F2C) metin/buton için yetersiz kontrast** (beyaz üstünde 2.93:1; hedef 4.5:1) | 18/19 sayfada; **245 öğe** (112 turuncu metin üstü beyaz, 76 beyaz yazı üstü turuncu: butonlar ve üst çubuk) | Lighthouse `color-contrast` |
| S2 | **Mobil ürün sayfalarında "Ürünlerimiz" yan menüsü içeriğin üstüne yığılıyor** | 8 sayfa. Menü 607–668 px yer kaplıyor, ilk ürün görseli 913–974 px'te başlıyor; 844 px'lik ilk ekranda **ürün hiç görünmüyor** | DOM ölçümü |
| S3 | Başlık sırası bozuk (yan menü başlığı `h3`) | 11/19 sayfa | `heading-order` |
| S4 | Küçük yazı (< 13 px) | Mobilde: `/kontrol-kartlari/` 124 öğe, `/huidu-…/` 55, `/cob-ekran/` 47, `/program-indir/` 28, `/` 24 | DOM ölçümü |
| S5 | Küçük dokunma hedefi (< 40 px) | Sayfa başına 28–71 öğe; 6 sayfada Lighthouse `target-size` hatası | DOM + Lighthouse |
| S6 | Link yalnızca renkle ayırt ediliyor (altı çizili değil) | 5 sayfa, 16 öğe | `link-in-text-block` |
| S7 | Konsol hatası: `Swiper is not defined` (tema `main.js`) ve `eSendElementorFormsSettings is not defined` (send-app eklentisi) | 19/19 sayfa | Lighthouse `errors-in-console` |
| S8 | Sohbet (Chaty) butonu sol altta; mobilde metni ve listeyi örtüyor | Tüm mobil sayfalar | Ekran görüntüleri |
| S9 | Aynı sayfada iki font ailesi: Kumbh Sans + `system-ui`/`ui-sans-serif` (satır içi widget CSS'inden) | Neredeyse tüm sayfalar; `/sertifikalarimiz/` ve `/led-ekran/`'de sistem fontu baskın | DOM ölçümü |
| S10 | Kırık görsel: `/rental-ekran/` Grand Air kartı (`Air-II-scaled.png`) | 1 sayfa (bilinçli olarak dağıtımdan çıkarılmıştı) | DOM ölçümü |
| S11 | Mobil menüde arama/teklif/telefon eylemi yok | Tüm sayfalar | Ekran görüntüsü |

**S7 hakkında dürüst not:** `Swiper is not defined` hatası, 17 Kasım'daki **mobil hız yamamdan** (v1.3.0) kaynaklanıyor: yama, sayfada Swiper kullanan bir öğe yokken `swiper.min.js`'i kaldırıyor, tema `main.js` ise yine de çağırıyor. 19 sayfanın hiçbirinde Swiper'lı Elementor öğesi yok (`init-carousel-swiper` işaretlemesi: 0/19), yani **görünümde bozulma yok**; yalnızca konsol hatası ve en iyi uygulamalar skorunda ~4 puan. Düzeltme basit (kaldırılan yerde boş bir `Swiper` tanımı bırakmak) ve Faz 0'da.

### 3.3 Menü incelemesi

- **Masaüstü:** Üst çubuk 76 px, menü yazısı 14.4 px; açılır listeler beyaz kart, temiz, ancak öğeler küçük (≈13 px) ve "Tüm ürünler" öğesi yalnızca mobil listede var.
- **Mobil:** Çekmece menü temiz (büyük satırlar, "+" ile alt menü); ancak hiçbir CTA yok (Ara / WhatsApp / Teklif). Dil seçici bayrakla "Türkçe" olarak gösteriliyor.
- **Her sayfada ortak:** turuncu üst çubuk üzerinde beyaz 14 px yazı → kontrast 2.93:1 (S1'in bir parçası).

## 4. Sayfa sayfa bulgular ve öneriler

Öncelik: **P1** = ilk dalga, **P2** = ikinci dalga, **P3** = cila.

### Anasayfa `/` — erişilebilirlik 94
Gördüklerim: Güçlü hero (stant görseli, net CTA). Sertifika şeridinden sonra büyük boş alan; "Ledajans olarak hemen her sektördeyiz" bölümünde dev logo bloğu metinden daha baskın, metin küçük; "İç Mekan / Dış Mekan" tanıtımlarında yan boşluklar ve küçük açıklama yazısı; yorum kartlarında yer tutucu tırnak simgeleri; blog kartlarından birinin kapağı düz turuncu "LED" kutusu; 24 küçük yazı, 57 küçük dokunma hedefi, 15 alt metni boş görsel.
- **P1** Bölümler arası dikey boşluk sistemi (tek ölçek: 64/96 px) ve sertifika sonrası boşluğun kapatılması.
- **P1** "Hemen her sektördeyiz" bölümünü iki kolon, metin/rakam odaklı yeniden dengele (logo bloğu küçülsün, 25 yıl rozeti kalsın).
- **P2** Müşteri yorumlarında gerçek avatar/baş harf + puan yıldızları tek stil; boş tırnak simgesi kaldır.
- **P2** Blog kartı kapakları fotoğraflı (ücretsiz Stock ile) ve tek oran (16:10).
- **P3** Ürün karuseli oklarını büyüt (44 px), kart başlığı 16 → 18 px.

### Kurumsal
- **`/hakkimizda/`** (a11y 100): Sol sütunda uzun düz paragraf, sağda dev turuncu logo şekli; sayfa kısa (2623 px) ve görsel olarak boş. **P2:** paragrafı 3 kısa bloğa böl (kim, ne yapıyoruz, neden biz) + rakam şeridi (25 yıl, 2 yıl garanti, sertifikalar) + sertifika/ekip fotoğrafı. Metin SEO için korunur, yalnızca bölünür.
- **`/sertifikalarimiz/`** (96): Sertifika önizlemeleri küçük, sayfa uzun (4807 px); baskın font `system-ui`. **P2:** 2–3 sütunlu kart ızgarası (önizleme + ad + "PDF indir"), tek font, tıklayınca büyüt.
- **`/firma-bilgilerimiz/`** (96): Tablo okunaklı ama silik filigran logo satırların arkasında; hücre yazısı küçük. **P2:** filigranı kaldır/yalnızca üst köşeye al, satır yüksekliği ve yazıyı artır, IBAN/vergi bilgisi için "kopyala" düğmesi.

### Ürünlerimiz
- **`/led-ekran/`** (96): İyi hub; model kartları ve senaryolar net. Okunan eksikler: kart başlıkları küçük, "Rehberler ve fiyat" bağlantı listesi kalabalık. **P2:** bağlantı listesini 2 sütun etiket (chip) hâline getir; fiyat tablosunun başlık satırı belirgin.
- **Ürün şablonu — `/cob-ekran/`, `/ic-mekan-led-ekran/`, `/dis-mekan-led-ekran/`, `/rental-ekran/`, `/ic-mekan-rgb-panel/`, `/dis-mekan-rgb-panel/`, `/kontrol-kartlari/`, `/guc-kaynaklari/`** (a11y 85–95): Hepsi aynı şablon (200 px banner + sol yan menü + ürün slider + uzun içerik). En büyük sorun **S2**. Ek olarak: içerik "metin duvarı" (`/ic-mekan-led-ekran/` ≈1800 kelime, `/kontrol-kartlari/` ≈1700, `/ic-mekan-rgb-panel/` ≈1400); turuncu kalın alt başlıklar çok küçük; `/cob-ekran/`'da özellik tablosu ve model kartları yoğun; `/kontrol-kartlari/` mobilde 124 küçük yazı öğesi; `/guc-kaynaklari/` ilk ekranda slider alanı boş görünüyor (gerçek mi gecikme mi, doğrulanacak).
  - **P1** Mobilde yan menüyü **yatay kaydırmalı çip şeridine** çevir (tek satır, ~56 px) ve slider/ürün görselini banner'ın hemen altına al.
  - **P1** İlk ekranda: ürün görseli + başlık + "Fiyat teklifi al" ve "Ara" butonları.
  - **P2** Uzun içeriği okunur kıl: içindekiler (sabit çapa bağlantıları), alt başlık boyutu 18–20 px, paragraf ≤ 70 karakter genişlik, açıklayıcı bölümler katlanır (içerik DOM'da kalır; SEO etkilenmez), özellik listeleri 2 sütun kart.
  - **P2** Teknik özellik tabloları mobilde yatay kaydırma yerine kart/satır düzeni.
  - **P3** Sayfa sonu tek tip "Teklif al" bandı ve ilgili ürünler.
  - `/rental-ekran/`: **P1** Grand Air görselini yenile (şu an kırık).
- **Banner (200 px)** — 16 sayfada aynı yapı: koyu örtü, küçük turuncu alt yazı. **P2:** alt yazı beyaz/açık turuncu, kırıntı (breadcrumb) ekle, örtüyü %20 hafiflet.

### Blog `/blog/` (a11y 94)
Gördüklerim: Arama kutusu iyi; kart meta yazısı çok küçük (18–20 öğe), hiç `h2` yok, öne çıkan yazı ayrımı yok. **P2:** öne çıkan yazı (büyük kart), kategori çipleri, sayfalama, kart başlığı 18 px, meta ≥ 13 px.

### Teknik Destek & Bilgi
- **`/colorlight/`** (92): Üstte kırpılmış ürün karuseli, altında indirme kartları. Kırıntı linkleri küçük ve düşük kontrastlı. **P2:** kırıntı 14 px koyu turuncu; indirme kartlarında dosya türü/boyutu satırı; karuselde ortalanmış kart.
- **`/huidu-processor-hdplayer-indir/`** (96): Benzer; mobilde 55 küçük yazı öğesi. **P2:** rozet ve alt etiketler ≥ 12 px, kartlarda tek birincil "İndir" düğmesi.
- **`/program-indir/`** (96): En iyi tasarlanmış sayfalardan; filtre çipleri iyi. 28–30 küçük yazı öğesi, arama kutusu placeholder rengi düşük kontrast (#82828a, 3.81:1). **P2:** placeholder `#6B6B73`, "Ürün: …" satırı büyüt.
- **`/teknik-destek-videolari/`** (96, en iyi performans): Uzun giriş paragrafı + YouTube gömmeleri (üzerinde "Watch on YouTube" katmanı). **P3:** girişi iki satıra indir + kategori çipleri; videoların başlıkları Türkçe, tek tip oran.

### İletişim `/iletisim/` (a11y 95, en iyi uygulamalar 75)
Gördüklerim: Form solda, bilgi kartı sağda; alan etiketleri çok küçük, placeholder soluk, tek tıkla ara/WhatsApp yok görünümde zayıf. **P1:** alan etiketi 14 px, placeholder kontrastı, gönder düğmesi tam genişlik (mobil), Ara/WhatsApp düğmeleri formun üstünde. **P1:** konsol/en iyi uygulamalar 75'in sebebi (form eklentisi hatası + üçüncü taraf çerez) incelenecek. **P2:** harita tıklayınca yüklenen "tembel" gömme.

## 5. Tasarım sistemi önerisi (tüm sayfalara tek kaynaktan)

Kural: değişiklikler **`Ek-CSS-final.css`** (WordPress → Ek CSS) ve mobil yamadaki (`wordpress-mobil-hiz-patch.php`) kurallarla yapılır; masaüstü yalnızca kontrast ve yazı boyutu gibi erişilebilirlik düzeltmeleriyle değişir.

| Konu | Karar |
|---|---|
| **İki tonlu turuncu** | `#F46F2C` (marka) yalnızca **büyük başlık, dolgu, ikon, çizgi** için. **Metin ve buton** için `#C2410C` (beyaz üstünde 5.18:1) ya da en az `#CC4A12` (4.61:1). Koyu lacivert zemin üstünde `#F46F2C` zaten geçiyor (4.8–6.0:1). |
| Üst çubuk | Karar noktası: ① turuncuyu aynen bırak, yazıyı 15–16 px/700 yap (2.93:1 kalır, kabul edilen risk); ② çubuğu `#D9531A`'a (4.04:1) ya da `#CC4A12`'ye (4.61:1) koyulaştır; ③ turuncu çubuk, **lacivert yazı** (6.05:1). Öneri: **②**. |
| Yazı ölçeği | Gövde 16 px (mobil min 15), açıklama/etiket min 13 px, başlık h1 32–40, h2 24–28, h3 18–20; satır yüksekliği 1.6. |
| Font | Yalnızca **Kumbh Sans** (yeni font yok); `system-ui`/`ui-sans-serif` yedeklerini kaldır. |
| Boşluk | Bölüm dikey boşluğu mobil 48, masaüstü 80 px; kart iç boşluğu 20–24; 8 px ızgara. |
| Dokunma hedefi | Tüm bağlantı/buton min 44×44 px (mobil); satır içi bağlantılar altı çizili. |
| Kartlar | Tek yarıçap (16 px), tek gölge, tek görsel oranı (16:10). |
| Sohbet butonu | Mobilde sağ alta, 48 px; sayfa kaydırılırken ve form alanındayken gizle. |
| Mobil sabit eylem çubuğu | Alt çubuk: **Ara · WhatsApp · Teklif** (sayfa içi CTA'lar tekrarlanmaz). |
| Mobil menü | Alta telefon/WhatsApp/Teklif satırı ekle. |

## 6. Uygulama fazları

| Faz | İş | Sayfalar | Tahmini süre* | Risk |
|---|---|---|---|---|
| **0 — Hızlı düzeltmeler** | `Swiper` stub'ı (S7), send-app konsol hatası, `Air-II` görseli, alt metinler, `h3→div` (S3), link altı çizgisi (S6) | 19 | 0.5 gün | Çok düşük |
| **1 — Tasarım sistemi (CSS)** | İki tonlu turuncu, yazı ölçeği, tek font, dokunma hedefleri, sohbet butonu, mobil sabit eylem çubuğu, mobil menü CTA | 19 | 2–3 gün | Düşük–orta (kontrast kararı) |
| **2 — Ürün şablonu** | S2 (çip şeridi + ürün ilk ekranda), banner yenileme + breadcrumb, içindekiler, katlanır bölümler, tablo kartları | 8 ürün + hub | 3–4 gün | Orta (en çok trafik alan şablon) |
| **3 — Ana sayfa** | Bölüm ritmi, "sektör" bölümü, yorumlar, blog kapakları, karusel | 1 | 2–3 gün | Orta (LCP kuralları: hero'ya dokunma) |
| **4 — Kurumsal, destek, iletişim** | Hakkımızda, Sertifikalar, Firma, Colorlight, Huidu, Program İndir, Videolar, İletişim | 8 | 3 gün | Düşük |
| **5 — Blog** | Öne çıkan, kategori çipleri, sayfalama | 1 | 1–2 gün | Düşük |
| **6 — Doğrulama** | Tüm sayfalarda ölçüm ve piksel karşılaştırma, en/de sayfaları kontrolü | 19 | 1 gün | — |

*Tahmin, tek geliştirici + onay turlarını içermez.

Faz sırası: **0 → 1 → 2 → 3 → 4 → 5 → 6**. Her faz kendi başına yayınlanabilir; Faz 1 ve 2 en büyük görünür kazancı verir.

## 7. Çalışma yöntemi (güvenli yayın)

1. **Önce yerelde:** `preview/server.mjs` proxy'sine bir CSS/JS enjeksiyonu eklenir; değişiklikler canlıya dokunmadan gerçek sayfalar üzerinde görülür.
2. **Onay:** her faz için önce/sonra ekran görüntüsü (masaüstü + mobil, 19 sayfa).
3. **Yayın:** CSS → WordPress "Ek CSS" (yedekle, yapıştır) ve gerekiyorsa mu-plugin; her yayında geri alma yolu belgelenir (bu projedeki panel zip'leri gibi).
4. **Doğrulama:** Lighthouse ve piksel karşılaştırma.

## 8. Başarı ölçütleri (faz sonunda)

| Ölçüt | Şimdi | Hedef |
|---|---|---|
| Erişilebilirlik (mobil, 19 sayfa ortalaması) | ~93 | ≥ 97, hiçbir sayfa < 95 |
| `color-contrast` ihlali | 245 öğe / 18 sayfa | 0 (yalnızca büyük metin istisnası) |
| Ürün görseli mobil ilk ekranda | 0/8 sayfa | 8/8 |
| Dokunma hedefi < 44 px (mobil) | 28–71 öğe/sayfa | < 5 |
| Küçük yazı (< 13 px) | 0–124 öğe/sayfa | < 5 |
| Konsol hatası | 19/19 sayfa | 0 |
| CLS (mobil) | < 0.03 | **< 0.1** (bozulmayacak) |
| SEO | 92–100 | değişmeyecek |

## 9. Dokunulmayacaklar (önceki performans çalışmasından ve SEO'dan)

- Rank Math başlık/açıklama/canonical, **başlık metinleri** ve **iç bağlantılar** (görünümü değiştirirken metin aynı kalır; bölme/katlama içerik DOM'da kalarak yapılır).
- jQuery'yi `defer` etme; ana sayfa hero'su için tek poster preload'u ve hero verisi; video preload yok (LCP düzeni).
- Yeni font eklenmez; masaüstü yerleşimi yalnızca erişilebilirlik düzeltmesi ölçüsünde değişir.
- Canlıya yazma yalnızca ayrı onayla.

## 10. Performans notu (kapsam dışı ama görünümü etkiler)

Mobil laboratuvar LCP'leri 3.5–12 sn arası; ölçtüğüm yerden sunucu yanıtı tek başına ~1.8 sn. Sunucu tarafı önbellek (Plesk/nginx FastCGI veya CDN) hâlâ en büyük kazanç; ayrıca `/kontrol-kartlari/` (LCP 11 sn), `/guc-kaynaklari/` (12 sn), `/colorlight/` (10 sn) ve `/blog/` (TBT 524 ms) için sayfa bazlı bir performans turu önerilir.

## 11. Karar bekleyen konular

1. **Üst çubuk/buton turuncusu:** §5'teki seçenek ①/②/③ (öneri ②).
2. **Metin duvarı sayfalarında katlanır bölüm:** içerik DOM'da kalır; kabul mü?
3. **Mobil sabit eylem çubuğu (Ara · WhatsApp · Teklif):** istenir mi?
4. **Kapsam:** İngilizce/Almanca sayfalar da aynı şekilde yapılsın mı?
5. **Önizleme:** Faz 1'den başlayarak yerel önizlemeye enjeksiyon eklememi onaylıyor musun?

## Ekler (`docs/gorunum-plani/`)

`sheetD1.jpg`, `sheetD2.jpg` masaüstü ilk ekranlar · `sheetM1.jpg`, `sheetM2.jpg` mobil ilk ekranlar · `ana-sayfa-masaustu.jpg` · `urun-sayfalari-masaustu.jpg` · `menu-masaustu.jpg`, `menu-mobil.jpg` · `olcum-lighthouse-mobil.json` · `olcum-dom.json`
