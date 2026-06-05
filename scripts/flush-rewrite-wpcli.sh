#!/bin/bash
# Sunucuda bir kez calistirin (rewrite kurallarini yeniler)
WP_PATH="/var/www/vhosts/ledajans.com/httpdocs"
WP_USER="l3daj2ns"
sudo -u "$WP_USER" -- wp --path="$WP_PATH" option get permalink_structure
sudo -u "$WP_USER" -- wp --path="$WP_PATH" option update permalink_structure '/blog/%postname%/'
sudo -u "$WP_USER" -- wp --path="$WP_PATH" rewrite flush --hard
sudo -u "$WP_USER" -- wp --path="$WP_PATH" rewrite list --format=count
echo "Tamam. Ornek: wp post list --post_type=post --fields=post_name,url --max=3"
