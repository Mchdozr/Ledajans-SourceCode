// Code Snippets: "LEDAJANS Projeler LCP" — PHP snippet, Run everywhere
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

add_action('wp_enqueue_scripts', function () {
    if (is_admin() || !ledajans_is_projeler_page()) {
        return;
    }

    $dropStyles = ['contact-form-7', 'chaty-front', 'chaty', 'elementor-icons', 'elementor-animations'];
    foreach ($dropStyles as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }

    foreach (['chaty', 'chaty-front-js'] as $handle) {
        wp_dequeue_script($handle);
        wp_deregister_script($handle);
    }

    global $wp_styles;
    if (empty($wp_styles) || empty($wp_styles->queue)) {
        return;
    }

    $needles = ['/contact-form-7/', '/chaty/', '/widget-icon-list', '/widget-icon-box', '/widget-social-icons'];
    foreach ((array) $wp_styles->queue as $handle) {
        if (empty($wp_styles->registered[$handle]->src)) {
            continue;
        }
        $src = (string) $wp_styles->registered[$handle]->src;
        foreach ($needles as $needle) {
            if (stripos($src, trim($needle, '/')) !== false) {
                wp_dequeue_style($handle);
                wp_deregister_style($handle);
                break;
            }
        }
    }
}, 250);

add_filter('wp_resource_hints', function ($urls, $relation_type) {
    if ('preconnect' !== $relation_type || !ledajans_is_projeler_page()) {
        return $urls;
    }
    return array_values(array_filter($urls, function ($url) {
        return stripos($url, 'googletagmanager.com') === false
            && stripos($url, 'google-analytics.com') === false;
    }));
}, 99, 2);

add_action('wp_head', function () {
    if (is_admin() || !ledajans_is_projeler_page()) {
        return;
    }
    echo "<script>document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('link[rel=\"preload\"][href*=\"fonts.googleapis.com\"]').forEach(function(n){n.remove();});});</script>\n";
}, 99);
