# LEDAJANS Katalog — Paket kullanimi

## EN KOLAY: Matbaa PDF (InDesign yok)

**LEDAJANS-Katalog-MATBAA.pdf** → matbaaya direkt ver.

Detay: `BASIT-KILAVUZ.md` veya `INDESIGN-ACILMIYOR.md`

---

## InDesign'da duzenlemek

**IDML dosyasini kullanma** — acilmama hatasi normal.

### Script ile (onerilen)

1. Zip'i `C:\LEDAJANS-Katalog\` gibi yerel klasore cikart
2. InDesign ac
3. **Dosya → Komut Dosyalari → Diger Komut Dosyasi**
4. `LEDAJANS-Katalog-Import.jsx` sec
5. 15 sayfa yerlesince **Dosya → Disa Aktar → Adobe PDF (Baski)**

JSX **Dosya → Ac** ile acilmaz.

### Manuel

`Links` klasorundeki `page-01.png` … `page-15.png` dosyalarini **Dosya → Yerlestir** ile her sayfaya tek tek koy.

---

## Paket icerigi

| Dosya | Aciklama |
|-------|----------|
| LEDAJANS-Katalog-MATBAA.pdf | Matbaa (A4, 300 DPI) |
| LEDAJANS-Katalog-Import.jsx | InDesign otomatik yerlestirme |
| Links/page-XX.png | 15 sayfa gorseli |
| INDESIGN-ACILMIYOR.md | Sorun giderme |
