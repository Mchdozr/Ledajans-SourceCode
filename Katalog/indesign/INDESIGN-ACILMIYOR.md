# InDesign'da dosya acilmiyor — cozum

## Onemli: Ne acilmaz?

| Dosya | Dosya > Ac ile | Ne yapilir |
|-------|----------------|------------|
| `.jsx` | **ACILMAZ** (script) | Asagidaki "Script calistir" |
| `.idml` | Cogu zaman hata verir | Kullanma — script veya PDF kullan |
| `.pdf` | Acilir ama matbaa icin gerek yok | Direkt matbaaya ver |

**InDesign'da "dosya acmak" = duzenlenebilir belge.** JSX script degil; IDML otomatik uretimde bozuluyor.

---

## Cozum A — InDesign GEREKMEZ (matbaa)

1. GitHub'dan indir: **LEDAJANS-Katalog-MATBAA.pdf**
2. Matbaaya gonder. Bitti.

Indirme:
https://github.com/Mchdozr/Ledajans-SourceCode/raw/master/Katalog/indesign/LEDAJANS-Katalog-MATBAA.pdf

---

## Cozum B — InDesign'da duzenlemek (script)

Zip'i **OneDrive disinda** yerel klasore cikart, ornek: `C:\LEDAJANS-Katalog\`

### Adim 1 — Script'i calistir (Dosya > Ac DEGIL)

**Turkce InDesign:**
1. InDesign ac
2. **Dosya → Komut Dosyalari → Diger Komut Dosyasi...**
3. `C:\LEDAJANS-Katalog\LEDAJANS-Katalog-Import.jsx` sec → **Ac**
4. Links klasoru otomatik bulunursa **Tamam**; istenirse `Links` klasorunu sec
5. "15 sayfa yerlestirildi" mesaji gelince: **Dosya → Disa Aktar → Adobe PDF (Baski)**

**Alternatif (panel):**
1. **Pencere → Yardimci Programlar → Komut Dosyalari**
2. `LEDAJANS-Katalog-Import.jsx` dosyasini su klasore kopyala:
   `C:\Users\KULLANICI_ADIN\AppData\Roaming\Adobe\InDesign\Version 20.0\tr_TR\Scripts\Scripts Panel\`
3. Panelde script adina **cift tik**

### Adim 2 — Hata alirsan

- **"Gecerli belge degil"** → JSX'i Dosya>Ac ile acmaya calisiyorsun; Cozum B Adim 1
- **"page-01.png bulunamadi"** → Zip tam cikmamis; `Links` icinde 15 PNG olmali
- **Bos sayfa** → Links yolunu elle sec
- **OneDrive** → Dosyalari `C:\LEDAJANS-Katalog\` gibi yerel klasore tasi

---

## Cozum C — Tamamen manuel (script de calismazsa)

1. InDesign → **Dosya → Yeni → Belge** → 15 sayfa, A4, cift sayfa kapali
2. **Dosya → Yerlestir** (Ctrl+D) → `Links\page-01.png`
3. Sayfa 1'e tikla → gorsel yerlesir
4. Sayfa 2'ye gec, `page-02.png` yerlestir ... 15'e kadar
5. **Dosya → Disa Aktar → Adobe PDF (Baski)**

Bu yontem her InDesign surumunde calisir.
