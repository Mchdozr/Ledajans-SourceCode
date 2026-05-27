---
name: ledajans-cloud-run
description: LEDAJANS WordPress içerik staging deposunda bulut aracıları için çalıştırma, doğrulama ve güvenli test akışları (Python 3.12+, /workspace kökü).
---

# LEDAJANS Cloud Agent — Çalıştırma ve Test

Bu depo **derleme adımı içermez**; statik HTML + Python araçlarıdır. Node zorunlu değildir. Tüm komutlar **repo kökünden** (`cd /workspace`) çalıştırılmalıdır; betikler `/workspace` yolunu varsayar.

## Oturum ve kimlik

| Bağlam | Ne yap |
|--------|--------|
| **WordPress REST dağıtımı** | Canlı API çağrısı kimlik bilgisi ister. Bulutta varsayılan olarak **`python3 deploy-to-wordpress.py --dry-run`** kullan; gerçek yayın için kullanıcı ortamında geçerli Uygulama Şifresi gerekir. Kimlik bilgilerini beceriye veya sohbete yapıştırma. |
| **WP-CLI (`deploy-wp-cli.sh`)** | Sunucuda SSH + `wp` CLI gerekir; bulut VM’de genelde yoktur — yerelde veya hedef sunucuda çalıştır. |
| **Özellik bayrakları** | Bu repoda uygulama/feature flag yoktur; “bayrak” yerine **`DRY_RUN`** (`--dry-run`) ve rapor imzası (orchestrator) kullanılır. |

## Ortam

- **Python:** 3.12+, `requests` (Cloud VM’de hazır olabilir).
- **Çalışma dizini:** `/workspace` (Cursor Cloud ile eşleşir).
- **Doğrulama:** Birim test suite yok; çıkış kodu ve üretilen dosyalar kontrol edilir.

---

## Alan bazlı çalıştırma ve test iş akışları

### 1) HTML içerik ve widget snippet’leri

**Klasörler:** `Anasayfa/`, `Blog/`, `Urunlerimiz/`, `Kurumsal/`, `LED Ekran/`, `Footer/`, `Ust-Menu/`, `İletisim/`, `Teknik-Destek-Bilgi/`, `Code-Snippets/`

**Çalıştırma (önizleme):**

```bash
cd /workspace && python3 -m http.server 8080
```

Tarayıcıdan ilgili `.html` yolunu aç (ör. `http://localhost:8080/Blog/...html`). Cloud’ta port erişimi kısıtlıysa dosyayı okuyup iç linkleri `grep` ile kontrol et.

**Somut test akışı:**

1. Düzenlenen dosyayı aç; kritik `href` ve görsel yollarının göreli olduğunu doğrula.
2. İsteğe bağlı: `python3 -c "from pathlib import Path; print(Path('...').read_text(encoding='utf-8')[:2000])"` ile içerik önizlemesi.

### 2) SEO içerik kitaplığı (`SEO-Icerik-Widgets/`)

Alt alanlar: `temel-rehberler/`, `sektor-rehberleri/`, `karsilastirmalar/`, `sozluk/`, `sehir-sayfalari/`, `kullanim-alanlari/`, `referanslar/`, `schema/`

**Dağıtım eşlemesi:** `deploy-to-wordpress.py` içindeki `PAGES_TO_DEPLOY` listesi dosya → slug eşler.

**Somut test akışı:**

1. `python3 deploy-to-wordpress.py --dry-run` — HTTP yazımı yok; mantık ve listelenen sayfalar doğrulanır.
2. Yeni sayfa eklediysen aynı dosyada slug ve relative path’in listeye uyduğunu kontrol et.

### 3) Dağıtım betikleri

| Betik | Güvenli test | Not |
|-------|----------------|-----|
| `deploy-to-wordpress.py` | `--dry-run` | REST kimliği olmadan da dry-run akışı çalışır; 403 yalnızca gerçek istekte. |
| `deploy-wp-cli.sh` | Shell sözdizimi: `bash -n deploy-wp-cli.sh` | Gerçek çalıştırma hedef WP ortamında. |
| `set-rankmath-meta.sh` | `bash -n set-rankmath-meta.sh` | Üretimde RankMath / WP erişimi gerekir. |

### 4) AGENT-HUB (SEO orkestrasyonu)

**Betikler:** `AGENT-HUB/auto_orchestrator.py`, `AGENT-HUB/live_dashboard.py`, isteğe bağlı döngüler: `run-auto-orchestrator.sh`, `run-live-dashboard.sh`, haftalık SERP günlüğü: `weekly_serp_led_ekran.py` / `run-weekly-serp-led-ekran.sh` (DuckDuckGo HTML; Google yerine geçmez)

**Somut test akışı:**

```bash
cd /workspace
python3 AGENT-HUB/auto_orchestrator.py && echo OK
python3 AGENT-HUB/live_dashboard.py && echo OK
```

- Orchestrator: `AGENT-HUB/REPORTS/*.md` imzası değişmediyse **no-op** olabilir; test için bir rapor dosyası güncellendi mi veya `TASKS.md` / `.auto-orchestrator-state.json` üretimi gözleniyor mu bak.
- Dashboard: `AGENT-HUB/DASHBOARD.md` ve `DASHBOARD.html` güncellenir.

**Dashboard önizleme:**

```bash
python3 -m http.server 8080 --directory /workspace/AGENT-HUB
```

Sonra `DASHBOARD.html` yolu (yerel erişim mümkünse).

### 5) Lighthouse / performans / SEO JSON varlıkları

Kök dizinde: `audit-*.json`, `perf-*.json`, `seo-audit-*.json`, `psi-mobile.json`, `lighthouse-ledajans.report.html`

**Somut test akışı:**

```bash
python3 -m json.tool /workspace/psi-mobile.json > /dev/null && echo "JSON OK"
```

Büyük dosyalar için aynı kalıp; HTML için dosyanın var olduğu ve açıldığı kontrol edilir.

### 6) WordPress performans eklentisi

**Dosya:** `wordpress-mobil-hiz-patch.php`

**Test:** PHP sözdizimi — `php -l wordpress-mobil-hiz-patch.php` (ortamda `php` varsa). Dağıtım WordPress dosya sistemi / eklenti kurulumu ile yapılır; bulutta genelde sadece sözdizimi kontrolü.

---

## Hızlı referans (tüm depo duman testi)

```bash
cd /workspace
python3 AGENT-HUB/auto_orchestrator.py && echo OK
python3 AGENT-HUB/live_dashboard.py && echo OK
python3 deploy-to-wordpress.py --dry-run && echo OK
```

---

## Bu beceriyi ne zaman güncelle

1. **Yeni betik veya bayrak:** `AGENTS.md` veya ilgili `.py` / `.sh` başına bak; bu dosyada tablo ve komutları eşitle.
2. **Yeni içerik kökü:** Üst düzey klasör eklendiyse “Alan bazlı” bölümüne bir satır ve somut test adımı ekle (ör. önizleme URL’si veya `dry-run` kapsamı).
3. **Dağıtım veya WP API değişti:** `deploy-to-wordpress.py` içindeki ortam değişkenleri / `--dry-run` davranışı güncellendiyse “Oturum ve kimlik” ile dağıtım tablosunu düzenle.
4. **Yeni doğrulama aracı:** Repo’ya `Makefile`, `pytest` veya CI eklendiğinde “Hızlı referans”a tek satır komut olarak yansıt.

Değişiklikten sonra bu listedeki komutları bir kez çalıştırarak becerinin gerçeklik kontrolünü yap.
