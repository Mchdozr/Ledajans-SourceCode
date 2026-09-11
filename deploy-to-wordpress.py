"""
LEDAJANS SEO Sayfalarını WordPress'e Toplu Yayınlama Scripti
=============================================================
Kullanım:
  1) WP Admin → Kullanıcılar → Profilim → Uygulama Şifreleri → Yeni şifre oluştur
  2) Aşağıdaki 3 değişkeni doldur
  3) python deploy-to-wordpress.py
"""

import os, re, json, time, sys

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
except ImportError:
    print("requests kütüphanesi yükleniyor...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

def load_dotenv(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ======================== AYARLAR ========================
WP_SITE_URL = os.environ.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
WP_USERNAME = os.environ.get("WP_USERNAME", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "").replace(" ", "")
# =========================================================

DRY_RUN = "--dry-run" in sys.argv  # Test modu: gerçekten yayınlamadan kontrol eder
BLOG_ONLY = "--blog-only" in sys.argv  # Yalnızca Blog/* post kayıtları

API_BASE = f"{WP_SITE_URL}/wp-json/wp/v2"

PAGES_TO_DEPLOY = [
    # (dosya_yolu, slug, başlık, tip: "page" veya "post")
    # === ANA SAYFA / HUB ===
    ("Anasayfa/widget-7-projeler.html",                            "projeler",                   "LED Ekran Projeleri",                             "page"),

    # === TEMEL REHBERLER ===
    ("SEO-Icerik-Widgets/temel-rehberler/led-ekran-nedir.html",         "led-ekran-nedir",            "LED Ekran Nedir? Kapsamlı Rehber",                "page"),
    ("SEO-Icerik-Widgets/temel-rehberler/led-tabela-rehberi.html",      "led-tabela",                 "LED Tabela Rehberi",                              "page"),
    ("SEO-Icerik-Widgets/temel-rehberler/led-ekran-kurulum-rehberi.html","led-ekran-kurulum",          "LED Ekran Kurulum Rehberi",                       "page"),
    ("SEO-Icerik-Widgets/temel-rehberler/led-ekran-bakim-rehberi.html", "led-ekran-bakim",            "LED Ekran Bakım Rehberi",                         "page"),

    # === SEKTÖR REHBERLERİ ===
    ("SEO-Icerik-Widgets/sektor-rehberleri/avm-led-ekran-rehberi.html",           "avm-led-ekran-rehberi",      "AVM LED Ekran Rehberi",          "page"),
    ("SEO-Icerik-Widgets/sektor-rehberleri/stadyum-led-ekran-rehberi.html",       "stadyum-led-ekran",          "Stadyum LED Ekran Rehberi",      "page"),
    ("SEO-Icerik-Widgets/sektor-rehberleri/magaza-vitrin-led-rehberi.html",       "magaza-vitrin-led-ekran",    "Mağaza Vitrin LED Ekran",        "page"),
    ("SEO-Icerik-Widgets/sektor-rehberleri/belediye-bilgi-ekrani-rehberi.html",   "belediye-bilgi-ekrani",      "Belediye Bilgi Ekranı Rehberi",  "page"),
    ("SEO-Icerik-Widgets/sektor-rehberleri/eczane-led-tabela-rehberi.html",       "eczane-led-tabela",          "Eczane LED Tabela Rehberi",      "page"),
    ("SEO-Icerik-Widgets/sektor-rehberleri/cami-led-ekran-rehberi.html",          "cami-led-ekran",             "Cami LED Ekran Rehberi",         "page"),

    # === KARŞILAŞTIRMALAR ===
    ("SEO-Icerik-Widgets/karsilastirmalar/p2-vs-p3-led-ekran.html",              "p2-vs-p3-led-ekran",         "P2 vs P3 LED Ekran Karşılaştırma",    "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/ic-mekan-vs-dis-mekan-led.html",       "ic-mekan-dis-mekan-led-farki","İç Mekan vs Dış Mekan LED Farkı",     "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/cob-led-ne-zaman.html",                "cob-led-ne-zaman",           "COB LED Ne Zaman Tercih Edilmeli?",   "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/gob-vs-cob-smd.html",                  "gob-vs-cob-smd",             "GOB vs COB vs SMD LED Ekran",         "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/led-ekran-vs-lcd.html",                "led-ekran-lcd-farki",        "LED Ekran vs LCD Karşılaştırma",      "page"),
    ("SEO-Icerik-Widgets/karsilastirmalar/led-ekran-vs-projeksiyon.html",        "led-ekran-projeksiyon",      "LED Ekran vs Projeksiyon",            "page"),

    # === TEKNİK SÖZLÜK ===
    ("SEO-Icerik-Widgets/sozluk/pitch-led-nedir.html",       "pitch-led-nedir",       "Piksel Pitch Nedir?",             "page"),
    ("SEO-Icerik-Widgets/sozluk/refresh-hz-nedir.html",      "refresh-hz-nedir",      "Refresh Rate (Hz) Nedir?",        "page"),
    ("SEO-Icerik-Widgets/sozluk/nits-parlaklik-nedir.html",  "nits-parlaklik-nedir",  "Nits Parlaklık Nedir?",           "page"),
    ("SEO-Icerik-Widgets/sozluk/ip-koruma-led-ekran.html",   "ip-koruma-led-ekran",   "IP Koruma Sınıfı ve LED Ekran",   "page"),
    ("SEO-Icerik-Widgets/sozluk/led-panel-nedir.html",       "led-panel-nedir",       "LED Panel Nedir?",                "page"),
    ("SEO-Icerik-Widgets/sozluk/smd-led-nedir.html",         "smd-led-nedir",         "SMD LED Nedir?",                  "page"),
    ("SEO-Icerik-Widgets/sozluk/gob-led-nedir.html",         "gob-led-nedir",         "GOB LED Nedir?",                  "page"),

    # === P1 PARA SAYFA (GOB hub) ===
    ("Urunlerimiz/Gob-Led-Ekran/page.html",                 "gob-led-ekran",         "GOB LED Ekran",                   "page"),

    # === ŞEHİR SAYFALARI ===
    ("SEO-Icerik-Widgets/sehir-sayfalari/istanbul-led-ekran.html",  "istanbul-led-ekran",  "İstanbul LED Ekran",   "page"),
    ("SEO-Icerik-Widgets/sehir-sayfalari/ankara-led-ekran.html",    "ankara-led-ekran",    "Ankara LED Ekran",     "page"),
    ("SEO-Icerik-Widgets/sehir-sayfalari/izmir-led-ekran.html",     "izmir-led-ekran",     "İzmir LED Ekran",      "page"),

    # === KULLANIM ALANLARI ===
    ("SEO-Icerik-Widgets/kullanim-alanlari/havaalani-led-ekran.html",         "havaalani-led-ekran",         "Havalimanı LED Ekran",          "page"),
    ("SEO-Icerik-Widgets/kullanim-alanlari/otel-led-ekran.html",              "otel-led-ekran",              "Otel LED Ekran",                "page"),
    ("SEO-Icerik-Widgets/kullanim-alanlari/fuar-led-ekran.html",              "fuar-led-ekran",              "Fuar LED Ekran",                "page"),
    ("SEO-Icerik-Widgets/kullanim-alanlari/billboard-led-ekran.html",         "billboard-led-ekran",         "Billboard LED Ekran",           "page"),
    ("SEO-Icerik-Widgets/kullanim-alanlari/toplanti-odasi-led-ekran.html",    "toplanti-odasi-led-ekran",    "Toplantı Odası LED Ekran",      "page"),

    # === BLOG ===
    ("Blog/led-ekran-fiyatlari-2026-rehber.html",  "led-ekran-fiyatlari-2026",  "LED Ekran Fiyatları 2026 (Mayıs Güncel)",  "post"),
    ("Blog/ic-mekan-led-ekran-fiyatlari-2026-rehber.html", "ic-mekan-led-ekran-fiyatlari-2026", "İç Mekan LED Ekran Fiyatları 2026", "post"),
    ("Blog/dis-mekan-led-ekran-fiyatlari-2026-rehber.html", "dis-mekan-led-ekran-fiyatlari-2026", "Dış Mekan LED Ekran Fiyatları 2026", "post"),
    ("Blog/rental-led-ekran-kiralama-fiyatlari-2026-rehber.html", "rental-led-ekran-kiralama-fiyatlari-2026", "Rental LED Ekran Kiralama Fiyatları 2026", "post"),
    ("Blog/led-ekran-nasil-secilir-rehber.html", "led-ekran-nasil-secilir-rehber", "LED Ekran Nasıl Seçilir? 2026 Rehber", "post"),
    ("Blog/gob-led-ekran-ne-zaman-tercih-edilir.html", "gob-led-ekran-ne-zaman-tercih-edilir", "GOB LED Ekran Ne Zaman Tercih Edilir?", "post"),
]

SCHEMA_FILES = [
    "SEO-Icerik-Widgets/schema/organization-schema.html",
    "SEO-Icerik-Widgets/schema/website-schema.html",
    "SEO-Icerik-Widgets/schema/navigation-schema.html",
]

session = requests.Session()
session.auth = (WP_USERNAME, WP_APP_PASSWORD)
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Deploy/1.0",
})


