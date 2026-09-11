#!/usr/bin/env python3
"""Ust menu turuncu bar + kullanici logosu (media + Elementor snippet)."""
from __future__ import annotations

import io
import json
import sys
import time
import xmlrpc.client
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_LOGO = Path(
    r"C:\Users\kacma\.cursor\projects\c-Users-kacma-Desktop-Ledajans-SourceCode\assets"
    r"\c__Users_kacma_AppData_Roaming_Cursor_User_workspaceStorage_7dfb9ce5533c561a018b26f3b896825b_images_Ba_l_ks_z__1_-111cf095-7104-409f-b95f-e1ddfb01a41a.png"
)
LOCAL_WEBP = ROOT / "Ust-Menu" / "ledajans-logo-white.webp"
LOCAL_PNG = ROOT / "Ust-Menu" / "ledajans-logo-white.png"
SNIPPET_SLUG = "ledajans-header-2026"
FOOTER_SLUG = "ledajans-footer-2026"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-Check"
BACKUP_DIR = ROOT / "AGENT-HUB" / "BACKUPS"


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


def prepare_logo() -> tuple[bytes, bytes]:
    img = Image.open(SRC_LOGO).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        pad = 4
        l, t, r, b = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        r = min(img.width, r + pad)
        b = min(img.height, b + pad)
        img = img.crop((l, t, r, b))
    png_buf = io.BytesIO()
    img.save(png_buf, format="PNG", optimize=True)
    png = png_buf.getvalue()
    webp_buf = io.BytesIO()
    img.save(webp_buf, format="WEBP", quality=90, method=6, lossless=True)
    webp = webp_buf.getvalue()
    LOCAL_PNG.write_bytes(png)
    LOCAL_WEBP.write_bytes(webp)
    print("logo", img.size, "png", len(png), "webp", len(webp))
    return png, webp


