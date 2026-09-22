#!/usr/bin/env python3
"""Üst menü logosunu WebP olarak yükle ve header şablon 43 / widget c7f7f5c güncelle."""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_PNG_CANDIDATES = [
    Path("/home/ubuntu/.cursor/projects/workspace/assets/f750ac1b-21ba-4cbb-b2d4-49ad30a29d0b.png"),
    ROOT / "Ust-Menu" / "ledajans-ust-menu-logo-source.png",
]
LOCAL_WEBP = ROOT / "Ust-Menu" / "ledajans-ust-menu-logo.webp"
HEADER_HTML = ROOT / "Ust-Menu" / "ust-menu.html"
PLUGIN_PHP = ROOT / "wordpress-header-logo-filter.php"
PLUGIN_SLUG = "ledajans-header-logo-filter/ledajans-header-logo-filter.php"
REST_PLUGIN = "ledajans-header-logo-filter/ledajans-header-logo-filter"
FILENAME = "ledajans-ust-menu-logo.webp"
HEADER_ID = 43
WIDGET_ID = "c7f7f5c"
UA = "LEDAJANS-Header-Logo/1.0"
OLD_LOGO_FILES = (
    "logo-scaled.png",
    "LedajansLogo.png",
    "ledajans-logo-web.jpg",
)
INVERT_OLD = "filter: brightness(0) invert(1) !important;"
INVERT_NEW = "filter: none !important;"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    env_path = ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip("\"'")
    site = (data.get("WP_SITE_URL") or os.environ.get("WP_SITE_URL") or "").rstrip("/")
    user = data.get("WP_USERNAME") or os.environ.get("WP_USERNAME") or ""
    password = (data.get("WP_APP_PASSWORD") or os.environ.get("WP_APP_PASSWORD") or "").replace(" ", "")
    return site, user, password


