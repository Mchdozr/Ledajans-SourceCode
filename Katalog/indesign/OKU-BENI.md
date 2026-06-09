# LEDAJANS Katalog — InDesign Paketi

## İndir ve aç

`LEDAJANS-Katalog-InDesign-Paket.zip` dosyasını indir → zip'i aç → klasörde:

- `LEDAJANS-Katalog-2026.idml`
- `Links/` (15 sayfa görseli)

## Hızlı kullanım (3 adım)

1. **LEDAJANS-Katalog-2026.idml** dosyasını InDesign ile aç (çift tık)
2. Eksik link uyarısı çıkarsa: aynı klasördeki **Links** klasörünü seç
3. **Dosya → Dışa Aktar → Adobe PDF (Baskı)** → [Baskı Kalitesi] → Kaydet

## İçerik
- 15 sayfa A4 + 3mm taşma (bleed)
- 300 DPI sayfa görselleri (HTML katalogdan render)

## Yeniden üret
```bash
python3 Katalog/generate-katalog.py
python3 Katalog/generate-indesign.py
```
