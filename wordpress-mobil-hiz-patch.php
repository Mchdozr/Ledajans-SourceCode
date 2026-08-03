<?php
/**
 * Plugin Name: LEDAJANS Mobile Perf
 * Description: Yalnizca mobil UA icin LCP/TBT optimizasyonu. Desktop no-op. Rank Math REST meta kaydi tum cihazlarda acik.
 * Version: 1.1.0
 * Author: LEDAJANS
 *
 * Alternatif kurulum: wp-content/mu-plugins/ledajans-perf-patch.php
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('ledajans_is_projeler_page')) {
    function ledajans_is_projeler_page() {
        if (is_admin()) {
            return false;
        }
        if (function_exists('is_page') && is_page('projeler')) {
            return true;
        }
        $path = isset($_SERVER['REQUEST_URI']) ? (string) wp_unslash($_SERVER['REQUEST_URI']) : '';
        return (bool) preg_match('#/projeler/?($|[?#])#i', $path);
    }
}

/**
 * Bu eklentinin kapisi (benzersiz ad — eski mu-plugin return true kirmasin).
 * Desktop: her zaman false.
 */
function ledajans_mp_v11_active() {
    if (is_admin()) {
        return false;
    }
    return function_exists('wp_is_mobile') && wp_is_mobile();
}

// Eski mu-plugin uyarisi (desktop'i kirletmesin diye silinmeli)
add_action('admin_notices', function () {
    if (!current_user_can('manage_options')) {
        return;
    }
    $mu = WP_CONTENT_DIR . '/mu-plugins/ledajans-perf-patch.php';
    if (!file_exists($mu)) {
        return;
    }
    echo '<div class="notice notice-warning"><p><strong>LEDAJANS Mobile Perf:</strong> Eski dosya hala var: <code>wp-content/mu-plugins/ledajans-perf-patch.php</code>. Desktop etkilenmemesi icin bu mu-plugin dosyasini silin.</p></div>';
});

// Rank Math REST — tum cihazlar (gorunum/JS yok)
add_action('init', function () {
    $keys = array(
        'rank_math_title'         => 'Rank Math SEO title',
        'rank_math_description'   => 'Rank Math meta description',
        'rank_math_focus_keyword' => 'Rank Math focus keyword(s)',
    );
    foreach (array('post', 'page') as $object_type) {
        foreach ($keys as $key => $description) {
            register_post_meta(
                $object_type,
                $key,
                array(
                    'type'              => 'string',
                    'description'       => $description,
                    'single'            => true,
                    'show_in_rest'      => true,
                    'sanitize_callback' => 'sanitize_text_field',
                    'auth_callback'     => function () {
                        return current_user_can('edit_posts');
                    },
                )
            );
        }
    }
});

// === Asagidaki tum hook'lar yalnizca mobil ===

add_action('init', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
    remove_action('wp_head', 'wp_generator');
    remove_action('wp_head', 'wlwmanifest_link');
    remove_action('wp_head', 'rsd_link');
});

add_action('wp_enqueue_scripts', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }

    wp_dequeue_style('wp-block-library');
    wp_dequeue_style('wp-block-library-theme');
    wp_dequeue_style('global-styles');
    wp_dequeue_style('wp-block-editor');
    wp_dequeue_style('wp-components');
    wp_dequeue_style('wp-preferences');
    wp_dequeue_style('classic-theme-styles');

    wp_deregister_script('jquery');
    wp_register_script('jquery', includes_url('/js/jquery/jquery.min.js'), [], null, true);
    wp_enqueue_script('jquery');
}, 100);

add_action('wp_print_styles', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }

    global $wp_styles;
    if (empty($wp_styles) || empty($wp_styles->registered)) {
        return;
    }

    $dropCssNeedles = [
        '/line-awesome/',
        '/block-editor/style.min.css',
        '/components/style.min.css',
        '/preferences/style.min.css',
        '/popup-maker/dist/packages/block-library-style.css',
        '/widget-icon-list',
        '/widget-icon-box',
        '/widget-social-icons',
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

// Mobil LCP: yalnizca q60 preload (desktop hero preload yok)
add_action('wp_head', function () {
    if (!ledajans_mp_v11_active() || !is_front_page()) {
        return;
    }
    echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q60.webp" fetchpriority="high">' . "\n";
}, 1);

add_filter('wp_get_attachment_image_attributes', function ($attr) {
    if (!ledajans_mp_v11_active() || !is_front_page()) {
        return $attr;
    }
    $src = $attr['src'] ?? '';
    if (stripos($src, 'ldajsn2-mobile') !== false) {
        $attr['fetchpriority'] = 'high';
        $attr['loading'] = 'eager';
        $attr['decoding'] = 'async';
    }
    return $attr;
}, 10, 1);

add_action('wp_head', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }
    ?>
<script>
window.ledajansRunWhenIdle=function(callback){if('requestIdleCallback'in window){requestIdleCallback(callback,{timeout:2500});}else{setTimeout(callback,1800);}};
</script>
<style id="ledajans-font-display">@font-face{font-display:swap}</style>
    <?php
}, 0);

