# Yerel önizleme (canlıya dokunmaz)

Depo kökünden çalıştırın (Windows'ta `python`, macOS/Linux'ta `python3`):

```
python ONIZLEME/server.py
```

Tarayıcıda **http://localhost:8080/_onizleme/** adresini açın.

## Görünüm önizlemesi (varsayılan)
- Sayfaların metni, title'ı, açıklaması ve SEO ayarları 24.11.2026 canlı yedeğiyle birebir aynı.
- Üzerine sadece `gorunum/` klasöründeki CSS/JS katmanı eklenir. Hangi sayfaya hangi dosyanın ekleneceği `gorunum/degisiklikler.json` içinde.
- Dosyaları kaydedip sayfayı yenilemek yeterli; sunucuyu yeniden başlatmaya gerek yok.
- `/<yol>` yeni görünüm, `/_once/<yol>` canlı yedeği.

## SEO önizlemesi (arşiv)
- Title/meta/H1/yönlendirme önerileri `_arsiv-seo/` klasöründe saklanıyor: `python ONIZLEME/server.py --seo`

Gerekenler: Python 3.10+, `pip install beautifulsoup4`, internet (görseller ve CSS canlı siteden yüklenir).
