#!/usr/bin/env python3
"""Site geneli footer: Elementor snippet (body_end) + eski #wp-footer gizle."""
from __future__ import annotations

import json
import sys
import time
import xmlrpc.client
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
FOOTER_FILE = ROOT / "Footer" / "footer.html"
MARKER = "ledajans-footer"
SNIPPET_SLUG = "ledajans-footer-2026"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
BACKUP_DIR = ROOT / "AGENT-HUB" / "BACKUPS"

HIDE_OLD = """<style id="ledajans-hide-old-footer">
#wp-footer { display: none !important; }
</style>
"""


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip("\"'")
    return (
        data.get("WP_SITE_URL", "https://ledajans.com").rstrip("/"),
        data["WP_USERNAME"],
        data["WP_APP_PASSWORD"].replace(" ", ""),
    )


def load_code() -> str:
    html = FOOTER_FILE.read_text(encoding="utf-8")
    if MARKER not in html:
        raise SystemExit("HATA: Footer/footer.html gecersiz")
    return HIDE_OLD + html


def main() -> int:
    apply = "--apply" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    code = load_code()
    print("code_bytes", len(code))

    r = requests.get(
        f"{site}/wp-json/wp/v2/elementor_snippet",
        params={"slug": SNIPPET_SLUG, "context": "edit", "per_page": 20},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    existing = r.json() if r.status_code == 200 else []
    if not isinstance(existing, list):
        existing = []
    print("existing_snippets", [(x.get("id"), x.get("slug"), x.get("status")) for x in existing])

    live = requests.get(
        site + "/",
        headers={"User-Agent": "Mozilla/5.0 (iPhone)", "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    print("live_new_marker", MARKER in live)
    print("live_old_2024", "2024 Ledajans" in live)

    if not apply:
        print("DRY_RUN: yazilmadi — --apply ile elementor_snippet publish")
        return 0

    payload = {
        "title": "LEDAJANS Footer",
        "slug": SNIPPET_SLUG,
        "status": "publish",
        "meta": {
            "_elementor_location": "elementor_body_end",
            "_elementor_priority": 1,
            "_elementor_code": code,
        },
    }

    if existing:
        sid = existing[0]["id"]
        ru = requests.post(
            f"{site}/wp-json/wp/v2/elementor_snippet/{sid}",
            json=payload,
            auth=auth,
            headers=headers,
            timeout=180,
        )
        print("snippet_update", sid, ru.status_code, (ru.text or "")[:220].replace("\n", " "))
    else:
        ru = requests.post(
            f"{site}/wp-json/wp/v2/elementor_snippet",
            json=payload,
            auth=auth,
            headers=headers,
            timeout=180,
        )
        print("snippet_create", ru.status_code, (ru.text or "")[:220].replace("\n", " "))
        if ru.status_code not in (200, 201):
            return 1
        sid = ru.json().get("id")

    if not sid:
        print("HATA: snippet id yok")
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    note = BACKUP_DIR / "2026-09-11-footer-snippet.json"
    note.write_text(
        json.dumps({"id": sid, "slug": SNIPPET_SLUG, "location": "elementor_body_end"}, indent=2),
        encoding="utf-8",
    )

    wp = xmlrpc.client.ServerProxy(f"{site}/xmlrpc.php", allow_none=True)
    try:
        wp.wp.editPost(
            0,
            user,
            pw,
            int(sid),
            {
                "post_status": "publish",
                "custom_fields": [
                    {"key": "_elementor_conditions", "value": ["include/general"]},
                ],
            },
        )
        print("conditions_xmlrpc_ok")
    except Exception as exc:
        print("conditions_xmlrpc", type(exc).__name__, str(exc)[:200])
        try:
            wp.wp.editPost(
                0,
                user,
                pw,
                int(sid),
                {
                    "custom_fields": [
                        {
                            "key": "_elementor_conditions",
                            "value": 'a:1:{i:0;s:16:"include/general";}',
                        },
                    ],
                },
            )
            print("conditions_xmlrpc_serialized_ok")
        except Exception as exc2:
            print("conditions_xmlrpc2", type(exc2).__name__, str(exc2)[:200])

    rc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers=headers,
        timeout=60,
    )
    print("elementor_cache_del", rc.status_code)

    time.sleep(2)
    live2 = requests.get(
        site + "/?nocache=" + str(int(time.time())),
        headers={"User-Agent": "Mozilla/5.0 (iPhone)", "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    checks = {
        MARKER: MARKER in live2,
        "hide_css": "ledajans-hide-old-footer" in live2,
        "Hızlı Linkler": "Hızlı Linkler" in live2,
        "old_visible_class": 'class="footer-main"' in live2,
    }
    print("verify", checks)
    # old footer HTML may still exist but hidden; new marker must be present
    return 0 if checks[MARKER] and checks["Hızlı Linkler"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