add_filter('wp_resource_hints', function ($urls, $relation_type) {
    if (!ledajans_mp_v11_active() || 'preconnect' !== $relation_type) {
        return $urls;
    }

    $urls = array_values(array_filter((array) $urls, function ($url) {
        $u = is_array($url) ? ($url['href'] ?? '') : (string) $url;
        return stripos($u, 'googletagmanager.com') === false
            && stripos($u, 'google-analytics.com') === false;
    }));

    $urls[] = [
        'href'        => 'https://fonts.gstatic.com',
        'crossorigin' => 'anonymous',
    ];
    return $urls;
}, 99, 2);

add_action('wp_enqueue_scripts', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }

    global $wp_scripts;
    if (empty($wp_scripts) || empty($wp_scripts->queue)) {
        return;
    }

    $moveFooterNeedles = [
        'elementor', 'swiper', 'masonry', 'imagesloaded', 'bootstrap',
        'magnific', 'jquery.appear', 'jquery.cookie', 'modins', 'main',
    ];

    foreach ((array) $wp_scripts->queue as $handle) {
        if (empty($wp_scripts->registered[$handle]) || $handle === 'jquery') {
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

add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (!ledajans_mp_v11_active() || empty($src) || $handle === 'jquery') {
        return $tag;
    }

    $deferNeedles = [
        'elementor', 'swiper', 'masonry', 'imagesloaded', 'bootstrap',
        'magnific', 'appear', 'cookie', 'modins', 'main',
    ];
    $hit = false;
    foreach ($deferNeedles as $needle) {
        if (stripos($handle, $needle) !== false || stripos($src, $needle) !== false) {
            $hit = true;
            break;
        }
    }
    if (!$hit) {
        return $tag;
    }
    if (stripos($tag, ' defer') === false && stripos($tag, ' async') === false) {
        $tag = str_replace(' src=', ' defer src=', $tag);
    }
    return $tag;
}, 20, 3);

add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (!ledajans_mp_v11_active() || empty($src)) {
        return $tag;
    }
    if (stripos($src, 'googletagmanager.com/gtm.js') !== false
        || stripos($src, 'googletagmanager.com/gtag/js') !== false) {
        return '';
    }
    return $tag;
}, 100, 3);

add_action('template_redirect', function () {
    if (!ledajans_mp_v11_active() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST)) {
        return;
    }
    ob_start('ledajans_mp_v11_gtm_buffer');
}, 0);

function ledajans_mp_v11_gtm_buffer($html) {
    if (!is_string($html) || $html === '') {
        return $html;
    }

    $html = preg_replace(
        '#<link[^>]+(?:href|src)=["\'][^"\']*googletagmanager\.com[^"\']*["\'][^>]*>\s*#i',
        '',
        $html
    );
    $html = preg_replace(
        '#<link[^>]+(?:href|src)=["\'][^"\']*google-analytics\.com[^"\']*["\'][^>]*>\s*#i',
        '',
        $html
    );

    $delayMs = ledajans_is_projeler_page() ? 4000 : 3000;
    $gtmId = 'GTM-WDLJTMSV';

    $pattern = '#<script>\s*\(function\(w,d,s,l,i\)\{.*?\}\)\(window,document,\'script\',\'dataLayer\',\'([^\']+)\'\);\s*</script>#is';
    if (preg_match($pattern, $html, $matches)) {
        $gtmId = $matches[1];
        $html = preg_replace($pattern, '', $html, 1);
    }

    $html = preg_replace(
        '#<script[^>]+src=["\'][^"\']*googletagmanager\.com/gtm\.js[^"\']*["\'][^>]*></script>#i',
        '',
        $html
    );
    $html = preg_replace(
        '#<script[^>]+src=["\'][^"\']*googletagmanager\.com/gtag/js[^"\']*["\'][^>]*></script>#i',
        '',
        $html
    );

    if (stripos($html, 'ledajansGtmLoaded') === false) {
        $loader = '<script>(function(){window.dataLayer=window.dataLayer||[];var gtmId='
            . wp_json_encode($gtmId)
            . ',delayMs='
            . (int) $delayMs
            . ';function loadGtm(){if(window.ledajansGtmLoaded){return;}window.ledajansGtmLoaded=1;(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({"gtm.start":new Date().getTime(),event:"gtm.js"});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!="dataLayer"?"&l="+l:"";j.async=true;j.src="https://www.googletagmanager.com/gtm.js?id="+i+dl;f.parentNode.insertBefore(j,f);})(window,document,"script","dataLayer",gtmId);}function schedule(){setTimeout(loadGtm,delayMs);}if(window.ledajansRunWhenIdle){window.ledajansRunWhenIdle(schedule);}else{setTimeout(schedule,1800);}})();</script>';

        if (stripos($html, '</body>') !== false) {
            $html = str_ireplace('</body>', $loader . '</body>', $html);
        } else {
            $html .= $loader;
        }
    }

    return $html;
}

