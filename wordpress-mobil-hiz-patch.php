<?php
/**
 * LEDAJANS Mobil Performans Patch
 * Aktif tema functions.php sonuna ekleyin veya
 * wp-content/mu-plugins/ledajans-perf-patch.php olarak kaydedin.
 *
 * Hedef: mobil LCP/TBT — GTM erteleme, render-blocking defer,
 * unused CSS/JS azaltma, hero LCP önceliği.
 */

if (!defined('ABSPATH')) {
    exit;
}

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

function ledajans_wants_mobile_perf() {
    if (is_admin()) {
        return false;
    }
    if (function_exists('wp_is_mobile') && wp_is_mobile()) {
        return true;
    }
    // UA yoksa (cache/edge) yine de agresif erteleme uygula; desktop maliyeti düşük.
    return true;
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

// 2) Kaynağa göre gereksiz CSS düşür (audit: FA, block-editor, popup-maker)
add_action('wp_print_styles', function () {
    if (is_admin()) {
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

// 3) LCP hero preload — mobilde yalnızca q60 (srcset q72 LCP kaçırmasın)
add_action('wp_head', function () {
    if (is_admin() || !is_front_page()) {
        return;
    }

    echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q60.webp" media="(max-width: 768px)" fetchpriority="high" imagesrcset="https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q60.webp 768w" imagesizes="100vw">' . "\n";
    echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/04/hero-poster.webp" media="(min-width: 769px)" fetchpriority="high">' . "\n";
}, 1);

add_filter('wp_get_attachment_image_attributes', function ($attr) {
    if (is_admin() || !is_front_page()) {
        return $attr;
    }

    $src = $attr['src'] ?? '';
    if (stripos($src, 'ldajsn2-mobile') !== false || stripos($src, 'hero-poster.webp') !== false) {
        $attr['fetchpriority'] = 'high';
        $attr['loading'] = 'eager';
        $attr['decoding'] = 'async';
    }

    return $attr;
}, 10, 1);

// 4) Idle helper + font-display swap (erken)
add_action('wp_head', function () {
    if (is_admin()) {
        return;
    }
    ?>
<script>
window.ledajansRunWhenIdle=function(callback){if('requestIdleCallback'in window){requestIdleCallback(callback,{timeout:2500});}else{setTimeout(callback,1800);}};
</script>
<style id="ledajans-font-display">@font-face{font-display:swap}</style>
    <?php
}, 0);

// 5) Preconnect — GTM'yi LCP öncesi isteme (mobilde kaldır)
add_filter('wp_resource_hints', function ($urls, $relation_type) {
    if ('preconnect' !== $relation_type) {
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

// 6) Ağır / tema scriptlerini footer + defer
add_action('wp_enqueue_scripts', function () {
    if (is_admin()) {
        return;
    }

    global $wp_scripts;
    if (empty($wp_scripts) || empty($wp_scripts->queue)) {
        return;
    }

    $moveFooterNeedles = [
        'elementor',
        'swiper',
        'masonry',
        'imagesloaded',
        'bootstrap',
        'magnific',
        'jquery.appear',
        'jquery.cookie',
        'modins',
        'main',
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

        if (!$hit || $handle === 'jquery') {
            continue;
        }

        wp_dequeue_script($handle);
        wp_deregister_script($handle);
        wp_register_script($handle, $src, $reg->deps, $reg->ver, true);
        wp_enqueue_script($handle);
    }
}, 110);

add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || empty($src) || $handle === 'jquery') {
        return $tag;
    }

    $deferNeedles = [
        'elementor',
        'swiper',
        'masonry',
        'imagesloaded',
        'bootstrap',
        'magnific',
        'appear',
        'cookie',
        'modins',
        'main',
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

// 7) GTM/gtag enqueue etiketlerini kaldır (buffer ile idle yükleme)
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || empty($src)) {
        return $tag;
    }

    if (stripos($src, 'googletagmanager.com/gtm.js') !== false
        || stripos($src, 'googletagmanager.com/gtag/js') !== false) {
        return '';
    }

    return $tag;
}, 100, 3);

// 8) Site geneli: inline GTM → idle + timeout (mobil LCP öncelikli)
add_action('template_redirect', function () {
    if (is_admin() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST)) {
        return;
    }
    if (!ledajans_wants_mobile_perf()) {
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

// 9) Font CSS async (projeler hariç)
add_action('wp_head', function () {
    if (is_admin() || ledajans_is_projeler_page()) {
        return;
    }

    echo '<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" onload="this.onload=null;this.rel=\'stylesheet\'">' . "\n";
    echo '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"></noscript>' . "\n";
}, 2);

// 10) Elementor non-critical CSS
add_action('wp_enqueue_scripts', function () {
    if (is_admin()) {
        return;
    }

    $nonCriticalHandles = [
        'elementor-gallery',
        'elementor-lightbox',
        'e-animations',
        'elementor-animations',
    ];
    foreach ($nonCriticalHandles as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }
}, 200);

// FA / Elementor icon CSS: render-blocking olmasın (media=print → all)
add_filter('style_loader_tag', function ($html, $handle, $href) {
    if (is_admin() || empty($href)) {
        return $html;
    }

    $asyncNeedles = [
        '/font-awesome/',
        '/fontawesome/',
        'elementor-icons',
        'elementor-icons-fa',
    ];
    $hit = false;
    foreach ($asyncNeedles as $needle) {
        if (stripos($handle, $needle) !== false || stripos($href, $needle) !== false) {
            $hit = true;
            break;
        }
    }
    if (!$hit) {
        return $html;
    }

    if (stripos($html, 'onload=') !== false) {
        return $html;
    }

    return sprintf(
        '<link rel="stylesheet" id="%s-css" href="%s" media="print" onload="this.media=\'all\'"><noscript>%s</noscript>',
        esc_attr($handle),
        esc_url($href),
        $html
    );
}, 20, 3);

// 11) Mobil: motion/sticky + CF7/chaty (ana sayfa form yoksa)
add_action('wp_enqueue_scripts', function () {
    if (is_admin() || !(function_exists('wp_is_mobile') && wp_is_mobile())) {
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

// 12) /projeler/ — ekstra asset kesimi
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

// 13) Görseller: eksik width/height CLS önlemi (bilinen hero)
add_filter('the_content', function ($content) {
    if (is_admin() || !is_string($content) || $content === '') {
        return $content;
    }

    $content = preg_replace(
        '#(<img[^>]+ldajsn2-mobile[^>]*?)(?:\s*/?>)#i',
        '$1 width="1200" height="1600">',
        $content,
        1
    );

    return $content;
}, 20);

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
