#!/bin/bash
# Plesk/SSH: wp-cli ile P0 RankMath meta (REST kayitli degilse kullanin)
# Kullanim: cd /var/www/vhosts/ledajans.com/httpdocs && bash set-rankmath-p0-wpcli.sh

set -euo pipefail
WP="${WP_CLI:-wp}"

# led-ekran (5557)
$WP post meta update 5557 rank_math_title "LED Ekran ve Fiyatları 2026 | İç-Dış Mekan - LEDAJANS"
$WP post meta update 5557 rank_math_description "LED ekran, fiyatları ve m² hesaplama. İç mekan, dış mekan, rental modeller. 25 yıl tecrübe, 2 yıl garanti. Ücretsiz keşif — Türkiye geneli teklif alın."
$WP post meta update 5557 rank_math_focus_keyword "led ekran,led ekran fiyatları,led ekran m2 fiyatı,led ekran firmaları"

# dis-mekan-led-ekran (6012)
$WP post meta update 6012 rank_math_title "Dış Mekan LED Ekran | Outdoor IP65 P4-P10 - LEDAJANS"
$WP post meta update 6012 rank_math_description "Dış mekan ve açık hava LED ekran. IP65, yüksek parlaklık, reklam panosu ve cephe için. Outdoor LED çözümleri. Ücretsiz keşif ve teklif."
$WP post meta update 6012 rank_math_focus_keyword "dış mekan led ekran,outdoor led ekran,açık hava led ekran,ip65 led ekran"

# rental-ekran (6083)
$WP post meta update 6083 rank_math_title "LED Ekran Kiralama | Rental Ekran 2026 - LEDAJANS"
$WP post meta update 6083 rank_math_description "LED ekran kiralama ve rental LED ekran. Konser, fuar, düğün için hızlı kurulum, teknik ekip, flight case. Kiralık LED ekran fiyat teklifi alın."
$WP post meta update 6083 rank_math_focus_keyword "led ekran kiralama,rental led ekran,kiralık led ekran,led ekran kiralama fiyatları"

# ic-mekan-led-ekran (6004)
$WP post meta update 6004 rank_math_title "İç Mekan LED Ekran | Indoor P2-P3 Fiyat - LEDAJANS"
$WP post meta update 6004 rank_math_description "İç mekan ve indoor LED ekran. P2, P2.5, P3 modeller; mağaza, stüdyo, toplantı odası. 3840Hz, 2 yıl garanti. Ücretsiz danışmanlık."
$WP post meta update 6004 rank_math_focus_keyword "iç mekan led ekran,indoor led ekran,p2 led ekran,p3 led ekran"

echo "OK: 4 sayfa RankMath meta guncellendi."