add_action('wp_head', function () {
    if (!ledajans_mp_v11_active() || ledajans_is_projeler_page()) {
        return;
    }
    echo '<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" onload="this.onload=null;this.rel=\'stylesheet\'">' . "\n";
    echo '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"></noscript>' . "\n";
}, 2);

add_action('wp_enqueue_scripts', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }
    foreach (['elementor-gallery', 'elementor-lightbox', 'e-animations', 'elementor-animations'] as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }
}, 200);

add_filter('style_loader_tag', function ($html, $handle, $href) {
    if (!ledajans_mp_v11_active() || empty($href)) {
        return $html;
    }

    $asyncNeedles = ['/font-awesome/', '/fontawesome/', 'elementor-icons', 'elementor-icons-fa'];
    $hit = false;
    foreach ($asyncNeedles as $needle) {
        if (stripos($handle, $needle) !== false || stripos($href, $needle) !== false) {
            $hit = true;
            break;
        }
    }
    if (!$hit || stripos($html, 'onload=') !== false) {
        return $html;
    }

    return sprintf(
        '<link rel="stylesheet" id="%s-css" href="%s" media="print" onload="this.media=\'all\'"><noscript>%s</noscript>',
        esc_attr($handle),
        esc_url($href),
        $html
    );
}, 20, 3);

add_action('wp_enqueue_scripts', function () {
    if (!ledajans_mp_v11_active()) {
        return;
    }

    foreach (['elementor-motion-effects', 'e-sticky'] as $handle) {
        wp_dequeue_script($handle);
        wp_deregister_script($handle);
    }

    if (is_front_page()) {
        foreach (['contact-form-7', 'swv', 'chaty', 'chaty-front', 'chaty-front-js', 'chaty-front-end-js'] as $handle) {
            wp_dequeue_script($handle);
            wp_deregister_script($handle);
        }
        foreach (['contact-form-7', 'chaty-front', 'chaty'] as $handle) {
            wp_dequeue_style($handle);
            wp_deregister_style($handle);
        }
    }
}, 200);

if (!function_exists('ledajans_drop_projeler_assets')) {
function ledajans_drop_projeler_assets() {
    if (!ledajans_mp_v11_active() || !ledajans_is_projeler_page()) {
        return;
    }

    foreach ([
        'contact-form-7', 'chaty-front', 'chaty', 'elementor-icons', 'elementor-animations',
        'elementor-widget-icon-list', 'elementor-widget-icon-box', 'elementor-widget-social-icons',
    ] as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }

    foreach (['swv', 'contact-form-7', 'chaty', 'chaty-front-js', 'chaty-front-end-js', 'chaty-front'] as $handle) {
        wp_dequeue_script($handle);
        wp_deregister_script($handle);
    }

    global $wp_styles;
    if (!empty($wp_styles) && !empty($wp_styles->queue)) {
        $dropCssNeedles = ['/contact-form-7/', '/chaty/', '/widget-icon-list', '/widget-icon-box', '/widget-social-icons'];
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
    }
}
}

add_action('wp_enqueue_scripts', 'ledajans_drop_projeler_assets', 9999);
add_action('wp_print_styles', 'ledajans_drop_projeler_assets', 9999);
add_action('wp_print_scripts', 'ledajans_drop_projeler_assets', 9999);
add_action('wp_print_footer_scripts', 'ledajans_drop_projeler_assets', 1);

add_action('wp_print_scripts', function () {
    if (!ledajans_mp_v11_active() || !ledajans_is_projeler_page()) {
        return;
    }
    global $wp_scripts;
    if (empty($wp_scripts) || empty($wp_scripts->queue)) {
        return;
    }
    foreach ((array) $wp_scripts->queue as $handle) {
        if (empty($wp_scripts->registered[$handle]->src)) {
            continue;
        }
        $src = (string) $wp_scripts->registered[$handle]->src;
        foreach (['/contact-form-7/', '/chaty/'] as $needle) {
            if (stripos($src, trim($needle, '/')) !== false) {
                wp_dequeue_script($handle);
                wp_deregister_script($handle);
                break;
            }
        }
    }
}, 9999);

add_filter('the_content', function ($content) {
    if (!ledajans_mp_v11_active() || !is_string($content) || $content === '') {
        return $content;
    }
    $content = preg_replace(
        '#(<img[^>]+ldajsn2-mobile[^>]*?)(?:\s*/?>)#i',
        '$1 width="768" height="1024">',
        $content,
        1
    );
    return $content;
}, 20);
