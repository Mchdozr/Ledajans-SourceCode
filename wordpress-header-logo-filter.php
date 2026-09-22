<?php
/**
 * Plugin Name: LEDAJANS Header Logo Filter
 * Description: Turuncu üst menüde beyaz outline logoyu invert etme; offcanvas beyaz zeminde koyulaştır.
 * Version: 1.0.0
 * Author: LEDAJANS
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('wp_head', function () {
    echo <<<'CSS'
<style id="ledajans-header-logo-filter">
.elementor-element-123bc72 .site-branding-logo img,
.elementor-element-123bc72 .elementor-widget-gva-logo img {
  filter: none !important;
}
.canvas-mobile .top-canvas .logo-mm img {
  filter: brightness(0) !important;
}
</style>
CSS;
}, 1000);

add_action('init', function () {
    if (get_option('ledajans_header_logo_css_patched')) {
        return;
    }
    if (!function_exists('wp_get_custom_css') || !function_exists('wp_update_custom_css_data')) {
        return;
    }
    $css = (string) wp_get_custom_css();
    $needle = 'filter: brightness(0) invert(1) !important;';
    if (strpos($css, $needle) === false) {
        update_option('ledajans_header_logo_css_patched', '1', false);
        return;
    }
    wp_update_custom_css_data(str_replace($needle, 'filter: none !important;', $css));
    update_option('ledajans_header_logo_css_patched', '1', false);
}, 20);
