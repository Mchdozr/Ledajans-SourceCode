<?php
/**
 * LEDAJANS Mobil Performans Patch
 * Bu kodu aktif temanın functions.php dosyasının SONUNA ekleyin
 * veya wp-content/mu-plugins/ledajans-perf-patch.php olarak kaydedin.
 */

if (!defined('ABSPATH')) {
    exit;
}

define('LEDAJANS_PERF_PATCH_VERSION', '2026-07-13-iter8');
define('LEDAJANS_MOBILE_CRITICAL_CSS_B64', '__LEDAJANS_MOBILE_CRITICAL_CSS_B64__');

function ledajans_is_public_mobile_request() {
    return wp_is_mobile() && !is_user_logged_in();
}

add_action('init', function () {
    if (get_option('ledajans_perf_patch_version') === LEDAJANS_PERF_PATCH_VERSION) {
        return;
    }
    if (function_exists('w3tc_config')) {
        $w3tcConfig = w3tc_config();
        $mobileGroups = $w3tcConfig->get_array('mobile.rgroups');
        unset($mobileGroups['ledajans_mobile']);
        $mobileEnabled = false;
        foreach ($mobileGroups as $mobileGroup) {
            if (!empty($mobileGroup['enabled'])) {
                $mobileEnabled = true;
                break;
            }
        }
        $w3tcConfig->set('mobile.rgroups', $mobileGroups);
        $w3tcConfig->set('mobile.enabled', $mobileEnabled);
        $w3tcConfig->set('pgcache.reject.front_page', true);
        $w3tcConfig->save();
    }
    if (function_exists('w3tc_flush_all')) {
        w3tc_flush_all();
    }
    if (function_exists('litespeed_purge_all')) {
        litespeed_purge_all();
    }
    wp_cache_flush();
    update_option('ledajans_perf_patch_version', LEDAJANS_PERF_PATCH_VERSION, false);
}, 1);

function ledajans_mobile_critical_theme_css() {
    static $criticalCss = null;
    if (is_string($criticalCss)) {
        return $criticalCss;
    }

    $encoded = LEDAJANS_MOBILE_CRITICAL_CSS_B64;
    if (substr($encoded, 0, 2) === '__') {
        $criticalCss = '';
        return $criticalCss;
    }

    $decoded = base64_decode($encoded, true);
    $criticalCss = is_string($decoded) ? $decoded : '';
    return $criticalCss;
}

add_action('wp_head', function () {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page()) {
        return;
    }
    $criticalCss = ledajans_mobile_critical_theme_css();
    if ($criticalCss !== '') {
        echo '<style id="ledajans-mobile-critical-theme">' . $criticalCss . '</style>' . "\n";
    }
}, 0);

function ledajans_drop_mobile_theme_styles() {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page()) {
        return;
    }
    $criticalHandles = [
        'bootstrap',
        'modins-template',
        'elementor-frontend',
        'widget-icon-box',
        'elementor-post-9',
        'elementor-post-43',
        'elementor-post-1248',
        'modins-style',
        'modins-parent-style',
        'modins-child-style',
        'modins-custom-style-color',
    ];
    foreach ($criticalHandles as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }
}

add_action('wp_enqueue_scripts', 'ledajans_drop_mobile_theme_styles', 9999);
add_action('wp_print_styles', 'ledajans_drop_mobile_theme_styles', 0);

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

// LCP açısından kritik sayfalar: anasayfa (head-term "led ekran") + /projeler/
// GTM ertelemesi ve ağır asset düşürme bu sayfalarda uygulanır.
function ledajans_is_lcp_critical_page() {
    if (is_admin()) {
        return false;
    }
    if (function_exists('is_front_page') && is_front_page()) {
        return true;
    }
    if (ledajans_is_projeler_page()) {
        return true;
    }
    return wp_is_mobile() && ledajans_is_money_page();
}

