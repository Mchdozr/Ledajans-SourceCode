<?php
/**
 * LEDAJANS Mobil Performans Patch
 * Bu kodu aktif temanın functions.php dosyasının SONUNA ekleyin
 * veya wp-content/mu-plugins/ledajans-perf-patch.php olarak kaydedin.
 */

if (!defined('ABSPATH')) {
    exit;
}

// 1) Gereksiz WordPress frontend yüklerini azalt
add_action('init', function () {
    if (is_admin()) {
        return;
    }

    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
    remove_action('wp_head', 'wp_generator');
    remove_action('wp_head', 'wlwmanifest_link');
    remove_action('wp_head', 'rsd_link');
});

add_action('wp_enqueue_scripts', function () {
    if (is_admin()) {
        return;
    }

    // Gutenberg block CSS (frontend kullanılmıyorsa ciddi tasarruf)
    wp_dequeue_style('wp-block-library');
    wp_dequeue_style('wp-block-library-theme');
    wp_dequeue_style('global-styles');

    // jQuery Migrate kaldır (uyumsuz eski eklenti yoksa güvenli)
    if (!is_admin()) {
        wp_deregister_script('jquery');
        wp_register_script('jquery', includes_url('/js/jquery/jquery.min.js'), [], null, true);
        wp_enqueue_script('jquery');
    }
}, 100);

// 2) Kaynağa göre gereksiz CSS/JS dosyalarını düşür (audit odaklı)
add_action('wp_print_styles', function () {
    if (is_admin()) {
        return;
    }

    global $wp_styles;
    if (empty($wp_styles) || empty($wp_styles->registered)) {
        return;
    }

    $dropCssNeedles = [
        '/block-editor/style.min.css',
    ];

    foreach ((array) $wp_styles->queue as $handle) {
        if (empty($wp_styles->registered[$handle]->src)) {
            continue;
        }

        $src = (string) $wp_styles->registered[$handle]->src;
        foreach ($dropCssNeedles as $needle) {
            if (stripos($src, trim($needle, '/')) !== false) {
                wp_dequeue_style($handle);
                wp_deregister_style($handle);
                break;
            }
        }
    }
}, 999);

// 3) GTM/GA scriptlerini parse-blocking olmaktan çıkar
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || empty($src)) {
        return $tag;
    }

    $isGtm = (stripos($src, 'googletagmanager.com/gtm.js') !== false);
    $isGtag = (stripos($src, 'googletagmanager.com/gtag/js') !== false);

    if ($isGtm || $isGtag) {
        if (stripos($tag, 'defer') === false) {
            $tag = str_replace(' src=', ' defer src=', $tag);
        }
    }

    return $tag;
}, 10, 3);

// 4) Önemli origin'ler için preconnect (mobilde ilk bağlantı maliyetini düşürür)
add_filter('wp_resource_hints', function ($urls, $relation_type) {
    if ('preconnect' !== $relation_type) {
        return $urls;
    }

    $urls[] = 'https://www.googletagmanager.com';
    $urls[] = 'https://fonts.gstatic.com';
    return array_unique($urls);
}, 10, 2);

// 5) Home sayfasında ağır scriptleri footer'a it
add_action('wp_enqueue_scripts', function () {
    if (is_admin() || !is_front_page()) {
        return;
    }

    global $wp_scripts;
    if (empty($wp_scripts) || empty($wp_scripts->queue)) {
        return;
    }

    $moveFooterNeedles = [
        'elementor',
        'swiper',
    ];

    foreach ((array) $wp_scripts->queue as $handle) {
        if (empty($wp_scripts->registered[$handle])) {
            continue;
        }

        $reg = $wp_scripts->registered[$handle];
        $src = (string) $reg->src;
        $hit = false;

        foreach ($moveFooterNeedles as $needle) {
            if (stripos($handle, $needle) !== false || stripos($src, $needle) !== false) {
                $hit = true;
                break;
            }
        }

        if (!$hit) {
            continue;
        }

        wp_dequeue_script($handle);
        wp_deregister_script($handle);
        wp_register_script($handle, $src, $reg->deps, $reg->ver, true);
        wp_enqueue_script($handle);
    }
}, 110);
