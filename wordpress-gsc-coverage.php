<?php
/**
 * Plugin Name: LEDAJANS GSC Coverage
 * Description: GSC 404/301/410, EN/DE kapanis, demo/kopya URL, video JSON-LD, breadcrumb.
 * Version: 1.2.0
 * Author: LEDAJANS
 */
if (!defined('ABSPATH')) { exit; }

// === GSC coverage — tum cihazlar (404/canonical/breadcrumb/robots) ===

if (!function_exists('ledajans_gsc_request_path')) {
    function ledajans_gsc_request_path() {
        $path = isset($_SERVER['REQUEST_URI']) ? (string) wp_unslash($_SERVER['REQUEST_URI']) : '/';
        $path = strtolower(strtok($path, '?'));
        $path = '/' . trim($path, '/');
        if ($path !== '/') {
            $path = rtrim($path, '/');
        }
        return $path === '' ? '/' : $path;
    }
}

if (!function_exists('ledajans_gsc_abs')) {
    function ledajans_gsc_abs($to) {
        if (!is_string($to) || $to === '') {
            $to = '/';
        }
        if (preg_match('#^https?://#i', $to)) {
            return $to;
        }
        if ($to[0] !== '/') {
            $to = '/' . $to;
        }
        return 'https://ledajans.com' . $to;
    }
}

if (!function_exists('ledajans_gsc_go')) {
    function ledajans_gsc_go($to, $code = 301) {
        nocache_headers();
        if (!headers_sent()) {
            header('Cache-Control: no-cache, must-revalidate, max-age=0', true);
            header('X-Redirect-By: LEDAJANS-GSC', true);
        }
        wp_safe_redirect(ledajans_gsc_abs($to), (int) $code);
        exit;
    }
}

