#!/bin/bash
# LEDAJANS SEO Sayfalarını WP-CLI ile toplu oluşturma
# Kullanım: bash /var/www/vhosts/ledajans.com/httpdocs/seo-deploy/deploy-wp-cli.sh

WP_PATH="/var/www/vhosts/ledajans.com/httpdocs"
DEPLOY_DIR="$WP_PATH/seo-deploy"
WP_USER="l3daj2ns"
WP_CMD="sudo -u $WP_USER -- wp --path=$WP_PATH"

echo "========================================"
echo "LEDAJANS SEO Deploy Basliyor..."
echo "========================================"

create_page() {
    local file="$1"
    local slug="$2"
    local title="$3"
    local type="$4"

    local filepath="$DEPLOY_DIR/$file"

    if [ ! -f "$filepath" ]; then
        echo "  DOSYA YOK: $file"
        return
    fi

    local content
    content=$(cat "$filepath")

    local existing
    if [ "$type" = "post" ]; then
        existing=$($WP_CMD post list --post_type=post --name="$slug" --field=ID 2>/dev/null)
    else
        existing=$($WP_CMD post list --post_type=page --name="$slug" --field=ID 2>/dev/null)
    fi

    if [ -n "$existing" ]; then
        $WP_CMD post update "$existing" --post_content="$content" --post_title="$title" 2>/dev/null
        echo "  GUNCELLENDI: $title -> /$slug/ (ID: $existing)"
    else
        local new_id
        if [ "$type" = "post" ]; then
            new_id=$($WP_CMD post create --post_type=post --post_status=draft --post_name="$slug" --post_title="$title" --post_content="$content" --porcelain 2>/dev/null)
        else
            new_id=$($WP_CMD post create --post_type=page --post_status=draft --post_name="$slug" --post_title="$title" --post_content="$content" --porcelain 2>/dev/null)
        fi
        echo "  OLUSTURULDU: $title -> /$slug/ (ID: $new_id, TASLAK)"
    fi
}

echo ""
echo "--- TEMEL REHBERLER ---"
create_page "temel-rehberler/led-ekran-nedir.html"          "led-ekran-nedir"             "LED Ekran Nedir? Kapsamli Rehber"               "page"
create_page "temel-rehberler/led-tabela-rehberi.html"       "led-tabela"                  "LED Tabela Rehberi"                             "page"
create_page "temel-rehberler/led-ekran-kurulum-rehberi.html" "led-ekran-kurulum"           "LED Ekran Kurulum Rehberi"                      "page"
create_page "temel-rehberler/led-ekran-bakim-rehberi.html"  "led-ekran-bakim"             "LED Ekran Bakim Rehberi"                        "page"

echo ""
echo "--- SEKTOR REHBERLERI ---"
create_page "sektor-rehberleri/avm-led-ekran-rehberi.html"          "avm-led-ekran-rehberi"       "AVM LED Ekran Rehberi"           "page"
create_page "sektor-rehberleri/stadyum-led-ekran-rehberi.html"      "stadyum-led-ekran"           "Stadyum LED Ekran Rehberi"       "page"
create_page "sektor-rehberleri/magaza-vitrin-led-rehberi.html"      "magaza-vitrin-led-ekran"     "Magaza Vitrin LED Ekran"         "page"
create_page "sektor-rehberleri/belediye-bilgi-ekrani-rehberi.html"  "belediye-bilgi-ekrani"       "Belediye Bilgi Ekrani Rehberi"   "page"
create_page "sektor-rehberleri/eczane-led-tabela-rehberi.html"      "eczane-led-tabela"           "Eczane LED Tabela Rehberi"       "page"
create_page "sektor-rehberleri/cami-led-ekran-rehberi.html"         "cami-led-ekran"              "Cami LED Ekran Rehberi"          "page"

