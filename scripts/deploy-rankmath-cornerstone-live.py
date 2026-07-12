#!/usr/bin/env python3
"""RankMath cornerstone — Code Snippets REST meta endpoint ile canli yaz."""
from __future__ import annotations

import argparse
import os
import sys
import time

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNIPPET_NAME = "LEDAJANS Post Meta REST"
HUB_PAGE_ID = 5557
CORNERSTONE_KEY = "rank_math_pillar_content"
CORNERSTONE_VAL = "on"

SNIPPET_CODE = r"""if (!defined('ABSPATH')) { exit; }

add_action('rest_api_init', static function (): void {
    register_rest_route('ledajans/v1', '/post-meta', array(
        'methods'             => 'POST',
        'permission_callback' => static function () {
            return current_user_can('edit_posts');
        },
        'callback'            => 'ledajans_rest_set_post_meta',
        'args'                => array(
            'post_id'    => array('required' => true, 'type' => 'integer'),
            'meta_key'   => array('required' => true, 'type' => 'string'),
            'meta_value' => array('required' => true, 'type' => 'string'),
        ),
    ));
});

function ledajans_rest_set_post_meta(WP_REST_Request $request) {
    $post_id = (int) $request->get_param('post_id');
    $meta_key = sanitize_key((string) $request->get_param('meta_key'));
    $meta_value = sanitize_text_field((string) $request->get_param('meta_value'));
    if ($post_id <= 0 || $meta_key === '') {
        return new WP_Error('bad_args', 'post_id ve meta_key gerekli', array('status' => 400));
    }
    if (!current_user_can('edit_post', $post_id)) {
        return new WP_Error('forbidden', 'Bu yaziyi duzenleme yetkiniz yok', array('status' => 403));
    }
    update_post_meta($post_id, $meta_key, $meta_value);
    return new WP_REST_Response(array(
        'ok'         => true,
        'post_id'    => $post_id,
        'meta_key'   => $meta_key,
        'meta_value' => get_post_meta($post_id, $meta_key, true),
    ), 200);
}
"""


def load_env() -> tuple[str, str, str]:
    path = os.path.join(ROOT, ".env")
    data: dict[str, str] = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    site = data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
    return site, data.get("WP_USERNAME", ""), data.get("WP_APP_PASSWORD", "").replace(" ", "")


def ensure_snippet(site: str, auth: tuple[str, str]) -> bool:
    headers = {"User-Agent": "LEDAJANS-Post-Meta-REST/1.0"}
    sid = None
    r = requests.get(
        f"{site}/wp-json/code-snippets/v1/snippets",
        auth=auth,
        headers=headers,
        timeout=60,
    )
    if r.status_code == 200:
        for s in r.json():
            if s.get("name") == SNIPPET_NAME:
                sid = int(s["id"])
                break
    payload = {
        "name": SNIPPET_NAME,
        "desc": "REST ile post meta yazimi (RankMath cornerstone vb.)",
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
            headers=headers,
            timeout=60,
        )
    else:
        resp = requests.post(
            f"{site}/wp-json/code-snippets/v1/snippets",
            json=payload,
            auth=auth,
            headers=headers,
            timeout=60,
        )
    if resp.status_code not in (200, 201):
        print(f"HATA snippet: HTTP {resp.status_code} {resp.text[:200]}")
        return False
    print(f"OK snippet id={resp.json().get('id', sid)}")
    return True


def set_cornerstone(site: str, auth: tuple[str, str], apply: bool) -> bool:
    payload = {
        "post_id": HUB_PAGE_ID,
        "meta_key": CORNERSTONE_KEY,
        "meta_value": CORNERSTONE_VAL,
    }
    if not apply:
        print(f"DRY-RUN: post-meta {payload}")
        return True
    for attempt in range(4):
        r = requests.post(
            f"{site}/wp-json/ledajans/v1/post-meta",
            json=payload,
            auth=auth,
            timeout=60,
            headers={"User-Agent": "LEDAJANS-Post-Meta-REST/1.0"},
        )
        if r.status_code == 200:
            body = r.json()
            print(f"OK cornerstone: post_id={body.get('post_id')} value={body.get('meta_value')}")
            return body.get("meta_value") == CORNERSTONE_VAL
        if r.status_code == 404:
            time.sleep(2 * (attempt + 1))
            continue
        print(f"HATA HTTP {r.status_code}: {r.text[:300]}")
        return False
    print("HATA: post-meta endpoint bulunamadi")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    site, user, pw = load_env()
    if not user or not pw:
        print("HATA: .env gerekli")
        return 1
    auth = (user, pw)
    if args.apply and not ensure_snippet(site, auth):
        return 1
    if args.apply:
        time.sleep(2)
    ok = set_cornerstone(site, auth, args.apply)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