def snippet_code(logo_url: str) -> str:
    return f"""<style id="ledajans-header-orange-css">
header.wp-site-header,
.wp-site-header,
.header-builder-frontend,
.elementor-element-a231664,
.elementor-element-123bc72,
.elementor-element-123bc72.gv-sticky-menu,
.gv-sticky-menu {{
  background: #F46F2C !important;
  background-color: #F46F2C !important;
}}
.elementor-element-123bc72 .gva-main-menu > li > a,
.elementor-element-123bc72 .gva-main-menu > li > a .menu-title,
.elementor-element-123bc72 .gva-main-menu > li > a .caret {{
  color: #fff !important;
}}
.elementor-element-123bc72 .site-branding-logo img,
.elementor-element-123bc72 .elementor-widget-gva-logo img,
.canvas-mobile .top-canvas .logo-mm img,
img.ledajans-footer-logo {{
  filter: none !important;
  opacity: 1 !important;
  visibility: visible !important;
  display: inline-block !important;
}}
@media (min-width: 1025px) {{
  html body .elementor-element-123bc72.gv-sticky-menu,
  html body section.elementor-element-123bc72.gv-sticky-menu {{
    min-height: 76px !important;
    max-height: 80px !important;
    height: 76px !important;
    padding: 0 !important;
    overflow: visible !important;
    box-sizing: border-box !important;
  }}
  html body .elementor-element-123bc72.gv-sticky-menu > .elementor-container,
  html body .elementor-element-123bc72 > .elementor-container {{
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    min-height: 76px !important;
    max-height: 80px !important;
    height: 76px !important;
    padding: 0 16px 0 8px !important;
    position: relative !important;
    overflow: visible !important;
    box-sizing: border-box !important;
  }}
  html body .elementor-element-123bc72 > .elementor-container > .elementor-row {{
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    width: 100% !important;
    min-height: 76px !important;
    max-height: 80px !important;
  }}
  html body .elementor-element-123bc72 > .elementor-container > .elementor-column.elementor-element-aa903d8,
  html body .elementor-element-123bc72 > .elementor-container > .elementor-column.elementor-col-50.elementor-element-aa903d8 {{
    flex: 0 0 auto !important;
    width: auto !important;
    max-width: 168px !important;
    position: relative !important;
  }}
  html body .elementor-element-123bc72 > .elementor-container > .elementor-column.elementor-element-0b7eb5f,
  html body .elementor-element-123bc72 > .elementor-container > .elementor-column.elementor-col-50.elementor-element-0b7eb5f {{
    flex: 1 1 auto !important;
    width: auto !important;
    max-width: none !important;
    min-width: 0 !important;
    position: relative !important;
  }}
  html body .elementor-element-123bc72 .elementor-element-aa903d8,
  html body .elementor-element-123bc72 .elementor-element-0b7eb5f {{
    position: relative !important;
  }}
  html body .elementor-element-123bc72 .elementor-element-aa903d8 > .elementor-widget-wrap,
  html body .elementor-element-123bc72 .elementor-element-0b7eb5f > .elementor-widget-wrap {{
    position: relative !important;
    overflow: visible !important;
    min-height: 76px !important;
    max-height: 80px !important;
    padding: 0 !important;
    margin: 0 !important;
  }}
  html body .elementor-element-aa903d8 > .elementor-widget-wrap {{
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    align-content: center !important;
    justify-content: center !important;
    min-height: 76px !important;
    height: 76px !important;
  }}
  html body .elementor-element-aa903d8 .elementor-widget-gva-logo,
  html body .elementor-element-aa903d8 .elementor-widget-container,
  html body .elementor-element-aa903d8 .gva-element-gva-logo,
  html body .elementor-element-aa903d8 .gsc-logo,
  html body .elementor-element-123bc72 .site-branding-logo {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    width: 100% !important;
    height: 76px !important;
  }}
  html body .elementor-element-0b7eb5f > .elementor-widget-wrap {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 12px !important;
    width: 100% !important;
  }}
  html body .elementor-element-123bc72 .elementor-element-548f702,
  html body .elementor-element-123bc72 .elementor-element-548f702.elementor-widget {{
    position: relative !important;
    left: auto !important;
    right: auto !important;
    top: auto !important;
    bottom: auto !important;
    transform: none !important;
    -webkit-transform: none !important;
    flex: 1 1 auto !important;
    width: auto !important;
    max-width: none !important;
    min-width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
  }}
  html body .elementor-element-123bc72 .elementor-element-548f702 .elementor-widget-container {{
    padding: 0 !important;
    overflow: visible !important;
  }}
  html body .elementor-element-0b7eb5f .elementor-element-b34583d {{
    flex: 0 0 auto !important;
    flex-shrink: 0 !important;
    width: auto !important;
    margin-left: 0 !important;
    padding: 0 !important;
    position: relative !important;
    z-index: 6 !important;
  }}
  html body .elementor-element-123bc72 .elementor-element-b34583d .elementor-widget-container,
  html body .elementor-element-123bc72 .elementor-element-fe10ed3 .elementor-widget-container {{
    padding: 0 !important;
    margin: 0 !important;
  }}
  html body .elementor-element-123bc72 .site-branding-logo {{
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }}
  html body .elementor-element-123bc72 .site-branding-logo img,
  html body .elementor-element-123bc72 .elementor-widget-gva-logo img {{
    height: 32px !important;
    width: auto !important;
    max-width: 160px !important;
    object-fit: contain !important;
    flex-shrink: 0 !important;
  }}
  html body #menu-anamenu-desktop,
  html body .elementor-element-548f702 .gva-main-menu,
  html body .elementor-element-123bc72 .gva-navigation-menu .gva-main-menu {{
    display: flex !important;
    flex-wrap: nowrap !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    height: 76px !important;
    row-gap: 0 !important;
    margin: 0 !important;
  }}
  html body .elementor-element-123bc72 .gva-main-menu > li {{
    display: flex !important;
    align-items: center !important;
    height: 76px !important;
    max-height: 76px !important;
    padding: 0 4px !important;
    margin: 0 !important;
  }}
  html body .elementor-element-123bc72 .gva-main-menu > li > a {{
    display: inline-flex !important;
    align-items: center !important;
    white-space: nowrap !important;
    padding: 0 0.35rem !important;
    line-height: 1.2 !important;
    font-size: 0.8125rem !important;
  }}
  html body .elementor-element-123bc72 .ledajans-header-phones,
  html body .ledajans-header-phones {{
    flex-shrink: 0 !important;
    padding-right: 4px !important;
    gap: 0.2rem !important;
  }}
  html body .elementor-element-123bc72 .ledajans-header-phone-row {{
    font-size: 0.875rem !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    display: flex !important;
    align-items: center !important;
  }}
}}
@media (min-width: 1025px) and (max-width: 1440px) {{
  html body .elementor-element-123bc72 .gva-main-menu > li {{
    padding: 0 2px !important;
  }}
  html body .elementor-element-123bc72 .gva-main-menu > li > a {{
    padding: 0 0.22rem !important;
    font-size: 0.75rem !important;
  }}
  html body .elementor-element-123bc72 .ledajans-header-phone-row {{
    font-size: 0.75rem !important;
  }}
}}
@media (max-width: 1024px) {{
  .elementor-element-123bc72 .site-branding-logo img,
  .elementor-element-123bc72 .elementor-widget-gva-logo img {{
    height: 26px !important;
    max-width: min(68vw, 240px) !important;
  }}
}}
</style>
<script id="ledajans-logo-swap">
(function () {{
  var NEW = {logo_url!r};
  var re = /LedajansLogo|ledajans-logo|leadajans-logo/i;
  function swap(root) {{
    (root || document).querySelectorAll("img").forEach(function (img) {{
      var s = img.getAttribute("src") || "";
      var hit = re.test(s) || img.classList.contains("ledajans-footer-logo")
        || img.closest(".site-branding-logo, .gsc-logo, .logo-mm");
      if (hit && s !== NEW) img.setAttribute("src", NEW);
    }});
  }}
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", function () {{ swap(document); }});
  }} else {{
    swap(document);
  }}
}})();
</script>
"""