if (!function_exists('ledajans_gsc_redirect_map')) {
    function ledajans_gsc_redirect_map() {
        return array(
            '/urunler/rental-ekran' => '/rental-ekran/',
            '/urunler/kontrol-kartlari' => '/kontrol-kartlari/',
            '/urunler/dis-mekan-rgb-panel' => '/dis-mekan-rgb-panel/',
            '/urunler/ic-mekan-rgb-panel' => '/ic-mekan-rgb-panel/',
            '/urunler/ic-mekan-led-ekran' => '/ic-mekan-led-ekran/',
            '/urunler/dis-mekan-led-ekran' => '/dis-mekan-led-ekran/',
            '/case' => '/projeler/',
            '/en/case' => '/projeler/',
            '/de/case' => '/projeler/',
            '/case/dis-mekan-led-ekran' => '/dis-mekan-led-ekran/',
            '/case/indoor-rgb-panels' => '/ic-mekan-rgb-panel/',
            '/case/outdoor-rgb-panel' => '/dis-mekan-rgb-panel/',
            '/case/rental-cabin' => '/rental-ekran/',
            '/case/rental-ekran' => '/rental-ekran/',
            '/case/control-cards' => '/kontrol-kartlari/',
            '/case/indoor-led-display' => '/ic-mekan-led-ekran/',
            '/case/outdoor-led-screen' => '/dis-mekan-led-ekran/',
            '/case/power-supply' => '/guc-kaynaklari/',
            '/case/power-supply-2' => '/guc-kaynaklari/',
            '/case/power-supply-2-2' => '/guc-kaynaklari/',
            '/ease/control-cards' => '/kontrol-kartlari/',
            '/ease/indoor-rgb-panels' => '/ic-mekan-rgb-panel/',
            '/en' => '/',
            '/de' => '/',
            '/en/contact' => '/iletisim/',
            '/en/about-us' => '/hakkimizda/',
            '/en/our-company-information' => '/firma-bilgilerimiz/',
            '/en/outdoor-led-screen' => '/dis-mekan-led-ekran/',
            '/en/case/indoor-led-display' => '/ic-mekan-led-ekran/',
            '/en/case/outdoor-led-screen' => '/dis-mekan-led-ekran/',
            '/en/case/outdoor-rgb-panel' => '/dis-mekan-rgb-panel/',
            '/en/case/rental-cabin' => '/rental-ekran/',
            '/en/case/power-supply' => '/guc-kaynaklari/',
            '/en/case/indoor-rgb-panels' => '/ic-mekan-rgb-panel/',
            '/en/case/control-cards' => '/kontrol-kartlari/',
            '/de/kommunikation' => '/iletisim/',
            '/de/uber-uns' => '/hakkimizda/',
            '/de/unsere-firmeninformationen' => '/firma-bilgilerimiz/',
            '/de/led-ekran' => '/led-ekran/',
            '/de/led-anzeige' => '/led-ekran/',
            '/de/led-bildschirm' => '/led-ekran/',
            '/de/led-ekran-10' => '/led-ekran/',
            '/de/hd-c10' => '/colorlight/',
            '/de/ticker' => '/blog/',
            '/de/gefuehrt' => '/led-ekran/',
            '/de/gefuehrt-2' => '/led-ekran/',
            '/de/gefuehrt-3' => '/led-ekran/',
            '/de/p10-panel-2-2' => '/p10-panel/',
            '/de/p10-panel-3' => '/p10-panel/',
            '/de/p10-panel-4-2' => '/p10-panel/',
            '/de/p10-panel-5' => '/p10-panel/',
            '/de/p10-rotes-panel' => '/p10-panel-kirmizi/',
            '/de/verwendung-des-p10-grafikdisplays' => '/p10-panel/',
            '/de/was-ist-ein-led-streifen' => '/blog/',
            '/de/category/genel-de' => '/blog/',
            '/de/case/led-anzeige-fuer-den-innenbereich' => '/ic-mekan-led-ekran/',
            '/de/case/mietbildschirm' => '/rental-ekran/',
            '/de/case/rgb-panel-fuer-den-aussenbereich' => '/dis-mekan-rgb-panel/',
            '/de/case/rgb-panel-fuer-den-innenbereich' => '/ic-mekan-rgb-panel/',
            '/de/case/steuerkarten' => '/kontrol-kartlari/',
            '/de/case/stromversorgung' => '/guc-kaynaklari/',
            '/de/case/verleihbildschirm' => '/rental-ekran/',
            '/de-case-rgb-panel-fuer-den-aussenbereich' => '/dis-mekan-rgb-panel/',
            '/gallery' => '/projeler/',
            '/portfolio-01' => '/projeler/',
            '/portfolio-02' => '/projeler/',
            '/portfolio-03' => '/projeler/',
            '/about-me' => '/hakkimizda/',
            '/led-ekran-2' => '/led-ekran/',
            '/led-ekran-3' => '/led-ekran/',
            '/led' => '/led-ekran/',
            '/led-2' => '/led-ekran/',
            '/tf-qs2n-kontrol-karti-2' => '/tf-qs2n-kontrol-karti/',
            '/rehber/toplanti-odasi-led-ekran' => '/ic-mekan-led-ekran/',
            '/sozluk/gob-led-nedir' => '/gob-led-ekran/',
            '/led-ekran-10' => '/led-ekran/',
            '/ic-mekan-indoor-led-ekranlar' => '/ic-mekan-led-ekran/',
            '/category/kontrol-kartlari' => '/kontrol-kartlari/',
            '/kayan-yazi-2' => '/blog/kayan-yazi/',
            '/ledajans.com/iletisim' => '/iletisim/',
            '/p10-panel-2' => '/p10-panel/',
            '/p2-5-gob-ic-mekan-rgb-panel' => '/ic-mekan-led-ekran/',
            '/p1-25-gob-ic-mekan-rgb-panel' => '/ic-mekan-led-ekran/',
            '/p1-53-gob-ic-mekan-rgb-panel' => '/ic-mekan-led-ekran/',
            '/p1-86-gob-ic-mekan-rgb-panel' => '/ic-mekan-led-ekran/',
            '/q1-25-flexible-ic-mekan-led-panel' => '/ic-mekan-led-ekran/',
            '/q1-53-flexible-ic-mekan-led-panel' => '/ic-mekan-led-ekran/',
            '/q1-86-flexible-ic-mekan-led-panel' => '/ic-mekan-led-ekran/',
        );
    }
}

