# Internal Link Report - 2026-05-06

## Money Pages
- kaynak URL: https://ledajans.com/ | hedef URL: https://ledajans.com/led-ekran/ | anchor: led ekran çözümleri | yerleşim önerisi: anasayfa hero altı kısa tanıtım paragrafının ilk 100 kelimesi.
- kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/ic-mekan-led-ekran/ | anchor: iç mekan led ekran modelleri | yerleşim önerisi: kategori intro metninde "kullanım alanları" cümlesi içinde.
- kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/dis-mekan-led-ekran | anchor: dış mekan led ekran fiyat ve teknik özellikler | yerleşim önerisi: ürün türleri karşılaştırma bloğunda ikinci paragraf.
- kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/rental-ekran/ | anchor: rental led ekran kiralama | yerleşim önerisi: etkinlik ve organizasyon kullanım senaryosu satırında.
- kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/cob-ekran/ | anchor: cob led ekran teknolojisi | yerleşim önerisi: premium segment açıklamasında CTA öncesi.

## Source Pages
- kaynak URL: https://ledajans.com/blog/ | hedef URL: https://ledajans.com/led-ekran/ | anchor: led ekran ürünleri | yerleşim önerisi: blog liste üst açıklama metni ve öne çıkan yazı kart altı.
- kaynak URL: https://ledajans.com/colorlight/ | hedef URL: https://ledajans.com/kontrol-kartlari/ | anchor: led ekran kontrol kartları | yerleşim önerisi: marka tanıtım girişinde "uyumlu donanımlar" cümlesi.
- kaynak URL: https://ledajans.com/huidu-processor-hdplayer-indir/ | hedef URL: https://ledajans.com/kontrol-kartlari/ | anchor: huidu uyumlu kontrol kartları | yerleşim önerisi: indirme bağlantıları sonrası destek notu bloğu.
- kaynak URL: https://ledajans.com/teknik-destek-videolari/ | hedef URL: https://ledajans.com/rental-ekran/ | anchor: rental ekran kurulum rehberi | yerleşim önerisi: video playlist açıklamasında "sahada kurulum" satırı.
- kaynak URL: https://ledajans.com/iletisim/ | hedef URL: https://ledajans.com/led-ekran/ | anchor: led ekran teklif formu öncesi ürünleri inceleyin | yerleşim önerisi: iletişim formu üstünde yardımcı bilgi metni.

## Anchor Set
- kaynak URL: https://ledajans.com/ | hedef URL: https://ledajans.com/led-ekran/ | anchor: led ekran | yerleşim önerisi: genel ve yüksek hacimli ana anchor, sadece 1 kez sitewide.
- kaynak URL: https://ledajans.com/blog/ | hedef URL: https://ledajans.com/ic-mekan-led-ekran/ | anchor: iç mekan led ekran | yerleşim önerisi: bilgilendirici yazılarda exact-match anchor, yazı başına en fazla 1 adet.
- kaynak URL: https://ledajans.com/blog/ | hedef URL: https://ledajans.com/dis-mekan-led-ekran | anchor: dış mekan led ekran çözümleri | yerleşim önerisi: ticari niyetli içeriklerde kısmi eşleşme anchor.
- kaynak URL: https://ledajans.com/teknik-destek-videolari/ | hedef URL: https://ledajans.com/kontrol-kartlari/ | anchor: kontrol kartları | yerleşim önerisi: işlem adımı anlatan paragraflarda kısa anchor.
- kaynak URL: https://ledajans.com/colorlight/ | hedef URL: https://ledajans.com/cob-ekran/ | anchor: cob smart screen serisi | yerleşim önerisi: ürün ailesi karşılaştırma satırında marka + kategori anchor.

## Link Injection Plan
- kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/ic-mekan-led-ekran/ | anchor: iç mekan led ekran modelleri | yerleşim önerisi: ilk içerik bloğu (üst fold altı) içine contextual link, footer/sitewide tekrar yok.
- kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/dis-mekan-led-ekran | anchor: dış mekan led ekran çözümleri | yerleşim önerisi: karşılaştırma tablosu altı kısa açıklamada tek link.
- kaynak URL: https://ledajans.com/blog/ | hedef URL: https://ledajans.com/rental-ekran/ | anchor: rental led ekran kiralama | yerleşim önerisi: "etkinlik ekranı" temalı 3 yazıya dağıtılmış derin linkleme.
- kaynak URL: https://ledajans.com/kontrol-kartlari/ | hedef URL: https://ledajans.com/led-ekran/ | anchor: uyumlu led ekran serileri | yerleşim önerisi: tablo üstü intro metnine geri besleyen hub link.
- [BLOCKER] kaynak URL: https://ledajans.com/led-ekran/ | hedef URL: https://ledajans.com/guc-kaynaklari/ ve https://ledajans.com/power-supply/ | anchor: güç kaynakları | yerleşim önerisi: link enjeksiyonu öncesi tek kanonik hedef URL belirlenmeli (slug tutarsızlığı çözülmeden link equity bölünür).

