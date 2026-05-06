# Internal Link Agent Raporu (2026-05-06)

## Mevcut durum
- `AGENT-HUB/STATE.md` dosyası workspace içinde bulunamadı; değerlendirme `SEO-Icerik-Widgets/ic-link-haritasi.html` ve `SEO-Icerik-Widgets/` içerikleri üzerinden yapıldı.
- Cornerstone `https://ledajans.com/led-ekran-nedir/` linki içeriklerde yaygın ama tam kapsayıcı değil (özellikle yeni eklenen bazı sayfalarda yok).
- Cornerstone `https://ledajans.com/led-tabela/` linki ciddi zayıf; mevcut taramada yalnızca `sektor-rehberleri/belediye-bilgi-ekrani-rehberi.html` içinden link aldığı görüldü.
- Hub-spoke dağılımında `led-ekran-nedir` kısmen hub rolünde, `led-tabela` ise hub olarak yeterince beslenmiyor.

## Eksik linkler

### 1) Cornerstone'a hiç/çok az link veren zayıf spoke sayfalar
- **Temel rehberler**: `led-ekran-kurulum-rehberi.html`, `led-ekran-bakim-rehberi.html` (özellikle `led-tabela`ya bağ yok).
- **Karşılaştırmalar**: `led-ekran-vs-lcd.html`, `led-ekran-vs-projeksiyon.html`.
- **Teknik sözlük**: `led-panel-nedir.html`, `smd-led-nedir.html`, `gob-led-nedir.html`.
- **Sektör rehberleri**: `eczane-led-tabela-rehberi.html`, `cami-led-ekran-rehberi.html`.
- **Kullanım alanları**: `havaalani-led-ekran.html`, `otel-led-ekran.html`, `fuar-led-ekran.html`, `billboard-led-ekran.html`, `toplanti-odasi-led-ekran.html`.
- **Şehir sayfaları**: `istanbul-led-ekran.html`, `ankara-led-ekran.html`, `izmir-led-ekran.html`.
- **Referans**: `istanbul-dis-mekan-led-referansi.html`.

### 2) Hub-spoke modelinde eksik omurga
- `led-ekran-nedir` ↔ `led-tabela` arasında karşılıklı güçlü bağ eksik.
- LED-ekran odaklı spoke’ların önemli kısmı `led-tabela` cornerstone’una bağlanmıyor.
- Tabela odaklı spoke’lar (`eczane`, `cami`, `belediye`) arasında yatay (sibling) çapraz bağlantı yetersiz.
- Şehir sayfaları ve referans sayfasından cornerstone’lara otorite taşıyan contextual linkler eksik.

## Önerilen link eklemeleri (kaynak -> hedef -> anchor)

### A) Cornerstone hub güçlendirme (öncelik: yüksek)
- `temel-rehberler/led-tabela-rehberi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED ekran nedir? kapsamlı rehber**
- `temel-rehberler/led-ekran-nedir.html` -> `https://ledajans.com/led-tabela/` -> **LED tabela ve dijital tabela rehberi**
- `temel-rehberler/led-ekran-kurulum-rehberi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED ekran teknolojisinin temelini inceleyin**
- `temel-rehberler/led-ekran-kurulum-rehberi.html` -> `https://ledajans.com/led-tabela/` -> **kurulum öncesi LED tabela seçim kriterleri**
- `temel-rehberler/led-ekran-bakim-rehberi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED ekran türleri ve çalışma mantığı**
- `temel-rehberler/led-ekran-bakim-rehberi.html` -> `https://ledajans.com/led-tabela/` -> **LED tabela bakım ve kullanım senaryoları**

### B) Tabela cluster (hub: led-tabela / spoke: eczane-cami-belediye)
- `sektor-rehberleri/eczane-led-tabela-rehberi.html` -> `https://ledajans.com/led-tabela/` -> **eczane için doğru LED tabela seçimi**
- `sektor-rehberleri/eczane-led-tabela-rehberi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED ekran altyapısını öğrenin**
- `sektor-rehberleri/cami-led-ekran-rehberi.html` -> `https://ledajans.com/led-tabela/` -> **cami LED tabela çözümleri rehberi**
- `sektor-rehberleri/cami-led-ekran-rehberi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **dış mekan LED ekran nedir**
- `sektor-rehberleri/belediye-bilgi-ekrani-rehberi.html` -> `https://ledajans.com/led-tabela/` -> **belediye dijital tabela çözümleri**
- `sektor-rehberleri/belediye-bilgi-ekrani-rehberi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **kamusal alanda LED ekran kullanım temelleri**
- `sektor-rehberleri/eczane-led-tabela-rehberi.html` -> `https://ledajans.com/belediye-bilgi-ekrani/` -> **kamu ve kurumsal LED bilgilendirme örnekleri**
- `sektor-rehberleri/belediye-bilgi-ekrani-rehberi.html` -> `https://ledajans.com/eczane-led-tabela/` -> **yüksek görünürlüklü eczane tabela uygulamaları**