add_action('template_redirect', function () {
    if (is_admin() || (defined('REST_REQUEST') && REST_REQUEST) || (defined('WP_CLI') && WP_CLI)) {
        return;
    }
    if (strpos($path = ledajans_gsc_request_path(), '/wp-json') === 0 || strpos($path, '/wp-admin') === 0) {
        return;
    }

    $path = ledajans_gsc_request_path();
    $qs = isset($_SERVER['QUERY_STRING']) ? (string) wp_unslash($_SERVER['QUERY_STRING']) : '';

    if (preg_match('#(?:^|&)p=(\d+)#', $qs, $m) && (strpos($path, '/blog') === 0 || $path === '/')) {
        $permalink = get_permalink((int) $m[1]);
        if ($permalink && !is_wp_error($permalink)) {
            ledajans_gsc_go($permalink);
        }
    }

    if (strpos($path, '/gva_template/') === 0 || $path === '/gva_template'
        || strpos($path, '/events/list') === 0 || strpos($path, '/events/liste') === 0
        || strpos($path, '/events/kategori') === 0
        || $path === '/*') {
        status_header(410);
        nocache_headers();
        exit;
    }

    $map = ledajans_gsc_redirect_map();
    if (isset($map[$path])) {
        ledajans_gsc_go($map[$path]);
    }

    if (preg_match('#^/urunler/([^/]+)$#', $path, $m)) {
        ledajans_gsc_go('/' . $m[1] . '/');
    }

    if (preg_match('#^/(?:en|de)/case(/.*)?$#', $path) || preg_match('#^/case(/.*)?$#', $path)) {
        $bare = preg_replace('#^/(?:en|de)#', '', $path);
        if ($bare === '') {
            $bare = $path;
        }
        if (isset($map[$bare])) {
            ledajans_gsc_go($map[$bare]);
        }
        ledajans_gsc_go('/projeler/');
    }

    if (preg_match('#^/(en|de)$#', $path) || preg_match('#^/(en|de)/#', $path)) {
        ledajans_gsc_go('/');
    }

    if ($path === '/feed' || $path === '/comments/feed' || preg_match('#/feed$#', $path)) {
        if ($path === '/feed' || $path === '/comments/feed' || preg_match('#^/(en|de)/feed$#', $path)) {
            ledajans_gsc_go('/');
        }
        $parent = preg_replace('#/feed$#', '/', $path);
        $parent = preg_replace('#/+#', '/', $parent);
        $slug = trim($parent, '/');
        if ($slug !== '' && strpos($slug, '/') === false) {
            $page = get_page_by_path($slug);
            if ($page instanceof WP_Post) {
                ledajans_gsc_go(get_permalink($page));
            }
            $post = get_page_by_path($slug, OBJECT, 'post');
            if ($post instanceof WP_Post) {
                ledajans_gsc_go(get_permalink($post));
            }
            status_header(410);
            nocache_headers();
            exit;
        }
        ledajans_gsc_go($parent);
    }
}, -1);

add_action('send_headers', function () {
    if (is_admin()) {
        return;
    }
    if (is_feed() || is_author() || is_search() || is_attachment()
        || (defined('REST_REQUEST') && REST_REQUEST)) {
        header('X-Robots-Tag: noindex, follow', true);
    }
}, 1);

add_filter('robots_txt', function ($output, $public) {
    unset($public);
    $extra = "Disallow: /gva_template/\nDisallow: /events/list\nDisallow: /events/liste\nDisallow: /feed/\nDisallow: /*/feed/\n";
    if (stripos($output, '/gva_template/') === false) {
        $output .= "\n# LEDAJANS GSC\n" . $extra;
    }
    return $output;
}, 99, 2);

add_filter('rank_math/json_ld', function ($data, $jsonld) {
    unset($jsonld);
    if (empty($data['BreadcrumbList']['itemListElement']) || !is_array($data['BreadcrumbList']['itemListElement'])) {
        return $data;
    }
    foreach ($data['BreadcrumbList']['itemListElement'] as &$el) {
        if (!is_array($el)) {
            continue;
        }
        $item = $el['item'] ?? null;
        if (is_string($item) && ($item === '#' || $item === '' || !preg_match('#^https?://#i', $item))) {
            $el['item'] = home_url('/');
        } elseif (is_array($item)) {
            $id = isset($item['@id']) ? (string) $item['@id'] : '';
            if ($id === '#' || $id === '' || !preg_match('#^https?://#i', $id)) {
                $el['item']['@id'] = home_url('/');
            }
        }
    }
    unset($el);
    return $data;
}, 99, 2);

add_action('wp_head', function () {
    if (is_admin() || is_feed()) {
        return;
    }
    if (function_exists('is_page') && is_page('led-ekran')) {
        echo '<style id="ledajans-hide-theme-h1">body.page-id-5001 .page-title,body.page-id-5001 .page-title h1,body.page-id-5001 .gva-breadcrumb-content h1,body.page-id-5001 header.entry-header h1,body.page-id-5001 .breadcrumb-page-title,body.page-id-5001 .title-info > h1.title{display:none!important}</style>' . "\n";
    }
    if (function_exists('wp_is_mobile') && wp_is_mobile() && function_exists('is_page')
        && is_page(array('led-ekran', 'ic-mekan-led-ekran', 'dis-mekan-led-ekran', 'rental-ekran'))) {
        echo '<link rel="preload" as="image" href="https://ledajans.com/wp-content/uploads/2026/09/ic-mekan-led-ekran.webp" fetchpriority="high">' . "\n";
    }
}, 1);