function ledajans_is_money_page() {
    if (is_admin()) {
        return false;
    }
    $path = isset($_SERVER['REQUEST_URI']) ? (string) wp_unslash($_SERVER['REQUEST_URI']) : '';
    return (bool) preg_match(
        '#/(led-ekran|ic-mekan-led-ekran|dis-mekan-led-ekran|rental-ekran)/?($|[?#])#i',
        $path
    );
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
    if (is_admin() || !ledajans_is_public_mobile_request()) {
        return;
    }

    // Gutenberg block CSS (frontend kullanılmıyorsa ciddi tasarruf)
    wp_dequeue_style('wp-block-library');
    wp_dequeue_style('wp-block-library-theme');
    wp_dequeue_style('global-styles');

    // Mobilde jQuery core kaydını koru, yalnızca migrate bağımlılığını çıkar.
    $scripts = wp_scripts();
    if (isset($scripts->registered['jquery'])) {
        $scripts->registered['jquery']->deps = array_values(
            array_diff((array) $scripts->registered['jquery']->deps, ['jquery-migrate'])
        );
    }
    wp_dequeue_script('jquery-migrate');
    wp_deregister_script('jquery-migrate');
}, 100);

// 2) Kaynağa göre gereksiz CSS/JS dosyalarını düşür (audit odaklı)
add_action('wp_print_styles', function () {
    if (is_admin() || !ledajans_is_public_mobile_request()) {
        return;
    }

    global $wp_styles;
    if (empty($wp_styles) || empty($wp_styles->registered)) {
        return;
    }

    $dropCssNeedles = [
        '/block-editor/style.min.css',
        '/popup-maker/dist/packages/block-library-style.css',
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

// 3) LCP hero görselini en erken isteğe sok
add_action('wp_head', function () {
    if (is_admin() || !is_front_page()) {
        return;
    }

    if (wp_is_mobile()) {
        echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/07/ldajsn2-mobile-q42-768x375-1.webp" fetchpriority="high">' . "\n";
        return;
    }

    echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/04/hero-poster.webp" fetchpriority="high">' . "\n";
}, 1);

add_filter('wp_get_attachment_image_attributes', function ($attr) {
    if (is_admin() || !is_front_page()) {
        return $attr;
    }

    $src = $attr['src'] ?? '';
    if (stripos($src, 'ldajsn2-mobile-q42-768x375') !== false || stripos($src, 'hero-poster.webp') !== false) {
        $attr['fetchpriority'] = 'high';
        $attr['loading'] = 'eager';
        $attr['decoding'] = 'async';
    }

    return $attr;
}, 10, 1);

// 3b) W3TC lazyload: mobil LCP görsellerini lazy dışı bırak (skip-lazy + eager)
add_action('template_redirect', function () {
    if (is_admin() || !wp_is_mobile() || !is_front_page()) {
        return;
    }
    ob_start('ledajans_mobile_lcp_lazyload_buffer');
}, -99999);

function ledajans_mobile_hero_source() {
    return 'https://ledajans.com/wp-content/uploads/2026/07/ldajsn2-mobile-q42-768x375-1.webp';
}

function ledajans_mobile_lcp_lazyload_buffer($html) {
    if (!is_string($html) || $html === '') {
        return $html;
    }

    $heroUrl = ledajans_mobile_hero_source();

    // W3TC/Elementor dahil tüm mobil hero preload'larını tek canonical isteğe indir.
    $html = (string) preg_replace(
        '#<link\b(?=[^>]*\brel=["\']preload["\'])(?=[^>]*(?:ldajsn2-mobile|hero-poster))[^>]*>\s*#i',
        '',
        $html
    );
    if (strpos($heroUrl, 'data:image/webp;base64,') !== 0) {
        $preload = '<link rel="preload" as="image" href="' . esc_url($heroUrl) . '" fetchpriority="high">';
        $html = (string) preg_replace('#<head([^>]*)>#i', '<head$1>' . "\n" . $preload, $html, 1);
    }

    $pattern = '#<img\b[^>]*ldajsn2-mobile[^>]*>#i';

    return (string) preg_replace_callback(
        $pattern,
        static function ($matches) use ($heroUrl) {
            $tag = $matches[0];
            $tag = preg_replace('#\sloading=["\']lazy["\']#i', ' loading="eager"', $tag);
            if (stripos($tag, 'loading=') === false) {
                $tag = str_replace('<img', '<img loading="eager"', $tag);
            }
            if (preg_match('#\sclass=["\']([^"\']*)["\']#i', $tag, $classMatch)) {
                $classes = preg_split('/\s+/', trim($classMatch[1]));
                $classes = array_values(array_filter(
                    (array) $classes,
                    static function ($className) {
                        return !in_array(
                            strtolower((string) $className),
                            ['lazy', 'entered', 'loaded', 'skip-', 'no-'],
                            true
                        );
                    }
                ));
                $classes[] = 'skip-lazy';
                $classes[] = 'no-lazy';
                $tag = preg_replace(
                    '#\sclass=["\'][^"\']*["\']#i',
                    ' class="' . esc_attr(implode(' ', array_unique($classes))) . '"',
                    $tag,
                    1
                );
            } else {
                $tag = str_replace('<img', '<img class="skip-lazy no-lazy"', $tag);
            }
            if (stripos($tag, 'data-no-lazy') === false) {
                $tag = str_replace('<img', '<img data-no-lazy="1"', $tag);
            }
            $tag = preg_replace('#\s(?:data-)?srcset=["\'][^"\']*["\']#i', '', $tag);
            $tag = preg_replace('#\s(?:data-)?sizes=["\'][^"\']*["\']#i', '', $tag);
            $tag = preg_replace('#\sdata-src=["\'][^"\']*["\']#i', '', $tag);
            $tag = preg_replace('#\sonerror=(["\']).*?\1#is', '', $tag);
            $tag = preg_replace('#\ssrc=["\'][^"\']*["\']#i', '', $tag);
            $tag = preg_replace('#\swidth=["\'][^"\']*["\']#i', '', $tag);
            $tag = preg_replace('#\sheight=["\'][^"\']*["\']#i', '', $tag);
            $tag = str_replace(
                '<img',
                '<img src="' . esc_attr($heroUrl) . '" width="768" height="375"',
                $tag
            );
            if (stripos($tag, 'fetchpriority=') === false) {
                $tag = str_replace('<img', '<img fetchpriority="high"', $tag);
            }
            return $tag;
        },
        $html
    );
}

// 4) GTM/GA scriptlerini parse-blocking olmaktan çıkar
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

// Inline GTM kodunu tarayıcı boştayken başlat
add_action('wp_head', function () {
    if (is_admin()) {
        return;
    }
    ?>
<script>
window.ledajansRunWhenIdle=function(callback){if('requestIdleCallback'in window){requestIdleCallback(callback,{timeout:2500});}else{setTimeout(callback,1800);}};
</script>
    <?php
}, 0);

// 5) Önemli origin'ler için preconnect (mobilde ilk bağlantı maliyetini düşürür)
add_filter('wp_resource_hints', function ($urls, $relation_type) {
    if ('preconnect' !== $relation_type) {
        return $urls;
    }

    if (!ledajans_is_projeler_page()) {
        $urls[] = 'https://www.googletagmanager.com';
        $urls[] = 'https://www.google-analytics.com';
    }
    $urls[] = 'https://fonts.gstatic.com';
    return array_unique($urls);
}, 10, 2);

// 6) Mobil anasayfada tema scriptlerini sıralamayı bozmadan footer'a taşı
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page() || empty($src)) {
        return $tag;
    }

    $footerHandles = [
        'jquery',
        'jquery-core',
        'bootstrap',
        'jquery-magnific-popup',
        'jquery-cookie',
        'jquery-appear',
        'imagesloaded',
        'masonry',
        'jquery-masonry',
        'modins-main',
    ];

    if (!in_array($handle, $footerHandles, true)) {
        return $tag;
    }
    if (!isset($GLOBALS['ledajans_mobile_footer_scripts'])) {
        $GLOBALS['ledajans_mobile_footer_scripts'] = [];
    }
    $GLOBALS['ledajans_mobile_footer_scripts'][] = [
        'handle' => $handle,
        'src' => $src,
    ];
    return '';
}, 40, 3);