def upsert_snippet(
    site: str,
    auth: tuple[str, str],
    headers: dict,
    user: str,
    pw: str,
    slug: str,
    title: str,
    location: str,
    code: str,
) -> int:
    r = requests.get(
        f"{site}/wp-json/wp/v2/elementor_snippet",
        params={"slug": slug, "context": "edit", "per_page": 20},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    existing = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    payload = {
        "title": title,
        "slug": slug,
        "status": "publish",
        "meta": {
            "_elementor_location": location,
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
        print("snippet_update", slug, sid, ru.status_code, location, (ru.text or "")[:160].replace("\n", " "))
    else:
        ru = requests.post(
            f"{site}/wp-json/wp/v2/elementor_snippet",
            json=payload,
            auth=auth,
            headers=headers,
            timeout=180,
        )
        print("snippet_create", slug, ru.status_code, (ru.text or "")[:160].replace("\n", " "))
        if ru.status_code not in (200, 201):
            return 0
        sid = ru.json().get("id")
    if not sid:
        return 0
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
        print("conditions_ok", slug, sid)
    except Exception as exc:
        print("conditions_err", slug, type(exc).__name__, str(exc)[:160])
    return int(sid)


def patch_footer_logo(site: str, auth: tuple[str, str], headers: dict, new_url: str) -> None:
    r = requests.get(
        f"{site}/wp-json/wp/v2/elementor_snippet",
        params={"slug": FOOTER_SLUG, "context": "edit", "per_page": 5},
        auth=auth,
        headers={"User-Agent": UA},
        timeout=60,
    )
    items = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
    if not items:
        print("footer_snippet_missing")
        return
    sid = items[0]["id"]
    code = ((items[0].get("meta") or {}).get("_elementor_code")) or ""
    old = "https://ledajans.com/wp-content/uploads/2026/02/ledajans-logo.png"
    if old in code:
        code = code.replace(old, new_url)
    elif "ledajans-footer-logo" in code and new_url not in code:
        code = code.replace(
            'src="https://ledajans.com/wp-content/uploads/2026/02/ledajans-logo.png"',
            f'src="{new_url}"',
        )
    ru = requests.post(
        f"{site}/wp-json/wp/v2/elementor_snippet/{sid}",
        json={"meta": {"_elementor_code": code}},
        auth=auth,
        headers=headers,
        timeout=180,
    )
    print("footer_logo_patch", ru.status_code, old in (items[0].get("meta") or {}).get("_elementor_code", ""))


def verify_header(site: str, new_url: str) -> dict:
    live2 = requests.get(
        site + "/?nocache=" + str(int(time.time())),
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    ct = requests.get(new_url, headers={"User-Agent": UA}, timeout=30).headers.get("content-type", "")
    snippet_idx = live2.find('id="ledajans-header-orange-css"')
    widget_idx = live2.find('id="ledajans-header-responsive-css"')
    snippet_block = live2[snippet_idx : snippet_idx + 12000] if snippet_idx >= 0 else ""
    layout_sel = "html body .elementor-element-123bc72 .elementor-element-548f702"
    checks = {
        "snippet_css": "ledajans-header-orange-css" in live2,
        "logo_swap": "ledajans-logo-swap" in live2,
        "logo_url_in_page": new_url in live2,
        "layout_override": layout_sel in snippet_block
        and "position: relative !important" in snippet_block,
        "height_76": "min-height: 76px !important" in snippet_block
        and "max-height: 80px !important" in snippet_block,
        "snippet_after_widget": snippet_idx > widget_idx >= 0,
        "body_end": snippet_idx > 0 and snippet_idx > widget_idx,
        "logo_ct": ct,
        "logo_wrap_center": "html body .elementor-element-aa903d8 > .elementor-widget-wrap" in snippet_block
        and "align-items: center !important" in snippet_block
        and "justify-content: center !important" in snippet_block,
        "menu_center": "html body #menu-anamenu-desktop" in snippet_block
        and "justify-content: center !important" in snippet_block,
        "snippet_idx": snippet_idx,
        "widget_idx": widget_idx,
    }
    print("verify", checks)
    return checks

def clear_elementor_cache(site: str, auth: tuple[str, str], headers: dict) -> None:
    rc = requests.delete(
        f"{site}/wp-json/elementor/v1/cache",
        auth=auth,
        headers=headers,
        timeout=60,
    )
    print("elementor_cache", rc.status_code)


def main() -> int:
    apply = "--apply" in sys.argv
    layout_only = "--layout-only" in sys.argv or "--snippet-only" in sys.argv
    site, user, pw = load_env()
    auth = (user, pw)
    headers = {"User-Agent": UA, "Content-Type": "application/json"}

    live = requests.get(
        site + "/",
        headers={"User-Agent": UA, "Cache-Control": "no-cache"},
        timeout=45,
    ).text
    print("live_header_css_id", "ledajans-header-orange-css" in live)
    print("live_broken_webp", "LedajansLogo.webp" in live)

    if layout_only:
        logo_meta = json.loads((BACKUP_DIR / "2026-09-11-header-logo.json").read_text(encoding="utf-8"))
        new_url = logo_meta["url"]
        print("layout_only logo", new_url)
        if not apply:
            print("DRY_RUN: yazilmadi")
            return 0
        sid = upsert_snippet(
            site,
            auth,
            headers,
            user,
            pw,
            SNIPPET_SLUG,
            "LEDAJANS Header Orange + Logo",
            "elementor_body_end",
            snippet_code(new_url),
        )
        if not sid:
            return 1
        clear_elementor_cache(site, auth, headers)
        time.sleep(2)
        checks = verify_header(site, new_url)
        ok = (
            checks["snippet_css"]
            and checks["layout_override"]
            and checks["height_76"]
            and checks["snippet_after_widget"]
            and checks["logo_wrap_center"]
            and checks["menu_center"]
        )
        return 0 if ok else 2

    png, webp = prepare_logo()

    if not apply:
        print("DRY_RUN: yazilmadi")
        return 0

    up = requests.post(
        f"{site}/wp-json/wp/v2/media",
        auth=auth,
        headers={
            "User-Agent": UA,
            "Content-Disposition": 'attachment; filename="ledajans-logo-white.webp"',
        },
        files={"file": ("ledajans-logo-white.webp", webp, "image/webp")},
        timeout=120,
    )
    print("media", up.status_code, (up.text or "")[:220].replace("\n", " "))
    if up.status_code not in (200, 201):
        up = requests.post(
            f"{site}/wp-json/wp/v2/media",
            auth=auth,
            headers={
                "User-Agent": UA,
                "Content-Disposition": 'attachment; filename="ledajans-logo-white.png"',
            },
            files={"file": ("ledajans-logo-white.png", png, "image/png")},
            timeout=120,
        )
        print("media_png", up.status_code, (up.text or "")[:220].replace("\n", " "))
        if up.status_code not in (200, 201):
            return 1
    new_url = up.json().get("source_url")
    print("logo_url", new_url)
    if not new_url:
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / "2026-09-11-header-logo.json").write_text(
        json.dumps({"url": new_url, "id": up.json().get("id")}, indent=2),
        encoding="utf-8",
    )

    sid = upsert_snippet(
        site,
        auth,
        headers,
        user,
        pw,
        SNIPPET_SLUG,
        "LEDAJANS Header Orange + Logo",
        "elementor_body_end",
        snippet_code(new_url),
    )
    if not sid:
        return 1

    patch_footer_logo(site, auth, headers, new_url)

    footer_path = ROOT / "Footer" / "footer.html"
    ft = footer_path.read_text(encoding="utf-8")
    ft2 = ft.replace(
        "https://ledajans.com/wp-content/uploads/2026/02/ledajans-logo.png",
        new_url,
    )
    if ft2 != ft:
        footer_path.write_text(ft2, encoding="utf-8")
        print("local_footer_logo_updated")

    menu_path = ROOT / "Ust-Menu" / "ust-menu.html"
    mt = menu_path.read_text(encoding="utf-8")
    mt2 = mt.replace(
        "https://ledajans.com/wp-content/uploads/2026/08/LedajansLogo.webp",
        new_url,
    ).replace(
        "https://ledajans.com/wp-content/uploads/2022/12/LedajansLogo.png",
        new_url,
    )
    desktop_orange = """    @media only screen and (min-width: 1025px) {
      .wp-site-header,
      header.wp-site-header,
      .elementor-element-a231664,
      .elementor-element-123bc72,
      .elementor-element-123bc72.gv-sticky-menu {
        background: #F46F2C !important;
        background-color: #F46F2C !important;
      }
      .elementor-element-123bc72 .gva-main-menu > li > a,
      .elementor-element-123bc72 .gva-main-menu > li > a .menu-title {
        color: #fff !important;
      }
"""
    if "background: #F46F2C !important;\n        background-color: #F46F2C !important;" not in mt2:
        mt2 = mt2.replace(
            "    @media only screen and (min-width: 1025px) {\n      .elementor-element-123bc72.gv-sticky-menu {",
            desktop_orange + "      .elementor-element-123bc72.gv-sticky-menu {",
            1,
        )
    mt2 = mt2.replace(
        "        filter: brightness(0) invert(1) !important;\n",
        "        filter: none !important;\n",
    )
    if mt2 != mt:
        menu_path.write_text(mt2, encoding="utf-8")
        print("local_ust_menu_updated")

    clear_elementor_cache(site, auth, headers)

    time.sleep(2)
    checks = verify_header(site, new_url)
    return 0 if checks["snippet_css"] and "image/" in checks["logo_ct"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