def auth_headers(user: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return {
        "User-Agent": UA,
        "Authorization": f"Basic {token}",
        "X-WP-Authorization": f"Basic {token}",
    }


def find_source_png() -> Path:
    for path in SRC_PNG_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError("Kaynak PNG bulunamadı")


def convert_webp() -> bytes:
    src = find_source_png()
    image = Image.open(src).convert("RGBA")
    if image.size != (1024, 219):
        print(f"WARN: kaynak boyut {image.size}, beklenen 1024x219")
    buf = io.BytesIO()
    image.save(buf, format="WEBP", lossless=True, method=6, exact=True)
    data = buf.getvalue()
    LOCAL_WEBP.write_bytes(data)
    print(f"webp_bytes={len(data)} size={image.size} src={src.name}")
    return data


def login(site: str, user: str, password: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    session.get(f"{site}/wp-login.php", timeout=30)
    response = session.post(
        f"{site}/wp-login.php",
        data={
            "log": user,
            "pwd": password,
            "wp-submit": "Log In",
            "redirect_to": f"{site}/wp-admin/",
            "testcookie": "1",
        },
        timeout=30,
        allow_redirects=True,
    )
    if "wp-admin" not in response.url:
        raise RuntimeError("wp-login başarısız")
    return session


def upload_media(site: str, user: str, password: str, webp: bytes) -> str:
    headers = auth_headers(user, password)
    existing = requests.get(
        f"{site}/wp-json/wp/v2/media",
        params={"search": "ledajans-ust-menu-logo", "per_page": 10},
        auth=(user, password),
        headers=headers,
        timeout=30,
    )
    if existing.status_code == 200:
        for item in existing.json():
            url = str(item.get("source_url") or "")
            if url.endswith(FILENAME) or FILENAME.replace(".webp", "") in url:
                print(f"media_reuse id={item.get('id')}")
                return url
    response = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=(user, password),
        headers={
            **headers,
            "Content-Disposition": f'attachment; filename="{FILENAME}"',
        },
        files={"file": (FILENAME, webp, "image/webp")},
        timeout=120,
    )
    print(f"media_upload={response.status_code}")
    if response.status_code not in (200, 201):
        raise RuntimeError(f"media upload failed: {response.text[:240]}")
    url = response.json().get("source_url") or ""
    if not url:
        raise RuntimeError("media source_url yok")
    print("media_new=1")
    return url


def patch_header_html(html: str, new_url: str) -> tuple[str, int]:
    changed = 0
    updated = html
    for name in OLD_LOGO_FILES:
        pattern = re.compile(rf"https?://[^\"'\s]+/{re.escape(name)}")
        updated, n = pattern.subn(new_url, updated)
        changed += n
        if name in updated:
            count = updated.count(name)
            updated = updated.replace(name, Path(new_url).name)
            changed += count
    if INVERT_OLD in updated:
        updated = updated.replace(INVERT_OLD, INVERT_NEW)
        changed += 1
    srcset_bit = f'srcset="{new_url} 1024w"'
    img_old = re.compile(
        r'<img([^>]*?)src="' + re.escape(new_url) + r'"([^>]*?)>',
        re.I,
    )

    def add_srcset(match: re.Match[str]) -> str:
        before, after = match.group(1), match.group(2)
        if "srcset=" in before or "srcset=" in after:
            return match.group(0)
        return f'<img{before}src="{new_url}" {srcset_bit} width="1024" height="219"{after}>'

    updated, n = img_old.subn(add_srcset, updated)
    changed += n
    if 'id="ledajans-header-logo-src"' not in updated:
        script = (
            '<script id="ledajans-header-logo-src">\n'
            "(function () {\n"
            f'  var url = "{new_url}";\n'
            "  function apply(img) {\n"
            "    if (!img) return;\n"
            "    img.src = url;\n"
            '    img.setAttribute("srcset", url + " 1024w");\n'
            '    img.removeAttribute("data-src");\n'
            '    img.removeAttribute("data-lazy-src");\n'
            '    img.removeAttribute("data-srcset");\n'
            "  }\n"
            "  function run() {\n"
            '    document.querySelectorAll(".elementor-element-123bc72 .site-branding-logo img, .elementor-element-123bc72 .elementor-widget-gva-logo img").forEach(apply);\n'
            '    document.querySelectorAll(".canvas-mobile .top-canvas .logo-mm img").forEach(apply);\n'
            "  }\n"
            '  if (document.readyState === "loading") {\n'
            '    document.addEventListener("DOMContentLoaded", run);\n'
            "  } else { run(); }\n"
            "})();\n"
            "</script>\n"
        )
        marker = '<script id="ledajans-header-glass-scroll">'
        if marker in updated:
            updated = updated.replace(marker, script + marker, 1)
        else:
            updated += "\n" + script
        changed += 1
    else:
        updated = re.sub(
            r'(<script id="ledajans-header-logo-src">[\s\S]*?var url = ")[^"]+(")',
            rf"\1{new_url}\2",
            updated,
            count=1,
        )
    return updated, changed


def walk_patch(nodes: Any, new_url: str) -> int:
    changed = 0
    if isinstance(nodes, list):
        for node in nodes:
            changed += walk_patch(node, new_url)
        return changed
    if not isinstance(nodes, dict):
        return 0
    settings = nodes.get("settings")
    if isinstance(settings, dict) and str(nodes.get("id") or "") == WIDGET_ID:
        html = settings.get("html")
        if isinstance(html, str):
            patched, n = patch_header_html(html, new_url)
            if n:
                settings["html"] = patched
                nodes["settings"] = settings
                changed += n
        if "htmlCache" in nodes:
            nodes.pop("htmlCache", None)
    for key in ("elements", "content"):
        if key in nodes:
            changed += walk_patch(nodes[key], new_url)
    return changed


def slim_elements(nodes: Any) -> Any:
    if isinstance(nodes, list):
        return [slim_elements(node) for node in nodes]
    if not isinstance(nodes, dict):
        return nodes
    keep = {}
    for key in ("id", "elType", "widgetType", "isInner", "settings", "elements"):
        if key in nodes:
            keep[key] = nodes[key]
    if "elements" in keep:
        keep["elements"] = slim_elements(keep["elements"])
    return keep


def load_elementor_document(session: requests.Session, site: str) -> tuple[list[Any], str]:
    editor = session.get(
        f"{site}/wp-admin/post.php?post={HEADER_ID}&action=elementor",
        timeout=90,
    )
    if editor.status_code != 200:
        raise RuntimeError(f"elementor editor {editor.status_code}")
    match = re.search(r"var ElementorConfig = (\{.*?\})\s*;\s*\n", editor.text, re.S)
    if not match:
        raise RuntimeError("ElementorConfig yok")
    config = json.loads(match.group(1))
    elements = (config.get("initial_document") or {}).get("elements")
    if not isinstance(elements, list):
        raise RuntimeError("header elements yok")
    common = re.search(r"var elementorCommonConfig = (\{.*?\})\s*;\s*\n", editor.text, re.S)
    if not common:
        raise RuntimeError("elementorCommonConfig yok")
    nonce = json.loads(common.group(1)).get("ajax", {}).get("nonce") or ""
    if not nonce:
        raise RuntimeError("elementor ajax nonce yok")
    return elements, nonce


def save_builder(session: requests.Session, site: str, nonce: str, elements: list[Any]) -> requests.Response:
    payload = {
        "action": "elementor_ajax",
        "_nonce": nonce,
        "editor_post_id": str(HEADER_ID),
        "initial_document_id": str(HEADER_ID),
        "actions": json.dumps(
            {
                "save_builder": {
                    "action": "save_builder",
                    "data": {
                        "status": "publish",
                        "elements": slim_elements(elements),
                    },
                }
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    return session.post(f"{site}/wp-admin/admin-ajax.php", data=payload, timeout=120)


def clear_elementor_cache(session: requests.Session, site: str) -> None:
    tools = session.get(f"{site}/wp-admin/admin.php?page=elementor-tools", timeout=30).text
    nonce = None
    for pat in (
        r'id="elementor-clear-cache-button"[^>]*data-nonce="([^"]+)"',
        r'data-nonce="([^"]+)"[^>]*id="elementor-clear-cache-button"',
    ):
        match = re.search(pat, tools)
        if match:
            nonce = match.group(1)
            break
    if not nonce:
        print("WARN: elementor cache nonce yok")
        return
    response = session.post(
        f"{site}/wp-admin/admin-ajax.php",
        data={"action": "elementor_clear_cache", "_nonce": nonce},
        timeout=60,
    )
    print(f"elementor_clear_cache={response.status_code}")


def make_plugin_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(PLUGIN_PHP, PLUGIN_SLUG)
    return buf.getvalue()


def install_filter_plugin(session: requests.Session, site: str, user: str, password: str) -> None:
    headers = auth_headers(user, password)
    current = requests.get(
        f"{site}/wp-json/wp/v2/plugins/{REST_PLUGIN}",
        auth=(user, password),
        headers=headers,
        timeout=30,
    )
    if current.status_code == 200 and current.json().get("status") == "active":
        print("filter_plugin=already_active")
        return
    requests.delete(
        f"{site}/wp-json/wp/v2/plugins/{REST_PLUGIN}",
        auth=(user, password),
        headers=headers,
        params={"force": "true"},
        timeout=60,
    )
    page = session.get(f"{site}/wp-admin/plugin-install.php?tab=upload", timeout=30)
    nonce_m = re.search(r'id="_wpnonce" name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce_m:
        nonce_m = re.search(r'name="_wpnonce" value="([^"]+)"', page.text)
    if not nonce_m:
        print("WARN: plugin upload nonce yok")
        return
    upload = session.post(
        f"{site}/wp-admin/update.php?action=upload-plugin",
        data={
            "_wpnonce": nonce_m.group(1),
            "_wp_http_referer": "/wp-admin/plugin-install.php?tab=upload",
            "install-plugin-submit": "Install Now",
        },
        files={"pluginzip": ("ledajans-header-logo-filter.zip", make_plugin_zip(), "application/zip")},
        timeout=120,
        allow_redirects=True,
    )
    print(f"filter_plugin_upload={upload.status_code}")
    activate = requests.post(
        f"{site}/wp-json/wp/v2/plugins/{REST_PLUGIN}",
        json={"status": "active"},
        auth=(user, password),
        headers={**headers, "Content-Type": "application/json"},
        timeout=60,
    )
    print(f"filter_plugin_activate={activate.status_code}")


def purge_cache(site: str) -> None:
    try:
        response = requests.get(
            f"{site}/?LSCWP_CTRL=purge&litespeed_type=purge_all",
            headers={"User-Agent": UA, "Cache-Control": "no-cache"},
            timeout=20,
        )
        print(f"litespeed_purge={response.status_code}")
    except requests.RequestException as exc:
        print(f"WARN: purge {exc}")


def verify_live(site: str, new_url: str) -> int:
    response = requests.get(
        site + "/",
        headers={"User-Agent": UA, "Cache-Control": "no-cache", "Pragma": "no-cache"},
        timeout=45,
    )
    html = response.text
    print(f"verify_home={response.status_code} len={len(html)}")
    print(f"verify_new_url={html.count(new_url)}")
    print(f"verify_logo_scaled={html.count('logo-scaled.png')}")
    print(f"verify_invert={html.count(INVERT_OLD)}")
    print(f"verify_widget={html.count(WIDGET_ID)}")
    print(f"verify_hero_logo={html.count('2026/09/ledajans-logo.webp')}")
    branding = html.find("site-branding-logo")
    if branding >= 0:
        snippet = html[branding : branding + 800]
        print(f"verify_branding_has_new={new_url in snippet or Path(new_url).name in snippet}")
    return 0 if html.count(new_url) > 0 and html.count("ledajans-logo.webp") >= 1 else 2


def main() -> int:
    dry = "--dry-run" in sys.argv
    site, user, password = load_env()
    if not site or not user or not password:
        print("HATA: WP_SITE_URL / WP_USERNAME / WP_APP_PASSWORD gerekli")
        return 1
    webp = convert_webp()
    print(f"local_html={HEADER_HTML.is_file()} invert_repo={INVERT_OLD in HEADER_HTML.read_text(encoding='utf-8')}")
    if dry:
        print("DRY_RUN: medya/header yazılmadı")
        print(f"will_update_widget={WIDGET_ID} header_id={HEADER_ID}")
        print(f"will_replace={','.join(OLD_LOGO_FILES)}")
        return 0

    new_url = upload_media(site, user, password, webp)
    print("new_url_ok=1")
    session = login(site, user, password)
    elements, nonce = load_elementor_document(session, site)
    patched = walk_patch(elements, new_url)
    print(f"widget_patches={patched}")
    if patched == 0:
        print("HATA: header widget içinde logo/invert değişmedi")
        return 2
    saved = save_builder(session, site, nonce, elements)
    print(f"save_builder={saved.status_code} body={saved.text[:240].replace(chr(10), ' ')}")
    if saved.status_code != 200:
        return 1
    try:
        body = saved.json()
        success = (((body.get("data") or {}).get("responses") or {}).get("save_builder") or {}).get("success")
        print(f"save_success={success}")
        if success is False:
            print(json.dumps(body, ensure_ascii=False)[:400])
            return 1
    except ValueError:
        print("WARN: save_builder JSON değil")
    install_filter_plugin(session, site, user, password)
    clear_elementor_cache(session, site)
    purge_cache(site)
    return verify_live(site, new_url)


if __name__ == "__main__":
    sys.exit(main())
