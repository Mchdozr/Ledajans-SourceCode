<?php
/**
 * Plugin Name: LEDAJANS Mobile Perf
 * Description: Yalnizca mobil UA icin LCP/TBT optimizasyonu. Desktop no-op. Rank Math REST meta kaydi tum cihazlarda acik.
 * Version: 1.3.0
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
        return (bool) preg_match('~/projeler/?($|[?#])~i', $path);
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

// Not: Canli kurulum yolu zaten mu-plugins/ledajans-perf-patch.php (write-files).

// Logo: v1.3.0'da mobil-only optimizer'a tasindi (masaustu NO-OP).

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

    // jQuery footer + defer adayi (head render-blocking ~350ms)
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

// Mobil LCP preload: v1.3.0 buffer'da sablon basina TEK preload (ledajans_mp_v13_optimize).

add_filter('wp_get_attachment_image_attributes', function ($attr) {
    if (!ledajans_mp_v11_active() || !is_front_page()) {
        return $attr;
    }
    $src = $attr['src'] ?? '';
    if (stripos($src, 'ldajsn2-mobile') !== false
        || stripos($src, 'hero-stant-poster-mobile') !== false
        || stripos($src, 'hero-atrium-led-mobile') !== false) {
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
    $urls[] = 'https://fonts.googleapis.com';
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
    if (stripos($html, '<html') === false) {
        return $html;
    }

    $html = ledajans_mp_v13_optimize($html);

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

    // Mobil: 1.2MB Firefly PNG CSS background'unu tamamen kes
    $html = str_ireplace(
        "url('https://ledajans.com/wp-content/uploads/2026/05/Firefly_Gemini-Flash-8.png')",
        'none',
        $html
    );
    $html = str_ireplace(
        'url("https://ledajans.com/wp-content/uploads/2026/05/Firefly_Gemini-Flash-8.png")',
        'none',
        $html
    );

    // Mobil: video preload yasak (LCP poster WebP); eski q72 / hero-poster baskisini kes
    $html = preg_replace(
        '#<link[^>]+rel=["\']preload["\'][^>]+as=["\']video["\'][^>]*>\s*#i',
        '',
        $html
    );
    $html = preg_replace(
        '#<link[^>]+rel=["\']preload["\'][^>]+(?:hero-stant-1920|hero-stant-1280|StantVideo|Firefly-548225-1)\.mp4[^>]*>\s*#i',
        '',
        $html
    );
    $html = preg_replace(
        '#<link[^>]+rel=["\']preload["\'][^>]+hero-poster\.webp[^>]*>\s*#i',
        '',
        $html
    );
    $html = preg_replace(
        '#<link[^>]+rel=["\']preload["\'][^>]+ldajsn2-mobile-q72\.webp[^>]*>\s*#i',
        '',
        $html
    );
    $html = preg_replace(
        '#,\s*https://ledajans\.com/wp-content/uploads/2026/04/ldajsn2-mobile-q72\.webp\s+\d+w#i',
        '',
        $html
    );
    // onerror ile q72 cekilmesini engelle
    $html = str_ireplace(
        "this.src='https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q72.webp'",
        "this.src='https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q60.webp'",
        $html
    );
    $html = str_ireplace(
        'ldajsn2-mobile-q72.webp',
        'ldajsn2-mobile-q60.webp',
        $html
    );

    // Ana sayfa mobil: Chaty CSS/JS tamamen cikar
    if (function_exists('is_front_page') && is_front_page()) {
        $html = preg_replace(
            '#<link[^>]+href=["\'][^"\']*chaty[^"\']*["\'][^>]*>\s*#i',
            '',
            $html
        );
        $html = preg_replace(
            '#<script[^>]+src=["\'][^"\']*chaty[^"\']*["\'][^>]*></script>\s*#i',
            '',
            $html
        );
    }

    // Logo LCP rekabetini dusur (95KiB PNG)
    $html = preg_replace(
        '#(<img[^>]+LedajansLogo\.png[^>]*?)>#i',
        '$1 fetchpriority="low" loading="lazy" decoding="async">',
        $html
    );
    // Google Fonts (Kumbh) — async
    $html = preg_replace_callback(
        '#<link([^>]+fonts\.googleapis\.com/css[^>]*)>#i',
        function ($m) {
            $tag = $m[0];
            if (stripos($tag, 'onload=') !== false) {
                return $tag;
            }
            if (stripos($tag, 'rel="preload"') !== false || stripos($tag, "rel='preload'") !== false) {
                return $tag;
            }
            if (!preg_match('#href=["\']([^"\']+)#i', $tag, $hm)) {
                return $tag;
            }
            return '<link rel="stylesheet" href="' . esc_url($hm[1]) . '" media="print" onload="this.media=\'all\'">';
        },
        $html
    );

    // Non-critical CSS async (desktop HTML dokunulmaz — buffer sadece mobil UA)
    $asyncCssNeedles = [
        'font-awesome',
        'fontawesome',
        'swiper.min.css',
        'chaty-front',
        'magnific-popup.css',
        'bootstrap.css',
        'template.css',
        'eicons',
        'widget-spacer',
        'v4-shims',
    ];
    $html = preg_replace_callback(
        '#<link([^>]+rel=["\']stylesheet["\'][^>]*)>#i',
        function ($m) use ($asyncCssNeedles) {
            $tag = $m[0];
            if (stripos($tag, 'onload=') !== false || stripos($tag, 'media="print"') !== false) {
                return $tag;
            }
            $hit = false;
            foreach ($asyncCssNeedles as $needle) {
                if (stripos($tag, $needle) !== false) {
                    $hit = true;
                    break;
                }
            }
            if (!$hit) {
                return $tag;
            }
            if (!preg_match('#href=["\']([^"\']+)#i', $tag, $hm)) {
                return $tag;
            }
            $href = $hm[1];
            return '<link rel="stylesheet" href="' . esc_url($href) . '" media="print" onload="this.media=\'all\'">';
        },
        $html
    );

    // Head'deki tema/plugin scriptlerini body sonuna defer ile tasi (jquery haric)
    $moved = [];
    $html = preg_replace_callback(
        '#<script([^>]+src=["\']([^"\']+)["\'][^>]*)></script>#i',
        function ($m) use (&$moved) {
            $full = $m[0];
            $src = $m[2];
            $needles = [
                'bootstrap.min.js',
                'magnific-popup',
                'jquery.cookie',
                'jquery.appear',
                'imagesloaded',
                'masonry',
                'main.js',
                'swiper.min.js',
                'v4-shims.min.js',
            ];
            $hit = false;
            foreach ($needles as $n) {
                if (stripos($src, $n) !== false) {
                    $hit = true;
                    break;
                }
            }
            if (!$hit) {
                return $full;
            }
            if (stripos($full, ' defer') === false) {
                $full = str_ireplace('<script', '<script defer', $full);
            }
            $moved[] = $full;
            return '';
        },
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

    $tail = '';
    if (!empty($moved)) {
        $tail .= implode("\n", $moved);
    }

    if (stripos($html, 'ledajansGtmLoaded') === false) {
        // GTM (+ icindeki gtag G-W42DVVXRT9): ilk etkilesim veya load + gecikme + idle. LCP'den sonra.
        $tail .= '<script>(function(){window.dataLayer=window.dataLayer||[];var gtmId='
            . wp_json_encode($gtmId)
            . ',delayMs='
            . (int) $delayMs
            . ',ev=["pointerdown","keydown","touchstart","scroll"];function loadGtm(){if(window.ledajansGtmLoaded){return;}window.ledajansGtmLoaded=1;ev.forEach(function(e){removeEventListener(e,loadGtm,{passive:true});});(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({"gtm.start":new Date().getTime(),event:"gtm.js"});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!="dataLayer"?"&l="+l:"";j.async=true;j.src="https://www.googletagmanager.com/gtm.js?id="+i+dl;f.parentNode.insertBefore(j,f);})(window,document,"script","dataLayer",gtmId);}ev.forEach(function(e){addEventListener(e,loadGtm,{passive:true});});function later(){setTimeout(function(){if(window.ledajansRunWhenIdle){window.ledajansRunWhenIdle(loadGtm);}else{loadGtm();}},delayMs);}if(document.readyState==="complete"){later();}else{addEventListener("load",later);}})();</script>';
    }

    if ($tail !== '') {
        if (stripos($html, '</body>') !== false) {
            $html = str_ireplace('</body>', $tail . '</body>', $html);
        } else {
            $html .= $tail;
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


/* =============================================================================
 * v1.3.0 — Mobil LCP optimizer (yalnizca ledajans_mp_v11_gtm_buffer icinden;
 * o buffer sadece mobil UA'da acilir => masaustu NO-OP).
 * Gorunum: piksel ayni hedef. Yeni gorsel varyantlari yalnizca sunucuda
 * wp-content/uploads/ledajans-mobile/<dosya> VARSA kullanilir (yoksa orijinal).
 * ============================================================================= */