add_action('wp_footer', function () {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page()
        || empty($GLOBALS['ledajans_mobile_footer_scripts'])) {
        return;
    }

    foreach ((array) $GLOBALS['ledajans_mobile_footer_scripts'] as $script) {
        printf(
            '<script id="%s-js" src="%s"></script>' . "\n",
            esc_attr($script['handle']),
            esc_url($script['src'])
        );
    }
}, 1);

// 7) Kritik font preload hint'leri (mobilde sistem font fallback; desktop preload korunur)
add_action('wp_head', function () {
    if (is_admin() || ledajans_is_projeler_page()) {
        return;
    }

    if (wp_is_mobile()) {
        echo '<style id="ledajans-mobile-font-fallback">@media (max-width:768px){body,.ledajans-hero-content{font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important}}</style>' . "\n";
        return;
    }

    echo '<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" onload="this.onload=null;this.rel=\'stylesheet\'">' . "\n";
    echo '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"></noscript>' . "\n";
}, 2);

// 8) Sayfa bazlı gereksiz Elementor widget CSS'lerini kaldır
add_action('wp_enqueue_scripts', function () {
    if (is_admin() || !wp_is_mobile()) {
        return;
    }

    $nonCriticalHandles = ['elementor-gallery', 'elementor-lightbox', 'e-animations'];
    foreach ($nonCriticalHandles as $handle) {
        if (wp_style_is($handle, 'enqueued')) {
            wp_dequeue_style($handle);
        }
    }
}, 200);

