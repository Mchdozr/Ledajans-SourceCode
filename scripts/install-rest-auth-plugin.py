#!/usr/bin/env python3
"""LEDAJANS REST Auth Header eklentisini wp-admin zip ile yukler ve etkinlestirir."""
from __future__ import annotations

import io
import os
import re
import sys
import zipfile

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Install-REST-Auth/1.1"
PLUGIN = "ledajans-rest-auth-header/ledajans-rest-auth-header.php"


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
    site = (data.get("WP_SITE_URL") or os.environ.get("WP_SITE_URL") or "").rstrip("/")
    user = data.get("WP_USERNAME") or os.environ.get("WP_USERNAME") or ""
    pw = (data.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")
    return site, user, pw


def make_zip() -> bytes:
    src = os.path.join(ROOT, "wordpress-rest-auth-header.php")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src, PLUGIN)
    return buf.getvalue()


def login(site: str, user: str, pw: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    s.get(f"{site}/wp-login.php", timeout=30)
    r = s.post(
        f"{site}/wp-login.php",
        data={
            "log": user,
            "pwd": pw,
            "wp-submit": "Log In",
            "redirect_to": f"{site}/wp-admin/",
            "testcookie": "1",
        },
        timeout=30,
        allow_redirects=True,
    )
    if "wp-admin" not in r.url:
        print("HATA: wp-login basarisiz")
        sys.exit(1)
    return s


def main() -> int:
    site, user, pw = load_env()
    if not site or not user or not pw:
        print("HATA: WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD gerekli")
        return 1

    s = login(site, user, pw)
    plugins_page = s.get(f"{site}/wp-admin/plugins.php", timeout=30)
    if PLUGIN in plugins_page.text:
        deact = re.search(
            r'href="(plugins\.php\?action=deactivate[^"]*ledajans-rest-auth-header[^"]*)"',
            plugins_page.text,
        )
        if deact:
            print("already_active")
            return 0
        act = re.search(
            r'href="(plugins\.php\?action=activate[^"]*ledajans-rest-auth-header[^"]*)"',
            plugins_page.text,
        )
        if act:
            href = f"{site}/wp-admin/" + act.group(1).replace("&amp;", "&")
            s.get(href, timeout=60, allow_redirects=True)
            print("activated_existing")
            return 0

    page = s.get(f"{site}/wp-admin/plugin-install.php?tab=upload", timeout=30)
    nonce_m = re.search(r'id="_wpnonce" name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce_m:
        nonce_m = re.search(r'name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce_m:
        print("HATA: upload nonce yok")
        return 1

    r = s.post(
        f"{site}/wp-admin/update.php?action=upload-plugin",
        data={
            "_wpnonce": nonce_m.group(1),
            "_wp_http_referer": "/wp-admin/plugin-install.php?tab=upload",
            "install-plugin-submit": "Install Now",
        },
        files={"pluginzip": ("ledajans-rest-auth-header.zip", make_zip(), "application/zip")},
        timeout=120,
        allow_redirects=True,
    )
    print("upload", r.status_code)
    if "Eklenti kuruldu" not in r.text and "Plugin installed" not in r.text:
        print("HATA: kurulum sayfasi beklenen degil")
        print(re.sub("<[^>]+>", " ", r.text)[:240])
        return 1

    pl = s.get(f"{site}/wp-admin/plugins.php", timeout=30)
    act = re.search(
        r'href="(plugins\.php\?action=activate[^"]*ledajans-rest-auth-header[^"]*)"',
        pl.text,
    )
    deact = re.search(
        r'href="(plugins\.php\?action=deactivate[^"]*ledajans-rest-auth-header[^"]*)"',
        pl.text,
    )
    if deact:
        print("active")
        return 0
    if not act:
        print("HATA: activate link yok")
        return 1
    href = f"{site}/wp-admin/" + act.group(1).replace("&amp;", "&")
    s.get(href, timeout=60, allow_redirects=True)
    print("activated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