if (!function_exists('ledajans_mp_v13_asset')) {
    /** uploads/ledajans-mobile/<file> varsa URL, yoksa ''. */
    function ledajans_mp_v13_asset($file) {
        static $cache = array();
        if (isset($cache[$file])) {
            return $cache[$file];
        }
        $url = '';
        if (function_exists('wp_upload_dir')) {
            $up = wp_upload_dir(null, false);
            if (!empty($up['basedir']) && is_file(rtrim($up['basedir'], '/') . '/ledajans-mobile/' . $file)) {
                $url = 'https://ledajans.com/wp-content/uploads/ledajans-mobile/' . rawurlencode($file);
            }
        }
        $cache[$file] = $url;
        return $url;
    }
}

if (!function_exists('ledajans_mp_v13_uploads_file_exists')) {
    function ledajans_mp_v13_uploads_file_exists($relative) {
        if (!function_exists('wp_upload_dir')) {
            return true; // emin degilsek dokunma
        }
        $up = wp_upload_dir(null, false);
        if (empty($up['basedir'])) {
            return true;
        }
        return is_file(rtrim($up['basedir'], '/') . '/' . ltrim($relative, '/'));
    }
}

if (!function_exists('ledajans_mp_v13_markup')) {
    /** $fn yalnizca <script>/<style> DISINDAKI HTML parcalarina uygulanir. */
    function ledajans_mp_v13_markup($html, $fn) {
        // Yorumlar da korunur (yorum icindeki "<style>" metni bolmeyi bozmasin)
        $parts = preg_split('#(<!--.*?-->|<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)#is', $html, -1, PREG_SPLIT_DELIM_CAPTURE);
        if (!is_array($parts)) {
            return $html;
        }
        foreach ($parts as $i => $part) {
            if ($i % 2 === 0 && $part !== '') {
                $parts[$i] = call_user_func($fn, $part);
            }
        }
        return implode('', $parts);
    }
}