// 9) Mobil cihazlarda ek optimizasyonlar (anasayfa + para sayfaları)
add_action('wp_enqueue_scripts', function () {
    if (is_admin() || !wp_is_mobile()) {
        return;
    }

    $scope = is_front_page() || ledajans_is_money_page();
    if (!$scope) {
        return;
    }

    $mobileDropHandles = ['elementor-motion-effects', 'e-sticky', 'elementor-gallery', 'elementor-lightbox'];
    foreach ($mobileDropHandles as $handle) {
        if (wp_script_is($handle, 'enqueued')) {
            wp_dequeue_script($handle);
        }
        if (wp_style_is($handle, 'enqueued')) {
            wp_dequeue_style($handle);
        }
    }
}, 200);

// 10) /projeler/ — gereksiz eklenti CSS/JS (LCP/TBT)
function ledajans_drop_projeler_assets() {
    if (is_admin() || !ledajans_is_projeler_page()) {
        return;
    }

    $dropStyles = [
        'contact-form-7',
        'chaty-front',
        'chaty',
        'elementor-icons',
        'elementor-animations',
        'elementor-widget-icon-list',
        'elementor-widget-icon-box',
        'elementor-widget-social-icons',
    ];
    foreach ($dropStyles as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }

    $dropScripts = [
        'swv',
        'contact-form-7',
        'chaty',
        'chaty-front-js',
        'chaty-front-end-js',
        'chaty-front',
    ];
    foreach ($dropScripts as $handle) {
        wp_dequeue_script($handle);
        wp_deregister_script($handle);
    }

    global $wp_styles;
    if (!empty($wp_styles) && !empty($wp_styles->queue)) {
        $dropCssNeedles = [
            '/contact-form-7/',
            '/chaty/',
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
    }
}

add_action('wp_enqueue_scripts', 'ledajans_drop_projeler_assets', 9999);
add_action('wp_print_styles', 'ledajans_drop_projeler_assets', 9999);
add_action('wp_print_scripts', 'ledajans_drop_projeler_assets', 9999);
add_action('wp_print_footer_scripts', 'ledajans_drop_projeler_assets', 1);

add_action('wp_print_scripts', function () {
    if (is_admin() || !ledajans_is_projeler_page()) {
        return;
    }

    global $wp_scripts;
    if (empty($wp_scripts) || empty($wp_scripts->queue)) {
        return;
    }

    $dropScriptNeedles = ['/contact-form-7/', '/chaty/'];
    foreach ((array) $wp_scripts->queue as $handle) {
        if (empty($wp_scripts->registered[$handle]->src)) {
            continue;
        }
        $src = (string) $wp_scripts->registered[$handle]->src;
        foreach ($dropScriptNeedles as $needle) {
            if (stripos($src, trim($needle, '/')) !== false) {
                wp_dequeue_script($handle);
                wp_deregister_script($handle);
                break;
            }
        }
    }
}, 9999);

// 11) Anasayfa + /projeler/ — GTM'yi LCP sonrasına ertele (inline + enqueue)
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || !ledajans_is_lcp_critical_page() || empty($src)) {
        return $tag;
    }

    if (stripos($src, 'googletagmanager.com/gtm.js') !== false
        || stripos($src, 'googletagmanager.com/gtag/js') !== false) {
        return '';
    }

    return $tag;
}, 100, 3);

