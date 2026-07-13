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
    if (function_exists('litespeed_purge_all')) { litespeed_purge_all(); }
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
    mu_b64 = read_b64_file(OPS_WORDPRESS / "mobil-hiz-patch.php")

    if not args.apply:
        print("DRY-RUN: write-files REST ile robots + mu-plugin")
        return 0

    if not ensure_snippet(site, auth):
        print("UYARI: snippet guncellenemedi — write-files deneniyor.")

    print("write-files deneniyor...")
    time.sleep(2)

    for attempt in range(4):
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
        if r.status_code == 404:
            time.sleep(3)
            continue
        print(f"HATA {r.status_code}: {r.text[:400]}")
        return 1
    else:
        print("HATA: write-files endpoint yok")
        return 1

    time.sleep(2)
    rb = requests.get(f"{site}/robots.txt", timeout=20)
    crawl = "Disallow: /*?s=" in rb.text
    mu = requests.get(f"{site}/wp-content/mu-plugins/ledajans-perf-patch.php", timeout=20)
    mu_ok = mu.status_code == 200 and "ledajans_is_lcp_critical_page" in mu.text
    print(f"robots crawl kurallari: {'OK' if crawl else 'EKSIK'}")
    print(f"mu-plugin guncel: {'OK' if mu_ok else 'EKSIK'}")
    return 0 if crawl and mu_ok else 1


if __name__ == "__main__":
    sys.exit(main())