def extract_meta_description(html_content: str) -> str:
    match = re.search(r"<!-- SEO Meta Description:\s*(.+?)\s*-->", html_content)
    return match.group(1).strip() if match else ""


def extract_focus_keyword(html_content: str) -> str:
    match = re.search(r"<!-- SEO Focus Keyword:\s*(.+?)\s*-->", html_content)
    return match.group(1).strip() if match else ""


def build_rankmath_meta(title: str, meta_desc: str, focus_kw: str) -> dict:
    meta = {}
    if meta_desc:
        meta["rank_math_description"] = meta_desc
    if focus_kw:
        meta["rank_math_focus_keyword"] = focus_kw
    if title:
        meta["rank_math_title"] = title
    return meta


def read_file(rel_path: str) -> str:
    full = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def check_existing(slug: str, post_type: str) -> dict | None:
    endpoint = f"{API_BASE}/{'posts' if post_type == 'post' else 'pages'}"
    r = session.get(endpoint, params={"slug": slug, "status": "any"})
    items = r.json() if r.status_code == 200 else []
    return items[0] if items else None


def deploy_page(file_path: str, slug: str, title: str, post_type: str) -> bool:
    try:
        content = read_file(file_path)
    except FileNotFoundError:
        print(f"  ❌ DOSYA BULUNAMADI: {file_path}")
        return False

    meta_desc = extract_meta_description(content)
    focus_kw = extract_focus_keyword(content)
    endpoint = f"{API_BASE}/{'posts' if post_type == 'post' else 'pages'}"

    existing = check_existing(slug, post_type)

    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "status": "draft",  # Önce taslak olarak oluştur, inceledikten sonra yayınla
    }

    if meta_desc:
        payload["excerpt"] = meta_desc
        payload["meta"] = build_rankmath_meta(title, meta_desc, focus_kw)

    if DRY_RUN:
        status = "GÜNCELLE" if existing else "YENİ"
        print(f"  🔍 [DRY-RUN] {status}: {title} → /{slug}/")
        return True

    if existing:
        r = session.post(f"{endpoint}/{existing['id']}", json=payload)
        action = "GÜNCELLEME"
    else:
        r = session.post(endpoint, json=payload)
        action = "OLUŞTURMA"

    if r.status_code in (200, 201):
        page_data = r.json()
        print(f"  ✅ {action} OK: {title} → /{slug}/ (ID: {page_data['id']}, Durum: TASLAK)")
        return True
    else:
        print(f"  ❌ {action} HATA: {title} → HTTP {r.status_code}")
        try:
            print(f"     {r.json().get('message', r.text[:200])}")
        except Exception:
            print(f"     {r.text[:200]}")
        return False


