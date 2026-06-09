# LEDAJANS Katalog — En Basit Yol (InDesign GEREKMEZ)

## MATBAA ICIN — SADECE BU DOSYAYI INDIR

**LEDAJANS-Katalog-MATBAA.pdf**

15 sayfa, A4, 300 DPI gorseller. Matbaaya direkt ver.

Indir:
https://github.com/Mchdozr/Ledajans-SourceCode/raw/master/Katalog/indesign/LEDAJANS-Katalog-MATBAA.pdf

---

## InDesign'da acmak istiyorsan (manuel, garantili)

IDML ve JSX ile ugrasma. Su adimlar %100 calisir:

1. InDesign ac
2. **Dosya → Yeni → Belge**
   - Baskı
   - Sayfa: **15**
   - Boyut: **A4** (210 x 297 mm)
   - Cift sayfa: **kapali**
3. **Dosya → Yerlestir** (Ctrl+D)
4. Zip'teki **Links** klasorune git
5. **page-01.png** den **page-15.png** ye kadar HEPSINI sec (Ctrl+A)
6. **Ac** tikla
7. Sayfa 1'e tikla → gorsel yerlesir
8. Sonraki sayfaya gec, tekrar tikla... (15 kez)
   - VEYA: her sayfada tek tek yerlestir

9. **Dosya → Disa Aktar → Adobe PDF (Baski)** → Kaydet

---

## JSX script nasil calistirilir?

1. Zip → `C:\LEDAJANS-Katalog\` (OneDrive kullanma)
2. InDesign → **Dosya → Komut Dosyalari → Diger Komut Dosyasi**
3. `LEDAJANS-Katalog-Import.jsx` sec
4. Links otomatik bulunur; 15 sayfa yerlesir

**Dosya → Ac ile JSX ACILMAZ.**

Detayli hata cozumu: `INDESIGN-ACILMIYOR.md`