## Execution Update - 2026-05-06 11:38 UTC
### Completed Analysis
- Mevcut iç link matrisi, para sayfa önceliğine göre tekrar sıralandı ve enjeksiyonun "önce hub -> sonra alt kategori -> sonra destekleyici içerik" akışında ilerlemesi gerektiği doğrulandı.
- Slug çakışması bulunan hedefte (`/guc-kaynaklari/` vs `/power-supply/`) tek hedefe konsolidasyon yapılmadan yeni link enjeksiyonu yapılmasının otoriteyi böleceği teyit edildi.
- [BLOCKER] Slug standardı netleşmeden aynı anchor ailesinin iki URL'ye dağılması, takip ve ölçüm katmanında yanlış pozisyon/CTR yorumlarına yol açabilir.

### Proposed Changes (No Apply)
1. Link enjeksiyon sırası (uygulama sırası önerisi):
   - Faz-1 (Hub Güçlendirme): `/` ve `/blog/` kaynaklarından yalnızca `/led-ekran/` hedefine 2-3 adet yüksek görünürlükte contextual link.
   - Faz-2 (Kategori Dağıtımı): `/led-ekran/` üzerinden `/ic-mekan-led-ekran/`, `/dis-mekan-led-ekran`, `/rental-ekran/`, `/cob-ekran/` hedeflerine tekil ve niyet uyumlu anchor dağıtımı.
   - Faz-3 (Destekleyici Derin Link): teknik ve eğitim içeriklerinden (`/teknik-destek-videolari/`, marka/sürücü sayfaları) ilgili ticari alt sayfalara kısmi eşleşme anchor ile kontrollü linkleme.
   - Faz-4 (Geri Besleme): `/kontrol-kartlari/` ve alt donanım sayfalarından `/led-ekran/` hub'ına geri dönüş linkleri ile silo kapanışı.
2. Slug blocker çözüm önerisi:
   - Tek kanonik slug seç: tercih edilen hedef örn. `/guc-kaynaklari/` (TR dil yapısıyla uyumlu).
   - Diğer varyantı (`/power-supply/`) 301 ile kanonik sluga yönlendir; canonical, sitemap, breadcrumb ve iç linkleri tek hedefte birleştir.
   - Anchor normalizasyon kuralı ekle: "güç kaynakları" anchor'ı sprint boyunca sadece seçilen kanonik hedefe bağlansın.
   - Ölçüm planı: değişim sonrası 14 gün boyunca hedef URL bazında internal click, GSC query-url eşleşmesi ve index kapsam tutarlılığı kontrol edilsin.
3. Emniyet kuralı:
   - Slug konsolidasyonu tamamlanana kadar yeni "güç kaynakları" anchor enjeksiyonu dondurulsun; yalnızca mevcut kritik linkler korunup çoğaltma yapılmasın.

### Data/Approval Needs
- URL standardizasyon kararı için onay: kanonik hedef `/guc-kaynaklari/` mı, `/power-supply/` mı olacak?
- Mevcut CMS yönlendirme yetkinliği bilgisi gerekli: 301 ve canonical güncellemesi tek panelden yapılabiliyor mu?
- Ölçümde kullanılacak birincil kaynak onayı gerekli: GSC + analytics event eşleştirmesi hangi panelden izlenecek?

### Next Step
- Onay gelir gelmez önce slug konsolidasyon backlog maddesi "P0-blocker" olarak işaretlenecek, ardından link enjeksiyonu Faz-1 -> Faz-4 sırasıyla sadece kanonik hedefler üzerinde uygulanmak üzere orkestrasyona teslim edilecek.

## Brainstorm Round - 2026-05-06 11:41 UTC

### Cross-Agent Objections
- [Content raporu](./2026-05-06-content.md) içindeki "`/blog/led-ekran-fiyatlari-2026/` ilk %30 bölümüne para sayfa linkleri ekleme" önerisine itiraz: erken ve yoğun commercial anchor enjeksiyonu, bilgi niyetli içerikte link bloklaşması yaratıp editoryal akışı bozabilir. Link mimarisi açısından blog -> hub (`/led-ekran/`) -> alt kategori kademesi korunmalı; doğrudan çoklu money-page dağıtımı tek adımda yapılmamalı.
- [GSC raporu](./2026-05-06-gsc.md) içindeki "internal linklerde tek kanonik URL standardı uygula" ifadesi doğru yönlü olsa da eksik: yalnız URL standardizasyonu, anchor kümesindeki niyet ayrışması ve sayfa-şablon konumu kontrol edilmezse link equity yine yanlış sayfalara yığılır. İtiraz noktası, standardın sadece teknik URL tekilleştirme değil "kaynak tipi + anchor intent + tıklama derinliği" boyutlarıyla tanımlanması gerekliliği.
- [Tech SEO raporu](./2026-05-06-tech-seo.md) içindeki "`llms.txt` P1 adımı" önceliğine kısmi itiraz: mevcut sprintte link mimarisi darboğazı (slug çakışması + hub akışı) çözülmeden bu adımın etki/kazanç oranı düşük kalır. İç link akışı düzeltilmeden yardımcı sinyal dosyaları organik dağılımı anlamlı ölçüde iyileştirmez.

