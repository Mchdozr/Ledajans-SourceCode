# SEO önizleme (yerel, canlıya dokunmaz)

Depo kökünden çalıştırın:

```bash
python3 ONIZLEME/server.py
```

Sonra tarayıcıda **http://localhost:8080/_onizleme/** adresini açın.

- `/<yol>` → önerilen hali, `/_once/<yol>` → 24.11.2026 canlı yedeği
- Yönlendirmeler, robots.txt ve sitemap'ler de yerelde önerilen haliyle çalışır
- Gerekenler: Python 3.10+, `pip install beautifulsoup4`; görseller ve CSS canlı siteden yüklendiği için internet
- Değişiklik listesi `build_preview.py` içindeki `PAGES` tablosunda; düzenledikten sonra `python3 ONIZLEME/build_preview.py`

Hiçbir script canlı siteye yazmaz. Canlıya alma ayrı bir adım olacak ve onayınızla yapılacak.