### C) Karşılaştırma + sözlük cluster (bilgi mimarisi güçlendirme)
- `karsilastirmalar/led-ekran-vs-lcd.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED ekran nedir ve neden avantajlıdır**
- `karsilastirmalar/led-ekran-vs-lcd.html` -> `https://ledajans.com/led-tabela/` -> **mağaza ve cephe için LED tabela seçenekleri**
- `karsilastirmalar/led-ekran-vs-projeksiyon.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED ekran çalışma prensibi**
- `karsilastirmalar/led-ekran-vs-projeksiyon.html` -> `https://ledajans.com/led-tabela/` -> **dijital tabela yatırım rehberi**
- `sozluk/led-panel-nedir.html` -> `https://ledajans.com/led-ekran-nedir/` -> **LED panel ve LED ekran farkı**
- `sozluk/smd-led-nedir.html` -> `https://ledajans.com/led-ekran-nedir/` -> **SMD dahil LED ekran türleri**
- `sozluk/gob-led-nedir.html` -> `https://ledajans.com/led-ekran-nedir/` -> **GOB teknolojisi hangi LED ekranlarda kullanılır**
- `sozluk/led-panel-nedir.html` -> `https://ledajans.com/led-tabela/` -> **LED panelden tabela çözümüne geçiş rehberi**

### D) Local/Commercial cluster (şehir + kullanım alanı + referans)
- `sehir-sayfalari/istanbul-led-ekran.html` -> `https://ledajans.com/led-ekran-nedir/` -> **İstanbul için LED ekran seçimi öncesi temel rehber**
- `sehir-sayfalari/istanbul-led-ekran.html` -> `https://ledajans.com/led-tabela/` -> **İstanbul LED tabela çözümleri**
- `sehir-sayfalari/ankara-led-ekran.html` -> `https://ledajans.com/led-ekran-nedir/` -> **Ankara projeleri için LED ekran nedir**
- `sehir-sayfalari/ankara-led-ekran.html` -> `https://ledajans.com/led-tabela/` -> **Ankara dijital tabela uygulamaları**
- `sehir-sayfalari/izmir-led-ekran.html` -> `https://ledajans.com/led-ekran-nedir/` -> **İzmir’de doğru LED ekran tipini seçin**
- `sehir-sayfalari/izmir-led-ekran.html` -> `https://ledajans.com/led-tabela/` -> **İzmir LED tabela çözümleri**
- `referanslar/istanbul-dis-mekan-led-referansi.html` -> `https://ledajans.com/led-ekran-nedir/` -> **projede kullanılan LED ekran teknolojisi**
- `referanslar/istanbul-dis-mekan-led-referansi.html` -> `https://ledajans.com/led-tabela/` -> **benzer dış mekan dijital tabela çözümleri**

### E) Kullanım alanları cluster
- `kullanim-alanlari/billboard-led-ekran.html` -> `https://ledajans.com/led-tabela/` -> **billboard için dijital LED tabela rehberi**
- `kullanim-alanlari/otel-led-ekran.html` -> `https://ledajans.com/led-tabela/` -> **otel içi yönlendirme ve LED tabela çözümleri**
- `kullanim-alanlari/fuar-led-ekran.html` -> `https://ledajans.com/led-ekran-nedir/` -> **fuar alanı için LED ekran temelleri**
- `kullanim-alanlari/toplanti-odasi-led-ekran.html` -> `https://ledajans.com/led-ekran-nedir/` -> **yakın izleme için LED ekran seçimi**
- `kullanim-alanlari/havaalani-led-ekran.html` -> `https://ledajans.com/led-tabela/` -> **havaalanı dijital tabela sistemleri**

## Anchor metin stratejisi (kısa)
- `led-ekran-nedir` için anchor varyasyonu: **LED ekran nedir**, **LED ekran türleri**, **LED ekran seçimi rehberi**, **iç/dış mekan LED ekran farkları**.
- `led-tabela` için anchor varyasyonu: **LED tabela rehberi**, **dijital tabela çözümleri**, **LED yazı tabelası**, **işletmeler için LED tabela seçimi**.
- Aynı sayfada tek tip exact-match tekrarından kaçın: 1 exact + 1 partial/semantic anchor dağılımı kullanılmalı.