### Self-Corrections
- Önceki planımda `/blog/` kaynağından `/rental-ekran/` için "3 yazıya dağıtılmış derin linkleme" önerisi vardı; bunu tek turda açmak yerine aşamalı test (1 yazı -> ölçüm -> genişletme) yaklaşımına çekiyorum.
- Anchor setinde exact-match oranını bazı kaynaklarda fazla agresif kurguladım; link mimarisi sağlığı için branded/partial varyasyon oranını artırıp aynı paragrafta tekrar anchor kullanımını sınırlandırmak daha doğru.

### Proposed Changes (No Apply)
- Faz-2 öncesi "Anchor Intent Matrix" tablosu eklensin: her hedef için izinli anchor tipleri (`exact`, `partial`, `branded`) ve kaynak şablon kotası (hero, intro, karşılaştırma, FAQ).
- Blog kaynaklarında kural seti tanımlansın: ilk 400 kelimede en fazla 1 ticari anchor, ikinci ticari anchor sadece hub sayfaya; alt kategori linkleri içerik niyeti doğrulanınca açılsın.
- `/dis-mekan-led-ekran` ve benzeri trailing-slash tutarsız URL'ler için tek kanonik format zorunlu hale getirilsin; link enjeksiyonu check-list'ine "final URL normalization" maddesi eklensin.
- İç link uygulama sonrası doğrulama metriği genişletilsin: sadece GSC değil, kaynak sayfa scroll-depth ve link click event'i birlikte izlenerek konumsal link performansı ölçülsün.

### Next Debate Question
- Para sayfa otoritesini artırırken bilgi niyetli blog sayfalarında "ticari anchor yoğunluğu" için güvenli üst sınır ne olmalı: sayfa başına sabit adet mi, yoksa kelime sayısı ve intent skoruna göre dinamik eşik mi?

## Execution Update - 2026-05-06 15:28 TR
### Completed Analysis
- `STATE.md`, `TASKS.md` ve `MASTER-PLAN.md` ile internal-link kapsamı tekrar hizalandı; P1 öncelik içinde iç link akışının hub merkezli kademeli dağıtım prensibi korunarak ilerlemesi teyit edildi.
- Önceki turdaki slug/canonical blocker etkisi yeniden değerlendirildi; kanonik karar netleşmeden yeni money anchor yayılımının ölçüm kalitesini bozacağı doğrulandı.

### Team Sync Notes
- Kabul: GSC tarafındaki kanonik tekilleştirme yönü, iç link enjeksiyonu için ön koşul olarak kabul edildi; ancak anchor intent katmanı ile birlikte yürütülmesi gerektiği notu korundu.
- Revize: Content tarafında blog üst bölümde ticari link kullanımına "aşamalı açılım" yaklaşımı önerisi uygulanabilir bulundu (tek içerik pilotu -> ölçüm -> genişletme).
- [TO:gsc] [FB:IL-2026-05-06-01] `/guc-kaynaklari/` vs `/power-supply/` için nihai kanonik URL kararını ve GSC URL Inspection sonucunu paylaş; karar gelmeden ilgili anchor ailesi genişletilmeyecek.

### Proposed Changes (No Apply)
- Dosya/şablon bazlı uygulama tanımı: `/blog/*` içeriklerinde ilk 400 kelimede en fazla 1 ticari anchor kuralı check-list maddesi olarak standartlaştırılsın (teknik etki: link sinyali seyrelmesini azaltır; SEO etki: niyet uyumu artar; risk: düşük, editoryal güncelleme ihtiyacı).
- Dosya/şablon bazlı uygulama tanımı: `/led-ekran/` sayfasında alt kategoriye giden linkler için `exact` anchor oranı düşürülüp `partial/branded` karışımı zorunlu hale getirilsin (teknik etki: anchor profile dengelenir; SEO etki: aşırı optimizasyon riski azalır; risk: orta, metin revizyon koordinasyonu gerekir).

### QA / Risk Check
- QA-1: Kaynak şablon başına link sayısı ve konumu (hero/intro/orta blok) yayın öncesi kontrol listesi ile doğrulanmalı.
- QA-2: Kırık link ve normalize URL doğrulaması (tek kanonik hedef) tamamlanmadan dağıtım yapılmamalı.
- Risk: KANONİK karar gecikirse Faz-2/Faz-3 planı beklemeye alınır ve money-page iç link büyümesi geçici olarak yalnız hub yönünde tutulur.

### Data/Approval Needs
- GSC onayı: `IL-2026-05-06-01` için URL Inspection + canonical seçimi çıktısı gerekli.
- Orchestrator onayı: Blog kaynaklarında pilot kapsam (kaç URL ile başlayacağı) netleştirilmeli.

### Next Step (Owner + ETA)
- Owner: gsc | ETA: 2026-05-06 16:00 TR -> `IL-2026-05-06-01` canonical karar dönüşü.
- Owner: internal-link | ETA: 2026-05-06 16:20 TR -> karar sonrası anchor dağıtım matrisi v2 (yalnız kanonik hedeflerle) rapora eklenecek.
