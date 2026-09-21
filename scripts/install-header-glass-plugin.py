#!/usr/bin/env python3
"""LEDAJANS Header Glass eklentisini gunceller (plugin-editor, yoksa zip)."""
from __future__ import annotations

import io
import os
import re
import sys
import zipfile

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LEDAJANS-Install-Header-Glass/1.1"
PLUGIN = "ledajans-header-glass/ledajans-header-glass.php"
SLUG = "ledajans-header-glass"


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


def editor_update(s: requests.Session, site: str) -> bool:
    url = (
        f"{site}/wp-admin/plugin-editor.php"
        f"?file={PLUGIN.replace('/', '%2F')}&plugin={PLUGIN.replace('/', '%2F')}"
    )
    page = s.get(url, timeout=30)
    if page.status_code != 200 or "newcontent" not in page.text:
        print("editor_skip", page.status_code)
        return False
    nonce = re.search(r'name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce:
        print("editor_skip nonce yok")
        return False
    r = s.post(
        f"{site}/wp-admin/plugin-editor.php",
        data={
            "_wpnonce": nonce.group(1),
            "_wp_http_referer": f"/wp-admin/plugin-editor.php?file={PLUGIN}&plugin={PLUGIN}",
            "newcontent": source(),
            "action": "update",
            "file": PLUGIN,
            "plugin": PLUGIN,
            "submit": "Güncelle",
        },
        timeout=60,
        allow_redirects=True,
    )
    ok = r.status_code == 200 and (
        "File edited successfully" in r.text
        or "Dosya başarıyla düzenlendi" in r.text
        or "updated" in r.text.lower()
        or "1.1.0" in r.text
    )
    print("editor", r.status_code, "ok" if ok else "maybe")
    return ok


def activate_if_needed(s: requests.Session, site: str) -> None:
    pl = s.get(f"{site}/wp-admin/plugins.php", timeout=30)
    deact = re.search(
        rf'href="(plugins\.php\?action=deactivate[^"]*{SLUG}[^"]*)"',
        pl.text,
    )
    if deact:
        print("already_active")
        return
    act = re.search(
        rf'href="(plugins\.php\?action=activate[^"]*{SLUG}[^"]*)"',
        pl.text,
    )
    if not act:
        print("HATA: activate link yok")
        return
    href = f"{site}/wp-admin/" + act.group(1).replace("&amp;", "&")
    s.get(href, timeout=60, allow_redirects=True)
    print("activated")


def delete_plugin(s: requests.Session, site: str) -> None:
    pl = s.get(f"{site}/wp-admin/plugins.php", timeout=30)
    deact = re.search(
        rf'href="(plugins\.php\?action=deactivate[^"]*{SLUG}[^"]*)"',
        pl.text,
    )
    if deact:
        href = f"{site}/wp-admin/" + deact.group(1).replace("&amp;", "&")
        s.get(href, timeout=60, allow_redirects=True)
        pl = s.get(f"{site}/wp-admin/plugins.php", timeout=30)
        print("deactivated")
    delete = re.search(
        rf'href="(plugins\.php\?action=delete-selected[^"]*{SLUG}[^"]*)"',
        pl.text,
    )
    if not delete:
        delete = re.search(
            rf'href="(plugins\.php\?action=delete-selected[^"]*plugin_status[^"]*)"',
            pl.text,
        )
    nonce_page = s.get(
        f"{site}/wp-admin/plugins.php?action=delete-selected"
        f"&checked%5B0%5D={PLUGIN}&plugin_status=all&paged=1&s=",
        timeout=30,
        allow_redirects=True,
    )
    nonce = re.search(r'name="_wpnonce" value="([^"]+)"', nonce_page.text)
    verify = re.search(r'name="verify-delete" value="1"', nonce_page.text)
    if nonce:
        s.post(
            f"{site}/wp-admin/plugins.php",
            data={
                "_wpnonce": nonce.group(1),
                "_wp_http_referer": "/wp-admin/plugins.php",
                "checked[]": PLUGIN,
                "action": "delete-selected",
                "verify-delete": "1",
                "submit": "Evet, bu dosyaları sil",
            },
            timeout=60,
            allow_redirects=True,
        )
        print("deleted")
    elif delete:
        href = f"{site}/wp-admin/" + delete.group(1).replace("&amp;", "&")
        s.get(href, timeout=60, allow_redirects=True)
        print("deleted_link")
    else:
        print("delete_skip", bool(verify))


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
    print("upload", r.status_code)
    ok = "Eklenti kuruldu" in r.text or "Plugin installed" in r.text
    if not ok:
        print(re.sub("<[^>]+>", " ", r.text)[:240])
    return ok


def main() -> int:
    site, user, pw = load_env()
    if not site or not user or not pw:
        print("HATA: WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD gerekli")
        return 1

    s = login(site, user, pw)
    if editor_update(s, site):
        activate_if_needed(s, site)
        return 0

    print("editor basarisiz, zip ile yeniden kur")
    delete_plugin(s, site)
    if not upload_zip(s, site):
        return 1
    activate_if_needed(s, site)
    return 0


if __name__ == "__main__":
    sys.exit(main())