if (!function_exists('ledajans_gsc_support_videos')) {
    function ledajans_gsc_support_videos() {
        return array(
            array(
                'id' => 'gJQv-leg8oc',
                'name' => 'LED Ekran Kurulum Rehberi',
                'description' => 'LED ekran modül bağlantısı, kasa montajı ve ilk çalıştırma adımları.',
                'uploadDate' => '2023-06-15',
            ),
            array(
                'id' => '999EzF8kP6M',
                'name' => 'LED Ekran Bağlantı ve Konfigürasyon',
                'description' => 'Güç kaynağı, veri kablosu ve kontrol kartı bağlantı şeması.',
                'uploadDate' => '2023-07-10',
            ),
            array(
                'id' => 'Vgq50Gu4dWI',
                'name' => 'Huidu Kontrol Kartı Ayarlama',
                'description' => 'Huidu HD serisi kontrol kartlarının kurulumu ve yazılım ayarları.',
                'uploadDate' => '2023-08-01',
            ),
            array(
                'id' => 'aFCCt8OQklY',
                'name' => 'Colorlight Kontrol Kartı Ayarlama',
                'description' => 'Colorlight iLED yazılımı ile LED ekran ölçülendirme ve ayar rehberi.',
                'uploadDate' => '2023-08-20',
            ),
            array(
                'id' => 'puyzg_r1cI0',
                'name' => 'LED Ekran Yazılım Kullanımı',
                'description' => 'HDPlayer ve Colorlight LEDVISION programlarının kullanım rehberi.',
                'uploadDate' => '2023-09-05',
            ),
            array(
                'id' => 'Mh6QUz8r46U',
                'name' => 'LED Ekran Arıza Tespiti',
                'description' => 'Yaygın LED ekran arızaları ve adım adım çözüm yöntemleri.',
                'uploadDate' => '2023-09-22',
            ),
            array(
                'id' => '0Udxlih4HHA',
                'name' => 'LED Modül Değişimi ve Bakım',
                'description' => 'Arızalı LED modül tespiti, sökme-takma ve kalibrasyon işlemleri.',
                'uploadDate' => '2023-10-08',
            ),
            array(
                'id' => 'g5ee8cNIIUs',
                'name' => 'Uzaktan Erişim ve Yönetim',
                'description' => 'Wi-Fi, 4G ve Cloud üzerinden LED ekran uzaktan içerik yönetimi.',
                'uploadDate' => '2023-10-25',
            ),
        );
    }
}

add_action('wp_head', function () {
    if (is_admin() || is_feed() || !function_exists('is_page') || !is_page('teknik-destek-videolari')) {
        return;
    }
    $page_url = home_url('/teknik-destek-videolari/');
    $items = array();
    foreach (ledajans_gsc_support_videos() as $i => $v) {
        $vid = $v['id'];
        $items[] = array(
            '@type' => 'ListItem',
            'position' => $i + 1,
            'item' => array(
                '@type' => 'VideoObject',
                'name' => $v['name'],
                'description' => $v['description'],
                'thumbnailUrl' => 'https://i.ytimg.com/vi/' . $vid . '/hqdefault.jpg',
                'uploadDate' => $v['uploadDate'],
                'embedUrl' => 'https://www.youtube.com/embed/' . $vid,
                'contentUrl' => 'https://www.youtube.com/watch?v=' . $vid,
                'url' => $page_url,
                'publisher' => array(
                    '@type' => 'Organization',
                    'name' => 'LEDAJANS',
                    'url' => home_url('/'),
                ),
            ),
        );
    }
    $payload = array(
        '@context' => 'https://schema.org',
        '@type' => 'ItemList',
        'name' => 'LEDAJANS Teknik Destek Videoları',
        'url' => $page_url,
        'itemListElement' => $items,
    );
    echo '<script type="application/ld+json">' . wp_json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>' . "\n";
}, 20);

add_filter('rank_math/sitemap/entry', function ($url, $type, $object) {
    if (!is_string($type) || stripos($type, 'video') === false) {
        return $url;
    }
    $front = (int) get_option('page_on_front');
    if ($front && is_object($object) && isset($object->ID) && (int) $object->ID === $front) {
        return false;
    }
    return $url;
}, 10, 3);

add_action('template_redirect', function () {
    if (is_admin() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST)) {
        return;
    }
    ob_start(static function ($html) {
        if (!is_string($html) || $html === '') {
            return $html;
        }
        $html = str_replace(
            array(
                '{"@type":"ListItem","position":2,"name":"Kurumsal","item":"#"}',
                '{"@type":"ListItem","position":2,"name":"Teknik Destek","item":"#"}',
            ),
            array(
                '{"@type":"ListItem","position":2,"name":"Kurumsal","item":"https://ledajans.com/hakkimizda/"}',
                '{"@type":"ListItem","position":2,"name":"Teknik Destek","item":"https://ledajans.com/teknik-destek-videolari/"}',
            ),
            $html
        );
        $html = preg_replace('/("item"\s*:\s*)"#"/', '$1"https://ledajans.com/"', $html);
        return $html;
    });
}, 1);

