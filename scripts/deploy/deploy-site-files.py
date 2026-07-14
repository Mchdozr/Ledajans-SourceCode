#!/usr/bin/env python3
"""robots.txt + mu-plugin canli yazim (ledajans/v1/write-files REST)."""
from __future__ import annotations

from pathlib import Path
import sys

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from lib.repo_paths import ROOT, CONTENT, OPS, OPS_WORDPRESS, OPS_NGINX, DATA, DATA_BASELINES, AGENT_HUB, content_path, data_path
import argparse
import base64
import os
import sys
import time

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

SNIPPET_NAME = "LEDAJANS Write Site Files REST"
CRITICAL_CSS_PLACEHOLDER = "__LEDAJANS_MOBILE_CRITICAL_CSS_B64__"
MENU_CSS_PLACEHOLDER = "__LEDAJANS_MOBILE_MENU_CSS_B64__"
SNIPPET_CODE = r"""if (!defined('ABSPATH')) { exit; }

add_action('rest_api_init', static function (): void {
    register_rest_route('ledajans/v1', '/write-files', array(
        'methods'             => 'POST',
        'permission_callback' => static function () {
            return current_user_can('manage_options');
        },
        'callback'            => 'ledajans_rest_write_site_files',
        'args'                => array(
            'robots_b64' => array('required' => false, 'type' => 'string'),
            'mu_b64'     => array('required' => false, 'type' => 'string'),
        ),
    ));
});

function ledajans_rest_write_site_files(WP_REST_Request $request) {
    $written = array();
    $robots = $request->get_param('robots_b64');
    if (is_string($robots) && $robots !== '') {
        $body = base64_decode($robots, true);
        if (!is_string($body) || $body === '') {
            return new WP_Error('bad_robots', 'robots decode failed', array('status' => 400));
        }
        if (false === file_put_contents(ABSPATH . 'robots.txt', $body)) {
            return new WP_Error('robots_write', 'robots.txt yazilamadi', array('status' => 500));
        }
        $written[] = 'robots.txt';
    }
    $mu = $request->get_param('mu_b64');
    if (is_string($mu) && $mu !== '') {
        $body = base64_decode($mu, true);
        if (!is_string($body) || $body === '') {
            return new WP_Error('bad_mu', 'mu-plugin decode failed', array('status' => 400));
        }
        $dir = WP_CONTENT_DIR . '/mu-plugins';
        if (!is_dir($dir)) {
            wp_mkdir_p($dir);
        }
        $path = $dir . '/ledajans-perf-patch.php';
        if (false === file_put_contents($path, $body)) {
            return new WP_Error('mu_write', 'mu-plugin yazilamadi', array('status' => 500));
        }
        $written[] = 'mu-plugin';
    }
    if (function_exists('w3tc_flush_all')) { w3tc_flush_all(); }
    if (function_exists('litespeed_purge_all')) { litespeed_purge_all(); }
    wp_cache_flush();
    do_action('w3tc_flush_all');
    do_action('litespeed_purge_all');
    return new WP_REST_Response(array('ok' => true, 'written' => $written), 200);
}
"""


def load_env() -> tuple[str, str, str]:
    path = ROOT / ".env"
    data: dict[str, str] = {}
    if path.is_file():
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    user = data.get("WP_USERNAME", "")
    pw = data.get("WP_APP_PASSWORD", "").replace(" ", "")
    return site, user, pw