add_action('template_redirect', function () {
    if (is_admin() || !ledajans_is_lcp_critical_page()) {
        return;
    }

    ob_start('ledajans_delay_gtm_html_buffer');
}, 0);

function ledajans_delay_gtm_html_buffer($html) {
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

    $pattern = '#<script>\s*\(function\(w,d,s,l,i\)\{.*?\}\)\(window,document,\'script\',\'dataLayer\',\'([^\']+)\'\);\s*</script>#is';
    if (preg_match($pattern, $html, $matches)) {
        $gtmId = $matches[1];
        $delayMs = wp_is_mobile() ? 6000 : 4000;
        $replacement = '<script>(function(){window.dataLayer=window.dataLayer||[];var gtmId='
            . wp_json_encode($gtmId)
            . ',delayMs='
            . (int) $delayMs
            . ';function loadGtm(){if(window.ledajansGtmLoaded){return;}window.ledajansGtmLoaded=1;(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({"gtm.start":new Date().getTime(),event:"gtm.js"});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!="dataLayer"?"&l="+l:"";j.async=true;j.src="https://www.googletagmanager.com/gtm.js?id="+i+dl;f.parentNode.insertBefore(j,f);})(window,document,"script","dataLayer",gtmId);}function schedule(){setTimeout(loadGtm,delayMs);}if(window.ledajansRunWhenIdle){window.ledajansRunWhenIdle(schedule);}else{setTimeout(schedule,1800);}})();</script>';

        $html = preg_replace($pattern, $replacement, $html, 1);
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

    return $html;
}

// 12) Mobil anasayfada fold-altı CSS'i asenkrona al
add_filter('style_loader_tag', function ($tag, $handle, $href) {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page() || empty($href)) {
        return $tag;
    }

    $asyncNeedles = [
        'chaty',
        'contact-form-7',
        'elementor-icons',
        'line-awesome',
        'fontawesome',
        'font-awesome',
        'fonts.googleapis.com',
        'elementor-gf-local-roboto',
        'elementor-gf-local-robotoslab',
        'widget-icon-list',
        'widget-social-icons',
        'widget-spacer',
        'elementor-post-176',
        'magnific',
        'popup-maker',
        'swiper',
        'elementor-widget-',
        'elementor-animations',
        'e-animation',
    ];

    foreach ($asyncNeedles as $needle) {
        if (stripos($handle, $needle) !== false || stripos($href, $needle) !== false) {
            $mediaAsync = 'media="print" onload="this.media=\'all\';this.onload=null;"';
            if (stripos($tag, 'media=') !== false) {
                $async = preg_replace('#media=(["\'])[^"\']*\1#i', $mediaAsync, $tag, 1);
            } else {
                $async = str_replace(' href=', " {$mediaAsync} href=", $tag);
            }
            $fallback = sprintf('<link rel="stylesheet" href="%s" media="all">', esc_url($href));
            return $async . '<noscript>' . $fallback . '</noscript>';
        }
    }

    return $tag;
}, 20, 3);

// 12b) Mobil anasayfada fold-altı Elementor JS'ini ilk etkileşime kadar beklet
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page() || empty($src)) {
        return $tag;
    }

    $delayNeedles = [
        '/elementor/assets/js/',
        '/elementor-pro/assets/js/',
        '/modins-themer/elementor/assets/main.js',
        '/elementor/assets/lib/swiper/',
        '/send-app/',
        '/contact-form-7/',
        '/jquery/ui/',
        '/font-awesome/js/',
    ];

    foreach ($delayNeedles as $needle) {
        if (stripos($src, $needle) === false) {
            continue;
        }
        $GLOBALS['ledajans_has_mobile_deferred_scripts'] = true;
        return (string) preg_replace_callback(
            '#<script\b([^>]*)\bsrc=(["\'])([^"\']+)\2([^>]*)>\s*</script>#i',
            static function ($matches) use ($src) {
                $attributes = (string) $matches[1] . (string) $matches[4];
                $attributes = (string) preg_replace(
                    '#\stype=(["\'])[^"\']*\1#i',
                    '',
                    $attributes
                );
                return '<script'
                    . $attributes
                    . ' type="text/plain" data-ledajans-deferred="1" data-ledajans-src="'
                    . esc_attr($src)
                    . '"></script>';
            },
            $tag,
            1
        );
    }

    return $tag;
}, 60, 3);