def deploy_schemas():
    print("\n" + "=" * 60)
    print("SCHEMA DOSYALARI (manuel ekleme gerekebilir)")
    print("=" * 60)
    combined = []
    for sf in SCHEMA_FILES:
        try:
            content = read_file(sf)
            combined.append(content)
            print(f"  📋 Okundu: {sf}")
        except FileNotFoundError:
            print(f"  ❌ BULUNAMADI: {sf}")

    output_path = os.path.join(BASE_DIR, "schema-birlesik-header.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(combined))
    print(f"\n  💾 Birleşik schema → schema-birlesik-header.html")
    print("  ℹ️  Bu dosyanın içeriğini WP → Görünüm → Tema Düzenleyicisi → header.php")
    print("     veya Insert Headers/Footers eklentisi ile <head> bölümüne ekleyin.")


def publish_all_drafts():
    """Tüm taslakları yayınla (ikinci aşama)"""
    print("\n" + "=" * 60)
    print("TASLAKLARI YAYINLA")
    print("=" * 60)

    publish_list = [p for p in PAGES_TO_DEPLOY if p[3] == "post"] if BLOG_ONLY else PAGES_TO_DEPLOY
    for _, slug, title, post_type in publish_list:
        existing = check_existing(slug, post_type)
        if existing and existing.get("status") == "draft":
            endpoint = f"{API_BASE}/{'posts' if post_type == 'post' else 'pages'}/{existing['id']}"
            r = session.post(endpoint, json={"status": "publish"})
            if r.status_code == 200:
                print(f"  ✅ YAYINLANDI: {title} → /{slug}/")
            else:
                print(f"  ❌ HATA: {title} → HTTP {r.status_code}")
        elif existing:
            print(f"  ⏭️  Zaten yayında: {title}")
        else:
            print(f"  ⚠️  Bulunamadı: {title}")


def main():
    if not WP_USERNAME or not WP_APP_PASSWORD:
        print("=" * 60)
        print("⚠️  ÖNCE AYARLARI YAPIN!")
        print("=" * 60)
        print()
        print("1) WP Admin → Kullanıcılar → Profilim")
        print("2) Aşağı kaydır → 'Uygulama Şifreleri' bölümü")
        print("3) Yeni isim gir (örn: 'Deploy Script') → 'Yeni Uygulama Şifresi Ekle'")
        print("4) Oluşan şifreyi kopyala")
        print("5) Repo kökünde .env oluştur (.env.example şablonu)")
        print("6) Tekrar çalıştır: python deploy-to-wordpress.py")
        print()
        print("Detay: scripts/SECURITY-ROTATE-WP-APP-PASSWORD.md")
        print()
        if DRY_RUN:
            print("🔍 Kimlik yok — yalnızca dosya varlık kontrolü (DRY-RUN)\n")
            ok, fail = 0, 0
            for file_path, slug, title, _post_type in PAGES_TO_DEPLOY:
                try:
                    read_file(file_path)
                    print(f"  🔍 [DRY-RUN] OK: {title} → /{slug}/")
                    ok += 1
                except FileNotFoundError:
                    print(f"  ❌ DOSYA YOK: {file_path}")
                    fail += 1
            print(f"\n  Dosya kontrolü: {ok} OK, {fail} hata")
            return
        print("İPUCU: Önce test için → python deploy-to-wordpress.py --dry-run")
        return

    # API erişim testi
    print("🔗 WordPress API bağlantı testi...")
    try:
        r = session.get(f"{API_BASE}/users/me")
        if r.status_code == 200:
            user = r.json()
            print(f"  ✅ Bağlantı OK — {user.get('name', 'Bilinmeyen')}")
        elif r.status_code == 403 and "nginx" in (r.text or "").lower() and not (r.text or "").strip().startswith("{"):
            print("  ❌ REST API engelli (nginx 403) — /wp-json/ bu ağdan erişilemiyor.")
            print("     Şifre doğru olsa bile Cursor/bulut IP'si engellenmiş olabilir.")
            print("     Çözüm: Komutu kendi PC'nizde PowerShell'den çalıştırın:")
            print("       python deploy-to-wordpress.py --blog-only")
            return
        else:
            print(f"  ❌ Kimlik doğrulama hatası (HTTP {r.status_code})")
            print("     Kullanıcı adı ve uygulama şifresini kontrol edin.")
            try:
                print(f"     {r.json().get('message', '')[:120]}")
            except Exception:
                pass
            return
    except requests.ConnectionError:
        print(f"  ❌ {WP_SITE_URL} adresine bağlanılamadı")
        return

    if DRY_RUN:
        print("\n🔍 DRY-RUN MODU — Hiçbir şey yayınlanmayacak, sadece kontrol\n")

    if "--publish" in sys.argv:
        publish_all_drafts()
        return

    deploy_list = [p for p in PAGES_TO_DEPLOY if p[3] == "post"] if BLOG_ONLY else PAGES_TO_DEPLOY

    # Ana deploy
    print("\n" + "=" * 60)
    print(f"SAYFA DEPLOY ({len(deploy_list)} dosya)" + (" [blog-only]" if BLOG_ONLY else ""))
    print("=" * 60)

    success, fail = 0, 0
    for file_path, slug, title, post_type in deploy_list:
        result = deploy_page(file_path, slug, title, post_type)
        if result:
            success += 1
        else:
            fail += 1
        if not DRY_RUN:
            time.sleep(0.5)  # Rate limiting

    deploy_schemas()

    # Özet
    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    print(f"  ✅ Başarılı: {success}")
    print(f"  ❌ Hatalı:   {fail}")
    print(f"  📄 Toplam:   {len(deploy_list)}")

    if not DRY_RUN and success > 0:
        print()
        print("  📝 Tüm sayfalar TASLAK olarak oluşturuldu.")
        print("  📋 WP Admin'den kontrol edin, ardından yayınlamak için:")
        pub_cmd = "python deploy-to-wordpress.py --blog-only --publish" if BLOG_ONLY else "python deploy-to-wordpress.py --publish"
        print(f"     {pub_cmd}")
        print()
        print("  🔍 Yayın sonrası:")
        print("     - Google Search Console → URL Denetimi → Dizine eklenmesini iste")
        print("     - LiteSpeed / önbellek temizle")
        print("     - Schema test: https://search.google.com/test/rich-results")


if __name__ == "__main__":
    main()