def read_b64_file(path: Path) -> str:
    with path.open("rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def read_mu_b64() -> str:
    mu_path = OPS_WORDPRESS / "mobil-hiz-patch.php"
    css_path = OPS_WORDPRESS / "mobile-critical-theme.css"
    menu_css_path = OPS_WORDPRESS / "mobile-menu.css"
    hero_path = OPS / "assets" / "ldajsn2-mobile-q42-768x375.webp"
    mu_source = mu_path.read_text(encoding="utf-8")
    if mu_source.count(CRITICAL_CSS_PLACEHOLDER) != 1:
        raise RuntimeError("Mobil kritik CSS placeholder tekil olmali")
    if mu_source.count(MENU_CSS_PLACEHOLDER) != 1:
        raise RuntimeError("Mobil menu CSS placeholder tekil olmali")
    hero_b64 = base64.b64encode(hero_path.read_bytes()).decode("ascii")
    css_source = css_path.read_text(encoding="utf-8")
    css_source += (
        "\n@media (max-width:768px){"
        ".ledajans-hero-bg-mobile{"
        f'background-image:url("data:image/webp;base64,{hero_b64}");'
        "background-size:cover;background-position:center}"
        ".ledajans-mobile-hero-accessible{display:block;width:100%;height:100%}"
        "}\n"
    )
    css_b64 = base64.b64encode(css_source.encode("utf-8")).decode("ascii")
    menu_css_b64 = base64.b64encode(menu_css_path.read_bytes()).decode("ascii")
    rendered = mu_source.replace(CRITICAL_CSS_PLACEHOLDER, css_b64).replace(
        MENU_CSS_PLACEHOLDER, menu_css_b64
    )
    return base64.b64encode(rendered.encode("utf-8")).decode("ascii")


def ensure_snippet(site: str, auth: tuple[str, str]) -> bool:
    sid = 16  # LEDAJANS Write Site Files REST (sabit id, list 403 olabilir)
    r = requests.get(
        f"{site}/wp-json/code-snippets/v1/snippets",
        auth=auth,
        timeout=30,
        headers={"User-Agent": "LEDAJANS-Site-Files/1.0"},
    )
    if r.status_code == 200:
        sid = None
        for s in r.json():
            if s.get("name") == SNIPPET_NAME:
                sid = int(s["id"])
                break
    payload = {
        "name": SNIPPET_NAME,
        "desc": "REST ile robots.txt + mu-plugin yazimi",
        "code": SNIPPET_CODE,
        "scope": "global",
        "active": True,
        "priority": 1,
    }
    if sid:
        resp = requests.put(
            f"{site}/wp-json/code-snippets/v1/snippets/{sid}",
            json=payload,
            auth=auth,
            timeout=60,
        )
    else:
        resp = requests.post(
            f"{site}/wp-json/code-snippets/v1/snippets",
            json=payload,
            auth=auth,
            timeout=60,
        )
    return resp.status_code in (200, 201)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1

    auth = (user, pw)
    robots_b64 = read_b64_file(OPS / "robots.txt")
    mu_b64 = read_mu_b64()

    if not args.apply:
        print("DRY-RUN: write-files REST ile robots + mu-plugin")
        return 0

    if not ensure_snippet(site, auth):
        print("UYARI: snippet guncellenemedi — write-files deneniyor.")

    print("write-files deneniyor...")
    time.sleep(2)

    retry_delays = [4, 8, 16, 32]
    for attempt, retry_delay in enumerate(retry_delays, start=1):
        r = requests.post(
            f"{site}/wp-json/ledajans/v1/write-files",
            json={"robots_b64": robots_b64, "mu_b64": mu_b64},
            auth=auth,
            timeout=120,
            headers={"User-Agent": "LEDAJANS-Site-Files/1.0"},
        )
        if r.status_code == 200:
            print("OK:", r.json())
            break
        if r.status_code in (403, 404, 429, 502, 503, 504):
            print(f"UYARI {r.status_code}: tekrar {attempt}/4 ({retry_delay}s)")
            time.sleep(retry_delay)
            continue
        print(f"HATA {r.status_code}: {r.text[:400]}")
        return 1
    else:
        print("HATA: write-files endpoint yok")
        return 1

    time.sleep(2)
    desktop_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
    rb = requests.get(
        f"{site}/robots.txt",
        timeout=20,
        headers={"User-Agent": desktop_ua},
    )
    crawl = rb.status_code == 200 and "Disallow: /*?s=" in rb.text
    mobile_ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
        "Mobile/15E148 Safari/604.1"
    )
    verify_stamp = int(time.time())
    requests.get(
        f"{site}/?ledajans-cwv-activate={verify_stamp}",
        timeout=60,
        headers={"User-Agent": desktop_ua},
    )
    home = requests.get(
        f"{site}/?ledajans-cwv-check={verify_stamp}",
        timeout=60,
        headers={"User-Agent": mobile_ua},
    )
    mu_ok = (
        home.status_code == 200
        and "ledajans-mobile-font-fallback" in home.text
        and "ledajans-mobile-critical-theme" in home.text
        and "ledajans-mobile-critical-iter9.css" in home.text
        and "ledajans-mobile-menu" in home.text
        and "ledajans-mobile-menu.css" in home.text
        and "ledajans-mobile-menu-fallback" in home.text
        and "ledajans-mobile-hero-accessible" in home.text
    )
    inner = requests.get(
        f"{site}/led-ekran/?ledajans-cwv-check={verify_stamp}",
        timeout=60,
        headers={"User-Agent": mobile_ua},
    )
    menu_all_pages_ok = (
        inner.status_code == 200
        and "ledajans-mobile-menu.css" in inner.text
        and "ledajans-mobile-menu-fallback" in inner.text
    )
    print(f"robots crawl kurallari: {'OK' if crawl else 'EKSIK'}")
    print(f"mu-plugin guncel: {'OK' if mu_ok else 'EKSIK'}")
    print(f"mobil menu tum sayfalar: {'OK' if menu_all_pages_ok else 'EKSIK'}")
    return 0 if crawl and mu_ok and menu_all_pages_ok else 1


if __name__ == "__main__":
    sys.exit(main())
