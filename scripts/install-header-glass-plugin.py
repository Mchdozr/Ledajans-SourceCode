#!/usr/bin/env python3
"""LEDAJANS Header Glass eklentisini REST sil + zip + activate ile gunceller."""
from __future__ import annotations

import io
import os
import re
import sys
import zipfile

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Install-Header-Glass/1.2"
PLUGIN = "ledajans-header-glass/ledajans-header-glass.php"
REST_PLUGIN = "ledajans-header-glass/ledajans-header-glass"


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


def source() -> str:
    path = os.path.join(ROOT, "wordpress-header-glass.php")
    with open(path, encoding="utf-8") as f:
        return f.read()


def make_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(PLUGIN, source())
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


def rest_delete(site: str, auth: tuple[str, str]) -> None:
    r = requests.delete(
        f"{site}/wp-json/wp/v2/plugins/{REST_PLUGIN}",
        auth=auth,
        headers={"User-Agent": UA},
        params={"force": "true"},
        timeout=60,
    )
    print("rest_delete", r.status_code)


def rest_activate(site: str, auth: tuple[str, str]) -> bool:
    r = requests.post(
        f"{site}/wp-json/wp/v2/plugins/{REST_PLUGIN}",
        json={"status": "active"},
        auth=auth,
        headers={"User-Agent": UA, "Content-Type": "application/json"},
        timeout=60,
    )
    print("rest_activate", r.status_code)
    return r.status_code in (200, 201)


def upload_zip(s: requests.Session, site: str) -> bool:
    page = s.get(f"{site}/wp-admin/plugin-install.php?tab=upload", timeout=30)
    nonce_m = re.search(r'id="_wpnonce" name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce_m:
        nonce_m = re.search(r'name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce_m:
        print("HATA: upload nonce yok")
        return False
    r = s.post(
        f"{site}/wp-admin/update.php?action=upload-plugin",
        data={
            "_wpnonce": nonce_m.group(1),
            "_wp_http_referer": "/wp-admin/plugin-install.php?tab=upload",
            "install-plugin-submit": "Install Now",
        },
        files={"pluginzip": ("ledajans-header-glass.zip", make_zip(), "application/zip")},
        timeout=120,
        allow_redirects=True,
    )
    ok = "Eklenti kuruldu" in r.text or "Plugin installed" in r.text
    print("upload", r.status_code, "ok" if ok else "fail")
    if not ok:
        print(re.sub("<[^>]+>", " ", r.text)[:240])
    return ok


def main() -> int:
    site, user, pw = load_env()
    if not site or not user or not pw:
        print("HATA: WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD gerekli")
        return 1
    auth = (user, pw)
    rest_delete(site, auth)
    s = login(site, user, pw)
    if not upload_zip(s, site):
        return 1
    if not rest_activate(site, auth):
        return 1
    ver = requests.get(
        f"{site}/wp-json/wp/v2/plugins/{REST_PLUGIN}",
        auth=auth,
        headers={"User-Agent": UA},
        timeout=30,
    )
    print("plugin", ver.status_code, ver.text[:180].replace("\n", " "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