add_action('wp_footer', function () {
    if (is_admin() || !ledajans_is_public_mobile_request() || !is_front_page()
        || empty($GLOBALS['ledajans_has_mobile_deferred_scripts'])) {
        return;
    }
    ?>
<script>
(function(){
  var queue=Array.prototype.slice.call(document.querySelectorAll('script[data-ledajans-deferred="1"]')),started=false;
  function next(){
    var placeholder=queue.shift();
    if(!placeholder){return;}
    var script=document.createElement('script');
    Array.prototype.slice.call(placeholder.attributes).forEach(function(attribute){
      if(attribute.name==='type'||attribute.name==='data-ledajans-deferred'||attribute.name==='data-ledajans-src'){return;}
      script.setAttribute(attribute.name,attribute.value);
    });
    script.src=placeholder.getAttribute('data-ledajans-src');
    script.async=false;
    script.onload=next;
    script.onerror=next;
    placeholder.parentNode.replaceChild(script,placeholder);
  }
  function start(){
    if(started){return;}
    started=true;
    next();
  }
  ['pointerdown','touchstart','keydown','scroll'].forEach(function(eventName){
    window.addEventListener(eventName,start,{once:true,passive:true});
  });
  setTimeout(start,12000);
})();
</script>
    <?php
}, 98);

// 12c) Mobilde Chaty — tüm sayfalarda scroll/idle sonrası yükle
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || !ledajans_is_public_mobile_request()
        || empty($src) || stripos($src, 'chaty') === false) {
        return $tag;
    }
    if (!isset($GLOBALS['ledajans_deferred_chaty'])) {
        $GLOBALS['ledajans_deferred_chaty'] = [];
    }
    $GLOBALS['ledajans_deferred_chaty'][] = $src;
    return '';
}, 50, 3);

add_action('wp_footer', function () {
    if (is_admin() || !ledajans_is_public_mobile_request()
        || empty($GLOBALS['ledajans_deferred_chaty'])) {
        return;
    }
    $urls = array_values(array_unique((array) $GLOBALS['ledajans_deferred_chaty']));
    ?>
<script>
(function(){
  var urls=<?php echo wp_json_encode($urls); ?>;
  var loaded=0;
  function inject(url){
    var s=document.createElement('script');
    s.src=url;
    s.async=true;
    document.body.appendChild(s);
  }
  function loadAll(){
    if(loaded){return;}
    loaded=1;
    urls.forEach(inject);
  }
  function schedule(){
    if(window.ledajansRunWhenIdle){window.ledajansRunWhenIdle(loadAll);}else{setTimeout(loadAll,2500);}
  }
  window.addEventListener('scroll',schedule,{once:true,passive:true});
  setTimeout(schedule,6000);
})();
</script>
    <?php
}, 99);

// 12d) Anasayfa — geç yüklenen sohbet widget dequeue (desktop; mobil 12c kullanır)
add_action('wp_enqueue_scripts', function () {
    if (is_admin() || !is_front_page() || wp_is_mobile()) {
        return;
    }

    $chatHandles = ['chaty', 'chaty-front', 'chaty-front-js', 'chaty-front-end-js'];
    foreach ($chatHandles as $handle) {
        if (wp_script_is($handle, 'enqueued')) {
            wp_dequeue_script($handle);
        }
    }
}, 211);

// Rank Math: REST ile sayfa/yazi SEO meta guncellemesi (deploy script)
add_action('init', function () {
    $keys = array(
        'rank_math_title'           => 'Rank Math SEO title',
        'rank_math_description'     => 'Rank Math meta description',
        'rank_math_focus_keyword'   => 'Rank Math focus keyword(s)',
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
