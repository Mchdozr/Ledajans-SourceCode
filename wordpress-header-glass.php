<?php
/**
 * Plugin Name: LEDAJANS Header Glass
 * Description: Kaydirinca ust menu buğulu/seffaf (frosted) olur.
 * Version: 1.0.0
 * Author: LEDAJANS
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('wp_enqueue_scripts', function () {
    $css = <<<'CSS'
header.wp-site-header,
.elementor-element-123bc72.gv-sticky-menu {
  transition: background-color 0.28s ease, box-shadow 0.28s ease, backdrop-filter 0.28s ease, -webkit-backdrop-filter 0.28s ease !important;
}
html.ledajans-header-scrolled header.wp-site-header,
html.ledajans-header-scrolled .wp-site-header,
html.ledajans-header-scrolled .elementor-element-123bc72,
html.ledajans-header-scrolled .gv-sticky-menu.elementor-element-123bc72,
html.ledajans-header-scrolled .gv-sticky-menu {
  background: rgba(244, 111, 44, 0.55) !important;
  background-color: rgba(244, 111, 44, 0.55) !important;
  backdrop-filter: blur(16px) saturate(1.45) !important;
  -webkit-backdrop-filter: blur(16px) saturate(1.45) !important;
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.18) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.16) !important;
}
html.ledajans-header-scrolled .header-builder-inner,
html.ledajans-header-scrolled .header-main-wrapper,
html.ledajans-header-scrolled .header_default_screen,
html.ledajans-header-scrolled .elementor-43 {
  background: transparent !important;
  background-color: transparent !important;
}
CSS;
    $js = <<<'JS'
(function () {
  var last = null;
  function sync() {
    var on = window.scrollY > 12;
    if (on === last) return;
    last = on;
    document.documentElement.classList.toggle("ledajans-header-scrolled", on);
  }
  window.addEventListener("scroll", sync, { passive: true });
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", sync);
  } else {
    sync();
  }
})();
JS;
    wp_register_style('ledajans-header-glass', false, array(), '1.0.0');
    wp_enqueue_style('ledajans-header-glass');
    wp_add_inline_style('ledajans-header-glass', $css);
    wp_register_script('ledajans-header-glass', '', array(), '1.0.0', true);
    wp_enqueue_script('ledajans-header-glass');
    wp_add_inline_script('ledajans-header-glass', $js);
}, 40);