if (!function_exists('ledajans_mp_v13_optimize')) {
function ledajans_mp_v13_optimize($html) {
    $U = 'https://ledajans.com/wp-content/uploads/';

    // --- 0) Body baslangici (head'e dokunan islemler icin)
    $bodyPos = stripos($html, '<body');
    $body = $bodyPos === false ? $html : substr($html, $bodyPos);

    // --- 1) Kirik Elementor yerel Google Font CSS (dosya yok -> 301 ana sayfa HTML'i, render-blocking 2x)
    $html = preg_replace_callback(
        '#<link[^>]+href=["\']([^"\']*/wp-content/uploads/(elementor/google-fonts/css/[a-z0-9_-]+\.css))[^"\']*["\'][^>]*>\s*#i',
        function ($m) {
            return ledajans_mp_v13_uploads_file_exists($m[2]) ? $m[0] : '';
        },
        $html
    );

    // --- 2) Editor CSS (frontend'de gereksiz): id ile kesin sil
    $html = preg_replace(
        '#<link[^>]+id=["\'](?:wp-block-editor|wp-components|wp-preferences|popup-maker-block-library-style)-css["\'][^>]*>\s*#i',
        '',
        $html
    );

    // --- 3) Onceki surumun preconnect'i stylesheet'e cevirdigi bozuk link (fonts.googleapis.com kok istegi)
    $html = preg_replace(
        '#<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\'](?:https:)?//fonts\.googleapis\.com/?["\'][^>]*>\s*#i',
        '',
        $html
    );

    // --- 4) Kosullu varliklar (widget yoksa yukleme)
    $hasCf7    = stripos($body, 'wpcf7-form') !== false;
    $hasSwiper = (bool) preg_match('#class=["\'][^"\']*(?:swiper|carousel|elementor-slides|product-single-inner)#i', $body);
    $hasRev    = (bool) preg_match('#<(?:sr7-module|rs-module|sr7-)#i', $body);
    $hasPum    = (bool) preg_match('#pum-overlay|popmake-|class=["\'][^"\']*\bpum\b#i', $body);
    $drop = array();
    if (!$hasCf7) {
        $drop[] = '/contact-form-7/';
    }
    if (!$hasSwiper) {
        $drop[] = '/swiper/';
    }
    if (!$hasRev) {
        $drop[] = '/revslider/';
    }
    if (!$hasPum) {
        $drop[] = '/popup-maker/';
    }
    if (!empty($drop)) {
        $quoted = implode('|', array_map(function ($d) {
            return preg_quote($d, '#');
        }, $drop));
        $html = preg_replace('#<link[^>]+href=["\'][^"\']*(?:' . $quoted . ')[^"\']*["\'][^>]*>\s*#i', '', $html);
        $html = preg_replace('#<script[^>]+src=["\'][^"\']*(?:' . $quoted . ')[^"\']*["\'][^>]*>\s*</script>\s*#i', '', $html);
    }

    // --- 5) Ayni kare, kucuk varyant (yalnizca dosya sunucuda varsa)
    $variantSrc = array(
        $U . '2026/09/iso-9001-2015-1.webp'      => 'iso-9001-2015-1-320.webp',
        $U . '2026/09/iso-45001-2018-1.webp'     => 'iso-45001-2018-1-320.webp',
        $U . '2026/09/taha-led-14064-1.webp'     => 'taha-led-14064-1-320.webp',
        $U . '2026/09/iso-10002-2018-1.webp'     => 'iso-10002-2018-1-320.webp',
        $U . '2026/09/iso-14001-2015-1.webp'     => 'iso-14001-2015-1-320.webp',
        $U . '2026/09/iso-27001-2022-1.webp'     => 'iso-27001-2022-1-320.webp',
        $U . '2026/09/iso-31000-2018-1.webp'     => 'iso-31000-2018-1-320.webp',
        $U . '2025/10/创联logo5.png'               => 'chuanglian-logo5-320.webp',
        $U . '2026/09/dis-mekan-led-ekran-1.webp' => 'dis-mekan-led-ekran-1-768.webp',
        $U . '2023/01/breadcrumb-01.jpg'         => 'breadcrumb-01-1280.webp',
    );
    $map = array();
    foreach ($variantSrc as $orig => $file) {
        $v = ledajans_mp_v13_asset($file);
        if ($v !== '') {
            $map[$orig] = $v;
        }
    }

    // Ust menu logo: kirik 2026/08 webp (301 -> ana sayfa HTML) ve eski jpg/png -> tek webp (footer dokunulmaz)
    $headerLogo = ledajans_mp_v13_asset('ledajans-ust-menu-logo-400.webp');
    if ($headerLogo === '') {
        $headerLogo = $U . '2026/09/ledajans-ust-menu-logo.webp';
    }
    $logoMap = array(
        $U . '2026/08/LedajansLogo.webp'                                  => $headerLogo,
        $U . '2022/12/ledajans-logo-web.jpg'                              => $headerLogo,
        'https://www.ledajans.com/wp-content/uploads/2022/12/ledajans-logo-web.jpg' => $headerLogo,
        $U . '2022/12/LedajansLogo.png'                                   => $headerLogo,
    );
    // logo-swap script'inin HEADER sabiti (FOOTER ayni kalir)
    $html = preg_replace(
        '#(var HEADER = \')' . preg_quote($U . '2026/09/ledajans-ust-menu-logo.webp', '#') . '(\';)#',
        '${1}' . $headerLogo . '${2}',
        $html,
        1
    );

    // Marka logolari: boyut ver (CLS / unsized-images). style auto => render ayni.
    $brandDims = array(
        '2025/12/gkgd.png'      => array(150, 150),
        '2025/12/cl.png'        => array(150, 150),
        '2025/12/youyi.png'     => array(150, 150),
        '2025/12/u-motion.png'  => array(150, 150),
        '2025/10/创联logo5.png'   => isset($map[$U . '2025/10/创联logo5.png']) ? array(320, 346) : array(1113, 1203),
        'ledajans-mobile/chuanglian-logo5-320.webp' => array(320, 346),
    );

    // --- 6) LCP kaynagi (sablon basina tek)
    $lcp = '';
    $lcpIsImgTag = false;
    if (preg_match('#class=["\']la1-mobile["\'][^>]*>\s*<img\b[^>]*\ssrc=["\']([^"\']+)#i', $html, $m)) {
        $lcp = $m[1];                          // Anasayfa: stant poster (mobil)
        $lcpIsImgTag = true;
    } elseif (preg_match('#\.ledajans-blog-hero\s*\{[^}]*background-image:\s*url\(\s*[\'"]?([^\'")]+)#i', $html, $m)) {
        $lcp = $m[1];                          // Urun/sayfa ust banner (CSS background)
    } elseif (stripos($body, 'custom-breadcrumb') !== false && stripos($body, 'elementor-element-1070ed4') !== false) {
        $lcp = $U . '2023/01/breadcrumb-01.jpg'; // Blog tekil: breadcrumb arka plani (post-186.css)
        $bc = isset($map[$lcp]) ? $map[$lcp] : '';
        if ($bc !== '') {
            $html = str_ireplace('</head>', '<style id="ledajans-mp-bc">.elementor-186 .elementor-element.elementor-element-1070ed4 .custom-breadcrumb{background-image:url("' . $bc . '")!important}</style></head>', $html);
        }
        // tek yuksek oncelik: one cikan gorsel eager kalir, high oncelik breadcrumb'a
        $html = preg_replace_callback('#<img\b[^>]*wp-post-image[^>]*>#i', function ($m) {
            $t = preg_replace('#\sfetchpriority=["\']high["\']#i', '', $m[0]);
            return preg_replace('#<img\b#i', '<img data-lj-eager="1"', $t, 1);
        }, $html, 1);
    }
    if ($lcp !== '' && strpos($lcp, '//') === 0) {
        $lcp = 'https:' . $lcp;
    }
    if ($lcp !== '' && isset($map[$lcp])) {
        $lcp = $map[$lcp];
    }

    // Tum eski/cift image preload'lari sil (hero-poster, ldajsn2-mobile-q60/q72, desktop poster, govdedeki widget preload)
    $html = ledajans_mp_v13_markup($html, function ($part) {
        return preg_replace('#<link\b[^>]*rel=["\']preload["\'][^>]*as=["\'](?:image|video)["\'][^>]*>\s*#i', '', $part);
    });
    $html = ledajans_mp_v13_markup($html, function ($part) {
        return preg_replace('#<link\b[^>]*as=["\'](?:image|video)["\'][^>]*rel=["\']preload["\'][^>]*>\s*#i', '', $part);
    });
    if ($lcp !== '') {
        $type = preg_match('#\.webp($|\?)#i', $lcp) ? ' type="image/webp"' : '';
        $tag = '<link rel="preload" as="image" href="' . esc_url($lcp) . '"' . $type . ' fetchpriority="high">' . "\n";
        if (preg_match('#<meta[^>]+charset[^>]*>#i', $html, $cm, PREG_OFFSET_CAPTURE)) {
            $pos = $cm[0][1] + strlen($cm[0][0]);
            $html = substr($html, 0, $pos) . "\n" . $tag . substr($html, $pos);
        } else {
            $html = preg_replace('#<head\b[^>]*>#i', '$0' . "\n" . $tag, $html, 1);
        }
    }

    // --- 7) URL varyantlari: yalnizca <img>, style bloklari ve style="" (JSON-LD / meta / og DOKUNULMAZ)
    if (!empty($map)) {
        $html = preg_replace_callback('#<style\b[^>]*>.*?</style>#is', function ($m) use ($map) {
            return strtr($m[0], $map);
        }, $html);
        $html = preg_replace_callback('#\sstyle=["\'][^"\']*url\([^"\']*["\']#i', function ($m) use ($map) {
            return strtr($m[0], $map);
        }, $html);
    }

    // --- 8) <img> politikasi (script/style disi). Header oncesi: sadece logo map. Sonrasi: fold alti lazy.
    $hdrEnd = stripos($html, '</header>');
    $head = $hdrEnd === false ? '' : substr($html, 0, $hdrEnd);
    $rest = $hdrEnd === false ? $html : substr($html, $hdrEnd);

    $imgFix = function ($tag, $lazy) use ($map, $logoMap, $brandDims) {
        if (preg_match('#\ssrc=["\']data:#i', $tag)) {
            return $tag;
        }
        $tag = strtr($tag, $logoMap);
        $tag = strtr($tag, $map);
        $isHigh = (bool) preg_match('#fetchpriority=["\']high["\']|data-lj-eager#i', $tag);
        $isLogo = (bool) preg_match('#ledajans-ust-menu-logo#i', $tag);
        if ($isLogo && !$lazy) {
            // ust menu logo: kucuk, fold ustu -> normal yukleme (onceki lazy/low kaldirildi)
            $tag = preg_replace('#\s(?:loading|fetchpriority)=["\'][^"\']*["\']#i', '', $tag);
        }
        if ($lazy && !$isHigh) {
            $tag = preg_replace('#\sloading=["\'][^"\']*["\']#i', '', $tag);
            $tag = preg_replace('#\s*(/?)>$#', ' loading="lazy"$1>', $tag, 1);
            $tag = str_replace('"/>', '" />', $tag);
        }
        if ($isHigh) {
            $tag = preg_replace('#\sloading=["\']lazy["\']#i', '', $tag);
        }
        if (stripos($tag, 'decoding=') === false) {
            $tag = preg_replace('#\s*(/?)>$#', ' decoding="async"$1>', $tag, 1);
        }
        if (!preg_match('#\swidth=["\']?\d#i', $tag)) {
            foreach ($brandDims as $needle => $wh) {
                if (strpos($tag, $needle) !== false) {
                    $tag = preg_replace('#<img\b#i', '<img width="' . $wh[0] . '" height="' . $wh[1] . '"', $tag, 1);
                    if (stripos($tag, ' style=') === false) {
                        $tag = preg_replace('#<img\b#i', '<img style="width:auto;height:auto"', $tag, 1);
                    }
                    break;
                }
            }
        }
        return $tag;
    };

    $head = ledajans_mp_v13_markup($head, function ($part) use ($imgFix) {
        return preg_replace_callback('#<img\b[^>]*>#i', function ($m) use ($imgFix) {
            return $imgFix($m[0], false);
        }, $part);
    });
    $rest = ledajans_mp_v13_markup($rest, function ($part) use ($imgFix) {
        $part = preg_replace_callback('#<img\b[^>]*>#i', function ($m) use ($imgFix) {
            return $imgFix($m[0], true);
        }, $part);
        // Proje videolari: autoplay yok, preload=none, gorunce oynat (asagidaki IO script)
        $part = preg_replace_callback('#<video\b[^>]*>#i', function ($m) {
            $tag = $m[0];
            if (stripos($tag, 'autoplay') === false || stripos($tag, 'la1-video') !== false) {
                return $tag;
            }
            $tag = preg_replace('#\sautoplay(?:=["\'][^"\']*["\'])?#i', '', $tag);
            $tag = preg_replace('#\spreload=["\'][^"\']*["\']#i', '', $tag);
            return preg_replace('#<video\b#i', '<video preload="none" data-lj-autoplay="1"', $tag, 1);
        }, $part);
        return $part;
    });
    $html = $head . $rest;

    if (strpos($html, 'data-lj-autoplay') !== false && stripos($html, 'ledajansVideoIO') === false) {
        $io = '<script id="ledajansVideoIO">(function(){var vs=[].slice.call(document.querySelectorAll("video[data-lj-autoplay]"));if(!vs.length){return;}function on(v){if(v.getAttribute("data-lj-on")){return;}v.setAttribute("data-lj-on","1");v.preload="auto";var p=v.play();if(p&&p.catch){p.catch(function(){});}}function off(v){if(!v.getAttribute("data-lj-on")){return;}v.removeAttribute("data-lj-on");try{v.pause();}catch(e){}}if(!("IntersectionObserver" in window)){vs.forEach(on);return;}var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){on(e.target);}else{off(e.target);}});},{rootMargin:"200px 0px"});vs.forEach(function(v){io.observe(v);});})();</script>';
        $html = str_ireplace('</body>', $io . '</body>', $html);
    }

    // Ust menu logo onceden yuklensin mi? Hayir: 7.9KiB, normal oncelik yeterli.
    return $html;
}
}
