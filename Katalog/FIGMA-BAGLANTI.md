# Figma Bağlantısı — LEDAJANS Katalog

## Aktif Figma Dosyası

**LEDAJANS Katalog 2026:** https://www.figma.com/design/nzwEECDoNRqekt8pUo5Jsl

**15 sayfa** tam katalog HTML olarak hazır. Figma'ya aktarım için `generate_figma_design` veya html.to.design kullanın.

### Sayfa Listesi
01 Kapak · 02 Tanıtım · 03 İçindekiler · 04-13 Ürünler · 14 Referanslar · 15 İletişim

## 1. Cursor'da Figma MCP Kurulumu

1. **Figma Desktop** uygulamasını açın (web değil, masaüstü sürümü)
2. Cursor → **Settings → MCP → Add Server**
3. Figma MCP sunucusunu ekleyin:
   ```json
   {
     "mcpServers": {
       "figma": {
         "url": "http://127.0.0.1:3845/sse"
       }
     }
   }
   ```
4. Figma'da: **Preferences → Enable Dev Mode MCP Server** seçeneğini açın
5. Cursor'u yeniden başlatın

## 2. Figma'da Katalog Dosyası Oluşturma

1. Figma'da yeni dosya: **"LEDAJANS Katalog 2026"**
2. Frame boyutu: **210 × 297** (A4, mm birimi)
3. `design-tokens.json` dosyasındaki renkleri Figma Variables olarak ekleyin:
   - `brand-orange` → #f46f2c
   - `brand-dark` → #1a1a2e
   - `brand-navy` → #16213e
4. Font: **Inter** (Google Fonts'tan Figma'ya ekleyin)

## 3. Sayfa Şablonları (Component)

| Component | Boyut | Açıklama |
|-----------|-------|----------|
| `Page/Cover` | 210×297 | Kapak — logo + hero + kategori listesi |
| `Page/TOC` | 210×297 | İçindekiler — sol görseller + sağ liste |
| `Page/Product` | 210×297 | Ürün — hero + spec grid + galeri |
| `Page/Contact` | 210×297 | Arka kapak — 3 ofis bilgisi |
| `Page/Reference` | 210×297 | Referans kolaj |

## 4. HTML → Figma Aktarım

Bu repodaki örnek sayfalar (`Katalog/pages/`) Figma'ya referans olarak kullanılabilir:

- **html.to.design** Figma eklentisi ile HTML sayfalarını Figma'ya import edin
- Veya ekran görüntüsü alıp Figma'da trace edin

## 5. Baskı Çıktısı

Figma'dan baskı PDF:
- **File → Export → PDF** (300 DPI, CMYK profil)
- Bleed: 3mm her kenarda
- Matbaa için: PDF/X-4 formatı tercih edin

HTML'den baskı PDF:
- `index.html` açın → **PDF İndir / Yazdır** butonu
- Chrome'da: Yazdır → Hedef: PDF → Kağıt: A4 → Kenar boşlukları: Yok

## 6. Önizleme

```bash
cd /workspace
python3 -m http.server 8080 --directory Katalog
# http://localhost:8080/index.html
```
