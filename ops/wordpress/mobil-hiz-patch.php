<?php
/**
 * LEDAJANS Mobil Performans Patch
 * Bu kodu aktif temanın functions.php dosyasının SONUNA ekleyin
 * veya wp-content/mu-plugins/ledajans-perf-patch.php olarak kaydedin.
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
    return ledajans_is_money_page();
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
        '/line-awesome/',
        '/fontawesome/',
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

    echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q60.webp" media="(max-width: 768px)" fetchpriority="high">' . "\n";
    echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/04/hero-poster.webp" media="(min-width: 769px)" fetchpriority="high">' . "\n";
}, 1);

add_filter('wp_get_attachment_image_attributes', function ($attr) {
    if (is_admin() || !is_front_page()) {
        return $attr;
    }

    $src = $attr['src'] ?? '';
    if (stripos($src, 'ldajsn2-mobile-q60.webp') !== false || stripos($src, 'hero-poster.webp') !== false) {
        $attr['fetchpriority'] = 'high';
        $attr['loading'] = 'eager';
        $attr['decoding'] = 'async';
    }

    return $attr;
}, 10, 1);

// 3b) W3TC lazyload: mobil LCP görsellerini lazy dışı bırak (skip-lazy + eager)
add_action('template_redirect', function () {
    if (is_admin() || !wp_is_mobile()) {
        return;
    }
    ob_start('ledajans_mobile_lcp_lazyload_buffer');
}, 99999);

function ledajans_mobile_lcp_lazyload_buffer($html) {
    if (!is_string($html) || $html === '') {
        return $html;
    }

    // Çift preload temizliği — yalnızca q60 LCP preload kalsın
    $seenPreload = false;
    $html = (string) preg_replace_callback(
        '#<link[^>]+rel=["\']preload["\'][^>]*ldajsn2-mobile[^>]*>#i',
        static function ($match) use (&$seenPreload) {
            $tag = $match[0];
            if (stripos($tag, 'q72') !== false) {
                return '';
            }
            if ($seenPreload) {
                return '';
            }
            $seenPreload = true;
            return $tag;
        },
        $html
    );

    $lcpNeedles = ['ldajsn2-mobile', 'hero-poster', 'ledajans-hero-bg-mobile'];
    $pattern = '#<img\b([^>]*(?:' . implode('|', array_map('preg_quote', $lcpNeedles)) . ')[^>]*)>#i';

    return (string) preg_replace_callback(
        $pattern,
        static function ($matches) {
            $tag = $matches[0];
            $tag = preg_replace('#\sloading=["\']lazy["\']#i', ' loading="eager"', $tag);
            if (stripos($tag, 'loading=') === false) {
                $tag = str_replace('<img', '<img loading="eager"', $tag);
            }
            if (preg_match('#\sclass=["\']([^"\']*)["\']#i', $tag, $classMatch)) {
                $classes = trim(preg_replace('#(^|\s)lazy(\s|$)#i', ' ', $classMatch[1]) . ' skip-lazy no-lazy');
                $tag = preg_replace(
                    '#\sclass=["\'][^"\']*["\']#i',
                    ' class="' . esc_attr(preg_replace('/\s+/', ' ', $classes)) . '"',
                    $tag,
                    1
                );
            } else {
                $tag = str_replace('<img', '<img class="skip-lazy no-lazy"', $tag);
            }
            if (stripos($tag, 'data-no-lazy') === false) {
                $tag = str_replace('<img', '<img data-no-lazy="1"', $tag);
            }
            if (preg_match('#\sdata-src=["\']([^"\']+)["\']#i', $tag, $dataSrc)) {
                $realSrc = $dataSrc[1];
                if (!preg_match('#\ssrc=["\'][^"\']+["\']#i', $tag) || preg_match('#\ssrc=["\']data:#i', $tag)) {
                    $tag = preg_replace('#\ssrc=["\'][^"\']*["\']#i', '', $tag);
                    $tag = str_replace('<img', '<img src="' . esc_url($realSrc) . '"', $tag);
                }
                $tag = preg_replace('#\sdata-src=["\'][^"\']*["\']#i', '', $tag);
            }
            $tag = preg_replace('#\ssrc=["\']data:image[^"\']*["\']#i', '', $tag);
            if (stripos($tag, 'fetchpriority=') === false) {
                $tag = str_replace('<img', '<img fetchpriority="high"', $tag);
            }
            if (stripos($tag, 'ldajsn2-mobile-q60') !== false || stripos($tag, 'ledajans-hero-bg-mobile') !== false) {
                $tag = preg_replace(
                    '#\ssrc=["\'][^"\']*["\']#i',
                    ' src="https://ledajans.com/wp-content/uploads/2026/04/ldajsn2-mobile-q60.webp"',
                    $tag,
                    1
                );
            }
            return $tag;
        },
        $html
    );
}

// 3c) Mobilde jQuery defer (anasayfa — TBT düşürme)
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || !wp_is_mobile() || !is_front_page() || $handle !== 'jquery' || empty($src)) {
        return $tag;
    }
    if (stripos($tag, 'defer') === false) {
        $tag = str_replace(' src=', ' defer src=', $tag);
    }
    return $tag;
}, 15, 3);

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

// 6) Home sayfasında ağır scriptleri footer'a it
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

// 7) Kritik font preload hint'leri (mobilde sistem font fallback; desktop preload korunur)
add_action('wp_head', function () {
    if (is_admin() || ledajans_is_projeler_page()) {
        return;
    }

    if (wp_is_mobile()) {
        echo '<style id="ledajans-mobile-font-fallback">@media (max-width:768px){body,.ledajans-hero-content{font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important}}</style>' . "\n";
        echo '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" media="print" onload="this.media=\'all\';this.onload=null;">' . "\n";
        echo '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"></noscript>' . "\n";
        return;
    }

    echo '<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" onload="this.onload=null;this.rel=\'stylesheet\'">' . "\n";
    echo '<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"></noscript>' . "\n";
}, 2);

// 8) Sayfa bazlı gereksiz Elementor widget CSS'lerini kaldır
add_action('wp_enqueue_scripts', function () {
    if (is_admin()) {
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

// 12) Anasayfa — render-blocking olmayan CSS'i asenkrona al (mobilde genişletilmiş liste)
add_filter('style_loader_tag', function ($tag, $handle, $href) {
    if (is_admin() || empty($href)) {
        return $tag;
    }

    $mobileHome = wp_is_mobile() && is_front_page();
    $desktopHome = !wp_is_mobile() && is_front_page();
    if (!$mobileHome && !$desktopHome) {
        return $tag;
    }

    $asyncNeedles = ['chaty', 'contact-form-7', 'elementor-icons', 'line-awesome', 'fontawesome'];
    if ($mobileHome) {
        $asyncNeedles = array_merge($asyncNeedles, [
            'popup-maker',
            'swiper',
            'elementor-widget-',
            'elementor-animations',
            'e-animation',
        ]);
    }

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

// 12b) Mobilde Chaty — tüm sayfalarda scroll/idle sonrası yükle
add_filter('script_loader_tag', function ($tag, $handle, $src) {
    if (is_admin() || !wp_is_mobile() || empty($src) || stripos($src, 'chaty') === false) {
        return $tag;
    }
    if (!isset($GLOBALS['ledajans_deferred_chaty'])) {
        $GLOBALS['ledajans_deferred_chaty'] = [];
    }
    $GLOBALS['ledajans_deferred_chaty'][] = $src;
    return '';
}, 50, 3);

add_action('wp_footer', function () {
    if (is_admin() || !wp_is_mobile() || empty($GLOBALS['ledajans_deferred_chaty'])) {
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

// 12c) Anasayfa — geç yüklenen sohbet widget dequeue (desktop; mobil 12b kullanır)
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