echo ""
echo "--- KARSILASTIRMALAR ---"
create_page "karsilastirmalar/p2-vs-p3-led-ekran.html"             "p2-vs-p3-led-ekran"          "P2 vs P3 LED Ekran"             "page"
create_page "karsilastirmalar/ic-mekan-vs-dis-mekan-led.html"      "ic-mekan-dis-mekan-led-farki" "Ic Mekan vs Dis Mekan LED"      "page"
create_page "karsilastirmalar/cob-led-ne-zaman.html"               "cob-led-ne-zaman"            "COB LED Ne Zaman Tercih Edilmeli" "page"
create_page "karsilastirmalar/led-ekran-vs-lcd.html"               "led-ekran-lcd-farki"         "LED Ekran vs LCD"               "page"
create_page "karsilastirmalar/led-ekran-vs-projeksiyon.html"       "led-ekran-projeksiyon"       "LED Ekran vs Projeksiyon"       "page"

echo ""
echo "--- TEKNIK SOZLUK ---"
create_page "sozluk/pitch-led-nedir.html"        "pitch-led-nedir"        "Piksel Pitch Nedir"              "page"
create_page "sozluk/refresh-hz-nedir.html"       "refresh-hz-nedir"       "Refresh Rate Hz Nedir"           "page"
create_page "sozluk/nits-parlaklik-nedir.html"   "nits-parlaklik-nedir"   "Nits Parlaklik Nedir"            "page"
create_page "sozluk/ip-koruma-led-ekran.html"    "ip-koruma-led-ekran"    "IP Koruma Sinifi ve LED Ekran"   "page"
create_page "sozluk/led-panel-nedir.html"        "led-panel-nedir"        "LED Panel Nedir"                 "page"
create_page "sozluk/smd-led-nedir.html"          "smd-led-nedir"          "SMD LED Nedir"                   "page"
create_page "sozluk/gob-led-nedir.html"          "gob-led-nedir"          "GOB LED Nedir"                   "page"

echo ""
echo "--- SEHIR SAYFALARI ---"
create_page "sehir-sayfalari/istanbul-led-ekran.html"   "istanbul-led-ekran"   "Istanbul LED Ekran"   "page"
create_page "sehir-sayfalari/ankara-led-ekran.html"     "ankara-led-ekran"     "Ankara LED Ekran"     "page"
create_page "sehir-sayfalari/izmir-led-ekran.html"      "izmir-led-ekran"      "Izmir LED Ekran"      "page"

echo ""
echo "--- KULLANIM ALANLARI ---"
create_page "kullanim-alanlari/havaalani-led-ekran.html"       "havaalani-led-ekran"       "Havalimani LED Ekran"       "page"
create_page "kullanim-alanlari/otel-led-ekran.html"            "otel-led-ekran"            "Otel LED Ekran"             "page"
create_page "kullanim-alanlari/fuar-led-ekran.html"            "fuar-led-ekran"            "Fuar LED Ekran"             "page"
create_page "kullanim-alanlari/billboard-led-ekran.html"       "billboard-led-ekran"       "Billboard LED Ekran"        "page"
create_page "kullanim-alanlari/toplanti-odasi-led-ekran.html"  "toplanti-odasi-led-ekran"  "Toplanti Odasi LED Ekran"   "page"

echo ""
echo "--- BLOG ---"
create_page "Blog/led-ekran-fiyatlari-2026-rehber.html"  "led-ekran-fiyatlari-2026"  "LED Ekran Fiyatlari 2026 Mayis Guncel"  "post"

echo ""
echo "========================================"
echo "TAMAMLANDI!"
echo "Tum sayfalar TASLAK olarak olusturuldu."
echo "WP Admin'den kontrol edip yayinlayin."
echo "========================================"
echo ""
echo "Toplu yayinlamak icin:"
echo "  $WP_CMD post list --post_type=page --post_status=draft --format=ids | xargs -n1 $WP_CMD post update --post_status=publish"
