<?php
/**
 * Plugin Name: LEDAJANS Deployer (gecici)
 * Description: Tek seferlik dosya dagitimi (scripts/deploy-lcp-images.py). Etkinlestirilince payload'i yerine kopyalar, eski dosyalarin yedegini alir. Is bitince betik eklentiyi siler.
 * Version: 1.0.0
 * Author: LEDAJANS
 */

if (!defined('ABSPATH')) {
    exit;
}

register_activation_hook(__FILE__, 'ledajans_deployer_run');

function ledajans_deployer_mu_target() {
    $dir = defined('WPMU_PLUGIN_DIR') ? WPMU_PLUGIN_DIR : WP_CONTENT_DIR . '/mu-plugins';
    foreach ((array) glob(rtrim($dir, '/') . '/*.php') as $f) {
        $c = @file_get_contents($f);
        if (is_string($c) && strpos($c, 'function ledajans_mp_v11_active') !== false) {
            return $f;
        }
    }
    return rtrim($dir, '/') . '/ledajans-perf-patch.php';
}

function ledajans_deployer_dest($dest) {
    $up = wp_upload_dir(null, false);
    $ub = rtrim($up['basedir'], '/');
    if (strpos($dest, 'uploads/') === 0) {
        $rel = substr($dest, 8);
        if (strpos($rel, '..') !== false) {
            return '';
        }
        return $ub . '/' . $rel;
    }
    if ($dest === 'mu:auto') {
        return ledajans_deployer_mu_target();
    }
    return '';
}

function ledajans_deployer_run() {
    $m = json_decode((string) @file_get_contents(__DIR__ . '/manifest.json'), true);
    if (!is_array($m) || empty($m['tag'])) {
        update_option('ledajans_deployer_result', array('error' => 'manifest yok'), false);
        return;
    }
    $up = wp_upload_dir(null, false);
    $bk = rtrim($up['basedir'], '/') . '/ledajans-backup/' . preg_replace('/[^A-Za-z0-9_-]/', '', $m['tag']);
    $createdKey = 'ledajans_deployer_created_' . md5($m['tag']);
    $created = (array) get_option($createdKey, array());
    $res = array('tag' => $m['tag'], 'part' => $m['part'], 'mode' => $m['mode'], 'ok' => array(), 'err' => array(), 'backup' => array(), 'restored' => array(), 'removed' => array());

    if ($m['mode'] === 'rollback') {
        $map = (array) get_option('ledajans_deployer_map_' . md5($m['tag']), array());
        foreach ($map as $target => $backup) {
            if ($backup !== '' && is_file($backup)) {
                if (@copy($backup, $target)) {
                    $res['restored'][] = $target;
                } else {
                    $res['err'][] = 'restore ' . $target;
                }
            }
        }
        foreach ($created as $target) {
            if (is_file($target) && @unlink($target)) {
                $res['removed'][] = $target;
            }
        }
        update_option('ledajans_deployer_result', $res, false);
        return;
    }

    $map = (array) get_option('ledajans_deployer_map_' . md5($m['tag']), array());
    foreach ((array) $m['files'] as $f) {
        $src = __DIR__ . '/' . $f['src'];
        $target = ledajans_deployer_dest($f['dest']);
        if ($target === '' || !is_file($src)) {
            $res['err'][] = 'gecersiz ' . $f['dest'];
            continue;
        }
        if (!is_dir(dirname($target)) && !wp_mkdir_p(dirname($target))) {
            $res['err'][] = 'mkdir ' . dirname($target);
            continue;
        }
        if (is_file($target)) {
            if (!isset($map[$target])) {
                $b = $bk . '/' . md5($target) . '-' . basename($target);
                wp_mkdir_p($bk);
                if (@copy($target, $b)) {
                    $map[$target] = $b;
                    $res['backup'][] = $target;
                } else {
                    $res['err'][] = 'yedek ' . $target;
                    continue; // yedeksiz ustune yazma
                }
            }
        } else {
            if (!in_array($target, $created, true)) {
                $created[] = $target;
            }
        }
        $tmp = $target . '.ldj-tmp';
        if (@copy($src, $tmp) && @rename($tmp, $target)) {
            $res['ok'][] = $f['dest'] === 'mu:auto' ? 'mu:' . $target : $f['dest'];
        } else {
            @unlink($tmp);
            $res['err'][] = 'yaz ' . $f['dest'];
        }
    }
    update_option('ledajans_deployer_map_' . md5($m['tag']), $map, false);
    update_option($createdKey, $created, false);
    update_option('ledajans_deployer_result', $res, false);
    if (function_exists('opcache_invalidate')) {
        @opcache_invalidate(ledajans_deployer_mu_target(), true);
    }
}

add_action('rest_api_init', function () {
    register_rest_route('ledajans-deploy/v1', '/result', array(
        'methods'             => 'GET',
        'permission_callback' => function () {
            return current_user_can('manage_options');
        },
        'callback'            => function () {
            return get_option('ledajans_deployer_result');
        },
    ));
});
