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

add_action('wp_loaded', function () {
    if (!function_exists('wp_get_custom_css') || !function_exists('wp_update_custom_css_data')) {
        return;
    }
    $css = (string) wp_get_custom_css();
    if ($css === '') {
        return;
    }
    $updated = preg_replace(
        '/filter:\s*brightness\(0\)\s*invert\(1\)\s*!important;/',
        'filter: none !important;',
        $css,
        -1,
        $count
    );
    if (!$count) {
        return;
    }
    wp_update_custom_css_data($updated);
}, 20);
