<?php
/**
 * Plugin Name: LEDAJANS i18n Tools
 * Description: Polylang çeviri grubu REST + EN/DE dil anasayfası.
 * Version: 1.0.3
 * Author: LEDAJANS
 */
if (!defined('ABSPATH')) {
    exit;
}

add_action('rest_api_init', function () {
    register_rest_route('ledajans/v1', '/pll-link', array(
        'methods' => 'POST',
        'permission_callback' => function () {
            return current_user_can('manage_options');
        },
        'callback' => 'ledajans_pll_link',
    ));
    register_rest_route('ledajans/v1', '/pll-dump', array(
        'methods' => 'GET',
        'permission_callback' => function () {
            return current_user_can('manage_options');
        },
        'callback' => 'ledajans_pll_dump',
    ));
});

function ledajans_pll_link(WP_REST_Request $req)
{
    if (!function_exists('pll_save_post_translations') || !function_exists('pll_set_post_language')) {
        return new WP_Error('no_pll', 'Polylang yok', array('status' => 500));
    }
    $group = $req->get_json_params();
    if (!is_array($group)) {
        return new WP_Error('bad', 'JSON grup gerekli', array('status' => 400));
    }
    $clean = array();
    foreach ($group as $lang => $pid) {
        $lang = sanitize_key((string) $lang);
        $pid = (int) $pid;
        if (!$lang || $pid <= 0) {
            continue;
        }
        pll_set_post_language($pid, $lang);
        $clean[$lang] = $pid;
    }
    if (count($clean) < 2) {
        return new WP_Error('few', 'En az 2 dil', array('status' => 400));
    }
    pll_save_post_translations($clean);
    if (function_exists('PLL')) {
        PLL()->model->clean_languages_cache();
    }
    return array('ok' => true, 'group' => $clean);
}

function ledajans_pll_dump()
{
    $front = (int) get_option('page_on_front');
    $out = array(
        'page_on_front' => $front,
        'pll_get_post' => array(),
    );
    if (function_exists('pll_get_post')) {
        foreach (array('tr', 'en', 'de') as $lang) {
            $out['pll_get_post'][$lang] = (int) pll_get_post($front, $lang);
        }
    }
    if (function_exists('PLL')) {
        foreach (PLL()->model->get_languages_list() as $lang) {
            $out['langs'][] = array(
                'slug' => $lang->slug,
                'term_id' => $lang->term_id,
                'page_on_front' => isset($lang->page_on_front) ? (int) $lang->page_on_front : null,
                'home_url' => $lang->home_url,
            );
        }
    }
    return $out;
}

add_action('template_redirect', 'ledajans_junk_urls', -1);
function ledajans_junk_urls()
{
    if (is_admin() || (defined('REST_REQUEST') && REST_REQUEST) || (defined('WP_CLI') && WP_CLI)) {
        return;
    }
    $path = isset($_SERVER['REQUEST_URI']) ? (string) wp_unslash($_SERVER['REQUEST_URI']) : '/';
    $path = strtolower(strtok($path, '?'));
    $path = '/' . trim($path, '/');
    if ($path !== '/') {
        $path = rtrim($path, '/');
    }
    if (strpos($path, '/wp-json') === 0 || strpos($path, '/wp-admin') === 0) {
        return;
    }
    if (strpos($path, '/gva_template') === 0) {
        status_header(410);
        nocache_headers();
        exit;
    }
    if ($path === '/case' || preg_match('#^/(?:en|de)/case(/.*)?$#', $path) || preg_match('#^/case(/.*)?$#', $path)) {
        wp_safe_redirect('https://ledajans.com/projeler/', 301);
        exit;
    }
    if ($path === '/feed' || $path === '/comments/feed' || preg_match('#^/(en|de)/feed$#', $path)) {
        wp_safe_redirect('https://ledajans.com/', 301);
        exit;
    }
    if ($path === '/led' || $path === '/led-2') {
        wp_safe_redirect('https://ledajans.com/led-ekran/', 301);
        exit;
    }
}

add_filter('option_page_on_front', 'ledajans_option_front', 5);
function ledajans_option_front($id)
{
    if (is_admin() || (defined('REST_REQUEST') && REST_REQUEST)) {
        return $id;
    }
    if (!function_exists('pll_current_language') || !function_exists('pll_get_post') || !function_exists('pll_default_language')) {
        return $id;
    }
    $lang = pll_current_language();
    if (!$lang || $lang === pll_default_language()) {
        return $id;
    }
    $translated = (int) pll_get_post((int) $id, $lang);
    return $translated > 0 ? $translated : $id;
}
