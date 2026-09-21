<?php
/**
 * Plugin Name: LEDAJANS Header Glass
 * Description: Kaydirinca ust menu yapisir; buğulu/seffaf (frosted) olur.
 * Version: 1.1.0
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
html.ledajans-header-scrolled .gv-sticky-wrapper.is-fixed > .gv-sticky-menu,
html.ledajans-header-scrolled .elementor-element-123bc72.gv-sticky-menu,
html.ledajans-header-scrolled .elementor-element-123bc72,
html.ledajans-header-scrolled .gv-sticky-menu {
  background: rgba(244, 111, 44, 0.58) !important;
  background-color: rgba(244, 111, 44, 0.58) !important;
  background-image: none !important;
  backdrop-filter: blur(16px) saturate(1.45) !important;
  -webkit-backdrop-filter: blur(16px) saturate(1.45) !important;
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.18) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.16) !important;
}
html.ledajans-header-scrolled header.wp-site-header,
html.ledajans-header-scrolled .wp-site-header,
html.ledajans-header-scrolled .header-builder-frontend,
html.ledajans-header-scrolled .header-builder-inner,
html.ledajans-header-scrolled .header-main-wrapper,
html.ledajans-header-scrolled .header_default_screen,
html.ledajans-header-scrolled .elementor-43,
html.ledajans-header-scrolled .elementor-element-a231664 {
  background: transparent !important;
  background-color: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  filter: none !important;
  transform: none !important;
  -webkit-transform: none !important;
}
@media (min-width: 1025px) {
  html.ledajans-header-scrolled .gv-sticky-wrapper.is-fixed > .gv-sticky-menu,
  html.ledajans-header-scrolled .elementor-element-123bc72.gv-sticky-menu {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    z-index: 10050 !important;
    transform: none !important;
    -webkit-transform: none !important;
  }
}
@media (max-width: 1024px) {
  html.ledajans-header-scrolled header.wp-site-header,
  html.ledajans-header-scrolled .wp-site-header {
    background: rgba(244, 111, 44, 0.58) !important;
    background-color: rgba(244, 111, 44, 0.58) !important;
    backdrop-filter: blur(16px) saturate(1.45) !important;
    -webkit-backdrop-filter: blur(16px) saturate(1.45) !important;
  }
  html.ledajans-header-scrolled .elementor-element-123bc72,
  html.ledajans-header-scrolled .gv-sticky-menu {
    background: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
}
CSS;
    $js = <<<'JS'
(function () {
  var last = null;
  function sync() {
    var y = window.scrollY || window.pageYOffset || 0;
    var on = y > 12;
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
    wp_register_style('ledajans-header-glass', false, array(), '1.1.0');
    wp_enqueue_style('ledajans-header-glass');
    wp_add_inline_style('ledajans-header-glass', $css);
    wp_register_script('ledajans-header-glass', '', array(), '1.1.0', true);
    wp_enqueue_script('ledajans-header-glass');
    wp_add_inline_script('ledajans-header-glass', $js);
}, 40);
