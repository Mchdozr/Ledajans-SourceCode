<?php
/**
 * Plugin Name: LEDAJANS REST Auth Header
 * Description: Plesk/nginx Authorization basligini PHP'ye geri yazar; REST Basic Auth (hesap veya uygulama sifresi) calisir.
 * Version: 1.0.0
 * Author: LEDAJANS
 */

if (!defined('ABSPATH')) {
    exit;
}

function ledajans_rest_auth_restore_basic() {
    if (!empty($_SERVER['PHP_AUTH_USER'])) {
        return;
    }

    $header = '';
    foreach (array(
        'HTTP_AUTHORIZATION',
        'REDIRECT_HTTP_AUTHORIZATION',
        'REDIRECT_REDIRECT_HTTP_AUTHORIZATION',
        'HTTP_X_WP_AUTHORIZATION',
        'HTTP_X_AUTHORIZATION',
    ) as $key) {
        if (!empty($_SERVER[$key])) {
            $header = (string) $_SERVER[$key];
            break;
        }
    }

    if ($header === '' || stripos($header, 'basic ') !== 0) {
        return;
    }

    $decoded = base64_decode(substr($header, 6), true);
    if ($decoded === false || strpos($decoded, ':') === false) {
        return;
    }

    list($auth_user, $auth_pass) = explode(':', $decoded, 2);
    $_SERVER['PHP_AUTH_USER'] = $auth_user;
    $_SERVER['PHP_AUTH_PW'] = $auth_pass;
}

ledajans_rest_auth_restore_basic();
add_action('plugins_loaded', 'ledajans_rest_auth_restore_basic', 0);

function ledajans_rest_auth_is_api_request() {
    if (defined('REST_REQUEST') && REST_REQUEST) {
        return true;
    }
    $uri = isset($_SERVER['REQUEST_URI']) ? (string) wp_unslash($_SERVER['REQUEST_URI']) : '';
    if ($uri !== '' && strpos($uri, '/wp-json/') !== false) {
        return true;
    }
    return !empty($_GET['rest_route']);
}

add_filter('determine_current_user', function ($user_id) {
    if ($user_id || !ledajans_rest_auth_is_api_request()) {
        return $user_id;
    }
    if (empty($_SERVER['PHP_AUTH_USER']) || !isset($_SERVER['PHP_AUTH_PW'])) {
        return $user_id;
    }

    static $running = false;
    if ($running) {
        return $user_id;
    }
    $running = true;
    $user = wp_authenticate($_SERVER['PHP_AUTH_USER'], $_SERVER['PHP_AUTH_PW']);
    $running = false;

    if (is_wp_error($user)) {
        return $user_id;
    }
    return (int) $user->ID;
}, 21);
